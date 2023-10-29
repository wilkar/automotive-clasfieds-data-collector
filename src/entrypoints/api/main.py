import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from src.bootstrap.app import AppContainer
from src.config import log_init
from src.entrypoints.api.routes import operations

log_init.setup_logging()

logger = logging.getLogger(__name__)


def get_app(app_container: AppContainer) -> FastAPI:
    app = FastAPI()
    app.include_router(operations.get_router(app_container), prefix="/operations")

    @app.exception_handler(StarletteHTTPException)
    async def logging_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        logger.exception(
            "Exception occured",
            exc_info=exc,
            extra={
                "request_id": request.headers.get("X-Request-ID"),
                "path_params": request.path_params,
                "exception_args": exc.args,
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )
        return await http_exception_handler(request, exc)

    @app.get("/")
    def status():
        return {"status": "ok"}

    return app
