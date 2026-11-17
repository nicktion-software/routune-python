"""API resources. List methods' query arguments are checked against the spec by tests/test_spec_sync.py."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Mapping

from typing_extensions import Unpack

from .._base_client import path_param
from .._pagination import AsyncPaginator, SyncPage
from ..types import Customer, Driver, LegAssignment, Location, Order, PriceSet
from ..types._params import AssignLegDriver, CreateLocation, CreateOrder, UpdateOrder

if TYPE_CHECKING:
    from .._client import AsyncRoutune, Routune

OrderStatus = Literal["created", "in_progress", "delivered", "returned", "cancelled", "on_hold"]


def _opts(
    idempotency_key: str | None, timeout: float | None, max_retries: int | None, extra_headers: Mapping[str, str] | None
) -> dict[str, Any]:
    return {
        "idempotency_key": idempotency_key,
        "timeout": timeout,
        "max_retries": max_retries,
        "extra_headers": extra_headers,
    }


# --------------------------------------------------------------------------------------------- sync


class _SyncResource:
    def __init__(self, client: Routune) -> None:
        self._client = client

    def _page(self, model: type, path: str, query: dict[str, Any], opts: dict[str, Any]) -> SyncPage[Any]:
        cursor = query.pop("cursor", None)

        def fetch(next_cursor: str | None) -> dict[str, Any]:
            return self._client.request(None, "GET", path, query={**query, "cursor": next_cursor}, **opts)

        return SyncPage(model, fetch(cursor), fetch)


class OrderLegs(_SyncResource):
    def assign(
        self,
        order_id: str,
        leg_id: str,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[AssignLegDriver],
    ) -> LegAssignment:
        """Assigns a driver to one leg. Pass ``expected_current_driver_id`` to reassign safely
        (409 ``assignment_changed`` if it moved). Scope: ``orders.assign``."""
        return self._client.request(
            LegAssignment,
            "POST",
            f"/v1/orders/{path_param('order_id', order_id)}/legs/{path_param('leg_id', leg_id)}/assign",
            body=dict(params),
            **_opts(idempotency_key, timeout, max_retries, extra_headers),
        )


class Orders(_SyncResource):
    def __init__(self, client: Routune) -> None:
        super().__init__(client)
        self.legs = OrderLegs(client)

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        status: OrderStatus | None = None,
        customer_id: str | None = None,
        created_gte: str | datetime | None = None,
        created_lte: str | datetime | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> SyncPage[Order]:
        """Lists orders, newest first. Iterate the result to walk every page. Scope: ``orders.read``."""
        query = {
            "limit": limit,
            "cursor": cursor,
            "status": status,
            "customer_id": customer_id,
            "created_gte": created_gte,
            "created_lte": created_lte,
        }
        return self._page(Order, "/v1/orders", query, _opts(None, timeout, max_retries, extra_headers))

    def create(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CreateOrder],
    ) -> Order:
        """Creates an order. Retries are safe: an Idempotency-Key is sent automatically.
        Scope: ``orders.write``."""
        return self._client.request(
            Order, "POST", "/v1/orders", body=dict(params), **_opts(idempotency_key, timeout, max_retries, extra_headers)
        )

    def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Order:
        """Retrieves an order with its legs. Scope: ``orders.read``."""
        return self._client.request(
            Order, "GET", f"/v1/orders/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )

    def update(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[UpdateOrder],
    ) -> Order:
        """Updates notes, reference or stop times. Scope: ``orders.write``."""
        return self._client.request(
            Order,
            "PATCH",
            f"/v1/orders/{path_param('id', id)}",
            body=dict(params),
            **_opts(None, timeout, max_retries, extra_headers),
        )


class Customers(_SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> SyncPage[Customer]:
        """Lists customers, newest first. Scope: ``customers.read``."""
        query = {"limit": limit, "cursor": cursor, "search": search}
        return self._page(Customer, "/v1/customers", query, _opts(None, timeout, max_retries, extra_headers))

    def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Customer:
        """Scope: ``customers.read``."""
        return self._client.request(
            Customer, "GET", f"/v1/customers/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )


class Drivers(_SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> SyncPage[Driver]:
        """Lists active drivers you can assign to legs. Scope: ``drivers.read``."""
        query = {"limit": limit, "cursor": cursor, "search": search}
        return self._page(Driver, "/v1/drivers", query, _opts(None, timeout, max_retries, extra_headers))


class Locations(_SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        customer_id: str | None = None,
        has_coordinates: bool | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> SyncPage[Location]:
        """Lists saved locations, newest first. Scope: ``locations.read``."""
        query = {
            "limit": limit,
            "cursor": cursor,
            "search": search,
            "customer_id": customer_id,
            "has_coordinates": has_coordinates,
        }
        return self._page(Location, "/v1/locations", query, _opts(None, timeout, max_retries, extra_headers))

    def create(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CreateLocation],
    ) -> Location:
        """Saves a location (coordinates required). Scope: ``locations.write``."""
        return self._client.request(
            Location,
            "POST",
            "/v1/locations",
            body=dict(params),
            **_opts(idempotency_key, timeout, max_retries, extra_headers),
        )

    def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Location:
        """Scope: ``locations.read``."""
        return self._client.request(
            Location, "GET", f"/v1/locations/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )


class PriceSets(_SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        active: bool | None = None,
        customer_id: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> SyncPage[PriceSet]:
        """Lists price sets; use one's id as ``price_set_id`` when creating orders. Scope: ``pricing.read``."""
        query = {"limit": limit, "cursor": cursor, "active": active, "customer_id": customer_id}
        return self._page(PriceSet, "/v1/price_sets", query, _opts(None, timeout, max_retries, extra_headers))

    def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> PriceSet:
        """Scope: ``pricing.read``."""
        return self._client.request(
            PriceSet, "GET", f"/v1/price_sets/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )


# -------------------------------------------------------------------------------------------- async


class _AsyncResource:
    def __init__(self, client: AsyncRoutune) -> None:
        self._client = client

    def _page(self, model: type, path: str, query: dict[str, Any], opts: dict[str, Any]) -> AsyncPaginator[Any]:
        cursor = query.pop("cursor", None)

        async def fetch(next_cursor: str | None) -> dict[str, Any]:
            return await self._client.request(None, "GET", path, query={**query, "cursor": next_cursor}, **opts)

        return AsyncPaginator(model, fetch, cursor)


class AsyncOrderLegs(_AsyncResource):
    async def assign(
        self,
        order_id: str,
        leg_id: str,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[AssignLegDriver],
    ) -> LegAssignment:
        """See :meth:`OrderLegs.assign`."""
        return await self._client.request(
            LegAssignment,
            "POST",
            f"/v1/orders/{path_param('order_id', order_id)}/legs/{path_param('leg_id', leg_id)}/assign",
            body=dict(params),
            **_opts(idempotency_key, timeout, max_retries, extra_headers),
        )


class AsyncOrders(_AsyncResource):
    def __init__(self, client: AsyncRoutune) -> None:
        super().__init__(client)
        self.legs = AsyncOrderLegs(client)

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        status: OrderStatus | None = None,
        customer_id: str | None = None,
        created_gte: str | datetime | None = None,
        created_lte: str | datetime | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncPaginator[Order]:
        """``await`` for the first page, ``async for`` for every order. Scope: ``orders.read``."""
        query = {
            "limit": limit,
            "cursor": cursor,
            "status": status,
            "customer_id": customer_id,
            "created_gte": created_gte,
            "created_lte": created_lte,
        }
        return self._page(Order, "/v1/orders", query, _opts(None, timeout, max_retries, extra_headers))

    async def create(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CreateOrder],
    ) -> Order:
        """See :meth:`Orders.create`."""
        return await self._client.request(
            Order, "POST", "/v1/orders", body=dict(params), **_opts(idempotency_key, timeout, max_retries, extra_headers)
        )

    async def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Order:
        return await self._client.request(
            Order, "GET", f"/v1/orders/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )

    async def update(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[UpdateOrder],
    ) -> Order:
        return await self._client.request(
            Order,
            "PATCH",
            f"/v1/orders/{path_param('id', id)}",
            body=dict(params),
            **_opts(None, timeout, max_retries, extra_headers),
        )


class AsyncCustomers(_AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncPaginator[Customer]:
        query = {"limit": limit, "cursor": cursor, "search": search}
        return self._page(Customer, "/v1/customers", query, _opts(None, timeout, max_retries, extra_headers))

    async def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Customer:
        return await self._client.request(
            Customer, "GET", f"/v1/customers/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )


class AsyncDrivers(_AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncPaginator[Driver]:
        query = {"limit": limit, "cursor": cursor, "search": search}
        return self._page(Driver, "/v1/drivers", query, _opts(None, timeout, max_retries, extra_headers))


class AsyncLocations(_AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        search: str | None = None,
        customer_id: str | None = None,
        has_coordinates: bool | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncPaginator[Location]:
        query = {
            "limit": limit,
            "cursor": cursor,
            "search": search,
            "customer_id": customer_id,
            "has_coordinates": has_coordinates,
        }
        return self._page(Location, "/v1/locations", query, _opts(None, timeout, max_retries, extra_headers))

    async def create(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CreateLocation],
    ) -> Location:
        return await self._client.request(
            Location,
            "POST",
            "/v1/locations",
            body=dict(params),
            **_opts(idempotency_key, timeout, max_retries, extra_headers),
        )

    async def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Location:
        return await self._client.request(
            Location, "GET", f"/v1/locations/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )


class AsyncPriceSets(_AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        active: bool | None = None,
        customer_id: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncPaginator[PriceSet]:
        query = {"limit": limit, "cursor": cursor, "active": active, "customer_id": customer_id}
        return self._page(PriceSet, "/v1/price_sets", query, _opts(None, timeout, max_retries, extra_headers))

    async def retrieve(
        self,
        id: str,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> PriceSet:
        return await self._client.request(
            PriceSet, "GET", f"/v1/price_sets/{path_param('id', id)}", **_opts(None, timeout, max_retries, extra_headers)
        )
