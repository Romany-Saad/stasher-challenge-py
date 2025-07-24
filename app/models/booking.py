import uuid
from datetime import datetime
from sqlalchemy import Index
from app import db


class Booking(db.Model):
    """Represents a customer's booking to store bags at a stashpoint"""

    __tablename__ = "bookings"

    id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
    created_at = db.Column(
        db.DateTime(timezone=False), nullable=False, default=datetime.utcnow
    )

    # Booking details
    bag_count = db.Column(db.Integer, nullable=False, default=1)
    dropoff_time = db.Column(db.DateTime(timezone=False), nullable=False)
    pickup_time = db.Column(db.DateTime(timezone=False), nullable=False)

    # Status fields
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    is_cancelled = db.Column(db.Boolean, nullable=False, default=False)
    checked_in = db.Column(db.Boolean, nullable=False, default=False)
    checked_out = db.Column(db.Boolean, nullable=False, default=False)

    # Foreign keys
    stashpoint_id = db.Column(
        db.String, db.ForeignKey("stashpoints.id"), nullable=False
    )
    customer_id = db.Column(
        db.String, db.ForeignKey("customers.id"), nullable=False, index=True
    )

    # Relationships
    stashpoint = db.relationship("Stashpoint", back_populates="bookings")
    customer = db.relationship("Customer", back_populates="bookings")

    __table_args__ = (
        Index(
            "idx_booking_availability", "stashpoint_id", "dropoff_time", "pickup_time"
        ),
    )

    def to_dict(self):
        """Convert the model to a dictionary for API responses"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() + "Z",
            "bag_count": self.bag_count,
            "dropoff_time": self.dropoff_time.isoformat() + "Z",
            "pickup_time": self.pickup_time.isoformat() + "Z",
            "is_paid": self.is_paid,
            "is_cancelled": self.is_cancelled,
            "checked_in": self.checked_in,
            "checked_out": self.checked_out,
            "stashpoint_id": self.stashpoint_id,
            "customer_id": self.customer_id,
        }
