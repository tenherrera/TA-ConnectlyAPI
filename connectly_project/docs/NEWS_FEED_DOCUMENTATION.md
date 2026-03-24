# Connectly News Feed API Documentation

## Overview
The News Feed endpoint provides a comprehensive, paginated view of posts with advanced filtering, searching, and sorting capabilities. It's designed for displaying user-specific content with optimal database query performance.

## Endpoint

### GET /posts/feed/

Retrieves a paginated news feed with support for filtering, searching, and sorting.

**Authentication:** Not required (public endpoint)
**Method:** GET
**Content-Type:** application/json

---

## Query Parameters

### Pagination Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | - | Page number (must be >= 1) |
| `page_size` | integer | 10 | 50 | Number of posts per page (1-50) |

**Example:**
```
GET /posts/feed/?page=2&page_size=10
```

### Filtering Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `post_type` | string | text, image, video | Filter by one or more post types (comma-separated) |
| `author_id` | integer | - | Filter posts by specific author ID |
| `date_from` | string | YYYY-MM-DD | Get posts from this date onwards |
| `date_to` | string | YYYY-MM-DD | Get posts until this date (inclusive) |
| `search` | string | - | Search in title and content (case-insensitive) |

**Examples:**
```
GET /posts/feed/?post_type=text
GET /posts/feed/?post_type=text,video
GET /posts/feed/?author_id=5
GET /posts/feed/?date_from=2024-01-01&date_to=2024-12-31
GET /posts/feed/?search=Python
```

### Sorting Parameters

| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| `sort_by` | string | created_at, likes_count | created_at | Sort posts by specified field (descending) |

