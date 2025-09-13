# --- FILE: backend/main.py ---
import logging
from flask import Flask, jsonify, request, Response  # Import Response
from pydantic import ValidationError

from config import settings
from core.analyzer import Analyzer
from models import AnalysisRequest
from utils.logging_config import setup_logging
from utils.url_validator import validate_and_resolve_url

# Set up logging as the first step
setup_logging()

# Initialize the Flask app and our Analyzer
app = Flask(__name__)
analyzer = Analyzer()


@app.route("/", methods=["POST"])
def veracity_engine_api():
    """
    The main Cloud Function entry point.
    Handles incoming analysis requests.
    """
    if not request.is_json:
        logging.error("Request is not JSON.")
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415

    try:
        request_data = AnalysisRequest.model_validate(request.get_json())
        logging.info(f"Received analysis request for URL: {request_data.url}")

        validated_url = validate_and_resolve_url(str(request_data.url))
        result = analyzer.analyze(validated_url)

        # CORRECTED: Use a Response object to ensure the Content-Type header is set.
        return Response(result.model_dump_json(), mimetype="application/json"), 200

    except ValidationError as e:
        logging.warning(f"Request validation failed: {e}")
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400
    except ValueError as e:
        logging.warning(f"Input validation failed: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.critical(f"An unexpected server error occurred: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500


# This entry point is used by the functions-framework for local development
if __name__ == "__main__":
    # Note: The 'PORT' setting is not standard in pydantic-settings,
    # so we'll default to 8080 for local runs.
    port = int(settings.PORT) if hasattr(settings, 'PORT') else 8080
    app.run(host="0.0.0.0", port=port, debug=True)