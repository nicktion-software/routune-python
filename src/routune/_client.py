from __future__ import annotations

from typing import Mapping

import httpx

from ._base_client import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, AsyncAPIClient, SyncAPIClient
from .resources import (
    AsyncCustomers,
    AsyncDrivers,
    AsyncLocations,
    AsyncOrders,
    AsyncPriceSets,
    Customers,
    Drivers,
    Locations,
    Orders,
    PriceSets,
)


class Routune(SyncAPIClient):
    """Routune API client.

    >>> from routune import Routune
    >>> client = Routune()  # reads ROUTUNE_API_KEY
    >>> order = client.orders.retrieve("...")
    """

    orders: Orders
    customers: Customers
    drivers: Drivers
    locations: Locations
    price_sets: PriceSets

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.orders = Orders(self)
        self.customers = Customers(self)
        self.drivers = Drivers(self)
        self.locations = Locations(self)
        self.price_sets = PriceSets(self)


class AsyncRoutune(AsyncAPIClient):
    """Async Routune API client (same methods as :class:`Routune`, awaitable)."""

    orders: AsyncOrders
    customers: AsyncCustomers
    drivers: AsyncDrivers
    locations: AsyncLocations
    price_sets: AsyncPriceSets

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.orders = AsyncOrders(self)
        self.customers = AsyncCustomers(self)
        self.drivers = AsyncDrivers(self)
        self.locations = AsyncLocations(self)
        self.price_sets = AsyncPriceSets(self)
