from fastapi import APIRouter

from src.apis.binstore import router as binstoreRouter
from src.apis.filetree import router as filetreeRouter

apis = APIRouter()
apis.include_router(binstoreRouter)
apis.include_router(filetreeRouter)

__all__ = ["apis"]
