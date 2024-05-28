from dotenv import load_dotenv
import json
import os, io
from typing import List, Optional
from fastapi import (
  APIRouter,
  Header, Request, HTTPException, Response,
  File, UploadFile
)
from util.neo4j_helpers import get_credentials
from graphfs.graphstore import GraphStore
from src.models.binstore import (
    FileNode
)
from src.apis.resources import (
    graphStore as bs
)

router = APIRouter()


@router.get("/stats", tags=["stats"], status_code=200)
def info():
    json_resp = {
        "fs": bs.stats_file_system(),
        "store": bs.stats_data_store()
    }
    print(json.dumps(json_resp, indent=2))
    return json_resp
