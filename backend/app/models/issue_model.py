from pydantic import BaseModel
from typing import List, Optional

class Issue(BaseModel):
    title: str
    description: str
    priority: str
    tags: List[str]

class IssueResponse(BaseModel):
    issues: List[Issue]
    context: str
