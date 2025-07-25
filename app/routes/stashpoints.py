from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from services.stashpoint_search_service import StashpointSearchService
from app.schemas import StashpointSearchQueryArgsSchema, StashpointSearchResultSchema


bp = Blueprint("stashpoints", __name__, description="Operations on stashpoints")


@bp.route("/")
class StashpointList(MethodView):
    @bp.arguments(StashpointSearchQueryArgsSchema, location="query")
    @bp.response(200, StashpointSearchResultSchema(many=True))
    def get(self, args):
        """Finds available stashpoints based on search criteria

        Finds available stashpoints based on location, drop-off/pick-up times,
        and number of bags.
        """
        # The service expects naive UTC datetimes.
        # Marshmallow parses ISO strings with 'Z' into timezone-aware datetimes.
        # We convert them to naive UTC datetimes here before passing to the service.
        dropoff_dt = args["dropoff"].replace(tzinfo=None)
        pickup_dt = args["pickup"].replace(tzinfo=None)

        radius_km = args.get(
            "radius_km", current_app.config.get("DEFAULT_SEARCH_RADIUS_KM", 10.0)
        )

        service = StashpointSearchService()
        available_stashpoints = service.find_available(
            lat=args["lat"],
            lng=args["lng"],
            dropoff_dt=dropoff_dt,
            pickup_dt=pickup_dt,
            bag_count=args["bag_count"],
            radius_km=radius_km,
        )
        return available_stashpoints
