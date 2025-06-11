import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.constants import CLEANUP_MAX_AGE_SECONDS

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter implementation.
    Tracks requests per IP address with configurable limits and time windows.
    """

    def __init__(self):
        self._requests: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(
        self, identifier: str, limit: int, window_seconds: int
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if a request is allowed based on rate limits.

        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        with self._lock:
            request_times = self._requests[identifier]

            while request_times and request_times[0] < window_start:
                request_times.popleft()

            current_count = len(request_times)
            is_allowed = current_count < limit

            if is_allowed:
                request_times.append(current_time)

            remaining = max(0, limit - current_count - (1 if is_allowed else 0))
            reset_time = int(current_time + window_seconds)

            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": str(window_seconds),
            }

            if not is_allowed:
                oldest_request = request_times[0] if request_times else current_time
                retry_after = int(oldest_request + window_seconds - current_time)
                headers["Retry-After"] = str(max(1, retry_after))

            return is_allowed, headers

    def cleanup_old_entries(self, max_age_seconds: int = CLEANUP_MAX_AGE_SECONDS):
        """
        Clean up old entries to prevent memory leaks.
        Should be called periodically.
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        with self._lock:
            expired_keys = []
            for identifier, request_times in self._requests.items():
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()

                if not request_times:
                    expired_keys.append(identifier)

            for key in expired_keys:
                del self._requests[key]


rate_limiter = SlidingWindowRateLimiter()


class RateLimitConfig:
    """Configuration for different rate limit rules."""

    # Per-IP rate limits
    GLOBAL_REQUESTS_PER_MINUTE = 100
    GLOBAL_WINDOW_SECONDS = 60

    # URL creation limits (more restrictive)
    URL_CREATION_REQUESTS_PER_MINUTE = 10
    URL_CREATION_WINDOW_SECONDS = 60

    # URL access limits (less restrictive)
    URL_ACCESS_REQUESTS_PER_MINUTE = 50
    URL_ACCESS_WINDOW_SECONDS = 60


def get_client_identifier(request: Request) -> str:
    """
    Extract client identifier for rate limiting.
    Uses the same IP extraction logic as the routes.
    """
    from app.routes.urls import _extract_real_ip

    return _extract_real_ip(request)


async def rate_limit_middleware(request: Request, call_next) -> Any:
    """
    FastAPI middleware for rate limiting.
    """
    try:
        client_id = get_client_identifier(request)
        path = request.url.path
        method = request.method

        if method == "POST" and path.startswith("/"):
            limit = RateLimitConfig.URL_CREATION_REQUESTS_PER_MINUTE
            window = RateLimitConfig.URL_CREATION_WINDOW_SECONDS
            endpoint_type = "url_creation"
        elif method == "GET" and len(path.strip("/")) == 8:
            limit = RateLimitConfig.URL_ACCESS_REQUESTS_PER_MINUTE
            window = RateLimitConfig.URL_ACCESS_WINDOW_SECONDS
            endpoint_type = "url_access"
        else:
            limit = RateLimitConfig.GLOBAL_REQUESTS_PER_MINUTE
            window = RateLimitConfig.GLOBAL_WINDOW_SECONDS
            endpoint_type = "general"

        is_allowed, headers = rate_limiter.is_allowed(
            f"{client_id}:{endpoint_type}", limit, window
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {endpoint_type} "
                f"endpoint: {method} {path}"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per "
                    f"{window} seconds",
                },
                headers=headers,
            )

        response = await call_next(request)

        for key, value in headers.items():
            response.headers[key] = value

        return response

    except Exception as e:
        logger.error(f"Error in rate limiting middleware: {e!s}")
        return await call_next(request)


def cleanup_rate_limiter():
    """
    Cleanup function to be called periodically.
    Can be used with background tasks or scheduled jobs.
    """
    try:
        rate_limiter.cleanup_old_entries()
        logger.debug("Rate limiter cleanup completed")
    except Exception as e:
        logger.error(f"Error during rate limiter cleanup: {e!s}")
