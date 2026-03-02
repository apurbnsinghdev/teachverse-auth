from fastapi import Query
from typing import Optional, Tuple
from pydantic import BaseModel

class PaginationParams(BaseModel):
    """Pagination query parameters"""
    skip: int = 0
    limit: int = 100
    
    class Config:
        arbitrary_types_allowed = True

def get_pagination(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
) -> PaginationParams:
    """Dependency for pagination"""
    return PaginationParams(skip=skip, limit=limit)