from fastapi import APIRouter
from pydantic import BaseModel

from src.bootstrap.app import AppContainer


class Status(BaseModel):
    status: str


def get_router(app_container: AppContainer) -> APIRouter:
    router = APIRouter()

    @router.get("/status", tags=["operations"])
    async def status() -> Status:
        return Status(status="ok")

    return router
