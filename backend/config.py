# --- FILE: backend/config.py ---
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Manages application settings and secrets.
    It reads environment variables from a .env file for local development.
    """

    # Model configuration
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Google Cloud Project ID
    GCP_PROJECT_ID: str

    # API Keys
    GEMINI_API_KEY: str
    GOOGLE_API_KEY: str

    # Application Settings
    LOG_LEVEL: str = "INFO"
    APP_ENV: str = "development"


# Create a single, globally accessible instance of the settings.
# Other modules can import this `settings` object to access config values.
try:
    settings = Settings()
except Exception as e:
    logging.critical(f"FATAL: Could not load application settings. Error: {e}")
    # In a real application, you might exit here if settings are essential
    # for the app to function at all.
    raise ValueError(f"Configuration error: {e}") from e