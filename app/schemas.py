from marshmallow import Schema, fields, validate, post_load, ValidationError


class StashpointSearchQueryArgsSchema(Schema):
    """Schema for stashpoint search query parameters."""

    lat = fields.Float(
        required=True,
        validate=validate.Range(min=-90, max=90),
        description="Latitude for the search location.",
    )
    lng = fields.Float(
        required=True,
        validate=validate.Range(min=-180, max=180),
        description="Longitude for the search location.",
    )
    dropoff = fields.DateTime(
        format="iso",
        required=True,
        description="ISO 8601 datetime for drop-off (e.g., 2023-04-20T10:00:00Z).",
    )
    pickup = fields.DateTime(
        format="iso",
        required=True,
        description="ISO 8601 datetime for pick-up (e.g., 2023-04-20T18:00:00Z).",
    )
    bag_count = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        description="Number of bags to store.",
    )
    radius_km = fields.Float(
        validate=validate.Range(min=0, min_inclusive=False),
        description="Search radius in kilometers. Defaults to a configured value (e.g., 10km).",
    )

    @post_load
    def validate_dates(self, data, **kwargs):
        """Ensure pickup datetime is after dropoff datetime."""
        if "dropoff" in data and "pickup" in data and data["pickup"] <= data["dropoff"]:
            raise ValidationError(
                "Pickup datetime must be after dropoff datetime.", "pickup"
            )
        return data


class StashpointSearchResultSchema(Schema):
    """Schema for a stashpoint in search results."""

    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    address = fields.Str(dump_only=True)
    latitude = fields.Float(dump_only=True)
    longitude = fields.Float(dump_only=True)
    distance_km = fields.Float(dump_only=True)
    capacity = fields.Int(dump_only=True)
    available_capacity = fields.Int(dump_only=True)
    open_from = fields.Str(dump_only=True, description="Opening time in HH:MM format.")
    open_until = fields.Str(
        dump_only=True, description="Closing time in HH:MM format."
    )