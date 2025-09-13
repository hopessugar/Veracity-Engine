import logging

import requests
from requests.adapters import HTTPAdapter, Retry

from config import settings
from models import FactCheckResult

# Constants
FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
REQUEST_TIMEOUT_SECONDS = 15


class FactCheckClient:
    """A client for the Google Fact Check Tools API."""

    def __init__(self, api_key: str = settings.GOOGLE_API_KEY):
        if not api_key:
            raise ValueError("Google API key (for Fact Check) is not configured.")
        self.api_key = api_key
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Creates a requests session with retry logic."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def search(self, query: str, max_results: int = 5) -> list[FactCheckResult]:
        """
        Searches for fact checks related to a query.

        Args:
            query: The search term (e.g., a URL or a key claim).
            max_results: The maximum number of fact checks to return.

        Returns:
            A list of FactCheckResult objects. Returns an empty list if none are found.
        """
        params = {
            "query": query,
            "pageSize": max_results,
            "languageCode": "en",
            "key": self.api_key,
        }

        try:
            logging.info(f"Searching for fact checks with query: '{query[:50]}...'")
            response = self._session.get(
                FACT_CHECK_API_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()

            response_json = response.json()
            claims = response_json.get("claims", [])

            if not claims:
                logging.info(f"No fact checks found for query: '{query[:50]}...'")
                return []

            results = []
            for claim in claims:
                # The API returns a list of reviews for each claim; we'll take the first one.
                if "claimReview" in claim and claim["claimReview"]:
                    review = claim["claimReview"][0]
                    # Ensure all required fields are present before creating the model
                    if all(k in review for k in ["publisher", "title", "textualRating", "url"]):
                        results.append(
                            FactCheckResult(
                                publisher=review["publisher"]["name"],
                                claim=review["title"],
                                rating=review["textualRating"],
                                review_url=review["url"],
                            )
                        )

            logging.info(f"Found {len(results)} fact checks for query.")
            return results

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error calling Fact Check API: {e}")
            return [] # Return an empty list on network failure to not block the process
        except Exception as e:
            logging.error(f"An unexpected error occurred in FactCheckClient: {e}")
            return []
