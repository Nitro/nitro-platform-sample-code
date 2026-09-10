"""Base client for API authentication with OAuth2."""

import contextlib
import json
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self

import httpx2
import typer
from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TransferSpeedColumn,
    wrap_file,
)


class TokenResponse(BaseModel):
    """OAuth2 token response model, with the absolute UTC instant it expires at.

    ``expiry`` isn't part of the wire response; it's derived from
    ``expires_in`` right after parsing, using a ``buffer_seconds`` value
    passed in via validation context (see ``NitroClientCredentialsAuth``),
    so the access token and its expiry travel together as a single object.
    """

    access_token: str = Field(alias="accessToken")
    expires_in: int = Field(default=3600, alias="expiresIn")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def expiry(self) -> datetime:
        return self.created_at + timedelta(seconds=self.expires_in)


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    platform_client_id: str
    platform_client_secret: str
    platform_base_url: str = "https://api.gonitro.dev"


@dataclass(slots=True)
class NitroClientCredentialsAuthSettings:
    """Tunables for the OAuth2 client-credentials auth flow."""

    token_expiry_buffer: timedelta = timedelta(seconds=60)


@dataclass(slots=True)
class URLFile:
    """A file referenced by a presigned download URL, ready to submit as a multipart part."""

    url: str
    content_type: str
    name: str = "file"

    def to_file_part(self) -> tuple[str, bytes, str]:
        """Return the (name, content, content-type) multipart part for this file reference."""
        payload = json.dumps({"URL": self.url, "contentType": self.content_type})
        return self.name, payload.encode(), "application/vnd.gonitro.url+json"


class _PresignedURLPair(BaseModel):
    """One presigned URL pair for uploading a file and referencing it back by URL."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    upload_url: str = Field(alias="uploadURL")
    download_url: str = Field(alias="downloadURL")


class _PresignedURLPairsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    urls: list[_PresignedURLPair]


@dataclass
class FatalError(SystemExit):
    _reason: str

    def __post_init__(self) -> None:
        self.code = 1
        typer.secho(f"\nError: {self._reason}", fg=typer.colors.RED, err=True)


@dataclass
class NitroClientCredentialsAuth(httpx2.Auth):
    """httpx2 auth flow for OAuth2 client-credentials.

    Fetches and caches a bearer token on first use, and re-authenticates once
    (fetching a fresh token and retrying) if a request comes back 401.
    """

    _client_id: str
    _client_secret: str
    _base_url: str
    _settings: NitroClientCredentialsAuthSettings = field(
        default_factory=NitroClientCredentialsAuthSettings
    )
    _cached_token: TokenResponse | None = None

    def _fetch_token(self) -> str:
        """Fetch, cache and return a fresh access token from the token endpoint."""
        with httpx2.Client() as token_client:
            response = token_client.post(
                f"{self._base_url}/oauth/token",
                json={"clientID": self._client_id, "clientSecret": self._client_secret},
            )
            if response.status_code != httpx2.codes.OK.value:
                raise FatalError("Auth failed, check client credentials and try again")
        response.raise_for_status()

        token_data = TokenResponse.model_validate_json(response.content)
        self._cached_token = token_data
        return token_data.access_token

    def _get_token(self) -> str:
        """Return the cached token, fetching a fresh one if missing or expired."""
        cached = self._cached_token
        if cached and datetime.now(UTC) + self._settings.token_expiry_buffer < cached.expiry:
            return cached.access_token
        return self._fetch_token()

    def auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response]:
        """Attach a bearer token, refreshing once and retrying on a 401."""
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        response = yield request
        if response.status_code == httpx2.codes.UNAUTHORIZED.value:
            request.headers["Authorization"] = f"Bearer {self._fetch_token()}"  # Fetch a new token
            yield request


@dataclass
class BaseOAuthClient:
    """Base class for API clients with OAuth2 authentication."""

    _client: httpx2.Client
    _raw_client: httpx2.Client

    def _upload_to_url(self, url: str, file_path: Path) -> None:
        """Stream file_path to an arbitrary URL (e.g. a presigned upload URL), showing a
        progress bar. No platform auth is attached."""
        total = file_path.stat().st_size
        with (
            file_path.open("rb") as fp,
            wrap_file(
                fp, total, description=f"Uploading {file_path.name}...", transient=True
            ) as stream,
        ):
            response = self._raw_client.put(
                url, content=stream, headers={"Content-Length": str(total)}
            )
        response.raise_for_status()

    @staticmethod
    def _stream_with_progress(response: httpx2.Response, description: str) -> bytes:
        """Consume an already-open streaming response into bytes, showing a progress bar."""
        total = int(response.headers.get("content-length", 0)) or None
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(description, total=total)
            buf = bytearray()
            for chunk in response.iter_bytes():
                buf += chunk
                progress.update(task, advance=len(chunk))
        return bytes(buf)

    def _download_from_url(self, url: str, description: str = "Downloading...") -> bytes:
        """GET an arbitrary URL (e.g. a presigned download URL) with no platform auth attached,
        showing a progress bar."""
        with self._raw_client.stream("GET", url) as response:
            response.raise_for_status()
            return self._stream_with_progress(response, description)

    def _upload(
        self, file_path: Path, content_type: str, name: str = "file"
    ) -> tuple[str, bytes, str]:
        """Upload file_path to a fresh presigned URL and return the resulting ``file`` multipart
        part.

        Presigned pairs are single-use and expire after 15 minutes, so a fresh
        pair is minted right before each upload rather than cached or reused.
        """
        response = self._client.post("/presigned-file-urls", params={"n": 1})
        response.raise_for_status()
        presigned = _PresignedURLPairsResponse.model_validate_json(response.content).urls[0]
        self._upload_to_url(presigned.upload_url, file_path)
        url_file = URLFile(url=presigned.download_url, content_type=content_type, name=name)
        return url_file.to_file_part()

    @classmethod
    @contextlib.contextmanager
    def build(cls) -> Generator[Self]:
        """Build a client with two httpx2.Clients: one authenticated against the
        platform, one plain for arbitrary URLs (e.g. presigned upload/download
        URLs) that must never get the platform's bearer token attached.

        Client credentials and base URL are loaded from the environment/.env
        file.

        Returns:
            A ready-to-use client instance.
        """
        settings = Settings()  # type: ignore[reportCallIssue]
        auth = NitroClientCredentialsAuth(
            settings.platform_client_id,
            settings.platform_client_secret,
            settings.platform_base_url,
        )
        with (
            httpx2.Client(auth=auth, base_url=settings.platform_base_url) as client,
            httpx2.Client() as raw_client,
        ):
            yield cls(client, raw_client)
