import ipaddress
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request, status

from app.dependencies import get_url_service
from app.models import ResponseModel, UrlCreate, UrlModel
from app.service import UrlShortenerService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def shorten_url(
    payload: UrlCreate = Body(..., description="URL to shorten"),
    service: UrlShortenerService = Depends(get_url_service),
):
    try:
        shorten_url: UrlModel = service.shorten_url(url=payload.url)
    except Exception as e:
        logger.error(f"Error shortening URL: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel(data=shorten_url)


@router.get("/", response_model=ResponseModel)
def list_urls(service: UrlShortenerService = Depends(get_url_service)):
    try:
        shortened_urls = service.get_all_urls()
    except Exception as e:
        logger.error(f"Error listing URLs: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel(data=shortened_urls)


@router.get("/{shortened_url}", response_model=ResponseModel)
def get_url(
    request: Request,
    shortened_url: str = Path(..., min_length=8, max_length=8),
    service: UrlShortenerService = Depends(get_url_service),
):

    client_ip, city, country = _parse_request(request)

    shorten_url = service.get_url(
        shortened_url=shortened_url,
        request_ip=client_ip,
        city=city,
        country=country,
    )
    if not shorten_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    return ResponseModel(data=shorten_url)


def _parse_request(request: Request) -> tuple[str, str, str]:
    """
    Extracts the client's IP address, city, and country from the request headers.
    Implements proper IP validation to prevent spoofing.
    """
    client_ip = _extract_real_ip(request)
    city = request.headers.get("X-GeoIP-City", "unknown")
    country = request.headers.get("X-GeoIP-Country", "unknown")

    return client_ip, city, country


def _extract_real_ip(request: Request) -> str:
    """
    Extract the real client IP address with proper validation.
    Handles proxy chains and prevents IP spoofing.
    """
    # List of trusted proxy IP ranges (in production, configure these properly)
    trusted_proxies = [
        "127.0.0.0/8",  # localhost
        "10.0.0.0/8",  # private networks
        "172.16.0.0/12",  # private networks
        "192.168.0.0/16",  # private networks
        "169.254.0.0/16",  # link-local
    ]

    direct_ip = request.client.host if request.client else "0.0.0.0"

    # Check if we're behind a trusted proxy
    if not _is_trusted_proxy(direct_ip, trusted_proxies):
        return direct_ip

    forwarded_ips = _get_forwarded_ips(request)

    # Find the first non-private IP in the chain
    for ip in forwarded_ips:
        if _is_valid_public_ip(ip):
            return ip

    return direct_ip


def _is_trusted_proxy(ip_address: str, trusted_ranges: list[str]) -> bool:
    """Check if an IP address is in the trusted proxy ranges."""
    try:
        ip = ipaddress.ip_address(ip_address)
        for trusted_range in trusted_ranges:
            if ip in ipaddress.ip_network(trusted_range, strict=False):
                return True
        return False
    except (ValueError, ipaddress.AddressValueError):
        return False


def _get_forwarded_ips(request: Request) -> list[str]:
    """Extract IPs from various forwarded headers."""
    ips = []

    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Split by comma and clean up
        forwarded_ips = [ip.strip() for ip in x_forwarded_for.split(",")]
        ips.extend(forwarded_ips)

    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        ips.append(x_real_ip.strip())

    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        ips.append(cf_connecting_ip.strip())

    return ips


def _is_valid_public_ip(ip_str: str) -> bool:
    """Check if an IP address is valid and public (not private/reserved)."""
    try:
        ip = ipaddress.ip_address(ip_str)

        return (
            not ip.is_private
            and not ip.is_loopback
            and not ip.is_link_local
            and not ip.is_multicast
            and not ip.is_reserved
            and str(ip) != "0.0.0.0"
        )
    except (ValueError, ipaddress.AddressValueError):
        return False


@router.delete("/{shortened_url}", response_model=ResponseModel)
def delete_url(
    shortened_url: str = Path(..., min_length=8, max_length=8),
    service: UrlShortenerService = Depends(get_url_service),
):
    try:
        service.delete_url(shortened_url=shortened_url)
    except Exception as e:
        logger.error(f"Error deleting URL: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel()
