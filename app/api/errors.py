"""Maps errors to the single error envelope documented in docs/api-contract.md."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.search_service import SearchError

STATUS_BY_CODE = {
    "query_empty": 422,
    "limit_out_of_range": 422,
    "index_not_ready": 503,
}


def _envelope(code: str, message: str, field: str | None) -> dict:
    return {"error": {"code": code, "message": message, "field": field}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SearchError)
    async def handle_search_error(request: Request, exc: SearchError) -> JSONResponse:
        status = STATUS_BY_CODE.get(exc.code, 400)
        return JSONResponse(status_code=status, content=_envelope(exc.code, exc.message, exc.field))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        location = [str(part) for part in first.get("loc", ()) if part not in ("query", "body")]
        field = location[0] if location else None
        return JSONResponse(
            status_code=422,
            content=_envelope("invalid_request", first.get("msg", "invalid request"), field),
        )