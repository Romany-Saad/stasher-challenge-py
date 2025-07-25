from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from app.models import Stashpoint
from services.stashpoint_search_service import StashpointSearchService


bp = Blueprint("stashpoints", __name__)


@bp.route("/", methods=["GET"])
def get_stashpoints():
    """
    Finds available stashpoints based on search criteria or lists all if no
    search parameters are provided.

    If the 'lat' query parameter is present, a search is performed. All other
    search parameters then become mandatory.

    Query Parameters (for search):
        lat (float): Latitude for the search location.
        lng (float): Longitude for the search location.
        dropoff (str): ISO 8601 datetime for drop-off (e.g., 2023-04-20T10:00:00Z).
        pickup (str): ISO 8601 datetime for pick-up (e.g., 2023-04-20T18:00:00Z).
        bag_count (int): Number of bags to store.
        radius_km (float, optional): Search radius in kilometers. Defaults to 10km.

    Returns:
        A JSON response containing a list of stashpoints. If searching, the
        stashpoints are filtered by availability and enriched with distance
        and available capacity.
        Returns a 400 error with a dictionary of validation issues if search
        parameters are invalid.
    """
    # --- It's a search request. Proceed with validation. ---
    errors = {}
    args = request.args

    # --- 1. Extract and Validate Parameters ---
    try:
        lat = float(args.get("lat"))
        if not -90 <= lat <= 90:
            errors["lat"] = "Latitude must be between -90 and 90."
    except (ValueError, TypeError, AttributeError):
        errors["lat"] = "Invalid or missing 'lat' parameter. Must be a float."

    try:
        lng = float(args.get("lng"))
        if not -180 <= lng <= 180:
            errors["lng"] = "Longitude must be between -180 and 180."
    except (ValueError, TypeError, AttributeError):
        errors["lng"] = "Invalid or missing 'lng' parameter. Must be a float."

    try:
        bag_count = int(args.get("bag_count"))
        if bag_count < 1:
            errors["bag_count"] = "Bag count cannot be less than 1."
    except (ValueError, TypeError, AttributeError):
        errors["bag_count"] = (
            "Invalid or missing 'bag_count' parameter. Must be an integer > 0."
        )

    radius_km_str = args.get("radius_km")
    if radius_km_str:
        try:
            radius_km = float(radius_km_str)
            if radius_km <= 0:
                errors["radius_km"] = "Search radius must be a positive number."
        except (ValueError, TypeError):
            errors["radius_km"] = "Invalid radius format. Must be a float."
    else:
        radius_km = current_app.config.get("DEFAULT_SEARCH_RADIUS_KM", 10.0)

    dropoff_dt, pickup_dt = None, None
    for key in ["dropoff", "pickup"]:
        dt_str = args.get(key)
        if not dt_str:
            errors[key] = f"Missing '{key}' query parameter."
        else:
            try:
                # The service expects naive UTC datetimes. Remove 'Z' if present.
                if dt_str.upper().endswith("Z"):
                    dt_str = dt_str[:-1]
                dt_val = datetime.fromisoformat(dt_str)
                if key == "dropoff":
                    dropoff_dt = dt_val
                else:
                    pickup_dt = dt_val
            except (ValueError, TypeError):
                errors[key] = (
                    f"Invalid {key} datetime format. Must be ISO 8601 (e.g., 2023-04-20T10:00:00Z)."
                )

    if dropoff_dt and pickup_dt and pickup_dt <= dropoff_dt:
        errors["pickup"] = "Pickup datetime must be after dropoff datetime."

    if errors:
        return jsonify({"errors": errors}), 400

    # --- 2. Call the search service ---
    service = StashpointSearchService()
    available_stashpoints = service.find_available(
        lat=lat,
        lng=lng,
        dropoff_dt=dropoff_dt,
        pickup_dt=pickup_dt,
        bag_count=bag_count,
        radius_km=radius_km,
    )

    return jsonify(available_stashpoints)
