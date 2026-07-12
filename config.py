"""
config.py
Application configuration loaded from environment variables.
No secrets are hardcoded here — all sensitive values must be supplied
via environment variables or a local .env file (never committed).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared across environments."""

    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-change-me")
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", 5000))

    # Dashboard behavior
    REFRESH_INTERVAL_MS: int = int(os.environ.get("REFRESH_INTERVAL_MS", 2000))
    TOP_PROCESS_LIMIT: int = int(os.environ.get("TOP_PROCESS_LIMIT", 10))

    # Health thresholds (percent)
    CPU_CRITICAL_THRESHOLD: float = float(os.environ.get("CPU_CRITICAL_THRESHOLD", 90))
    CPU_WARNING_THRESHOLD: float = float(os.environ.get("CPU_WARNING_THRESHOLD", 75))
    RAM_CRITICAL_THRESHOLD: float = float(os.environ.get("RAM_CRITICAL_THRESHOLD", 90))
    RAM_WARNING_THRESHOLD: float = float(os.environ.get("RAM_WARNING_THRESHOLD", 85))
    DISK_CRITICAL_THRESHOLD: float = float(os.environ.get("DISK_CRITICAL_THRESHOLD", 90))
    DISK_WARNING_THRESHOLD: float = float(os.environ.get("DISK_WARNING_THRESHOLD", 80))

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.environ.get("LOG_FILE", "logs/app.log")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "production")
    return config_by_name.get(env, ProductionConfig)()
