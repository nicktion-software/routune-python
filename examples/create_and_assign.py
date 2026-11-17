"""python examples/create_and_assign.py <customer_id> <pickup_location_id> <dropoff_location_id>"""

import sys
from datetime import datetime, timedelta, timezone

import routune
from routune import Routune


def main() -> None:
    customer_id, pickup_id, dropoff_id = sys.argv[1:4]
    client = Routune()
    now = datetime.now(timezone.utc)

    price_set = client.price_sets.list(active=True, limit=1).data[0]
    order = client.orders.create(
        customer_id=customer_id,
        price_set_id=price_set.id,
        gross_weight=5,
        chargeable_weight=5,
        reference_number=f"example-{int(now.timestamp())}",
        pickup={
            "location_id": pickup_id,
            "earliest_time": (now + timedelta(minutes=30)).isoformat(),
            "latest_time": (now + timedelta(minutes=90)).isoformat(),
        },
        dropoff={
            "location_id": dropoff_id,
            "earliest_time": (now + timedelta(hours=2)).isoformat(),
            "latest_time": (now + timedelta(hours=4)).isoformat(),
            "signature_required": True,
        },
    )
    print("created", order.id, order.number)

    legs = client.orders.retrieve(order.id).legs or []
    drivers = client.drivers.list(limit=1).data
    if legs and drivers:
        assignment = client.orders.legs.assign(order.id, legs[0].id, driver_id=drivers[0].id)
        print("assigned", assignment.driver_id, "to leg", assignment.leg_id)


if __name__ == "__main__":
    try:
        main()
    except routune.APIError as err:
        print(err, file=sys.stderr)
        sys.exit(1)
