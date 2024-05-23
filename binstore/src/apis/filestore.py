from dotenv import load_dotenv
import json
import os, io
from pathlib import PurePath
from typing import List, Optional, Union
from fastapi import (
  APIRouter,
  Header, Request, HTTPException, Response,
  File, UploadFile
)
from fastapi_cache.decorator import cache

from util.neo4j_helpers import get_credentials
from graphfs.filestore import FileStore
from graphfs.graphstore import GraphStore
from src.models.binstore import (
    FileNode
)
from src.apis.resources import (
    graphStore as bs,
    fileStore as fs
)


router = APIRouter()

# creds = get_credentials('../etc', 'config.yml')
# bs = GraphStore(creds)
# fs = FileStore(creds)



# @router.get("/filestore", tags=["filestore"], status_code=200)
# def file_list():
#     ls_data = fs.list()
#     return ls_data


@router.get("/filestore", tags=["filestore"], status_code=200)
@router.get("/filestore/{path:path}", tags=["filestore"], status_code=200)
@cache(expire=600)
async def file_meta(path: str = None):
    print(f"path: {path}")

    ls_data = None

    if path is None:
        ls_data = fs.list()
    else:
        ls_data = fs.list(PurePath(path))
    
    return ls_data



@router.get("/identical/{path:path}", tags=["filestore"], status_code=200)
@cache(expire=600)
async def file_identical(path: str):
    print(f"path: {path}")

    identical = fs.list_identical_files(PurePath(path))

    return identical



@router.get("/similar/{path:path}", tags=["filestore"], status_code=200)
@cache(expire=600)
async def file_similar(path: str):
    print(f"path: {path}")

    identical = fs.list_similar_files(PurePath(path))

    return identical



@router.post("/filestore/{path:path}", tags=["filestore"], status_code=200)
async def file_upload(path: str, file: UploadFile = File(None)):
    print(f"path: {path}")
    print("file: ", file)
    signature = None

    if file is None:
        fs.make_dir(PurePath(path))

    else:
        print(f"file: {file.filename}")
        try:
            contents = file.file.read()
            signature = bs.put_file_node(contents)
            print (signature)

        except Exception:
            return {"message": "There was an error uploading the file(s)"}

        finally:
            file.file.close()

        fn = fs.create_file(signature, PurePath(path).joinpath(file.filename))

    return None


# TODO: Needs to be consolidated with the /filestore/{path:path} handler
#
@router.post("/filestore", tags=["filestore"], status_code=200)
def file_upload(file: UploadFile = File(None)):
    print(f"file: {file.filename}")
    signature = None

    try:
        contents = file.file.read()
        signature = bs.put_file_node(contents)
        print (signature)

    except Exception:
        return {"message": "There was an error uploading the file(s)"}

    finally:
        file.file.close()

    fn = fs.create_file(signature, PurePath(file.filename))

    return None


@router.delete("/filestore/{path:path}", tags=["filestore"], status_code=200)
def file_delete(path: str):
    print(f"path: {path}")
    print(f"PurePath: {PurePath(path)}")

    # fs.delete_file(PurePath(path))

    return None


