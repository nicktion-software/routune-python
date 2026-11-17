"""Official Python library for the Routune API."""

from . import types
from ._base_client import DEFAULT_BASE_URL
from ._client import AsyncRoutune, Routune
from ._errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    RoutuneError,
    UnprocessableEntityError,
)
from ._pagination import AsyncPage, AsyncPaginator, SyncPage
from ._version import __version__

__all__ = [
    "Routune",
    "AsyncRoutune",
    "DEFAULT_BASE_URL",
    "SyncPage",
    "AsyncPage",
    "AsyncPaginator",
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
    "types",
    "__version__",
]
