import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base config."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-for-interview-app")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost/stasher_interview"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(Config):
    """Development config."""

    DEBUG = True


class ProdConfig(Config):
    """Production config."""

    DEBUG = False


class TestConfig(Config):
    """Testing config."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost/stasher_interview_test",
    )


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    if env == "production":
        return ProdConfig
    elif env == "testing":
        return TestConfig
    return DevConfig
