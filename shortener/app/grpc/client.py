import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Optional

import grpc

from app.config import Settings, get_settings
from app.grpc.protos import analytics_pb2, analytics_pb2_grpc

logger = logging.getLogger(__name__)
Config : Settings = get_settings()

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

    @classmethod
    def get_instance(cls, target: Optional[str]) -> "AnalyticsClient":
        if not cls._instance:
            cls._instance = cls(target)
        return cls._instance

    def __init__(self, target: Optional[str] = None):
        if target is None:
            target = Config.ANALYTICS_SERVICE_GRPC
        self.target = target

        self._channel = grpc.insecure_channel(self.target)
        self._stub = analytics_pb2_grpc.AnalyticsServiceStub(self._channel)
        self._channel.subscribe(self._on_channel_event)

        logger.info(f"Initialized gRPC client for analytics service at {self.target}")

    def _on_channel_event(self, connectivity):
        logger.debug(f"Analytics service connectivity changed: {connectivity}")

    def record_click(
        self, short_link: str, ip: str = "", city: str = "", country: str = ""
    ) -> bool:
        try:
            click = analytics_pb2.ClickModel(ip=ip, city=city, country=country)
            request = analytics_pb2.RecordClickRequest(
                short_link=short_link, click=click
            )

            response = self._stub.RecordClick(request, timeout=2.0)
            return response.success
        except grpc.RpcError as e:
            status_code = e.code()
            logger.error(f"Error recording click: {status_code.name} - {e.details()}")
            return False
        except Exception as e:
            logger.exception(f"Error recording click: {str(e)}")
            return False
