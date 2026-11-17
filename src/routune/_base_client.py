from __future__ import annotations

import asyncio
import json
import os
import platform
import random
import time
import uuid
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Mapping, TypeVar, overload
from uuid import UUID

import httpx
import pydantic

from ._errors import APIConnectionError, APITimeoutError, RoutuneError, make_api_error
from ._version import __version__

DEFAULT_BASE_URL = "https://api.routune.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRY_DELAY = 60.0

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, pydantic.BaseModel):
        return value.model_dump(mode="json", exclude_unset=True)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def path_param(name: str, value: str) -> str:
    """Encodes one path parameter; an empty id would silently hit a different endpoint."""
    value = str(value) if isinstance(value, UUID) else value
    if not isinstance(value, str) or not value.strip():
        raise RoutuneError(f"Expected a non-empty string for {name}.")
    from urllib.parse import quote

    return quote(value, safe="")


def _clean_query(query: Mapping[str, Any] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (query or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        elif isinstance(value, (datetime, date)):
            out[key] = value.isoformat()
        else:
            out[key] = str(value)
    return out


def _read_error_body(response: httpx.Response) -> dict[str, Any] | None:
    try:
        parsed = response.json()
    except ValueError:
        return None
    if isinstance(parsed, dict):
        inner = parsed.get("error")
        return inner if isinstance(inner, dict) else parsed
    return None


def _should_retry(response: httpx.Response, body: dict[str, Any] | None) -> bool:
    status = response.status_code
    if status in (408, 429) or status >= 500:
        return True
    # Another call with the same Idempotency-Key is still running: its result will be replayed.
    return status == 409 and (body or {}).get("code") == "idempotency_in_progress"


def _backoff(attempt: int) -> float:
    return float(min(0.5 * 2**attempt, 8.0) * (1 - random.random() * 0.25))


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    raw = response.headers.get("retry-after")
    if raw is not None:
        try:
            return min(max(float(raw), 0.0), MAX_RETRY_DELAY)
        except ValueError:
            try:
                when = parsedate_to_datetime(raw).timestamp()
                return min(max(when - time.time(), 0.0), MAX_RETRY_DELAY)
            except (TypeError, ValueError):
                pass
    return _backoff(attempt)


class _Secret:
    """Holds the API key so that repr(), vars() and logging never show it."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "<redacted>"

    __str__ = __repr__


class BaseClient:
    """Shared configuration and request building for the sync and async clients."""

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | None,
        timeout: float,
        max_retries: int,
        default_headers: Mapping[str, str] | None,
    ) -> None:
        api_key = api_key or os.environ.get("ROUTUNE_API_KEY", "").strip() or None
        if not api_key:
            raise RoutuneError(
                "Missing API key. Pass api_key=... or set ROUTUNE_API_KEY. "
                "Create one in Routune: Settings > API keys."
            )
        self._api_key = _Secret(api_key)
        self.base_url = (base_url or os.environ.get("ROUTUNE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = dict(default_headers or {})

    def __repr__(self) -> str:  # never show the key
        return f"{type(self).__name__}(base_url={self.base_url!r}, timeout={self.timeout}, max_retries={self.max_retries})"

    def _headers(
        self, method: str, idempotency_key: str | None, attempt: int, extra: Mapping[str, str] | None, has_body: bool
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": f"routune-python/{__version__} python/{platform.python_version()} httpx/{httpx.__version__}",
            **self._default_headers,
            **(extra or {}),
            "Authorization": f"Bearer {self._api_key.get()}",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if attempt:
            headers["X-Routune-Retry-Count"] = str(attempt)
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _idempotency_key(method: str, given: str | None) -> str | None:
        if method != "POST":
            return None
        return given or f"routune-python-{uuid.uuid4()}"

    @staticmethod
    def _content(body: Any) -> bytes | None:
        if body is None:
            return None
        return json.dumps(body, default=_json_default).encode("utf-8")

    @staticmethod
    def _parse(cast_to: type[ModelT] | None, response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content:
            return None
        data = response.json()
        return cast_to.model_validate(data) if cast_to is not None else data


class SyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.Client | None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=self.timeout, follow_redirects=False)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @overload
    def request(
        self,
        cast_to: type[ModelT],
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ModelT: ...

    @overload
    def request(
        self,
        cast_to: None,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]: ...

    def request(
        self,
        cast_to: type[ModelT] | None,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Any:
        retries = self.max_retries if max_retries is None else max_retries
        key = self._idempotency_key(method, idempotency_key)
        content = self._content(body)
        url = f"{self.base_url}{path}"
        attempt = 0
        while True:
            try:
                response = self._client.request(
                    method,
                    url,
                    params=_clean_query(query),
                    content=content,
                    headers=self._headers(method, key, attempt, extra_headers, content is not None),
                    timeout=self.timeout if timeout is None else timeout,
                )
            except httpx.TimeoutException as exc:
                if attempt < retries:
                    time.sleep(_backoff(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError("Request timed out.") from exc
            except httpx.TransportError as exc:
                if attempt < retries:
                    time.sleep(_backoff(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError("Could not reach the Routune API.") from exc

            if response.is_success:
                return self._parse(cast_to, response)
            error_body = _read_error_body(response)
            if attempt < retries and _should_retry(response, error_body):
                time.sleep(_retry_delay(response, attempt))
                attempt += 1
                continue
            raise make_api_error(response, error_body)


class AsyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.AsyncClient | None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=False)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self):  # type: ignore[no-untyped-def]
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @overload
    async def request(
        self,
        cast_to: type[ModelT],
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ModelT: ...

    @overload
    async def request(
        self,
        cast_to: None,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]: ...

    async def request(
        self,
        cast_to: type[ModelT] | None,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Any:
        retries = self.max_retries if max_retries is None else max_retries
        key = self._idempotency_key(method, idempotency_key)
        content = self._content(body)
        url = f"{self.base_url}{path}"
        attempt = 0
        while True:
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=_clean_query(query),
                    content=content,
                    headers=self._headers(method, key, attempt, extra_headers, content is not None),
                    timeout=self.timeout if timeout is None else timeout,
                )
            except httpx.TimeoutException as exc:
                if attempt < retries:
                    await asyncio.sleep(_backoff(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError("Request timed out.") from exc
            except httpx.TransportError as exc:
                if attempt < retries:
                    await asyncio.sleep(_backoff(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError("Could not reach the Routune API.") from exc

            if response.is_success:
                return self._parse(cast_to, response)
            error_body = _read_error_body(response)
            if attempt < retries and _should_retry(response, error_body):
                await asyncio.sleep(_retry_delay(response, attempt))
                attempt += 1
                continue
            raise make_api_error(response, error_body)
