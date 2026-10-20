# API contract

> **Status: written contract only.** None of the endpoints below are implemented yet.
> This document describes the behavior the implementation must match when it is built.

## `POST /posts` — submit a new post

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

Every error uses the same envelope:

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

Listing or reading posts, editing, deleting, feeds, ranking, search, and any ML-based behavior.