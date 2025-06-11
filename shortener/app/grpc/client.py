import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import ClassVar, Optional

import grpc

from app.config import Settings, get_settings
from app.grpc.protos import analytics_pb2, analytics_pb2_grpc

logger = logging.getLogger(__name__)
Config: Settings = get_settings()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AnalyticsClient(ABC):
    @abstractmethod
    def record_click(
        self, short_link: str, ip: str = "", city: str = "", country: str = ""
    ) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_instance(cls, target: Optional[str]) -> "AnalyticsClient":
        raise NotImplementedError


class GrpcAnalyticsClient(AnalyticsClient):
    _instance: ClassVar[Optional["GrpcAnalyticsClient"]] = None
    _lock: ClassVar[Lock] = Lock()

    FAILURE_THRESHOLD = 5  # Number of failures before opening circuit
    RECOVERY_TIMEOUT = 30  # Seconds before trying half-open state
    HALF_OPEN_MAX_ATTEMPTS = 3  # Max attempts in half-open state

    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 0.1  # seconds
    MAX_RETRY_DELAY = 2.0  # seconds
    TIMEOUT = 2.0  # seconds

    @classmethod
    def get_instance(cls, target: Optional[str]) -> "AnalyticsClient":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls(target)
        return cls._instance

    def __init__(self, target: Optional[str] = None):
        if target is None:
            target = Config.ANALYTICS_SERVICE_GRPC
        self.target = target

        options = [
            # Send keepalive every 30s
            ("grpc.keepalive_time_ms", 30000),
            # Wait 10s for keepalive response
            ("grpc.keepalive_timeout_ms", 10000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.max_pings_without_data", 0),
        ]

        self._channel = grpc.insecure_channel(self.target, options=options)
        self._stub = analytics_pb2_grpc.AnalyticsServiceStub(self._channel)
        self._channel.subscribe(self._on_channel_event)

        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._circuit_opened_at = None
        self._half_open_attempts = 0
        self._state_lock = Lock()

        logger.info(f"Initialized gRPC client for analytics service at {self.target}")

    def _on_channel_event(self, connectivity):
        logger.debug(f"Analytics service connectivity changed: {connectivity}")

        # Reset circuit breaker on reconnection
        if connectivity == grpc.ChannelConnectivity.READY:
            with self._state_lock:
                if self._circuit_state != CircuitState.CLOSED:
                    logger.info(
                        "Analytics service reconnected, " "closing circuit breaker"
                    )
                    self._reset_circuit_breaker()

    def _reset_circuit_breaker(self):
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._circuit_opened_at = None
        self._half_open_attempts = 0

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit breaker state"""
        with self._state_lock:
            if self._circuit_state == CircuitState.CLOSED:
                return True

            if self._circuit_state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if self._circuit_opened_at is not None:
                    time_open = (
                        datetime.now() - self._circuit_opened_at
                    ).total_seconds()
                    if time_open >= self.RECOVERY_TIMEOUT:
                        logger.info("Circuit breaker entering half-open state")
                        self._circuit_state = CircuitState.HALF_OPEN
                        self._half_open_attempts = 0
                        return True
                return False

            # Half-open state
            if self._half_open_attempts < self.HALF_OPEN_MAX_ATTEMPTS:
                return True
            return False

    def _record_success(self):
        with self._state_lock:
            if self._circuit_state == CircuitState.HALF_OPEN:
                self._half_open_attempts += 1
                if self._half_open_attempts >= self.HALF_OPEN_MAX_ATTEMPTS:
                    logger.info(
                        "Circuit breaker closing after successful " "half-open tests"
                    )
                    self._reset_circuit_breaker()
            elif self._circuit_state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def _record_failure(self):
        with self._state_lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._circuit_state == CircuitState.HALF_OPEN:
                logger.warning("Request failed in half-open state, reopening circuit")
                self._circuit_state = CircuitState.OPEN
                self._circuit_opened_at = datetime.now()
            elif (
                self._circuit_state == CircuitState.CLOSED
                and self._failure_count >= self.FAILURE_THRESHOLD
            ):
                logger.warning(
                    f"Circuit breaker opening after " f"{self._failure_count} failures"
                )
                self._circuit_state = CircuitState.OPEN
                self._circuit_opened_at = datetime.now()

    def record_click(
        self, short_link: str, ip: str = "", city: str = "", country: str = ""
    ) -> bool:
        if not self._should_allow_request():
            logger.warning("Circuit breaker is open, skipping analytics request")
            return False

        retry_delay = self.INITIAL_RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                click = analytics_pb2.ClickModel(  # type: ignore
                    ip=ip, city=city, country=country
                )
                request = analytics_pb2.RecordClickRequest(  # type: ignore
                    short_link=short_link, click=click
                )

                response = self._stub.RecordClick(request, timeout=self.TIMEOUT)

                self._record_success()
                return bool(response.success)

            except grpc.RpcError as e:
                status_code = e.code()

                if status_code in [
                    grpc.StatusCode.INVALID_ARGUMENT,
                    grpc.StatusCode.NOT_FOUND,
                    grpc.StatusCode.PERMISSION_DENIED,
                    grpc.StatusCode.UNAUTHENTICATED,
                ]:
                    logger.error(
                        f"Non-retryable error recording click: "
                        f"{status_code.name} - {e.details()}"
                    )
                    self._record_failure()
                    return False

                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Error recording click (attempt "
                        f"{attempt + 1}/{self.MAX_RETRIES}): "
                        f"{status_code.name} - {e.details()}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                else:
                    logger.error(
                        f"Failed to record click after "
                        f"{self.MAX_RETRIES} attempts: "
                        f"{status_code.name} - {e.details()}"
                    )

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Unexpected error recording click (attempt "
                        f"{attempt + 1}/{self.MAX_RETRIES}): "
                        f"{str(e)}. Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
                else:
                    logger.exception(
                        f"Failed to record click after " f"{self.MAX_RETRIES} attempts"
                    )

        # All retries failed
        self._record_failure()
        return False

    def __del__(self):
        """Cleanup gRPC channel on deletion"""
        if hasattr(self, "_channel"):
            try:
                self._channel.close()
            except Exception:
                pass
