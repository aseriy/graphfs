from dotenv import load_dotenv
import json
import os, io
from typing import List, Optional
from fastapi import APIRouter, Header, Request, HTTPException, Response
from util.neo4j_helpers import get_credentials
from binstore import BinaryStore
from src.models.binstore import (
    FileNode
)

router = APIRouter()

creds = get_credentials('etc', 'config.yml')
bs = BinaryStore(creds)


@router.get("/binstore/files", tags=["binstore"], status_code=200)
async def get_file_nodes():
    json_resp = bs.list_files()
    # print(json.dumps(json_resp, indent=2))
    return json_resp


@router.get("/binstore/files/{sha256}", tags=["binstore"], status_code=200)
async def get_file_nodes(sha256: str):
    json_resp = bs.get_meta(sha256)
    return json_resp


@router.get("/binstore/files/{sha256}/download", tags=["binstore"], status_code=200)
async def get_file_nodes(sha256: str):
    # Check if a valid sha256
    if not bs.is_valid_hex(sha256):
        raise HTTPException(status_code=404, detail="Node not found")

    # node_mime, node_cache_path = bs.get(sha256)
    file_meta = bs.get(sha256)
    node_cache_path = os.path.join(creds['bin_store_dir'], 'cache', file_meta['store'])
    node_mime = file_meta['mime']
    print(node_cache_path)
    with open (node_cache_path, "rb") as file_fh:
        data = io.BytesIO(bytearray(file_fh.read()))

    response = Response(content=data.getvalue(), media_type=node_mime)
    response.headers["Content-Disposition"] = f"attachment; filename={sha256}"

    return response
