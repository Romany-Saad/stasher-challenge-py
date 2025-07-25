from app import db
from app.models import Stashpoint, Booking
from sqlalchemy import func
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText


class StashpointSearchService:
    """
    A service class to handle the business logic for searching available stashpoints.
    """

    def find_available(self, lat, lng, dropoff_dt, pickup_dt, bag_count, radius_km):
        """
        Finds stashpoints based on location, time, and capacity.

        Args:
            lat (float): Latitude for the search location.
            lng (float): Longitude for the search location.
            dropoff_dt (datetime): The drop-off datetime (timezone-naive UTC).
            pickup_dt (datetime): The pick-up datetime (timezone-naive UTC).
            bag_count (int): The number of bags to store.
            radius_km (float): The search radius in kilometers.

        Returns:
            list: A list of available stashpoint dictionaries, enriched with
                  distance and available capacity.
        """
        # --- Stage 1: Geospatial + Opening Hours Filtering (Initial Query) ---
        from_geog = ST_GeogFromText(f"POINT({lng} {lat})")
        distance_km = (ST_Distance(Stashpoint.location, from_geog) / 1000).label(
            "distance_km"
        )

        candidate_query = db.session.query(Stashpoint, distance_km).filter(
            ST_DWithin(Stashpoint.location, from_geog, radius_km * 1000)
        ).filter(
            Stashpoint.open_from <= dropoff_dt.time(),
            Stashpoint.open_until >= pickup_dt.time(),
        ).order_by("distance_km")

        candidate_stashpoints = candidate_query.all()

        # --- Stage 2: Capacity Filtering (Secondary Check) ---
        available_stashpoints = []
        for stashpoint, dist in candidate_stashpoints:
            # For each candidate, check for overlapping bookings to calculate available capacity
            booked_bags = db.session.query(func.sum(Booking.bag_count)).filter(
                Booking.stashpoint_id == stashpoint.id,
                Booking.is_cancelled == False,
                Booking.dropoff_time < pickup_dt,
                Booking.pickup_time > dropoff_dt,
            ).scalar() or 0

            available_capacity = stashpoint.capacity - booked_bags
            if available_capacity >= bag_count:
                sp_dict = stashpoint.to_dict()
                sp_dict["distance_km"] = round(dist, 2)
                sp_dict["available_capacity"] = available_capacity
                available_stashpoints.append(sp_dict)

        return available_stashpoints