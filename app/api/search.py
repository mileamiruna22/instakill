"""HTTP edge for search: parse the request, call the service, format the response."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.services.search_service import IndexNotReadyError, SearchService

router = APIRouter()

DEFAULT_LIMIT = 10


class SearchResult(BaseModel):
    post_id: int
    user_id: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


def get_search_service(request: Request) -> SearchService:
    service = getattr(request.app.state, "search_service", None)
    if service is None:
        raise IndexNotReadyError("search service is not available")
    return service


@router.get("/search", response_model=SearchResponse)
def search(
    q: str | None = None,
    limit: int = DEFAULT_LIMIT,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    query = q or ""
    hits = service.search(query, limit)
    return SearchResponse(
        query=query,
        results=[SearchResult(**vars(hit)) for hit in hits],
    )