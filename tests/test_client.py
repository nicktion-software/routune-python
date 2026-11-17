from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import httpx
import pytest

import routune
from routune import (
    APIConnectionError,
    AsyncRoutune,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    Routune,
    RoutuneError,
)

KEY = "rtn_test_not_a_real_key_for_tests"
ORDER_ID = "b3c1a1de-0000-4000-8000-000000000001"


def order_body(**extra: object) -> dict:
    return {
        "object": "order",
        "id": ORDER_ID,
        "number": "ORD-000123",
        "status": "created",
        "pickup": {},
        "dropoff": {},
        "quantity": 1,
        "gross_weight": 5,
        "chargeable_weight": 5,
        "amounts": {"currency": "usd", "base": 1000, "accessorials": 0, "fuel_surcharge": 0, "tax": 0, "total": 1000},
        "created_at": "2026-11-18T10:00:00Z",
        "updated_at": "2026-11-18T10:00:00Z",
        **extra,
    }


class Recorder:
    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def resp(status: int, body: object = None, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=body, headers=headers or {})


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("routune._base_client.time.sleep", lambda s: None)

    async def fast(_: float) -> None:
        return None

    monkeypatch.setattr("routune._base_client.asyncio.sleep", fast)


def make(rec: Recorder, **kw: object) -> Routune:
    return Routune(api_key=KEY, http_client=httpx.Client(transport=httpx.MockTransport(rec)), **kw)  # type: ignore[arg-type]


def test_needs_key_and_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROUTUNE_API_KEY", raising=False)
    with pytest.raises(RoutuneError, match="Missing API key"):
        Routune()
    monkeypatch.setenv("ROUTUNE_API_KEY", KEY)
    assert Routune().base_url == "https://api.routune.com"


def test_key_never_in_repr() -> None:
    client = make(Recorder())
    assert KEY not in repr(client)
    assert KEY not in str(vars(client))


def test_version_matches_pyproject() -> None:
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, re.M)
    assert match and routune.__version__ == match.group(1)


def test_retrieve_sends_key_and_parses_model() -> None:
    rec = Recorder(resp(200, order_body(brand_new_field=1, status="scheduled")))
    order = make(rec).orders.retrieve(ORDER_ID)
    req = rec.requests[0]
    assert str(req.url) == f"https://api.routune.com/v1/orders/{ORDER_ID}"
    assert req.headers["authorization"] == f"Bearer {KEY}"
    assert req.headers["user-agent"].startswith("routune-python/")
    assert "idempotency-key" not in req.headers
    assert order.number == "ORD-000123"
    # A status this version does not know yet, and an unknown field, still parse.
    assert order.status == "scheduled"
    assert order.to_dict()["brand_new_field"] == 1


def test_path_ids_are_encoded_and_required() -> None:
    rec = Recorder(resp(200, order_body()))
    client = make(rec)
    client.orders.retrieve("a/b?c")
    assert rec.requests[0].url.raw_path == b"/v1/orders/a%2Fb%3Fc"
    with pytest.raises(RoutuneError):
        client.orders.retrieve("")


def test_post_reuses_one_idempotency_key_across_retries() -> None:
    rec = Recorder(resp(503, {"error": {"message": "busy"}}), resp(201, order_body()))
    make(rec).orders.create(
        customer_id="c",
        price_set_id="p",
        gross_weight=5,
        chargeable_weight=5,
        pickup={"location_id": "l1", "earliest_time": "2026-11-20T14:00:00Z", "latest_time": "2026-11-20T16:00:00Z"},
        dropoff={"location_id": "l2", "earliest_time": "2026-11-20T17:00:00Z", "latest_time": "2026-11-20T19:00:00Z"},
    )
    keys = [r.headers["idempotency-key"] for r in rec.requests]
    assert keys[0].startswith("routune-python-") and keys[0] == keys[1]
    assert rec.requests[1].headers["x-routune-retry-count"] == "1"
    assert json.loads(rec.requests[0].content)["customer_id"] == "c"


def test_caller_idempotency_key_and_leg_assign_path() -> None:
    rec = Recorder(
        resp(200, {"object": "leg_assignment", "order_id": "o1", "leg_id": "l1", "driver_id": "d1", "assigned_at": "2026-11-18T10:00:00Z"})
    )
    a = make(rec).orders.legs.assign("o1", "l1", driver_id="d1", idempotency_key="my-key")
    assert rec.requests[0].url.path == "/v1/orders/o1/legs/l1/assign"
    assert rec.requests[0].headers["idempotency-key"] == "my-key"
    assert a.driver_id == "d1"


