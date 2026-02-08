from __future__ import annotations

from typing import Any, Optional

from upwork_app.auth import TokenStore
from upwork_app.config import AppConfig


class UpworkGraphQLClient:
    def __init__(self, config: AppConfig, token_store: TokenStore) -> None:
        self.config = config
        self.token_store = token_store
        self.token_store.load()

    @property
    def access_token(self) -> str:
        return str(self.token_store.tokens["access_token"])

    @property
    def refresh_token(self) -> str:
        return str(self.token_store.tokens["refresh_token"])

    def refresh_access_token(self) -> None:
        import requests

        response = requests.post(
            self.config.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "refresh_token": self.refresh_token,
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        self.token_store.update_from_refresh_response(response.json())

    def gql(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> dict[str, Any]:
        import requests

        if self.token_store.access_token_expired():
            self.refresh_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload: dict[str, Any] = {"query": query, "variables": variables or {}}
        if operation_name:
            payload["operationName"] = operation_name

        response = requests.post(self.config.graphql_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.post(self.config.graphql_url, headers=headers, json=payload, timeout=30)

        response.raise_for_status()
        body = response.json()
        if "errors" in body:
            raise RuntimeError(body["errors"])

        return body["data"]
