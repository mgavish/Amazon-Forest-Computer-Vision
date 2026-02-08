from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    client_id: str
    client_secret: str
    token_url: str
    graphql_url: str
    tokens_path: Path


TOKEN_URL = "https://www.upwork.com/api/v3/oauth2/token"
GRAPHQL_URL = "https://api.upwork.com/graphql"


def load_environment() -> None:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())


def load_config(tokens_path: str | Path = "upwork_tokens.json") -> AppConfig:
    load_environment()

    client_id = os.getenv("UPWORK_CONSUMER_KEY")
    client_secret = os.getenv("UPWORK_CONSUMER_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Missing UPWORK_CONSUMER_KEY / UPWORK_CONSUMER_SECRET in .env")

    return AppConfig(
        client_id=client_id,
        client_secret=client_secret,
        token_url=TOKEN_URL,
        graphql_url=GRAPHQL_URL,
        tokens_path=Path(tokens_path),
    )
