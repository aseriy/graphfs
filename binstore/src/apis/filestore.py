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
from util.neo4j_helpers import get_credentials
from binstore.filestore import FileStore
from binstore.binstore import BinaryStore
from src.models.binstore import (
    FileNode
)

router = APIRouter()

creds = get_credentials('../etc', 'config.yml')
bs = BinaryStore(creds)
fs = FileStore(creds)


@router.get("/filestore", tags=["filestore"], status_code=200)
def file_list():
    ls_data = fs.list()
    return ls_data



@router.get("/filestore/{path:path}", tags=["filestore"], status_code=200)
def file_list(path: str):
    print(f"path: {path}")

    ls_data = fs.list(PurePath(path))
    
    return ls_data



@router.post("/filestore/{path:path}", tags=["filestore"], status_code=200)
def file_upload(path: str, file: UploadFile = File(None)):
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

        # TODO: This shouldn't really belong here but in the FileNode creation code
        bs.containerize_node(fn)
    
    return None


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

    # TODO: This shouldn't really belong here but in the FileNode creation code
    bs.containerize_node(fn)
    
    return None


@router.delete("/filestore/{path:path}", tags=["filestore"], status_code=200)
def file_delete(path: str):
    print(f"path: {path}")


    return None


