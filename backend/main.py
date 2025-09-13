# --- FILE: backend/main.py ---
import logging
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pydantic import ValidationError

from config import settings
from core.analyzer import Analyzer
from models import AnalysisRequest
from utils.logging_config import setup_logging
from utils.url_validator import validate_and_resolve_url

setup_logging()

app = Flask(__name__)
analyzer = Analyzer()
CORS(app)  # This handles adding the correct CORS headers

def veracity_engine_api(request):
    """
    The main Cloud Function entry point.
    Handles incoming analysis requests.
    """
    # This is a requirement for the Flask app context to work correctly
    # with the functions-framework.
    with app.request_context(request.environ):
        # NEW: Handle the browser's preflight OPTIONS request
        if request.method == "OPTIONS":
            # The CORS library will add the necessary headers to this response
            return Response(status=204)

        if not request.is_json:
            return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415

        try:
            request_data = AnalysisRequest.model_validate(request.get_json())
            validated_url = validate_and_resolve_url(str(request_data.url))
            result = analyzer.analyze(validated_url)
            return Response(result.model_dump_json(), mimetype="application/json"), 200

        except ValidationError as e:
            return jsonify({"error": "Invalid request body", "details": e.errors()}), 400
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logging.critical(f"An unexpected server error occurred: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500