# --- FILE: backend/tests/test_url_validator.py ---
import socket
from unittest.mock import patch

import pytest

from utils.url_validator import validate_and_resolve_url


# By patching 'socket.gethostbyname', we prevent actual network calls during tests.
# This makes tests faster, more reliable, and independent of network conditions.
@patch("socket.gethostbyname")
def test_valid_urls_are_allowed(mock_gethostbyname):
    """
    Tests that a list of valid, public URLs pass validation.
    """
    # We make the mock return a safe, public IP address.
    mock_gethostbyname.return_value = "8.8.8.8"  # A public Google DNS IP

    valid_urls = [
        "https://google.com",
        "http://example.com/path?query=string",
        "https://www.a-valid-domain.co.uk",
    ]

    for url in valid_urls:
        assert validate_and_resolve_url(url) == url


@patch("socket.gethostbyname")
def test_forbidden_ips_are_rejected(mock_gethostbyname):
    """
    Tests that URLs resolving to private or reserved IPs raise a ValueError.
    """
    forbidden_ips = {
        "http://localhost": "127.0.0.1",
        "http://127.0.0.1": "127.0.0.1",
        "http://192.168.1.1": "192.168.1.1",
        "http://10.0.0.1": "10.0.0.1",
        "http://[::1]": "::1",  # IPv6 localhost
    }

    for url, ip in forbidden_ips.items():
        mock_gethostbyname.return_value = ip
        with pytest.raises(ValueError, match="forbidden IP address"):
            validate_and_resolve_url(url)


def test_invalid_schemes_are_rejected():
    """
    Tests that URLs with non-HTTP/HTTPS schemes raise a ValueError.
    """
    invalid_scheme_urls = [
        "file:///etc/passwd",
        "ftp://example.com",
        "ssh://user@host.com",
        "javascript:alert('xss')",
    ]

    for url in invalid_scheme_urls:
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            validate_and_resolve_url(url)


@patch("socket.gethostbyname", side_effect=socket.gaierror)
def test_unresolvable_hostname_is_rejected(mock_gethostbyname):
    """
    Tests that a URL with a hostname that cannot be resolved raises a ValueError.
    """
    with pytest.raises(ValueError, match="Could not resolve hostname"):
        validate_and_resolve_url("http://this-is-not-a-real-domain.invalid")
