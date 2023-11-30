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
from filetree import FileTree
from binstore import BinaryStore
from src.models.binstore import (
    FileNode
)

router = APIRouter()

creds = get_credentials('etc', 'config.yml')
bs = BinaryStore(creds)
ft = FileTree(creds)


@router.post("/filetree/{path:path}", tags=["filetree"], status_code=200)
def make_directory(path: str, file: UploadFile = File(None)):
    print(f"path: {path}")
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

    fn = ft.create_file(signature, PurePath(path).joinpath(file.filename))

    # TODO: This shouldn't really belong here but in the FileNode creation code
    bs.containerize_node(fn)
    
    return None

