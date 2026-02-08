#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full Upwork bids export pipeline.")
    parser.add_argument("--tokens-path", default="upwork_tokens.json")
    parser.add_argument("--out", default="bids_with_job_details_and_skills.csv")
    parser.add_argument("--first", type=int, default=25, help="Rows per page (1..25)")
    parser.add_argument("--statuses", default="Archived,Declined,Withdrawn,Hired")
    parser.add_argument("--all-statuses", dest="all_statuses", action="store_true", default=True)
    parser.add_argument("--no-all-statuses", dest="all_statuses", action="store_false")
    parser.add_argument(
        "--augment-status-fallback",
        dest="augment_status_fallback",
        action="store_true",
        default=True,
        help="Also run per-status streams even when ALL returns rows",
    )
    parser.add_argument(
        "--no-augment-status-fallback",
        dest="augment_status_fallback",
        action="store_false",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from upwork_app.auth import TokenStore
    from upwork_app.config import load_config
    from upwork_app.enrichment import enrich_job_skills, enrich_job_title_desc
    from upwork_app.export import write_csv
    from upwork_app.graphql_client import UpworkGraphQLClient
    from upwork_app.proposals import fetch_bids

    if not 1 <= args.first <= 25:
        raise ValueError("--first must be between 1 and 25")

    statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]
    if not statuses and not args.all_statuses:
        raise ValueError("Provide at least one status or keep --all-statuses enabled")

    config = load_config(tokens_path=args.tokens_path)
    client = UpworkGraphQLClient(config=config, token_store=TokenStore(config.tokens_path))

    print("GraphQL ping:", client.gql("{ __typename }"))

    bids = fetch_bids(
        client=client,
        first_n=args.first,
        statuses=statuses,
        include_all_statuses=args.all_statuses,
        augment_status_fallback=args.augment_status_fallback,
    )
    bids_jobs = enrich_job_title_desc(client, bids)
    final_df = enrich_job_skills(client, bids_jobs)
    write_csv(final_df, args.out)


if __name__ == "__main__":
    main()
