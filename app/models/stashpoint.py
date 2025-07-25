import uuid
from datetime import datetime
from geoalchemy2.types import Geography
from sqlalchemy import Index, event
from app import db


class Stashpoint(db.Model):
    """A location where bags can be stored"""

    __tablename__ = "stashpoints"

    id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
    created_at = db.Column(
        db.DateTime(timezone=False), nullable=False, default=datetime.utcnow
    )

    # Basic details
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

    # Coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Spatial column for optimized geo queries
    location = db.Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    # Storage details
    capacity = db.Column(db.Integer, nullable=False)

    # Opening hours (simplified for interview test)
    open_from = db.Column(db.Time, nullable=False)
    open_until = db.Column(db.Time, nullable=False)

    # Relationships
    bookings = db.relationship("Booking", back_populates="stashpoint", lazy="dynamic")

    __table_args__ = (
        Index("idx_stashpoints_location", "location", postgresql_using="gist"),
    )

    def to_dict(self):
        """Convert the model to a dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity": self.capacity,
            "open_from": self.open_from.strftime("%H:%M") if self.open_from else None,
            "open_until": (
                self.open_until.strftime("%H:%M") if self.open_until else None
            ),
        }


@event.listens_for(Stashpoint, "before_insert")
@event.listens_for(Stashpoint, "before_update")
def set_location_from_lat_lng(mapper, connection, target):
    """Automatically update the `location` geography point from lat/lng."""
    if target.latitude is not None and target.longitude is not None:
        target.location = f"POINT({target.longitude} {target.latitude})"
