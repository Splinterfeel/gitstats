from datetime import date
from pydantic import BaseModel


class CommitDTO(BaseModel):
    commit_date: date
    commit_hash: str
    commit_author: str


class CommitStats(BaseModel):
    commit: str
    additions: int
    deletions: int
    file: str
