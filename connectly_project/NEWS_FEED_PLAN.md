# Connectly News Feed - Implementation Plan

## 1. Sorting Logic

### Primary Sorting (Recommended)
**Most Recent First (Chronological - Descending)**
- Sort by `created_at DESC`
- Most common and expected behavior for social feeds
- Users see latest posts immediately
- Mimics Twitter, Instagram, Facebook defaults

### Secondary Sorting Options (Optional)
| Option | Logic | Use Case |
|--------|-------|----------|
| **Popularity** | Sort by `likes.count()` DESC | Trending/Viral content |
| **Most Discussed** | Sort by `comments.count()` DESC | Community engagement |
| **Trending** | `(likes_count * 0.7 + comments_count * 0.3)` + time decay | Best of both |
| **Oldest First** | Sort by `created_at` ASC | Archive view |

**Recommendation**: Start with "Most Recent" as default, add popularity sorting as optional `sort_by` parameter.

---

## 2. Filters & User-Specific Logic

### Recommended Filters
| Filter | Parameter | Type | Example |
|--------|-----------|------|---------|
| **Post Type** | `post_type` | string | `?post_type=text` or `?post_type=image,video` |
| **Date Range** | `date_from`, `date_to` | ISO date | `?date_from=2026-01-01&date_to=2026-03-05` |
| **Author** | `author_id` | integer | `?author_id=5` |
| **Search** | `search` | string | `?search=django` |

### User-Specific Logic (Enhanced Feed)
- ✅ Show "liked by current user" status for each post
- ✅ Show comment count and like count on each post
- ✅ Include user's own posts in feed
- ❌ (Advanced) Follow-only filter - not in v1, requires follow model

### Decision: Follow-Only vs Public Feed
**Choose: Public Feed (All Posts)**
- Simpler implementation (no follow model required)
- All users see all posts
- User can still filter by specific author if interested
- Future enhancement: Add follow system later

---

## 3. Pagination Strategy

### Implementation Choice: Cursor/Page-Based Pagination
**Use Page-Based Pagination (simpler for this use case)**

**Parameters:**
```
GET /feed/?page=1&page_size=10&sort_by=created_at
```

**Default Values:**
- `page`: 1 (first page)
- `page_size`: 10 posts per page (max 50 to prevent abuse)
- `sort_by`: `created_at` (default) or `likes_count`

**Response Format:**
```json
{
  "count": 157,
  "next": "http://api.example.com/feed/?page=2&page_size=10",
  "previous": null,
  "results": [
    { "id": 1, "title": "...", "likes_count": 5, ... },
    { "id": 2, "title": "...", "likes_count": 3, ... }
  ]
}
```

### Why Page-Based?
- ✅ Simple to understand (`page=1`, `page=2`, etc.)
- ✅ User-friendly (can jump to specific page)
- ✅ Works with filters
- ❌ Less efficient for large datasets (but okay for Connectly)

---

## 4. Query Optimization

### Database Considerations
```python
# BAD (N+1 problem)
posts = Post.objects.all()[:10]
for post in posts:
    print(post.likes.count())  # ← Extra query per post!

# GOOD (efficient)
from django.db.models import Count, Prefetch
posts = Post.objects.annotate(
    likes_count=Count('likes'),
    comments_count=Count('comments')
).prefetch_related('author').order_by('-created_at')[:10]
```

**Optimizations to implement:**
1. Use `annotate()` to count likes/comments in one query
2. Use `select_related()` for author (ForeignKey)
3. Use `prefetch_related()` for comments if returning them
4. Index `created_at` field for sorting efficiency
5. Limit results per page (don't allow unlimited results)

---

## 5. Error Handling

| Scenario | Status | Response |
|----------|--------|----------|
| Page > max pages | 200 OK | Empty results array |
| Invalid page (negative/text) | 400 Bad Request | `{"error": "page must be positive integer"}` |
| Invalid page_size | 400 Bad Request | `{"error": "page_size must be 1-50"}` |
| Invalid sort_by | 400 Bad Request | `{"error": "sort_by must be 'created_at' or 'likes_count'}` |
| Invalid filter | 400 Bad Request | `{"error": "post_type must be text/image/video"}` |

---

## 6. Endpoint Specification

### GET /feed/

**Query Parameters:**
```
page=1                  # Page number (default: 1)
page_size=10           # Results per page (default: 10, max: 50)
sort_by=created_at     # Sorting field (created_at or likes_count)
post_type=text         # Filter by post type (text, image, video - comma-separated)
author_id=5            # Filter by author ID
search=keyword         # Search in title/content
date_from=2026-01-01   # Filter posts from this date
date_to=2026-03-05     # Filter posts until this date
```

**Success Response (200 OK):**
```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/feed/?page=2&page_size=10",
  "previous": null,
  "page": 1,
  "page_size": 10,
  "total_pages": 5,
  "results": [
    {
      "id": 10,
      "title": "New Django Feature",
      "content": "Django 6.0 released with...",
      "author": {
        "id": 3,
        "username": "smoketest",
        "email": "smoke@example.com"
      },
      "created_at": "2026-03-05T14:30:00Z",
      "post_type": "text",
      "likes_count": 7,
      "comments_count": 2,
      "user_liked": false
    }
  ]
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "page_size must be between 1 and 50"
}
```

**Edge Case - Beyond last page (200 OK with empty results):**
```json
{
  "count": 42,
  "next": null,
  "previous": "http://127.0.0.1:8000/feed/?page=4&page_size=10",
  "page": 5,
  "page_size": 10,
  "total_pages": 5,
  "results": []
}
```

---

## 7. Implementation Checklist

- [ ] Create FeedSerializer with likes_count and comments_count
- [ ] Create FeedView with pagination (rest_framework.pagination)
- [ ] Add sorting logic (order_by parameter)
- [ ] Add filters (post_type, author_id, date_range, search)
- [ ] Optimize queries (annotate, select_related, prefetch_related)
- [ ] Add URL route: `path('feed/', FeedView.as_view(), name='feed')`
- [ ] Write tests for pagination, sorting, filters, errors
- [ ] Create Postman collection with sample requests
- [ ] Document all parameters and responses

---

## 8. Testing Plan

### Test Cases
1. ✅ Retrieve first page of posts (default page=1)
2. ✅ Retrieve second page (page=2)
3. ✅ Pagination limits (page_size=50 max)
4. ✅ Invalid page (page=abc → error)
5. ✅ Beyond last page (page=999 → empty results)
6. ✅ Sort by created_at (default)
7. ✅ Sort by likes_count (popularity)
8. ✅ Filter by post_type
9. ✅ Filter by author_id
10. ✅ Search by keyword
11. ✅ Date range filter
12. ✅ Combination filters

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Primary Sort** | Most Recent (created_at DESC) |
| **Optional Sorts** | Likes count (popularity) |
| **Filters** | post_type, author_id, date_range, search |
| **Pagination** | Page-based (page, page_size) |
| **Feed Type** | Public (all posts visible) |
| **User-Specific** | Show "user_liked" status per post |
| **Default Page Size** | 10 posts |
| **Max Page Size** | 50 posts |
| **Query Optimization** | annotate() + select_related() |

Ready to implement? Let me know!
