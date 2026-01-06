"""Base client for API authentication with OAuth2."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

import httpx
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


TOKEN_EXPIRY_BUFFER_SECONDS = 60


class TokenResponse(BaseModel):
    """OAuth2 token response model."""

    model_config = {"populate_by_name": True}

    access_token: str = Field(alias="accessToken")
    expires_in: int = Field(default=3600, alias="expiresIn")


class _SettingsProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol defining required settings for OAuth clients."""

    platform_client_id: str
    platform_client_secret: str
    platform_base_url: str


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    platform_client_id: str
    platform_client_secret: str
    platform_base_url: str = "https://api.gonitro.dev"


@dataclass
class BaseOAuthClient:
    """Base class for API clients with OAuth2 authentication."""

    _settings: _SettingsProtocol = field(
        default_factory=lambda: Settings()  # type: ignore[reportCallIssue]  # pylint: disable=unnecessary-lambda
    )
    _token: str | None = field(default=None, init=False)
    _token_expiry: float = field(default=0, init=False)
    _client: httpx.Client = field(default_factory=httpx.Client, init=False)

    def _get_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        response = self._client.post(
            f"{self._settings.platform_base_url}/oauth/token",
            json={
                "clientID": self._settings.platform_client_id,
                "clientSecret": self._settings.platform_client_secret,
            },
        )
        response.raise_for_status()

        # Use Pydantic model for type-safe response parsing
        token_data = TokenResponse.model_validate_json(response.content)

        self._token = token_data.access_token
        self._token_expiry = time.time() + token_data.expires_in - TOKEN_EXPIRY_BUFFER_SECONDS
        return token_data.access_token

    def get_token(self) -> str:
        """Public method to get authentication token.

        Returns:
            OAuth2 access token for API authentication.
        """
        return self._get_token()
