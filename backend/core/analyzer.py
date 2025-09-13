# --- FILE: backend/core/analyzer.py ---
import logging
from concurrent.futures import ThreadPoolExecutor

from models import (
    AnalysisResponse,
    FactCheckResult,
    GeminiAnalysis,
    SafeBrowsingResult,
    Verdict,
)
from services.content_extractor import extract_text_from_url
from services.fact_check import FactCheckClient
from services.gemini_client import GeminiClient
from services.safe_browsing import SafeBrowsingClient


class Analyzer:
    """
    Orchestrates the analysis of a URL by coordinating various services.
    """

    def __init__(self):
        # In a larger application, these clients might be managed with dependency injection.
        self.safe_browsing_client = SafeBrowsingClient()
        self.gemini_client = GeminiClient()
        self.fact_check_client = FactCheckClient()

    def analyze(self, url: str) -> AnalysisResponse:
        """
        Performs a full analysis of a given URL.

        It fetches URL content and calls Safe Browsing, Gemini, and Fact Check
        APIs in parallel to reduce latency.

        Args:
            url: The validated URL to analyze.

        Returns:
            An AnalysisResponse object with the complete analysis.
        """
        logging.info(f"Starting analysis for URL: {url}")

        # Step 1: Extract content from the URL. This is blocking.
        text_content = extract_text_from_url(url)
        if not text_content:
            logging.error(f"Failed to extract content from {url}, aborting analysis.")
            # Return a default error-like response
            return self._build_error_response("Failed to extract content from URL.")

        # Step 2: Run all external API calls in parallel using a thread pool.
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks to the executor
            future_sb = executor.submit(self.safe_browsing_client.check_url, url)
            future_gemini = executor.submit(self.gemini_client.analyze_content, text_content)
            future_fc = executor.submit(self.fact_check_client.search, url)

            # Retrieve results as they complete
            safe_browsing_result = future_sb.result()
            gemini_analysis = future_gemini.result()
            fact_check_results = future_fc.result()

        # Step 3: Combine results and produce the final response
        return self._build_final_response(
            safe_browsing_result, gemini_analysis, fact_check_results
        )

    def _build_final_response(
        self,
        sb_result: SafeBrowsingResult,
        gemini_analysis: GeminiAnalysis,
        fc_results: list[FactCheckResult],
    ) -> AnalysisResponse:
        """Combines individual service results into the final API response."""

        # Determine final score and verdict
        final_score = gemini_analysis.credibility_score
        verdict = Verdict.CAUTION # Default verdict

        if sb_result.threat_type != "THREAT_TYPE_UNSPECIFIED":
            final_score = 0
            verdict = Verdict.DANGER
        elif final_score >= 80:
            verdict = Verdict.VERIFIED
        elif final_score <= 40:
            verdict = Verdict.UNRELIABLE

        return AnalysisResponse(
            veracity_score=final_score,
            verdict=verdict,
            summary=gemini_analysis.summary,
            flags=gemini_analysis.detected_flags,
            safe_browsing=sb_result,
            fact_checks=fc_results,
            raw_ai_analysis=gemini_analysis,
        )

    def _build_error_response(self, error_message: str) -> AnalysisResponse:
        """Builds a default response object in case of a critical failure."""
        return AnalysisResponse(
            veracity_score=0,
            verdict=Verdict.UNRELIABLE,
            summary=error_message,
            flags=["analysis_failed"],
            safe_browsing=SafeBrowsingResult(threat_type="API_ERROR", details={"error": error_message}),
            fact_checks=[],
            raw_ai_analysis=GeminiAnalysis(
                credibility_score=0,
                summary=error_message,
                detected_flags=["analysis_failed"],
                reasoning="Could not perform analysis due to a critical error.",
            ),
        )
