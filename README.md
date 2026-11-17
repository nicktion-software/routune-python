# Routune Python Library

[![PyPI version](https://img.shields.io/pypi/v/routune.svg)](https://pypi.org/project/routune/)
[![Python versions](https://img.shields.io/pypi/pyversions/routune.svg)](https://pypi.org/project/routune/)
[![CI](https://github.com/nicktion-software/routune-python/actions/workflows/ci.yml/badge.svg)](https://github.com/nicktion-software/routune-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The official Python library for the [Routune API](https://routune.com/developers). Create orders, assign drivers and read your customers, locations and price sets from Python, synchronously or with `asyncio`.

## Documentation

API reference and guides: [routune.com/developers](https://routune.com/developers).

## Requirements

- Python 3.10 or later
- A Routune workspace on a plan that includes API access
- An API key from **Settings → API keys** in Routune

## Installation

```sh
pip install routune
```

## Usage

The client reads your key from the `ROUTUNE_API_KEY` environment variable:

```python
from routune import Routune

client = Routune()

order = client.orders.create(
    customer_id="cus_uuid",
    price_set_id="price_set_uuid",
    gross_weight=12.5,
    chargeable_weight=12.5,
    reference_number="ERP-10042",
    pickup={
        "location_id": "pickup_location_uuid",
        "earliest_time": "2026-11-20T14:00:00Z",
        "latest_time": "2026-11-20T16:00:00Z",
    },
    dropoff={
        "location_id": "dropoff_location_uuid",
        "earliest_time": "2026-11-20T17:00:00Z",
        "latest_time": "2026-11-20T19:00:00Z",
        "signature_required": True,
    },
)

print(order.number)  # ORD-000123
```

Responses are [Pydantic](https://docs.pydantic.dev) models and request parameters are typed, so editors and type checkers catch mistakes. Field names match the API (`snake_case`), IDs are UUID strings, times are parsed as `datetime` and amounts are integers in the currency's smallest unit.

> **Keep your API key secret.** Use it only on your server. Never ship it in a desktop or mobile app.

## Resources

| Resource | Methods | Scope |
| --- | --- | --- |
| `orders` | `list`, `create`, `retrieve`, `update` | `orders.read`, `orders.write` |
| `orders.legs` | `assign` | `orders.assign` |
| `customers` | `list`, `retrieve` | `customers.read` |
| `drivers` | `list` | `drivers.read` |
| `locations` | `list`, `create`, `retrieve` | `locations.read`, `locations.write` |
| `price_sets` | `list`, `retrieve` | `pricing.read` |

### Assigning a driver

```python
order = client.orders.retrieve(order_id)

client.orders.legs.assign(order.id, order.legs[0].id, driver_id=driver_id)
```

To reassign a leg safely, send the driver you expect on it now. If the leg changed in the meantime, the API responds with `409 assignment_changed` and nothing is moved:

```python
client.orders.legs.assign(
    order.id,
    leg.id,
    driver_id=new_driver_id,
    expected_current_driver_id=leg.assigned_driver_id,
)
```

## Pagination

List methods return results newest first. A list call returns a single page:

```python
page = client.orders.list(status="delivered", limit=100)

page.data             # list[Order]
page.has_more         # bool
page.has_next_page()  # bool
page.get_next_page()
```

Iterate over the page to fetch every page automatically:

```python
for order in client.orders.list(created_gte="2026-11-01T00:00:00Z"):
    print(order.number)
```

## Async usage

`AsyncRoutune` has the same methods. Await a list call for one page, or use `async for` to go through all of them:

```python
import asyncio

from routune import AsyncRoutune


async def main() -> None:
    async with AsyncRoutune() as client:
        order = await client.orders.retrieve("order_uuid")

        async for driver in client.drivers.list():
            print(driver.name)


asyncio.run(main())
```

## Error handling

When the API returns an error, the library raises a subclass of `routune.APIError`:

```python
import routune

try:
    client.orders.legs.assign(order_id, leg_id, driver_id=driver_id)
except routune.ConflictError as err:
    if err.code == "assignment_changed":
        ...  # Reload the order and decide again.
    else:
        raise
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
| ≥ 500 | `InternalServerError` |
| No response | `APIConnectionError`, `APITimeoutError` |

Every `APIError` carries `status_code`, `type`, `code`, `message`, `details` and `request_id`. Include the `request_id` when you contact support.

## Retries

Connection errors, timeouts, `408`, `429` and `5xx` responses are retried twice by default with exponential backoff. `Retry-After` is respected. Configure the number of retries for the client or for a single request:

```python
client = Routune(max_retries=4)

client.orders.list(max_retries=0)
```

## Idempotency

Every `POST` request is sent with an `Idempotency-Key`, and retries reuse the same key, so a retried create never produces a duplicate. To stay safe across process restarts, pass a key derived from your own record:

```python
client.orders.create(..., idempotency_key=f"erp-order-{erp_order.id}")
```

## Timeouts

Each attempt times out after 60 seconds by default:

```python
client = Routune(timeout=20.0)  # seconds

client.orders.retrieve(order_id, timeout=5.0)
```

## Configuration

| Argument | Default | Description |
| --- | --- | --- |
| `api_key` | `ROUTUNE_API_KEY` | Workspace API key |
| `base_url` | `https://api.routune.com` | Also read from `ROUTUNE_BASE_URL` |
| `timeout` | `60.0` | Seconds per attempt |
| `max_retries` | `2` | Retries for retryable failures |
| `default_headers` | `None` | Headers sent with every request |
| `http_client` | new `httpx.Client` | Bring your own client (proxies, custom TLS) |

Per-request arguments: `idempotency_key` (POST only), `timeout`, `max_retries` and `extra_headers`.

## Forward compatibility

The API may add fields and enum values at any time. Unknown fields are kept and available through `.to_dict()`, and unknown enum values come through as plain strings, so older versions of this library keep working.

## Rate limits

Each API key can make 600 requests per minute, and each workspace 1,200. Responses include `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset` headers. Successful requests count towards your plan's monthly API requests.

## Versioning

This package follows [Semantic Versioning](https://semver.org). The API is versioned in its URL (`/v1`).

## Support

- API documentation: [routune.com/developers](https://routune.com/developers)
- Bugs in this library: [open an issue](https://github.com/nicktion-software/routune-python/issues)
- Security issues: see [SECURITY.md](SECURITY.md). Do not open a public issue.

## License

[MIT](LICENSE). Routune is a product of Nicktion LLC.
