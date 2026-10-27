# InstaKill — Starter Repo

Mini social-media platform. Mandatory backend: Python + FastAPI + SQLite (default) / PostgreSQL (allowed). See the full brief and grading rubric in `masterplan.md` (course root).

What the instructor provides (this starter):

- `app/main.py` — FastAPI hello-world with `GET /health`
- `app/db/database.py` — SQLite bootstrap (creates tables on startup)
- `app/domain/models.py` — `User` / `Post` schema
- `scripts/seed_db.py` — 5-10 synthetic users/posts
- `tests/test_health.py` — test skeleton

What it does **not** provide: the feed, ranking, ML models, search. Those are the team's work, in the following weeks.

## Running it

```bash
pip install -e ".[dev]"
python scripts/seed_db.py        # once; running it again adds the same posts again
uvicorn app.main:app --reload    # first start downloads the encoder model (~90 MB, needs internet)
# other terminal:
curl localhost:8000/health
curl "localhost:8000/search?q=cosine%20similarity&limit=3"

python -m pytest
```

Seed the database **before** starting the server: the search index is built at startup from the posts that exist at that moment.

## Semantic search (Week 3)

`GET /search?q=<text>&limit=<1..20>` returns the posts closest in meaning to the query. The full request/response/error contract is in [`docs/api-contract.md`](docs/api-contract.md).

How the code is split (each layer only knows the one next to it):

| Layer | File | Responsibility |
|-------|------|----------------|
| HTTP edge | `app/api/search.py`, `app/api/errors.py` | Parse `q` / `limit`, format the JSON response and the error envelope. |
| Application service | `app/services/search_service.py` | Validate input, hold the in-memory index, coordinate the pieces below. |
| Pure retrieval | `app/retrieval/similarity.py` | Cosine similarity and deterministic top-*k* in NumPy (score descending, then `post_id` ascending). No I/O, no model. |
| Model adapter | `app/adapters/encoder.py` | The only code that imports `sentence-transformers` (`all-MiniLM-L6-v2`, CPU). |
| Repository | `app/db/post_repository.py` | The only search code that reads SQLite. |

**Where the index is built.** In `app/main.py`, inside `lifespan` (the application start-up hook): it creates a `SearchService`, then calls `search_service.build_index()`. That reads every post from SQLite, encodes all post texts with the model, and keeps the vectors in memory. The model is loaded at that moment, so start-up takes a few seconds.

**How a new post would refresh it.** `build_index()` can be called again at any time: it re-reads all posts and swaps in a complete new index in one step, so searches never see a half-built index. When post creation is implemented, the create-post code should call `search_service.build_index()` afterwards (simple, fine for a small corpus). A later optimization is an `add_post()` that encodes only the new post and appends one row, instead of re-encoding everything. Until then, posts added after start-up are not searchable.


## Milestones (see masterplan.md for full details)

W1 Repo+API → W3 CRUD+DB → W4 Feed v0 → W7 Baseline+eval plan → W9 ML+pretrained feature → W11 Profile+optimize → W13 Feature freeze+E2E → W14 Red-team+Demo Day.

At the end of each week: a demonstrable commit/tag.
