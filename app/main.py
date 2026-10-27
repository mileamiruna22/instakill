from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.encoder import SentenceTransformerEncoder
from app.api.errors import register_error_handlers
from app.api.search import router as search_router
from app.db.database import init_db
from app.db.post_repository import SqlitePostRepository
from app.services.search_service import SearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Composition root: this is the one place where the concrete pieces are wired together.
    # The search index is built ONCE here, from the posts currently in SQLite.
    search_service = SearchService(SqlitePostRepository(), SentenceTransformerEncoder())
    search_service.build_index()
    app.state.search_service = search_service
    yield


app = FastAPI(title="InstaKill", lifespan=lifespan)
register_error_handlers(app)
app.include_router(search_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}