from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_smorest import Api

# Initialize SQLAlchemy without binding to a specific Flask app
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        # Import here to avoid circular imports
        from config import get_config

        app.config.from_object(get_config())

    # OpenAPI/Swagger-UI configuration
    app.config["API_TITLE"] = "Stasher Challenge API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    api = Api(app)

    # Register blueprints
    from app.routes.stashpoints import bp as stashpoints_bp

    api.register_blueprint(stashpoints_bp, url_prefix="/api/v1/stashpoints")

    @app.route("/healthcheck")
    def healthcheck():
        return {"status": "healthy"}

    return app
