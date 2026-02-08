#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pprint import pprint

from upwork_app.auth import TokenStore
from upwork_app.config import load_config
from upwork_app.graphql_client import UpworkGraphQLClient

PROBE_QUERY = """
query Probe($pagination: Pagination!) {
  vendorProposals(
    filter: {}
    sortAttribute: { field: MODIFIEDDATETIME, sortOrder: DESC }
    pagination: $pagination
  ) {
    pageInfo { hasNextPage endCursor }
    edges {
      cursor
      node { id status { status } }
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe Upwork GraphQL pagination/permission visibility.")
    parser.add_argument("--tokens-path", default="upwork_tokens.json")
    parser.add_argument("--first", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = load_config(tokens_path=args.tokens_path)
    client = UpworkGraphQLClient(config=config, token_store=TokenStore(config.tokens_path))

    print("GraphQL ping:", client.gql("{ __typename }"))

    try:
        data = client.gql(PROBE_QUERY, variables={"pagination": {"first": args.first}})
        proposals = data.get("vendorProposals") or {}
        page_info = proposals.get("pageInfo") or {}
        edges = proposals.get("edges") or []

        print("✅ Probe succeeded")
        print("pageInfo:")
        pprint(page_info)
        print("edges returned:", len(edges))
        if edges:
            print("sample edge cursor:", edges[0].get("cursor"))
            print("sample node id:", (edges[0].get("node") or {}).get("id"))
    except Exception as exc:  # noqa: BLE001
        print("❌ Probe failed with error payload:")
        print(exc)


if __name__ == "__main__":
    main()
