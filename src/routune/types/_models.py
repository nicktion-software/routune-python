# Generated from openapi/routune-public.v1.json (API 1.0.0) by scripts/generate.py.
# Do not edit by hand: run `python scripts/generate.py`.
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field
from routune._models import BaseModel


class Address(BaseModel):
    name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = Field(None, examples=["US"])
    latitude: float | None = None
    longitude: float | None = None


class OrderStop(BaseModel):
    location_id: str | None = None
    address: Address | None = None
    earliest_time: datetime | None = None
    latest_time: datetime | None = None
    actual_time: datetime | None = None


class DriverRef(BaseModel):
    id: str
    name: str | None = None


class Dimensions(BaseModel):
    length: float | None = None
    width: float | None = None
    height: float | None = None


class OrderAmounts(BaseModel):
    currency: str = Field(..., examples=["usd"])
    base: float
    """
    Minor units (cents).
    """
    fuel_surcharge: float
    accessorials: float
    tax: float
    total: float


class OrderLeg(BaseModel):
    id: str
    sequence: float
    status: Literal["pending", "in_transit", "completed", "cancelled"] | str
    assigned_driver_id: str | None = None
    pickup_location_id: str | None = None
    dropoff_location_id: str | None = None
    completed_at: datetime | None = None


class Order(BaseModel):
    id: str
    object: Literal["order"] | str
    number: str = Field(..., examples=["ORD-000123"])
    status: Literal[
        "created", "in_progress", "delivered", "returned", "cancelled", "on_hold"
    ] | str
    sub_status: str | None = None
    customer_id: str | None = None
    price_set_id: str | None = None
    reference_number: str | None = None
    pickup: OrderStop
    dropoff: OrderStop
    assigned_driver: DriverRef | None = None
    quantity: float
    gross_weight: float
    chargeable_weight: float
    volumetric_weight: float | None = None
    weight_unit: str | None = Field(None, examples=["kg"])
    dimensions: Dimensions | None = None
    amounts: OrderAmounts
    dispatcher_notes: str | None = None
    driver_notes: str | None = None
    legs: list[OrderLeg] | None = None
    """
    Only on GET /v1/orders/{id}, POST and PATCH responses.
    """
    created_at: datetime
    updated_at: datetime


class OrderList(BaseModel):
    object: Literal["list"] | str
    has_more: bool
    next_cursor: str | None = None
    data: list[Order]


class OrderStopInput(BaseModel):
    location_id: str
    """
    A location id (GET /v1/locations or POST /v1/locations).
    """
    earliest_time: datetime
    latest_time: datetime
    signature_required: bool | None = None
    """
    Ask the driver for a signature here.
    """
    photo_required: bool | None = None
    """
    Ask the driver for photos here.
    """
    min_photos: float | None = Field(None, ge=0.0, le=10.0)


class OrderItemInput(BaseModel):
    gross_weight_kg: float = Field(..., ge=0.0)
    quantity: float | None = Field(None, ge=1.0)
    description: str | None = Field(None, max_length=500)
    barcode: str | None = Field(None, max_length=255)
    sku_code: str | None = Field(None, max_length=100)
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    declared_value: float | None = None
    """
    In major units, e.g. 129.99.
    """
    declared_value_currency: str | None = Field(None, examples=["USD"])


class CreateOrder(BaseModel):
    customer_id: str
    price_set_id: str
    """
    GET /v1/price_sets.
    """
    pickup: OrderStopInput
    dropoff: OrderStopInput
    gross_weight: float = Field(..., ge=0.0)
    """
    In the workspace weight unit.
    """
    chargeable_weight: float = Field(..., ge=0.0)
    """
    Weight used for pricing.
    """
    volumetric_weight: float | None = Field(None, ge=0.0)
    quantity: float | None = Field(None, ge=1.0)
    """
    Number of pieces.
    """
    dimensions: Dimensions | None = None
    reference_number: str | None = Field(None, max_length=100)
    """
    Your own reference (e.g. ERP order number).
    """
    dispatcher_notes: str | None = Field(None, max_length=2000)
    driver_notes: str | None = Field(None, max_length=2000)
    items: list[OrderItemInput] | None = None


class OrderStopTimesInput(BaseModel):
    earliest_time: datetime | None = None
    latest_time: datetime | None = None


