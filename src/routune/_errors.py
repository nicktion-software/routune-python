from __future__ import annotations

from typing import Any

import httpx

__all__ = [
    "RoutuneError",
    "APIError",
    "BadRequestError",
    "AuthenticationError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "APIConnectionError",
    "APITimeoutError",
]


class RoutuneError(Exception):
    """Base class for every error this library raises."""


class APIError(RoutuneError):
    """The API answered with an error status. Fields come from ``{"error": {...}}``."""

    status_code: int
    type: str | None
    code: str | None
    request_id: str | None
    details: dict[str, Any] | None
    response: httpx.Response

    def __init__(self, message: str, *, response: httpx.Response, body: dict[str, Any] | None) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code
        body = body or {}
        self.type = body.get("type")
        self.code = body.get("code")
        self.request_id = body.get("request_id") or response.headers.get("x-request-id")
        details = body.get("details")
        self.details = details if isinstance(details, dict) else None

    def __str__(self) -> str:
        parts = [f"{self.status_code}"]
        if self.code:
            parts.append(self.code)
        text = f"[{' '.join(parts)}] {self.message}"
        if self.request_id:
            text += f" (request_id: {self.request_id})"
        return text


class BadRequestError(APIError):
    """400: the request was malformed or failed validation (see ``details``)."""


class AuthenticationError(APIError):
    """401: missing, invalid, revoked or expired API key."""


class PaymentRequiredError(APIError):
    """402: the workspace's plan or trial does not cover this request."""


class PermissionDeniedError(APIError):
    """403: the key lacks the scope, or the IP is not allowed for this key."""


class NotFoundError(APIError):
    """404: the resource does not exist in this workspace."""


class ConflictError(APIError):
    """409: e.g. ``assignment_changed`` or ``idempotency_conflict``."""


class UnprocessableEntityError(APIError):
    """422: understood but cannot be carried out."""


class RateLimitError(APIError):
    """429: too many requests (already retried with backoff)."""

    @property
    def retry_after(self) -> float | None:
        try:
            return float(self.response.headers["retry-after"])
        except (KeyError, ValueError):
            return None


class InternalServerError(APIError):
    """5xx: something went wrong on Routune's side (already retried)."""


class APIConnectionError(RoutuneError):
    """The request never got an answer (already retried)."""


class APITimeoutError(APIConnectionError):
    """No answer within the timeout (already retried)."""


_BY_STATUS: dict[int, type[APIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def make_api_error(response: httpx.Response, body: dict[str, Any] | None) -> APIError:
    status = response.status_code
    cls = _BY_STATUS.get(status) or (InternalServerError if status >= 500 else APIError)
    message = (body or {}).get("message") or response.reason_phrase or f"Request failed with status {status}"
    return cls(str(message), response=response, body=body)
