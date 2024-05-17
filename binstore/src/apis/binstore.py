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


# TODO: Need to implement pagination!!!
#
@router.get("/filenoodes", tags=["binstore"], status_code=200)
async def get_file_nodes():
    json_resp = bs.list_files()
    # print(json.dumps(json_resp, indent=2))
    return json_resp



@router.get("/filenodes/{sha256}", tags=["binstore"], status_code=200)
async def get_file_node_meta(sha256: str):
    json_resp = bs.get_meta(sha256)
    return json_resp



@router.get("/filenodes/{sha256}/containers", tags=["binstore"], status_code=200)
async def get_file_node_containers(sha256: str):
    json_resp = bs.get_node_containers(sha256)
    return json_resp



@router.get("/filenodes/{sha256}/similar", tags=["binstore"], status_code=200)
async def get_similar_filenodes(sha256: str):
    json_resp = bs.find_similar_filenodes(sha256)
    return json_resp



# TODO: This must be utterly broken at this point.
#       Need to store things in MinIO instead of locally.
#
@router.get("/filenodes/{sha256}/download", tags=["binstore"], status_code=200)
async def download_filenode(sha256: str):
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


# TODO: Is there a use case for uploading file content, i.e. FileNode, without actually
#       linking it to a file?
#
# @router.post("/filenodes", tags=["binstore"], status_code=200)
# def upload(files: List[UploadFile] = File(...)):
#     for file in files:
#         try:
#             contents = file.file.read()
#             signature = bs.put_file_node(contents)
#             print (signature)

#         except Exception:
#             return {"message": "There was an error uploading the file(s)"}

#         finally:
#             file.file.close()

#     return {"message": f"Successfully uploaded {[file.filename for file in files]}"}
