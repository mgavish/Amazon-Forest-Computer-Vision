#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

from upwork_app.auth import TokenStore
from upwork_app.config import load_config
from upwork_app.graphql_client import UpworkGraphQLClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Upwork OAuth token and save it.")
    parser.add_argument("--tokens-path", default="upwork_tokens.json")
    parser.add_argument("--force", action="store_true", help="Refresh even if access token is not expired")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = load_config(tokens_path=args.tokens_path)
    store = TokenStore(config.tokens_path)
    client = UpworkGraphQLClient(config=config, token_store=store)

    if not args.force and not store.access_token_expired():
        print("Access token is still valid. Skipping refresh (use --force to override).")
        return

    client.refresh_access_token()

    saved_at = int(store.tokens.get("saved_at", 0))
    expires_in = int(store.tokens.get("expires_in", 0))
    expires_at = datetime.fromtimestamp(saved_at + expires_in, tz=timezone.utc)

    print("✅ Token refreshed and saved.")
    print(f"saved_at: {saved_at}")
    print(f"expires_in: {expires_in}")
    print(f"expires_at_utc: {expires_at.isoformat()}")


if __name__ == "__main__":
    main()
