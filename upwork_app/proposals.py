from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from upwork_app.graphql_client import UpworkGraphQLClient
from upwork_app.queries import Q_VENDOR_PROPOSALS_PAGED, Q_VENDOR_PROPOSALS_SNAPSHOT

DEFAULT_STATUSES = ["Archived", "Declined", "Withdrawn", "Hired"]


def rows_from_edges(edges: list[dict[str, Any]], pulled_stream: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge in edges:
        node = edge.get("node") or {}
        cover = node.get("proposalCoverLetter") or ""
        rows.append(
            {
                "proposal_id": node.get("id"),
                "job_id": (node.get("marketplaceJobPosting") or {}).get("id"),
                "status": (node.get("status") or {}).get("status"),
                "cover_letter": cover,
                "cover_letter_len": len(cover),
                "pulled_from_status_filter": pulled_stream,
                "edge_cursor": edge.get("cursor"),
            }
        )
    return rows


def collect_stream(
    client: UpworkGraphQLClient,
    first_n: int,
    stream_name: str,
    base_variables: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    cursor: Optional[str] = None
    page_num = 0

    while True:
        page_num += 1
        pagination: dict[str, Any] = {"first": first_n}
        if cursor:
            pagination["after"] = cursor

        variables = {**base_variables, "pagination": pagination}

        try:
            output = client.gql(Q_VENDOR_PROPOSALS_PAGED, variables=variables)
        except RuntimeError as exc:
            if page_num == 1:
                output = client.gql(
                    Q_VENDOR_PROPOSALS_SNAPSHOT,
                    variables={**base_variables, "pagination": {"first": first_n}},
                )
                edges = output["vendorProposals"].get("edges") or []
                rows.extend(rows_from_edges(edges, pulled_stream=stream_name))
                print(
                    f"{stream_name}: pulled {len(edges)} snapshot rows only "
                    "(pagination scope unavailable)."
                )
                return rows, False
            raise RuntimeError(
                f"Pagination failed for stream={stream_name}. Upwork error payload: {exc}"
            ) from exc

        proposals = output["vendorProposals"]
        edges = proposals.get("edges") or []
        rows.extend(rows_from_edges(edges, pulled_stream=stream_name))

        page_info = proposals.get("pageInfo") or {}
        has_next = bool(page_info.get("hasNextPage"))
        end_cursor = page_info.get("endCursor")
        edge_cursor = edges[-1].get("cursor") if edges else None

        cursor = end_cursor or edge_cursor

        print(f"{stream_name}: page {page_num} pulled {len(edges)} (total {len(rows)})")

        if not has_next or not cursor:
            return rows, True


def fetch_bids(
    client: UpworkGraphQLClient,
    first_n: int,
    statuses: list[str],
    include_all_statuses: bool,
    augment_status_fallback: bool,
) -> pd.DataFrame:
    all_rows: list[dict[str, Any]] = []

    if include_all_statuses:
        try:
            rows, paged = collect_stream(
                client=client,
                first_n=first_n,
                stream_name="ALL",
                base_variables={
                    "filter": {},
                    "sort": {"field": "MODIFIEDDATETIME", "sortOrder": "DESC"},
                },
            )
            all_rows.extend(rows)
            print(f"ALL: finished with {len(rows)} rows via {'cursor paging' if paged else 'single snapshot'}")
        except Exception as exc:  # noqa: BLE001
            print(f"ALL stream failed, falling back to per-status streams: {exc}")

    should_run_status_fallback = (not include_all_statuses) or (not all_rows) or augment_status_fallback

    if should_run_status_fallback:
        for status in statuses:
            rows, paged = collect_stream(
                client=client,
                first_n=first_n,
                stream_name=status,
                base_variables={
                    "filter": {"status_eq": status},
                    "sort": {"field": "MODIFIEDDATETIME", "sortOrder": "DESC"},
                },
            )
            all_rows.extend(rows)
            print(f"{status}: finished with {len(rows)} rows via {'cursor paging' if paged else 'single snapshot'}")

    bids_raw = pd.DataFrame(all_rows)
    if bids_raw.empty:
        return bids_raw

    pulled_counts = bids_raw["pulled_from_status_filter"].fillna("UNKNOWN").value_counts().to_dict()
    actual_status_counts = bids_raw["status"].fillna("UNKNOWN").value_counts().to_dict()

    print("Raw rows by stream:")
    for key in sorted(pulled_counts):
        print(f"  - {key}: {pulled_counts[key]}")

    print("Raw rows by proposal.status:")
    for key in sorted(actual_status_counts):
        print(f"  - {key}: {actual_status_counts[key]}")

    bids = (
        bids_raw.sort_values("cover_letter_len", ascending=False)
        .drop_duplicates(subset=["proposal_id"], keep="first")
        .reset_index(drop=True)
    )

    print(f"Total rows before dedupe: {len(bids_raw)}")
    print(f"Unique proposals after dedupe: {len(bids)}")
    print(f"Non-empty cover letters: {(bids['cover_letter_len'] > 0).sum()}")

    return bids
