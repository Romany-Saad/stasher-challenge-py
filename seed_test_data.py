#!/usr/bin/env python3
"""
Script to seed test data for the interview challenge
Creates stashpoints, customers, and bookings with varied times and bag counts
"""

import random
from datetime import datetime, timedelta, time
from app import create_app, db
from app.models import Stashpoint, Customer, Booking


def seed_data():
    """Seed the database with test data"""
    print("Creating test data...")

    # Clear existing data
    Booking.query.delete()
    Customer.query.delete()
    Stashpoint.query.delete()
    db.session.commit()

    # Create stashpoints - mix of city center and transportation hubs
    stashpoints = [
        # City center locations
        Stashpoint(
            name="Central Cafe Storage",
            description="Cafe in the heart of the city with secure bag storage",
            address="123 Main Street",
            postal_code="EC1A 1AA",
            latitude=51.5107,
            longitude=-0.1246,
            capacity=20,
            open_from=time(8, 0),
            open_until=time(22, 0),
        ),
        Stashpoint(
            name="Downtown Hotel Lockers",
            description="24/7 hotel lockers with staff assistance",
            address="45 Park Avenue",
            postal_code="EC2A 2BB",
            latitude=51.5173,
            longitude=-0.0850,
            capacity=50,
            open_from=time(0, 0),
            open_until=time(23, 59),
        ),
        Stashpoint(
            name="Market Square Shop",
            description="Friendly local shop offering bag storage",
            address="8 Market Square",
            postal_code="EC3M 3CC",
            latitude=51.5128,
            longitude=-0.0849,
            capacity=15,
            open_from=time(9, 0),
            open_until=time(18, 0),
        ),
        # Transportation hubs
        Stashpoint(
            name="Central Station Lockers",
            description="Automated lockers at the main train station",
            address="Central Station, Platform 1",
            postal_code="NW1 2DX",
            latitude=51.5282,
            longitude=-0.1340,
            capacity=100,
            open_from=time(5, 0),
            open_until=time(23, 59),
        ),
        Stashpoint(
            name="Airport Express Storage",
            description="Convenient bag drop at airport express station",
            address="Airport Link, Terminal 1",
            postal_code="TW6 1EW",
            latitude=51.4700,
            longitude=-0.4543,
            capacity=80,
            open_from=time(4, 30),
            open_until=time(23, 30),
        ),
        # Tourist areas
        Stashpoint(
            name="Museum District Lockers",
            description="Self-service lockers near major museums",
            address="15 Exhibition Road",
            postal_code="SW7 2DD",
            latitude=51.4969,
            longitude=-0.1764,
            capacity=30,
            open_from=time(9, 30),
            open_until=time(18, 30),
        ),
        Stashpoint(
            name="Riverside Cafe Storage",
            description="Scenic cafe by the river offering secure storage",
            address="27 River Walk",
            postal_code="SE1 7GP",
            latitude=51.5074,
            longitude=-0.0982,
            capacity=12,
            open_from=time(8, 0),
            open_until=time(20, 0),
        ),
    ]

    # Add stashpoints to database
    for stashpoint in stashpoints:
        db.session.add(stashpoint)
    db.session.commit()
    print(f"Created {len(stashpoints)} stashpoints")

    # Create customers
    customers = [
        Customer(name="John Smith", email="john.smith@example.com"),
        Customer(name="Jane Doe", email="jane.doe@example.com"),
        Customer(name="Alice Johnson", email="alice.j@example.com"),
        Customer(name="Bob Williams", email="bob.w@example.com"),
        Customer(name="Charlie Brown", email="charlie.b@example.com"),
        Customer(name="Diana Prince", email="diana.p@example.com"),
        Customer(name="Edward Norton", email="edward.n@example.com"),
        Customer(name="Fiona Apple", email="fiona.a@example.com"),
    ]

    # Add customers to database
    for customer in customers:
        db.session.add(customer)
    db.session.commit()
    print(f"Created {len(customers)} customers")

    # Create bookings over a 30-day period
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bookings = []

    # Generate 100 bookings with various parameters
    for _ in range(100):
        # Choose random customer and stashpoint
        customer = random.choice(customers)
        stashpoint = random.choice(stashpoints)

        # Generate random dates within 30 days (both past and future)
        days_offset_start = random.randint(-10, 20)  # -10 to +20 days from today
        start_date = today + timedelta(days=days_offset_start)

        # Random hour based on stashpoint opening hours
        open_hour = stashpoint.open_from.hour
        close_hour = (
            stashpoint.open_until.hour if stashpoint.open_until.hour > 0 else 23
        )

        dropoff_hour = random.randint(open_hour, close_hour - 1)
        dropoff_time = start_date.replace(hour=dropoff_hour)

        # Stay duration between 2 hours and 5 days
        duration_type = random.choices(["hours", "days"], weights=[70, 30], k=1)[0]
        if duration_type == "hours":
            duration = random.randint(2, 8)  # 2-8 hours
            pickup_time = dropoff_time + timedelta(hours=duration)
        else:
            duration = random.randint(1, 5)  # 1-5 days
            pickup_hour = random.randint(open_hour, close_hour)
            pickup_time = (start_date + timedelta(days=duration)).replace(
                hour=pickup_hour
            )

        # Random number of bags (1-4)
        bag_count = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5], k=1)[0]

        # Create booking
        booking = Booking(
            customer_id=customer.id,
            stashpoint_id=stashpoint.id,
            bag_count=bag_count,
            dropoff_time=dropoff_time,
            pickup_time=pickup_time,
            is_paid=random.choices([True, False], weights=[90, 10], k=1)[0],
            is_cancelled=random.choices([True, False], weights=[5, 95], k=1)[0],
            checked_in=(
                random.choices([True, False], weights=[60, 40], k=1)[0]
                if dropoff_time < datetime.utcnow()
                else False
            ),
            checked_out=(
                random.choices([True, False], weights=[40, 60], k=1)[0]
                if dropoff_time < datetime.utcnow() and pickup_time < datetime.utcnow()
                else False
            ),
        )

        bookings.append(booking)

    # Add bookings to database
    for booking in bookings:
        db.session.add(booking)
    db.session.commit()
    print(f"Created {len(bookings)} bookings")

    # Create some particularly busy periods for specific stashpoints
    busy_stashpoint = stashpoints[0]  # Central Cafe Storage
    busy_date = today + timedelta(days=1)  # Tomorrow

    # Create almost-full capacity for this stashpoint on the busy date
    remaining_capacity = max(
        1, busy_stashpoint.capacity - 2
    )  # Leave 1-2 spots available

    busy_bookings = []
    for i in range(remaining_capacity):
        customer = random.choice(customers)
        dropoff_time = busy_date.replace(hour=10, minute=0)
        pickup_time = busy_date.replace(hour=18, minute=0)

        booking = Booking(
            customer_id=customer.id,
            stashpoint_id=busy_stashpoint.id,
            bag_count=1,  # 1 bag each to maximize count
            dropoff_time=dropoff_time,
            pickup_time=pickup_time,
            is_paid=True,
            is_cancelled=False,
            checked_in=False,
            checked_out=False,
        )
        busy_bookings.append(booking)

    # Add busy period bookings
    for booking in busy_bookings:
        db.session.add(booking)
    db.session.commit()
    print(f"Created {len(busy_bookings)} additional bookings for busy period testing")

    # Create a completely full stashpoint for a specific time
    full_stashpoint = stashpoints[2]  # Market Square Shop
    full_date = today + timedelta(days=2)  # Day after tomorrow

    full_bookings = []
    bags_stored = 0
    while bags_stored < full_stashpoint.capacity:
        customer = random.choice(customers)
        dropoff_time = full_date.replace(hour=9, minute=30)
        pickup_time = full_date.replace(hour=17, minute=30)

        # Random bag count that doesn't exceed capacity
        max_bags = min(4, full_stashpoint.capacity - bags_stored)
        if max_bags <= 0:
            break

        bag_count = random.randint(1, max_bags)
        bags_stored += bag_count

        booking = Booking(
            customer_id=customer.id,
            stashpoint_id=full_stashpoint.id,
            bag_count=bag_count,
            dropoff_time=dropoff_time,
            pickup_time=pickup_time,
            is_paid=True,
            is_cancelled=False,
            checked_in=False,
            checked_out=False,
        )
        full_bookings.append(booking)

    # Add full stashpoint bookings
    for booking in full_bookings:
        db.session.add(booking)
    db.session.commit()
    print(f"Created {len(full_bookings)} additional bookings for full capacity testing")

    print("Test data creation complete!")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_data()
