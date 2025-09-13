import logging
import socket
from ipaddress import AddressValueError, ip_address
from urllib.parse import urlparse

# A set of common private/reserved IP address ranges to block for SSRF protection.
# This is not exhaustive but covers the most common cases.
FORBIDDEN_IP_RANGES = [
    "0.0.0.0/8",  # Current network (only valid as source address)
    "10.0.0.0/8",  # Private network
    "127.0.0.0/8",  # Loopback
    "169.254.0.0/16",  # Link-local
    "172.16.0.0/12",  # Private network
    "192.168.0.0/16",  # Private network
    "::1/128",  # IPv6 loopback
    "fc00::/7",  # IPv6 unique local addresses
]


def is_ip_forbidden(ip_str: str) -> bool:
    """
    Checks if a given IP address string falls into a forbidden range.

    Args:
        ip_str: The IP address to check.

    Returns:
        True if the IP is in a forbidden range, False otherwise.
    """
    from ipaddress import ip_network

    try:
        ip_addr = ip_address(ip_str)
        for cidr in FORBIDDEN_IP_RANGES:
            if ip_addr in ip_network(cidr):
                logging.warning(
                    f"Forbidden IP address '{ip_str}' detected in range '{cidr}'."
                )
                return True
        return False
    except AddressValueError:
        logging.error(f"Invalid IP address format: {ip_str}")
        # Treat invalid IP formats as forbidden to be safe.
        return True


def validate_and_resolve_url(url: str) -> str:
    """
    Validates a URL and ensures it does not resolve to a forbidden IP address.

    Args:
        url: The URL string to validate.

    Returns:
        The original URL if it is valid.

    Raises:
        ValueError: If the URL is invalid or resolves to a forbidden IP.
    """
    try:
        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https"):
            raise ValueError("Invalid URL scheme. Only 'http' and 'https' are allowed.")

        if not parsed_url.hostname:
            raise ValueError("URL is missing a hostname.")

        # Resolve the hostname to an IP address.
        # This is the crucial step for SSRF protection.
        ip_addr = socket.gethostbyname(parsed_url.hostname)

        if is_ip_forbidden(ip_addr):
            raise ValueError(
                f"URL hostname resolves to a forbidden IP address: {ip_addr}"
            )

        logging.info(f"URL '{url}' validated successfully, resolves to {ip_addr}.")
        return url

    except socket.gaierror:
        # This happens if the hostname cannot be resolved (e.g., DNS lookup fails).
        raise ValueError(f"Could not resolve hostname: {parsed_url.hostname}")
    except Exception as e:
        # Re-raise other ValueErrors or catch unexpected errors.
        logging.error(f"URL validation failed for '{url}': {e}")
        raise ValueError(str(e))
