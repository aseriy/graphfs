from fastapi import APIRouter

from src.apis.binstore import router as binstoreRouter
from src.apis.filestore import router as filestoreRouter
from src.apis.stats import router as statsRouter

apis = APIRouter()
apis.include_router(binstoreRouter)
apis.include_router(filestoreRouter)
apis.include_router(statsRouter)

__all__ = ["apis"]
