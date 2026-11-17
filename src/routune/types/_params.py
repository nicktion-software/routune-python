# Generated from openapi/routune-public.v1.json (API 1.0.0) by scripts/generate.py.
# Do not edit by hand: run `python scripts/generate.py`.
from __future__ import annotations

from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired


class Address(TypedDict):
    name: NotRequired[str]
    address_line1: NotRequired[str]
    address_line2: NotRequired[str]
    city: NotRequired[str]
    state: NotRequired[str]
    postal_code: NotRequired[str]
    country: NotRequired[str]
    latitude: NotRequired[float]
    longitude: NotRequired[float]


class OrderStop(TypedDict):
    location_id: NotRequired[str]
    address: NotRequired[Address]
    earliest_time: NotRequired[str]
    latest_time: NotRequired[str]
    actual_time: NotRequired[str]


class DriverRef(TypedDict):
    id: str
    name: NotRequired[str]


class Dimensions(TypedDict):
    length: NotRequired[float]
    width: NotRequired[float]
    height: NotRequired[float]


class OrderAmounts(TypedDict):
    currency: str
    base: float
    """
    Minor units (cents).
    """
    fuel_surcharge: float
    accessorials: float
    tax: float
    total: float


class OrderLeg(TypedDict):
    id: str
    sequence: float
    status: Literal["pending", "in_transit", "completed", "cancelled"]
    assigned_driver_id: NotRequired[str]
    pickup_location_id: NotRequired[str]
    dropoff_location_id: NotRequired[str]
    completed_at: NotRequired[str]


class Order(TypedDict):
    id: str
    object: Literal["order"]
    number: str
    status: Literal[
        "created", "in_progress", "delivered", "returned", "cancelled", "on_hold"
    ]
    sub_status: NotRequired[str]
    customer_id: NotRequired[str]
    price_set_id: NotRequired[str]
    reference_number: NotRequired[str]
    pickup: OrderStop
    dropoff: OrderStop
    assigned_driver: NotRequired[DriverRef]
    quantity: float
    gross_weight: float
    chargeable_weight: float
    volumetric_weight: NotRequired[float]
    weight_unit: NotRequired[str]
    dimensions: NotRequired[Dimensions]
    amounts: OrderAmounts
    dispatcher_notes: NotRequired[str]
    driver_notes: NotRequired[str]
    legs: NotRequired[list[OrderLeg]]
    """
    Only on GET /v1/orders/{id}, POST and PATCH responses.
    """
    created_at: str
    updated_at: str


class OrderList(TypedDict):
    object: Literal["list"]
    has_more: bool
    next_cursor: NotRequired[str]
    data: list[Order]


class OrderStopInput(TypedDict):
    location_id: str
    """
    A location id (GET /v1/locations or POST /v1/locations).
    """
    earliest_time: str
    latest_time: str
    signature_required: NotRequired[bool]
    """
    Ask the driver for a signature here.
    """
    photo_required: NotRequired[bool]
    """
    Ask the driver for photos here.
    """
    min_photos: NotRequired[float]


class OrderItemInput(TypedDict):
    gross_weight_kg: float
    quantity: NotRequired[float]
    description: NotRequired[str]
    barcode: NotRequired[str]
    sku_code: NotRequired[str]
    length_cm: NotRequired[float]
    width_cm: NotRequired[float]
    height_cm: NotRequired[float]
    declared_value: NotRequired[float]
    """
    In major units, e.g. 129.99.
    """
    declared_value_currency: NotRequired[str]


class CreateOrder(TypedDict):
    customer_id: str
    price_set_id: str
    """
    GET /v1/price_sets.
    """
    pickup: OrderStopInput
    dropoff: OrderStopInput
    gross_weight: float
    """
    In the workspace weight unit.
    """
    chargeable_weight: float
    """
    Weight used for pricing.
    """
    volumetric_weight: NotRequired[float]
    quantity: NotRequired[float]
    """
    Number of pieces.
    """
    dimensions: NotRequired[Dimensions]
    reference_number: NotRequired[str]
    """
    Your own reference (e.g. ERP order number).
    """
    dispatcher_notes: NotRequired[str]
    driver_notes: NotRequired[str]
    items: NotRequired[list[OrderItemInput]]


