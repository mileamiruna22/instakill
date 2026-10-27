# API contract

| Endpoint        | Status                      |
|-----------------|-----------------------------|
| `GET /health`   | Implemented                 |
| `GET /search`   | **Implemented** (Week 3)    |
| `POST /posts`   | Planned — written contract only, not implemented yet |

## Error envelope

Every error response, from any endpoint, has this shape:

```json
{
  "error": {
    "code": "query_empty",
    "message": "q must not be empty",
    "field": "q"
  }
}
```

`code` is stable and meant for programs; `message` is for humans and may change; `field` names the offending request parameter and is `null` when no single field applies.

## `GET /search` — semantic search over posts

Returns the posts whose meaning is closest to the query, best first. Matching uses embeddings from a pretrained sentence encoder and cosine similarity, so a query like `cheap dinner` can find a post about a "budget-friendly restaurant" even when no words overlap.

### Request

```http
GET /search?q=cheap%20dinner&limit=5
```

| Query parameter | Type    | Required | Default | Rules |
|-----------------|---------|----------|---------|-------|
| `q`             | string  | yes      | —       | Not empty and not only whitespace. Missing and empty are treated the same way. |
| `limit`         | integer | no       | `10`    | Whole number from 1 to 20, inclusive. |

### Successful response — `200 OK`

```json
{
  "query": "cheap dinner",
  "results": [
    {
      "post_id": 3,
      "user_id": 2,
      "content": "just shipped a cosine similarity search, feels great",
      "score": 0.6123724356957945
    }
  ]
}
```

| Field                    | Type    | Notes |
|--------------------------|---------|-------|
| `query`                  | string  | The `q` value exactly as the client sent it (not stripped). |
| `results`                | array   | At most `limit` items; empty when no posts are indexed. |
| `results[].post_id`      | integer | Id of the post. |
| `results[].user_id`      | integer | Author of the post. |
| `results[].content`      | string  | Post text. |
| `results[].score`        | number  | Cosine similarity, between -1 and 1 (higher = closer in meaning). |

**Ordering:** by `score` descending. Posts with exactly equal scores are ordered by `post_id` ascending, so the same request always returns the same order.

**Index freshness:** the search index is built once when the application starts. Posts added afterwards do not appear in results until the index is rebuilt (see the README).

### Error responses

| HTTP status | `code`               | `field`  | When |
|-------------|----------------------|----------|------|
| 422         | `query_empty`        | `q`      | `q` is missing, empty, or only whitespace. |
| 422         | `limit_out_of_range` | `limit`  | `limit` is an integer outside 1..20. |
| 422         | `invalid_request`    | `limit`  | `limit` is not an integer (e.g. `limit=abc`). |
| 503         | `index_not_ready`    | `null`   | The search index has not been built (the application did not finish starting up). |

Evaluation order: parameter types first (`invalid_request`), then `q`, then `limit`.

Examples:

```http
GET /search?q=

422 Unprocessable Entity
{"error": {"code": "query_empty", "message": "q must not be empty", "field": "q"}}
```

```http
GET /search?q=cheap%20dinner&limit=99

422 Unprocessable Entity
{"error": {"code": "limit_out_of_range", "message": "limit must be between 1 and 20", "field": "limit"}}
```

## `POST /posts` — submit a new post (planned)

> **Written contract only.** This endpoint is not implemented yet.

Creates a post on behalf of an existing user. (Implemented in a later week; the
validation rules below are already encoded in `PostService.prepare_post` in
`app/services/post_service.py`.)

### Request

`Content-Type: application/json`

```json
{
  "user_id": 1,
  "content": "hello world, this is my first post"
}
```

| Field     | Type    | Required | Rules |
|-----------|---------|----------|-------|
| `user_id` | integer | yes      | Must be the `id` of an existing user. |
| `content` | string  | yes      | Surrounding whitespace is stripped. After stripping: not empty, at most 280 characters. |

There is no authentication in this version, so the author is named explicitly in the body.

### Successful response — `201 Created`

```json
{
  "id": 7,
  "user_id": 1,
  "content": "hello world, this is my first post",
  "created_at": "2026-10-19T09:30:00Z"
}
```

The body has the same shape as the `Post` model in `app/domain/models.py`.
`content` is the stripped content that was stored, which may differ from the request.

### Error responses

Errors use the [error envelope](#error-envelope) defined at the top of this document.

```json
{
  "error": {
    "code": "content_empty",
    "message": "content must not be empty",
    "field": "content"
  }
}
```

| HTTP status | `code`             | `field`              | When |
|-------------|--------------------|----------------------|------|
| 422         | `invalid_request`  | field name or `null` | Body is not valid JSON, a required field is missing, or a field has the wrong type. |
| 422         | `content_empty`    | `content`            | `content` is empty or only whitespace. |
| 422         | `content_too_long` | `content`            | `content` is longer than 280 characters after stripping. |
| 404         | `author_not_found` | `user_id`            | No user exists with the given `user_id`. |

Evaluation order: request shape, then `content` rules, then author lookup. Only the first problem is reported.

### Out of scope for this contract

Listing or reading posts, editing, deleting, feeds and ranking.