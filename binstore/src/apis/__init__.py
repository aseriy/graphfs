from fastapi import APIRouter

from src.apis.binstore import router as binstoreRouter
from src.apis.filestore import router as filestoreRouter

apis = APIRouter()
apis.include_router(binstoreRouter)
apis.include_router(filestoreRouter)

__all__ = ["apis"]