class OrderStopTimesInput(TypedDict):
    earliest_time: NotRequired[str]
    latest_time: NotRequired[str]


class UpdateOrder(TypedDict):
    pickup: NotRequired[OrderStopTimesInput]
    dropoff: NotRequired[OrderStopTimesInput]
    gross_weight: NotRequired[float]
    chargeable_weight: NotRequired[float]
    volumetric_weight: NotRequired[float]
    quantity: NotRequired[float]
    dimensions: NotRequired[Dimensions]
    reference_number: NotRequired[str]
    dispatcher_notes: NotRequired[str]
    driver_notes: NotRequired[str]
    status: NotRequired[Literal["on_hold", "cancelled", "created", "in_progress"]]
    """
    Put the order on hold, cancel it, or resume it from hold (created / in_progress). Delivery progress comes from the driver.
    """
    status_reason: NotRequired[str]
    """
    Required with on_hold and cancelled.
    """


class AssignLegDriver(TypedDict):
    driver_id: str
    """
    GET /v1/drivers.
    """
    expected_current_driver_id: NotRequired[str]
    """
    The driver you expect on the leg now. Omit or null to assign an unassigned leg; set it to reassign. A mismatch returns 409 assignment_changed.
    """


class LegAssignment(TypedDict):
    object: Literal["leg_assignment"]
    order_id: str
    leg_id: str
    previous_driver_id: NotRequired[str]
    driver_id: str
    assigned_at: str


class Customer(TypedDict):
    id: str
    object: Literal["customer"]
    name: str
    code: NotRequired[str]
    email: NotRequired[str]
    phone: NotRequired[str]
    tax_number: NotRequired[str]
    currency: str
    payment_term: str
    active: bool
    created_at: str
    updated_at: str


class CustomerList(TypedDict):
    object: Literal["list"]
    has_more: bool
    next_cursor: NotRequired[str]
    data: list[Customer]


class Driver(TypedDict):
    id: str
    object: Literal["driver"]
    name: NotRequired[str]
    email: NotRequired[str]
    created_at: str


class DriverList(TypedDict):
    object: Literal["list"]
    has_more: bool
    next_cursor: NotRequired[str]
    data: list[Driver]


class Location(TypedDict):
    id: str
    object: Literal["location"]
    code: NotRequired[str]
    customer_id: NotRequired[str]
    address: Address
    type: NotRequired[str]
    notes: NotRequired[str]
    service_time_minutes: NotRequired[float]
    created_at: str
    updated_at: str


class LocationList(TypedDict):
    object: Literal["list"]
    has_more: bool
    next_cursor: NotRequired[str]
    data: list[Location]


class CreateLocation(TypedDict):
    name: str
    address_line1: str
    address_line2: NotRequired[str]
    city: str
    state: NotRequired[str]
    postal_code: str
    country: str
    """
    ISO 3166-1 alpha-2.
    """
    latitude: float
    """
    Required: orders need coordinates to route and price.
    """
    longitude: float
    customer_id: NotRequired[str]
    """
    Belongs to this customer.
    """
    code: NotRequired[str]
    """
    Your own unique code.
    """
    notes: NotRequired[str]
    service_time_minutes: NotRequired[float]


class PriceSet(TypedDict):
    id: str
    object: Literal["price_set"]
    name: str
    display_name: NotRequired[str]
    description: NotRequired[str]
    currency: str
    active: bool
    active_from: NotRequired[str]
    active_until: NotRequired[str]
    customer_ids: list[str]
    """
    Customers this price set is limited to; empty = everyone.
    """
    created_at: str
    updated_at: str


class PriceSetList(TypedDict):
    object: Literal["list"]
    has_more: bool
    next_cursor: NotRequired[str]
    data: list[PriceSet]


class Error1(TypedDict):
    type: Literal[
        "authentication_error",
        "permission_error",
        "invalid_request_error",
        "billing_error",
        "rate_limit_error",
        "api_error",
    ]
    code: str
    message: str
    request_id: NotRequired[str]
    details: NotRequired[dict[str, Any]]


class Error(TypedDict):
    error: Error1
