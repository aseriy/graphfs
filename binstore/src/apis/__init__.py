from fastapi import APIRouter

from src.apis.binstore import router as binstoreRouter

apis = APIRouter()
apis.include_router(binstoreRouter)

__all__ = ["apis"]
