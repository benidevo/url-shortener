import logging
from concurrent import futures
from typing import Callable

import app.grpc.protos.analytics_pb2 as analytics_pb2
import grpc
from app.grpc.protos.analytics_pb2_grpc import (
    AnalyticsServiceServicer, add_AnalyticsServiceServicer_to_server)
from app.models import ClickModel
from app.repository import AnalyticsRepository, SqlAlchemyAnalyticsRepository
from grpc_reflection.v1alpha import reflection

logger = logging.getLogger(__name__)


class AnalyticsService(AnalyticsServiceServicer):
    def __init__(self, repository_factory: Callable):
        self.repository: AnalyticsRepository = repository_factory()

    def RecordClick(self, request, context):
        try:
            logger.info(f"Recording click for short link {request.short_link}")

            click_model = ClickModel(
                ip=request.click.ip,
                city=request.click.city,
                country=request.click.country,
            )

            self.repository.record_click(click_model, request.short_link)

            return analytics_pb2.RecordClickResponse(success=True)
        except Exception as e:
            logger.exception(f"Error recording click: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error recording click: {str(e)}")
            return analytics_pb2.RecordClickResponse(success=False)


def serve(session_factory: Callable, port: int = 50052):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    def get_repository():
        session = session_factory()
        return SqlAlchemyAnalyticsRepository(session)

    add_AnalyticsServiceServicer_to_server(
        AnalyticsService(get_repository),
        server,
    )

    SERVICE_NAMES = (
        analytics_pb2.DESCRIPTOR.services_by_name["AnalyticsService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"gRPC server started on port {port}")
    server.wait_for_termination()
