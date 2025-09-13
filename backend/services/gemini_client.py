# --- FILE: backend/services/gemini_client.py ---
import json
import logging
import re
import requests
from requests.adapters import HTTPAdapter, Retry

from config import settings
from models import GeminiAnalysis

# Constants
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-1.5-flash-latest"
REQUEST_TIMEOUT_SECONDS = 60  # Increased timeout to 60 seconds
MAX_CONTENT_CHARS = 30000     # Limit content to ~30k characters to ensure performance

# (The SYSTEM_PROMPT remains the same as before)
SYSTEM_PROMPT = """
You are the Veracity Engine. Your task is to analyze the provided text content and
determine its credibility. You must respond with a JSON object that strictly
adheres to the following structure:
{
  "credibility_score": integer (0-100, where 100 is highly credible),
  "summary": "string (a neutral, one-sentence summary of the content)",
  "detected_flags": ["string", ...],
  "reasoning": "string (a brief explanation for your score and flags)"
}

The possible flags are:
- "emotionally_charged": The text uses emotionally charged or inflammatory language.
- "logical_fallacy": The text contains logical fallacies.
- "no_trusted_sources": The text does not cite any trusted or verifiable sources.
- "sensationalist_title": The title is clickbait or sensationalist.
- "opinion_as_fact": The text presents opinions as established facts.
- "vague_claims": The claims made are vague or lack specific evidence.

Analyze the following text and provide your response in the specified JSON format.
"""

class GeminiClient:
    """A client for interacting with the Google Gemini Pro API."""

    def __init__(self, api_key: str = settings.GEMINI_API_KEY, model: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError("Gemini API key is not configured.")
        self.api_key = api_key
        self.model = model
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Creates a requests session with retry logic."""
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def _extract_json_from_text(self, text: str) -> str | None:
        """Finds and extracts the first valid JSON object from a string."""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return None

    def analyze_content(self, text_content: str) -> GeminiAnalysis:
        """
        Analyzes text content using the Gemini API.
        """
        # NEW: Truncate content to a max length
        truncated_content = text_content[:MAX_CONTENT_CHARS]

        api_url = f"{GEMINI_API_BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n---\n\n{truncated_content}"}]}]}

        try:
            logging.info(f"Sending analysis request to Gemini model: {self.model} with {len(truncated_content)} chars.")
            response = self._session.post(
                api_url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()

            response_json = response.json()
            analysis_text = response_json["candidates"][0]["content"]["parts"][0]["text"]

            json_string = self._extract_json_from_text(analysis_text)
            if not json_string:
                logging.error("Could not find valid JSON in the Gemini response.")
                logging.error(f"Raw response content: {analysis_text}")
                raise ValueError("Could not extract JSON from Gemini API response.")

            analysis_data = json.loads(json_string)

            validated_analysis = GeminiAnalysis(**analysis_data)
            logging.info("Successfully received and parsed Gemini analysis.")
            return validated_analysis

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error calling Gemini API: {e}")
            raise ValueError(f"Could not connect to Gemini API: {e}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logging.error(f"Failed to parse Gemini API response: {e}")
            logging.error(f"Raw response content from client: {response.text}")
            raise ValueError("Invalid or malformed response from Gemini API.")
        except Exception as e:
            logging.error(f"An unexpected error occurred in GeminiClient: {e}")
            raise