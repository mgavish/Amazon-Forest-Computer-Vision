from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class TokenStore:
    def __init__(self, tokens_path: Path) -> None:
        self.tokens_path = tokens_path
        self.tokens: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        if not self.tokens_path.exists():
            raise FileNotFoundError(f"{self.tokens_path} not found. Re-auth once to create it.")

        self.tokens = json.loads(self.tokens_path.read_text(encoding="utf-8"))
        if not self.tokens.get("access_token") or not self.tokens.get("refresh_token"):
            raise RuntimeError("access_token and refresh_token are required in token file")

        return self.tokens

    def save(self) -> None:
        self.tokens_path.write_text(json.dumps(self.tokens, indent=2), encoding="utf-8")
        try:
            os.chmod(self.tokens_path, 0o600)
        except OSError:
            pass

    def access_token_expired(self, skew_seconds: int = 60) -> bool:
        saved_at = self.tokens.get("saved_at")
        expires_in = self.tokens.get("expires_in")
        if saved_at is None or expires_in is None:
            return True
        return int(time.time()) >= (int(saved_at) + int(expires_in) - skew_seconds)

    def update_from_refresh_response(self, payload: dict[str, Any]) -> None:
        current_refresh = self.tokens.get("refresh_token")
        payload["refresh_token"] = payload.get("refresh_token", current_refresh)
        payload["saved_at"] = int(time.time())

        self.tokens.update(payload)
        self.save()
