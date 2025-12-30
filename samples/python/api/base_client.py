"""Base client for API authentication with OAuth2."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BaseOAuthClient:
    """Base class for API clients with OAuth2 authentication."""

    base_url: str = field(
        default_factory=lambda: os.getenv("PLATFORM_BASE_URL") or "https://api.gonitro.dev"
    )
    client_id: str = field(default_factory=lambda: os.getenv("PLATFORM_CLIENT_ID") or "")
    client_secret: str = field(
        default_factory=lambda: os.getenv("PLATFORM_CLIENT_SECRET") or ""
    )
    _token: str | None = field(default=None, init=False)
    _token_expiry: float = field(default=0, init=False)

    def _get_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        response = httpx.post(
            f"{self.base_url}/oauth/token",
            json={"clientID": self.client_id, "clientSecret": self.client_secret},
        )
        response.raise_for_status()
        data = response.json()
        token: str = data["accessToken"]
        self._token = token
        self._token_expiry = time.time() + data.get("expiresIn", 3600) - 60
        return token

    def get_token(self) -> str:
        """Public method to get authentication token.

        Returns:
            OAuth2 access token for API authentication.
        """
        return self._get_token()