class UpdateOrder(BaseModel):
    pickup: OrderStopTimesInput | None = None
    dropoff: OrderStopTimesInput | None = None
    gross_weight: float | None = Field(None, ge=0.0)
    chargeable_weight: float | None = Field(None, ge=0.0)
    volumetric_weight: float | None = Field(None, ge=0.0)
    quantity: float | None = Field(None, ge=1.0)
    dimensions: Dimensions | None = None
    reference_number: str | None = Field(None, max_length=100)
    dispatcher_notes: str | None = Field(None, max_length=2000)
    driver_notes: str | None = Field(None, max_length=2000)
    status: Literal["on_hold", "cancelled", "created", "in_progress"] | str | None = None
    """
    Put the order on hold, cancel it, or resume it from hold (created / in_progress). Delivery progress comes from the driver.
    """
    status_reason: str | None = Field(None, max_length=500)
    """
    Required with on_hold and cancelled.
    """


class AssignLegDriver(BaseModel):
    driver_id: str
    """
    GET /v1/drivers.
    """
    expected_current_driver_id: str | None = None
    """
    The driver you expect on the leg now. Omit or null to assign an unassigned leg; set it to reassign. A mismatch returns 409 assignment_changed.
    """


class LegAssignment(BaseModel):
    object: Literal["leg_assignment"] | str
    order_id: str
    leg_id: str
    previous_driver_id: str | None = None
    driver_id: str
    assigned_at: datetime


class Customer(BaseModel):
    id: str
    object: Literal["customer"] | str
    name: str
    code: str | None = None
    email: str | None = None
    phone: str | None = None
    tax_number: str | None = None
    currency: str = Field(..., examples=["usd"])
    payment_term: str
    active: bool
    created_at: datetime
    updated_at: datetime


class CustomerList(BaseModel):
    object: Literal["list"] | str
    has_more: bool
    next_cursor: str | None = None
    data: list[Customer]


class Driver(BaseModel):
    id: str
    object: Literal["driver"] | str
    name: str | None = None
    email: str | None = None
    created_at: datetime


class DriverList(BaseModel):
    object: Literal["list"] | str
    has_more: bool
    next_cursor: str | None = None
    data: list[Driver]


class Location(BaseModel):
    id: str
    object: Literal["location"] | str
    code: str | None = None
    customer_id: str | None = None
    address: Address
    type: str | None = None
    notes: str | None = None
    service_time_minutes: float | None = None
    created_at: datetime
    updated_at: datetime


class LocationList(BaseModel):
    object: Literal["list"] | str
    has_more: bool
    next_cursor: str | None = None
    data: list[Location]


class CreateLocation(BaseModel):
    name: str = Field(..., max_length=255)
    address_line1: str = Field(..., max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str | None = Field(None, examples=["CA"], max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., examples=["US"])
    """
    ISO 3166-1 alpha-2.
    """
    latitude: float = Field(..., ge=-90.0, le=90.0)
    """
    Required: orders need coordinates to route and price.
    """
    longitude: float = Field(..., ge=-180.0, le=180.0)
    customer_id: str | None = None
    """
    Belongs to this customer.
    """
    code: str | None = Field(None, max_length=50)
    """
    Your own unique code.
    """
    notes: str | None = Field(None, max_length=2000)
    service_time_minutes: float | None = Field(None, ge=0.0, le=480.0)


class PriceSet(BaseModel):
    id: str
    object: Literal["price_set"] | str
    name: str
    display_name: str | None = None
    description: str | None = None
    currency: str = Field(..., examples=["usd"])
    active: bool
    active_from: date | None = None
    active_until: date | None = None
    customer_ids: list[str]
    """
    Customers this price set is limited to; empty = everyone.
    """
    created_at: datetime
    updated_at: datetime


class PriceSetList(BaseModel):
    object: Literal["list"] | str
    has_more: bool
    next_cursor: str | None = None
    data: list[PriceSet]


class Error1(BaseModel):
    type: Literal[
        "authentication_error",
        "permission_error",
        "invalid_request_error",
        "billing_error",
        "rate_limit_error",
        "api_error",
    ] | str
    code: str = Field(..., examples=["api_key_revoked"])
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


class Error(BaseModel):
    error: Error1
