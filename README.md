# Routune Python library

The official Python library for the [Routune API](https://routune.com/developers): create and track deliveries in your Routune workspace from your own systems.

- Sync (`Routune`) and async (`AsyncRoutune`) clients built on httpx
- Typed responses (pydantic) and typed request params, generated from the public OpenAPI spec
- Automatic retries with backoff for timeouts, rate limits and server errors
- Safe retries for creates: every POST carries an `Idempotency-Key`
- Iterate any list to walk every page
- Python 3.10+

## Install

```sh
pip install routune
```

## Authentication

Create an API key in Routune under **Settings > API keys** and give it only the scopes you need. Keys are secrets: keep them on your server, in an environment variable or a secret manager.

```sh
export ROUTUNE_API_KEY="rtn_live_…"
```

## Usage

```python
from routune import Routune

client = Routune()  # reads ROUTUNE_API_KEY

price_set = client.price_sets.list(active=True, limit=1).data[0]

order = client.orders.create(
    customer_id="2f1d7c8e-…",
    price_set_id=price_set.id,
    gross_weight=12.5,
    chargeable_weight=12.5,
    reference_number="ERP-10042",
    pickup={
        "location_id": "7b0f…",
        "earliest_time": "2026-11-20T14:00:00Z",
        "latest_time": "2026-11-20T16:00:00Z",
    },
    dropoff={
        "location_id": "9c41…",
        "earliest_time": "2026-11-20T17:00:00Z",
        "latest_time": "2026-11-20T19:00:00Z",
        "signature_required": True,
    },
)
print(order.number, order.status)
```

### Assign a driver to a leg

```python
full = client.orders.retrieve(order.id)
leg = full.legs[0]
driver = client.drivers.list(limit=1).data[0]

client.orders.legs.assign(order.id, leg.id, driver_id=driver.id)
```

To reassign, pass the driver you expect on the leg now. If someone changed it in the meantime the API answers `409 assignment_changed` and nothing moves:

```python
client.orders.legs.assign(
    order.id, leg.id, driver_id=new_driver_id, expected_current_driver_id=leg.assigned_driver_id
)
```

### Lists and pagination

Lists are newest first. A list call returns one page; iterate it to walk every item, the library follows `next_cursor` for you.

```python
page = client.orders.list(status="delivered", limit=100)
print(len(page.data), page.has_more)

for order in client.orders.list(created_gte="2026-11-01T00:00:00Z"):
    print(order.id)
```

### Async

```python
import asyncio
from routune import AsyncRoutune

async def main() -> None:
    async with AsyncRoutune() as client:
        order = await client.orders.retrieve("…")
        async for driver in client.drivers.list():
            print(driver.id)

asyncio.run(main())
```

### Errors

Failed requests raise a subclass of `routune.APIError` with the API's `code` and a `request_id` to quote to support:

```python
import routune

try:
    client.orders.legs.assign(order_id, leg_id, driver_id=driver_id)
except routune.ConflictError as err:
    if err.code == "assignment_changed":
        ...  # reload the order and decide again
except routune.APIError as err:
    print(err.status_code, err.code, err.message, err.request_id)
```

| Status | Exception |
| --- | --- |
| 400 | `BadRequestError` |
| 401 | `AuthenticationError` |
| 402 | `PaymentRequiredError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` |
| 5xx | `InternalServerError` |
| no answer | `APIConnectionError`, `APITimeoutError` |

### Retries, timeouts and idempotency

Connection errors, timeouts, `429` and `5xx` answers are retried twice with exponential backoff (honouring `Retry-After`). POST requests carry an `Idempotency-Key`, the same on every retry, so a retried create never makes a second order. Pass your own key to stay safe across process restarts too:

```python
client = Routune(max_retries=4, timeout=20.0)
client.orders.create(..., idempotency_key=f"erp-order-{erp_id}")
```

| Option | Default |
| --- | --- |
| `api_key` | `ROUTUNE_API_KEY` |
| `base_url` | `ROUTUNE_BASE_URL`, then `https://api.routune.com` |
| `timeout` | `60.0` seconds |
| `max_retries` | `2` |
| `default_headers` | none |
| `http_client` | a new `httpx.Client` / `httpx.AsyncClient` |

Per-request options: `idempotency_key` (POST), `timeout`, `max_retries`, `extra_headers`.

## Forward compatibility

The API adds fields and values over time. Unknown fields are kept (see `.to_dict()`) and unknown enum values arrive as plain strings, so an older library keeps working.

## License

MIT
