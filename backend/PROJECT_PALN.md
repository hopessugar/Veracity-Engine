# Veracity Engine - Backend Project Plan

This document outlines the development plan for the Veracity Engine backend. The backend will be a secure, scalable, and production-ready Google Cloud Function written in Python.

## 1. File Generation Order

We will generate the project files in the following logical order. Each file will be a self-contained, production-quality module.

1.  **`backend/PROJECT_PLAN.md`** (This file) - The roadmap.
2.  **`backend/.gitignore`** - Standard Python gitignore.
3.  **`backend/requirements.txt`** - Python package dependencies.
4.  **`backend/pyproject.toml`** - Configuration for linters (`ruff`) and formatters (`black`).
5.  **`backend/utils/logging_config.py`** - Setup for structured JSON logging for GCP.
6.  **`backend/config.py`** - Centralized configuration management from environment variables.
7.  **`backend/models.py`** - Pydantic models for API request/response validation.
8.  **`backend/utils/url_validator.py`** - Secure URL validation and SSRF protection.
9.  **`backend/tests/test_url_validator.py`** - Unit tests for the URL validator.
10. **`backend/services/gemini_client.py`** - API client for Google Gemini Pro with retries and mocking support.
11. **`backend/services/safe_browsing.py`** - API client for Google Safe Browsing.
12. **`backend/services/fact_check.py`** - API client for Google Fact Check Tools.
13. **`backend/services/content_extractor.py`** - Service to fetch and parse web content securely.
14. **`backend/core/analyzer.py`** - Core business logic to orchestrate API calls, analyze content, and generate the final veracity score and report.
15. **`backend/main.py`** - The Flask app and Cloud Function entry point.
16. **`backend/tests/conftest.py`** - Pytest fixtures for testing.
17. **`backend/tests/core/test_analyzer.py`** - Tests for the core analyzer logic, using mocks.
18. **`backend/README.md`** - Developer documentation for setup, testing, and deployment.
19. **`.github/workflows/ci_cd.yml`** - GitHub Actions workflow for CI/CD.
20. **`deploy.sh`** - Deployment script for Cloud Functions and secrets.

---

## 2. Environment Variables

Create a `.env` file in the `backend/` directory for local development. **Do not commit this file.**

```bash
# .env

# Google Cloud Project ID
GCP_PROJECT_ID="your-gcp-project-id"

# API Keys (use real keys for testing, mocks are used for unit tests)
GEMINI_API_KEY="your-gemini-api-key"
GOOGLE_API_KEY="your-google-api-key-for-safe-browsing-and-fact-check"

# Application Settings
LOG_LEVEL="INFO"
APP_ENV="development" # development | production