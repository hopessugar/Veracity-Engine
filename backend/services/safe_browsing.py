import logging

import requests
from requests.adapters import HTTPAdapter, Retry

from config import settings
from models import SafeBrowsingResult

# Constants
SAFE_BROWSING_API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
REQUEST_TIMEOUT_SECONDS = 10


class SafeBrowsingClient:
    """A client for the Google Safe Browsing API."""

    def __init__(self, api_key: str = settings.GOOGLE_API_KEY):
        if not api_key:
            raise ValueError("Google API key (for Safe Browsing) is not configured.")
        self.api_key = api_key
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Creates a requests session with retry logic for network resilience."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def check_url(self, url_to_check: str) -> SafeBrowsingResult:
        """
        Checks a URL against the Google Safe Browsing list.

        Args:
            url_to_check: The URL to check.

        Returns:
            A SafeBrowsingResult object. If no threats are found, the threat_type
            will be 'THREAT_TYPE_UNSPECIFIED'.
        """
        payload = {
            "client": {"clientId": "veracity-engine", "clientVersion": "1.0.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url_to_check}],
            },
        }
        params = {"key": self.api_key}

        try:
            logging.info(f"Checking URL with Safe Browsing: {url_to_check}")
            response = self._session.post(
                SAFE_BROWSING_API_URL,
                params=params,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            response_json = response.json()

            # An empty JSON response ({}) from the API means the URL is safe.
            if not response_json or "matches" not in response_json:
                logging.info(f"URL is safe according to Safe Browsing: {url_to_check}")
                return SafeBrowsingResult(threat_type="THREAT_TYPE_UNSPECIFIED")

            # If a threat is found, return the first one.
            threat_match = response_json["matches"][0]
            threat_type = threat_match.get("threatType", "UNKNOWN")
            logging.warning(
                f"Safe Browsing threat found for {url_to_check}: {threat_type}"
            )
            return SafeBrowsingResult(threat_type=threat_type, details=threat_match)

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error calling Safe Browsing API: {e}")
            # In case of network failure, we fail safe and assume no threat was found
            # but log the error.
            return SafeBrowsingResult(
                threat_type="API_ERROR",
                details={"error": "Could not connect to Safe Browsing API."},
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred in SafeBrowsingClient: {e}")
            return SafeBrowsingResult(
                threat_type="CLIENT_ERROR",
                details={"error": "An internal error occurred."},
            )
