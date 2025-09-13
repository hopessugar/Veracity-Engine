import logging

import requests
from bs4 import BeautifulSoup

# Constants
REQUEST_TIMEOUT_SECONDS = 10
MAX_CONTENT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit
HEADERS = {
    "User-Agent": "VeracityEngine/1.0 (+http://example.com/bot)"  # Replace with a real URL later
}


def extract_text_from_url(url: str) -> str | None:
    """
    Fetches content from a URL and extracts the clean text.

    Args:
        url: A validated HTTP/HTTPS URL. This function assumes the URL
             has already been validated for SSRF and scheme.

    Returns:
        The extracted text content as a string, or None if extraction fails.
    """
    try:
        logging.info(f"Extracting content from URL: {url}")
        with requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()

            # Check content type to ensure we are processing HTML
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logging.warning(
                    f"Skipping non-HTML content type '{content_type}' for URL: {url}"
                )
                return None

            # Check content length to avoid downloading huge files
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_CONTENT_SIZE_BYTES:
                logging.warning(f"Content length exceeds limit for URL: {url}")
                return None

            # Read content incrementally to enforce size limit even without header
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_CONTENT_SIZE_BYTES:
                    logging.warning(
                        f"Streamed content exceeds size limit for URL: {url}"
                    )
                    return None

            # Use BeautifulSoup to parse HTML and extract text
            soup = BeautifulSoup(content, "html.parser")

            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            # Get text from the body, stripping excess whitespace
            body = soup.body
            if not body:
                return None

            text = body.get_text(separator=" ", strip=True)
            return text

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch URL {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during content extraction: {e}")
        return None
