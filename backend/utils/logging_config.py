import logging
import os
import sys

from google.cloud.logging import Client as CloudLoggingClient
from google.cloud.logging.handlers import CloudLoggingHandler


def setup_logging():
    """
    Set up application logging.

    - In a 'production' environment (as determined by APP_ENV), it configures
      a handler to send logs to Google Cloud Logging.
    - In a 'development' or other environment, it configures a standard
      stream handler to output logs to the console.
    - The log level is determined by the LOG_LEVEL environment variable.
    """
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    app_env = os.environ.get("APP_ENV", "development")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    if app_env == "production":
        try:
            # Set up Google Cloud Logging
            client = CloudLoggingClient()
            handler = CloudLoggingHandler(client, name="veracity-engine-backend")
            root_logger.addHandler(handler)
            logging.info("Production logging enabled (Google Cloud Logging).")
        except Exception as e:
            # Fallback to console logging if GCP setup fails
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s - %(name)s - %(levelname)s - [GCP_FALLBACK] - %(message)s",
            )
            logging.critical(f"Failed to set up Google Cloud Logging: {e}")
    else:
        # Set up local console logging
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        logging.info(
            f"Development logging enabled (console output) at level {log_level_str}."
        )
