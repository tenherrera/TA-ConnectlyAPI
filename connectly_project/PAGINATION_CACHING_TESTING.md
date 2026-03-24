# Pagination and Caching Testing Guide

## What Was Added

- Pagination for `GET /posts/feed/` now uses Django `Paginator`
- Feed responses are cached for 60 seconds using Django's cache framework
- Feed cache is invalidated when posts, comments, or likes change feed contents or counts
- Feed responses include an `X-Cache` header:
  - `MISS` means the response was generated fresh
  - `HIT` means the response was served from cache

## Manual Pagination Tests

### Successful Cases

1. Request page 1:
```http
GET /posts/feed/?page=1&page_size=2
```
Expected:
- `200 OK`
- `page=1`
- `page_size=2`
- `results` contains 2 posts

2. Request page 2:
```http
GET /posts/feed/?page=2&page_size=2
```
Expected:
- `200 OK`
- `results` contains the next subset of posts

### Failed Cases

1. Invalid page:
```http
GET /posts/feed/?page=-1
```
Expected:
- `400 Bad Request`

2. Too-large page size:
```http
GET /posts/feed/?page_size=51
```
Expected:
- `400 Bad Request`

3. Page out of range:
```http
GET /posts/feed/?page=99&page_size=2
```
Expected:
- `400 Bad Request`

## Manual Cache Tests

### Cache Miss then Hit

1. Send:
```http
GET /posts/feed/?page=1&page_size=2
```
Expected header:
- `X-Cache: MISS`

2. Repeat the exact same request immediately.
Expected header:
- `X-Cache: HIT`

This confirms the second response was served from cache.

### Cache Invalidation

1. Send:
```http
GET /posts/feed/
```
Expected header:
- `X-Cache: MISS`

2. Create a new post using:
```http
POST /posts/factory/
```

3. Send the same feed request again:
```http
GET /posts/feed/
```
Expected:
- `X-Cache: MISS`
- updated post count or updated results

This confirms the feed cache was invalidated and repopulated.

## Suggested Postman Demo

1. Run the same `GET /posts/feed/?page=1&page_size=2` request twice.
2. Show that the first response has `X-Cache: MISS`.
3. Show that the second response has `X-Cache: HIT`.
4. Create a new post.
5. Run the same feed request again.
6. Show `X-Cache: MISS` and updated feed data.

## Automated Validation

Automated tests cover:
- correct page slicing
- invalid page handling
- cache miss then hit
- cache invalidation after post creation

See:
- [`posts/tests.py`](c:\Users\masof\Downloads\MO-IT152-main\MO-IT152-main\connectly_project\posts\tests.py)
- [`TEST_RESULTS_REPORT.md`](c:\Users\masof\Downloads\MO-IT152-main\MO-IT152-main\connectly_project\TEST_RESULTS_REPORT.md)
