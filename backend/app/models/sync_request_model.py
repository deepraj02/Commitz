from pydantic import BaseModel
from typing import List

class Issue(BaseModel):
    title: str
    body: str

class SyncRequest(BaseModel):
    installation_id: int
    repo_name: str
    issues: List[Issue]