**Examples:**
```
GET /posts/feed/?sort_by=created_at
GET /posts/feed/?sort_by=likes_count
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "count": 45,
  "page": 1,
  "page_size": 10,
  "total_pages": 5,
  "next": "http://localhost:8000/posts/feed/?page=2&page_size=10&sort_by=created_at",
  "previous": null,
  "results": [
    {
      "id": 15,
      "title": "First Post",
      "content": "This is the content of the first post",
      "post_type": "text",
      "author": {
        "username": "john_doe",
        "email": "john@example.com"
      },
      "created_at": "2024-12-15T10:30:00Z",
      "likes_count": 5,
      "comments_count": 2,
      "user_liked": false
    },
    {
      "id": 14,
      "title": "Image Post",
      "content": "Check out this amazing image",
      "post_type": "image",
      "author": {
        "username": "jane_smith",
        "email": "jane@example.com"
      },
      "created_at": "2024-12-14T15:45:00Z",
      "likes_count": 12,
      "comments_count": 3,
      "user_liked": true
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of posts matching the filters |
| `page` | integer | Current page number |
| `page_size` | integer | Number of posts per page |
| `total_pages` | integer | Total number of pages |
| `next` | string/null | URL to next page (null if last page) |
| `previous` | string/null | URL to previous page (null if first page) |
| `results` | array | Array of post objects |

### Post Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Post unique identifier |
| `title` | string | Post title |
| `content` | string | Post content/body |
| `post_type` | string | Type of post (text, image, or video) |
| `author` | object | Author information (username, email) |
| `created_at` | string | ISO 8601 timestamp of post creation |
| `likes_count` | integer | Number of likes on the post |
| `comments_count` | integer | Number of comments on the post |
| `user_liked` | boolean | Whether the current user liked this post (false for unauthenticated) |

---

## Error Responses

### 400 Bad Request

Returned when invalid parameters are provided.

**Example:**
```json
{
  "error": "page must be a positive integer"
}
```

**Common Error Messages:**
- `page must be a positive integer` - Page number is less than 1
- `page_size must be between 1 and 50` - Page size is invalid
- `post_type must be one of: text, image, video` - Invalid post type provided
- `author_id must be an integer` - Author ID is not numeric
- `sort_by must be "created_at" or "likes_count"` - Invalid sort field
- `date_from must be in YYYY-MM-DD format` - Invalid date format
- `date_to must be in YYYY-MM-DD format` - Invalid date format

### 500 Internal Server Error

Returned when an unexpected server error occurs.

```json
{
  "error": "Feed retrieval failed: [error details]"
}
```

---

## Examples

### 1. Get Latest Posts (Default)
```bash
curl http://localhost:8000/posts/feed/
```

### 2. Get Second Page with Custom Page Size
```bash
curl http://localhost:8000/posts/feed/?page=2&page_size=5
```

### 3. Get Text Posts Only
```bash
curl http://localhost:8000/posts/feed/?post_type=text
```

### 4. Get Posts from Specific Author
```bash
curl http://localhost:8000/posts/feed/?author_id=3
```

### 5. Search Posts by Title/Content
```bash
curl http://localhost:8000/posts/feed/?search=Django
```

### 6. Get Most Popular Posts
```bash
curl http://localhost:8000/posts/feed/?sort_by=likes_count
```

### 7. Get Posts from Last Month
```bash
curl "http://localhost:8000/posts/feed/?date_from=2024-11-15&date_to=2024-12-15"
```

### 8. Advanced: Combined Filters
```bash
curl "http://localhost:8000/posts/feed/?post_type=text,image&author_id=2&sort_by=likes_count&page=1&page_size=20"
```

---

## Database Optimization

The feed endpoint uses Django's query optimization techniques:

1. **Annotations:** Likes and comments counts are calculated using `Count()` aggregation
2. **Select Related:** Author information is fetched in a single query
3. **Prefetch Related:** Likes are prefetched for efficient user_liked checking
4. **Indexing:** Posts are indexed by created_at and author_id for fast filtering

---

## Sorting Behavior

### By Created At (Default)
Posts are sorted by creation timestamp in descending order (most recent first).

```
sort_by=created_at
```

### By Likes Count
Posts are sorted by number of likes in descending order, with creation date as tiebreaker.

```
sort_by=likes_count
```

---

## Filtering Behavior

### Post Type
- Single type: `post_type=text`
- Multiple types: `post_type=text,video` (comma-separated, no spaces)
- Valid values: `text`, `image`, `video`

### Date Range
- From date: `date_from=2024-01-01` (inclusive)
- To date: `date_to=2024-12-31` (inclusive)
- Both are optional and can be used independently
- Format must be YYYY-MM-DD (ISO 8601)

### Search
- Case-insensitive search across title and content
- Returns all posts where title OR content contains the search term
- Example: `search=python` matches "Python Tutorial" and "Learn python basics"

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions may include:
- Per-IP rate limiting
- Per-user rate limiting
- Request throttling for large page sizes

---

## Testing

### Unit Tests
20 automated tests cover:
- Pagination (first page, last page, invalid page numbers)
- Sorting (created_at, likes_count, invalid sort)
- Filtering (post_type, author_id, date range, search)
- Combined filters
- Error handling
- Response structure

**Run tests:**
```bash
python manage.py test posts.tests.FeedAPITest -v 2
```

### Postman Collection
A comprehensive Postman collection (`postman_feed_collection.json`) includes:
- Basic feed requests
- Pagination examples
- Filtering examples
- Sorting examples
- Error test cases

**Import in Postman:**
1. Open Postman
2. Click "Import"
3. Choose the `postman_feed_collection.json` file
4. All endpoints will be available for testing

---

## Performance Notes

- **Pagination:** Always use reasonable page_size values (recommended: 10-50)
- **Large datasets:** For >10,000 posts, consider implementing cursor-based pagination
- **Search:** Complex searches may be slower; consider full-text search for production
- **Caching:** Consider implementing caching for frequently accessed feeds

---

## Future Enhancements

Potential improvements for future versions:
1. Cursor-based pagination for better performance
2. Full-text search capabilities
3. User feed (only posts from followed users)
4. Trending posts algorithm
5. Recommendation system
6. Real-time updates with WebSockets
7. Feed caching strategies
8. Advanced analytics (impressions, engagement)

---

## Support & Questions

For issues or questions about the news feed API:
1. Check the error message in the response
2. Verify all query parameters are correctly formatted
3. Test with the Postman collection
4. Review the automated tests for usage examples

