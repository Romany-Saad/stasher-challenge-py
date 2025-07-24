import uuid
from datetime import datetime
from app import db


class Customer(db.Model):
    """Represents a customer who can make bookings"""

    __tablename__ = "customers"

    id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
    created_at = db.Column(
        db.DateTime(timezone=False), nullable=False, default=datetime.utcnow
    )

    # Customer details
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    # Relationships
    bookings = db.relationship("Booking", back_populates="customer", lazy="dynamic")

    def to_dict(self):
        """Convert the model to a dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() + "Z",
        }
