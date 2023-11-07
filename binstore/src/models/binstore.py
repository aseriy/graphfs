from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FileNode(BaseModel):
  sha256: str
  cache: str
  mime: str
  ctime: datetime
