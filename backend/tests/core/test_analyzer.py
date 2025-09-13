# --- FILE: backend/tests/core/test_analyzer.py ---
from unittest.mock import patch

from models import (
    FactCheckResult,
    GeminiAnalysis,
    SafeBrowsingResult,
    Verdict,
)


# The 'client' fixture is automatically provided by conftest.py
def test_successful_analysis(client):
    """
    Tests the full end-to-end analysis process with mocked services.
    This is the "happy path" test.
    """
    # CORRECTED: The actual URL passed after Pydantic validation
    normalized_url = "https://example.com/"

    with (
        patch(
            "main.validate_and_resolve_url", return_value=normalized_url
        ) as mock_validate,
        patch(
            "core.analyzer.extract_text_from_url", return_value="Sample article text."
        ) as mock_extract,
        patch("main.analyzer.safe_browsing_client.check_url") as mock_sb_check,
        patch("main.analyzer.gemini_client.analyze_content") as mock_gemini_analyze,
        patch("main.analyzer.fact_check_client.search") as mock_fc_search,
    ):

        # Configure the return values of our mocks
        mock_sb_check.return_value = SafeBrowsingResult(
            threat_type="THREAT_TYPE_UNSPECIFIED"
        )
        mock_gemini_analyze.return_value = GeminiAnalysis(
            credibility_score=85,
            summary="This is a neutral summary.",
            detected_flags=["no_trusted_sources"],
            reasoning="The analysis was positive.",
        )
        mock_fc_search.return_value = [
            FactCheckResult(
                publisher="FactCheck.org",
                claim="A sample claim.",
                rating="True",
                review_url="https://factcheck.org/review/",
            )
        ]

        # Make the simulated API call with the original URL
        response = client.post("/", json={"url": "https://example.com"})

        # Assertions
        assert response.status_code == 200
        data = response.get_json()

        assert data["veracity_score"] == 85
        assert data["verdict"] == Verdict.VERIFIED.value

        # Verify that our mocks were called with the CORRECT, normalized URL
        mock_validate.assert_called_once_with(normalized_url)
        mock_extract.assert_called_once_with(normalized_url)
        mock_sb_check.assert_called_once_with(normalized_url)
        mock_gemini_analyze.assert_called_once_with("Sample article text.")
        mock_fc_search.assert_called_once_with(normalized_url)


def test_forbidden_url_request(client):
    """
    Tests that a request with a forbidden URL (e.g., localhost) is rejected.
    """
    response = client.post("/", json={"url": "http://127.0.0.1"})
    assert response.status_code == 400
    data = response.get_json()
    assert "forbidden IP address" in data["error"]


def test_bad_request_body(client):
    """
    Tests that a request with a malformed body (e.g., missing 'url') is rejected.
    """
    response = client.post("/", json={"not_a_url": "invalid"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Invalid request body"