def test_errors_are_typed_and_4xx_not_retried() -> None:
    rec = Recorder(
        resp(401, {"error": {"type": "authentication_error", "code": "api_key_revoked", "message": "Revoked.", "request_id": "req_1"}})
    )
    with pytest.raises(AuthenticationError) as info:
        make(rec).orders.retrieve("x")
    assert info.value.code == "api_key_revoked"
    assert info.value.request_id == "req_1"
    assert info.value.status_code == 401
    assert "req_1" in str(info.value)
    assert len(rec.requests) == 1


def test_conflict_rules() -> None:
    changed = Recorder(resp(409, {"error": {"code": "assignment_changed", "message": "Changed."}}))
    with pytest.raises(ConflictError):
        make(changed).orders.legs.assign("o", "l", driver_id="d")
    assert len(changed.requests) == 1

    in_progress = Recorder(resp(409, {"error": {"code": "idempotency_in_progress"}}, {"retry-after": "0"}), resp(201, order_body()))
    make(in_progress).orders.create(
        customer_id="c", price_set_id="p", gross_weight=1, chargeable_weight=1, pickup={}, dropoff={}  # type: ignore[typeddict-item]
    )
    assert len(in_progress.requests) == 2


def test_rate_limit_retries_then_raises() -> None:
    limited = lambda: resp(429, {"error": {"code": "rate_limited"}}, {"retry-after": "0"})  # noqa: E731
    rec = Recorder(limited(), limited(), limited())
    with pytest.raises(RateLimitError) as info:
        make(rec).drivers.list()
    assert info.value.retry_after == 0
    assert len(rec.requests) == 3


def test_connection_errors_retry_then_raise() -> None:
    rec = Recorder(httpx.ConnectError("boom"), httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError):
        make(rec, max_retries=1).customers.retrieve("c1")
    assert len(rec.requests) == 2


def test_not_found_uses_request_id_header() -> None:
    rec = Recorder(resp(404, {"error": {"message": "Not found"}}, {"x-request-id": "req_h"}))
    with pytest.raises(NotFoundError) as info:
        make(rec).locations.retrieve("nope")
    assert info.value.request_id == "req_h"


def page(ids: list[str], nxt: str | None) -> httpx.Response:
    data = [
        {
            "object": "driver",
            "id": i,
            "name": None,
            "email": None,
            "created_at": "2026-11-18T10:00:00Z",
        }
        for i in ids
    ]
    return resp(200, {"object": "list", "data": data, "has_more": nxt is not None, "next_cursor": nxt})


def test_sync_pagination_walks_every_item() -> None:
    rec = Recorder(page(["a", "b"], "cur_2"), page(["c"], None))
    first = make(rec).drivers.list(limit=2, search="pat")
    assert [d.id for d in first.data] == ["a", "b"]
    assert [d.id for d in first] == ["a", "b", "c"]
    assert "cursor" not in rec.requests[0].url.params
    assert rec.requests[1].url.params["cursor"] == "cur_2"
    assert rec.requests[1].url.params["search"] == "pat"


def test_query_bools_and_none() -> None:
    rec = Recorder(resp(200, {"object": "list", "data": [], "has_more": False, "next_cursor": None}))
    make(rec).price_sets.list(active=True, customer_id=None)
    assert dict(rec.requests[0].url.params) == {"active": "true"}


async def test_async_client_pages_and_awaits() -> None:
    rec = Recorder(page(["a"], "cur_2"), page(["b"], None), page(["x"], None))
    client = AsyncRoutune(api_key=KEY, http_client=httpx.AsyncClient(transport=httpx.MockTransport(rec)))
    ids = [d.id async for d in client.drivers.list()]
    assert ids == ["a", "b"]
    first = await client.drivers.list(limit=1)
    assert [d.id for d in first.data] == ["x"]
    await client.close()


def test_list_arguments_match_the_spec() -> None:
    """Hand-written list() keyword arguments must cover the spec's query parameters exactly."""
    import inspect

    spec = json.loads((Path(__file__).parent.parent / "openapi" / "routune-public.v1.json").read_text(encoding="utf-8"))
    client = make(Recorder())
    methods: dict[str, Callable[..., object]] = {
        "/v1/orders": client.orders.list,
        "/v1/customers": client.customers.list,
        "/v1/drivers": client.drivers.list,
        "/v1/locations": client.locations.list,
        "/v1/price_sets": client.price_sets.list,
    }
    options = {"timeout", "max_retries", "extra_headers"}
    for path, method in methods.items():
        expected = {p["name"] for p in spec["paths"][path]["get"].get("parameters", []) if p["in"] == "query"}
        actual = set(inspect.signature(method).parameters) - options
        assert actual == expected, path
