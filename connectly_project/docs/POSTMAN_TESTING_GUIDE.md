# Postman News Feed Testing Guide

**Prerequisites:**
- Django server running: `python manage.py runserver`
- Postman imported with `postman_feed_collection.json`
- Database has posts (can create via `/posts/posts/` or `/posts/factory/`)

---

## TEST GROUP 1: PAGINATION TESTS

### Test 1: Feed - Basic Request
**URL**: `http://localhost:8000/posts/feed/`
**Method**: GET
**Parameters**: None (uses defaults)

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "title": "Third Post",
      "content": "Content here",
      "post_type": "text",
      "author": {
        "username": "user2",
        "email": "user2@example.com"
      },
      "created_at": "2024-12-15T14:00:00Z",
      "likes_count": 0,
      "comments_count": 0,
      "user_liked": false
    },
    // ... more posts
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- No page parameter = defaults to page 1
- No page_size parameter = defaults to 10 posts per page
- All posts from database are returned (most recent first)
- If you have ≤10 posts, total_pages will be 1 and next will be null
- Each post includes author info, likes count, comments count, and user_liked status

**How It's Executed:**
1. Click the request name "Feed - Basic Request"
2. Click "Send" button
3. Response appears in bottom panel
4. Check "Status" shows "200 OK"
5. Check "Body" shows JSON with your posts

---

### Test 2: Feed - Pagination Page 1
**URL**: `http://localhost:8000/posts/feed/?page=1&page_size=5`
**Method**: GET
**Parameters**: 
- `page=1`
- `page_size=5`

**Expected Response** (if you have 15+ posts):
```json
{
  "count": 15,
  "page": 1,
  "page_size": 5,
  "total_pages": 3,
  "next": "http://localhost:8000/posts/feed/?page=2&page_size=5&sort_by=created_at",
  "previous": null,
  "results": [
    {
      "id": 15,  // Most recent post
      "title": "Latest Post",
      "content": "...",
      "created_at": "2024-12-15T15:00:00Z",
      // ... post data
    },
    {
      "id": 14,  // Second most recent
      "title": "Second Latest",
      // ...
    },
    // ... 3 more posts (total of 5)
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **page=1**: Gets the first page
- **page_size=5**: Shows exactly 5 posts per page
- **count=15**: Total posts in database
- **total_pages=3**: 15 posts ÷ 5 per page = 3 pages
- **next**: URL to page 2 (has more data)
- **previous**: null (already on first page)
- **Results**: Posts sorted newest first, limited to 5

**How It's Executed:**
1. Click "Feed - Pagination Page 1"
2. Click "Send"
3. See 5 posts in the results array
4. Note the "next" URL provided for fetching page 2

---

### Test 3: Feed - Pagination Page 2
**URL**: `http://localhost:8000/posts/feed/?page=2&page_size=5`
**Method**: GET
**Parameters**:
- `page=2`
- `page_size=5`

**Expected Response** (if you have 15+ posts):
```json
{
  "count": 15,
  "page": 2,
  "page_size": 5,
  "total_pages": 3,
  "next": "http://localhost:8000/posts/feed/?page=3&page_size=5&sort_by=created_at",
  "previous": "http://localhost:8000/posts/feed/?page=1&page_size=5&sort_by=created_at",
  "results": [
    {
      "id": 10,  // 6th most recent post
      "title": "Post 10",
      // ... post data
    },
    // ... 4 more posts (5 total)
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **page=2**: Gets the second page
- **previous**: Now shows URL to page 1 (can go back)
- **next**: Shows URL to page 3 (has more data)
- **Results**: Shows posts 6-10 from the newest

**How It's Executed:**
1. Click "Feed - Pagination Page 2"
2. Click "Send"
3. See different posts than page 1
4. Verify "previous" link goes back to page 1

---

## TEST GROUP 2: FILTERING TESTS

### Test 4: Feed - Filter by Post Type (text)
**URL**: `http://localhost:8000/posts/feed/?post_type=text`
**Method**: GET
**Parameters**: `post_type=text`

**Expected Response**:
```json
{
  "count": 2,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "title": "Text Post Example",
      "content": "This is text content",
      "post_type": "text",  // ← Notice this is always "text"
      "author": { ... },
      "created_at": "2024-12-15T14:00:00Z",
      "likes_count": 2,
      "comments_count": 1,
      "user_liked": false
    },
    {
      "id": 3,
      "title": "Another Text Post",
      "content": "More text",
      "post_type": "text",
      // ...
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **post_type=text**: Filters to show ONLY posts where post_type is "text"
- **count=2**: Only 2 posts in database have type "text"
- Posts with type "image" or "video" are NOT included
- All other data (author, likes, comments) shown normally

**How It's Executed:**
1. Click "Feed - Filter by Post Type (text)"
2. Click "Send"
3. Observe all returned posts have `"post_type": "text"`
4. Count is reduced (only text posts)

---

### Test 5: Feed - Filter by Post Type (image)
**URL**: `http://localhost:8000/posts/feed/?post_type=image`
**Method**: GET
**Parameters**: `post_type=image`

**Expected Response**:
```json
{
  "count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 4,
      "title": "Check out this image",
      "content": "Image post content",
      "post_type": "image",  // ← Always "image"
      // ... rest of data
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- Only posts with `post_type="image"` are returned
- Same logic as text filter, but for image posts only

---

### Test 6: Feed - Filter by Multiple Post Types
**URL**: `http://localhost:8000/posts/feed/?post_type=text,video`
**Method**: GET
**Parameters**: `post_type=text,video`

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 6,
      "title": "Video Post",
      "post_type": "video"  // ← Video post included
    },
    {
      "id": 5,
      "title": "Text Post",
      "post_type": "text"  // ← Text post included
    },
    {
      "id": 3,
      "title": "Another Text Post",
      "post_type": "text"  // ← Another text post
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **post_type=text,video**: Comma-separated values mean "OR" logic
- Returns posts that are EITHER text OR video
- Image posts are excluded (not in the filter list)
- count=3 if you have 2 text posts and 1 video post

**How It's Executed:**
1. Click "Feed - Filter by Multiple Post Types"
2. Click "Send"
3. See posts of two different types in results
4. No "image" type posts appear

---

### Test 7: Feed - Filter by Author ID
**URL**: `http://localhost:8000/posts/feed/?author_id=1`
**Method**: GET
**Parameters**: `author_id=1`

**Expected Response**:
```json
{
  "count": 2,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "title": "My First Post",
      "content": "User 1 content",
      "author": {
        "username": "john_doe",
        "email": "john@example.com"
      },
      // ... note author ID is 1
    },
    {
      "id": 7,
      "title": "My Second Post",
      "author": {
        "username": "john_doe",
        "email": "john@example.com"
      },
      // ... same author
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **author_id=1**: Only shows posts created by user with ID=1
- count=2: User 1 has created 2 posts
- All results have the same author
- Posts from other users are filtered out

**How It's Executed:**
1. Click "Feed - Filter by Author ID"
2. Click "Send"
3. Check all posts have the same author username
4. Try changing the `author_id` value to 2 to see different posts

---

## TEST GROUP 3: SEARCH TESTS

### Test 8: Feed - Search in Title
**URL**: `http://localhost:8000/posts/feed/?search=Python`
**Method**: GET
**Parameters**: `search=Python`

**Expected Response**:
```json
{
  "count": 2,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 12,
      "title": "Python Tutorial for Beginners",  // ← Contains "Python"
      "content": "Learn Python basics",
      // ...
    },
    {
      "id": 8,
      "title": "Advanced Python Tips",  // ← Contains "Python"
      "content": "Tips and tricks",
      // ...
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **search=Python**: Searches for "Python" in title AND content
- case-insensitive: "python", "Python", "PYTHON" all match
- Returns 2 posts that have "Python" in the title
- Posts without "Python" in title OR content are not returned

**How It's Executed:**
1. Click "Feed - Search in Title"
2. Click "Send"
3. Look at returned post titles - all contain "Python"
4. Try changing search term to test other keywords

---

### Test 9: Feed - Search in Content
**URL**: `http://localhost:8000/posts/feed/?search=Django`
**Method**: GET
**Parameters**: `search=Django`

**Expected Response**:
```json
{
  "count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 9,
      "title": "Web Development Guide",
      "content": "Learn Django framework...",  // ← Contains "Django"
      // ...
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **search=Django**: Searches content (even if title doesn't match)
- The title doesn't contain "Django" but the content does
- Still returns the post because search looks in both title AND content
- count=1: Only one post mentions "Django"

---

## TEST GROUP 4: SORTING TESTS

### Test 10: Feed - Sort by Created At (Default)
**URL**: `http://localhost:8000/posts/feed/?sort_by=created_at`
**Method**: GET
**Parameters**: `sort_by=created_at`

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "title": "Latest Post",
      "created_at": "2024-12-15T15:30:00Z"  // ← Most recent (newest)
    },
    {
      "id": 14,
      "title": "Second Latest",
      "created_at": "2024-12-15T14:00:00Z"  // ← Middle
    },
    {
      "id": 13,
      "title": "Oldest",
      "created_at": "2024-12-15T10:00:00Z"  // ← Oldest (appears last)
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **sort_by=created_at**: Orders by creation timestamp, newest FIRST
- Post created at 15:30 appears first (most recent)
- Post created at 10:00 appears last (oldest)
- This is the default sorting even without the parameter
- Perfect for social feeds (users see recent content first)

**How It's Executed:**
1. Click "Feed - Sort by Created At (Default)"
2. Click "Send"
3. Look at "created_at" timestamps
4. Notice they go from newest → oldest from top to bottom

---

### Test 11: Feed - Sort by Likes Count
**URL**: `http://localhost:8000/posts/feed/?sort_by=likes_count`
**Method**: GET
**Parameters**: `sort_by=likes_count`

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "title": "Popular Post",
      "likes_count": 15  // ← Most liked (appears first)
    },
    {
      "id": 12,
      "title": "Medium Popular",
      "likes_count": 8  // ← Middle
    },
    {
      "id": 7,
      "title": "Less Popular",
      "likes_count": 2  // ← Least liked (appears last)
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **sort_by=likes_count**: Orders by number of likes, most-liked FIRST
- Post with 15 likes appears first (most popular)
- Post with 2 likes appears last
- Great for seeing trending/popular posts
- Posts with same likes count sorted by most recent

**How It's Executed:**
1. Click "Feed - Sort by Likes Count"
2. Click "Send"
3. Check "likes_count" values in results
4. They should go from highest → lowest

---

## TEST GROUP 5: COMBINED FILTERS

### Test 12: Feed - Filter by Date Range
**URL**: `http://localhost:8000/posts/feed/?date_from=2024-01-01&date_to=2024-12-31`
**Method**: GET
**Parameters**: 
- `date_from=2024-01-01`
- `date_to=2024-12-31`

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "title": "December Post",
      "created_at": "2024-12-15T10:00:00Z"  // ← Within date range
    },
    {
      "id": 5,
      "title": "June Post",
      "created_at": "2024-06-20T10:00:00Z"  // ← Within date range
    },
    {
      "id": 3,
      "title": "January Post",
      "created_at": "2024-01-10T10:00:00Z"  // ← Within date range
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- **date_from=2024-01-01**: Show posts from Jan 1, 2024 onwards
- **date_to=2024-12-31**: Show posts until Dec 31, 2024
- Posts outside this date range are excluded
- Inclusive: Posts from Jan 1 and Dec 31 ARE included
- Format is YYYY-MM-DD (ISO 8601)

---

### Test 13: Feed - Filter by Date From
**URL**: `http://localhost:8000/posts/feed/?date_from=2024-01-01`
**Method**: GET
**Parameters**: `date_from=2024-01-01`

**Expected Response**:
```json
{
  "count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "created_at": "2024-12-15T10:00:00Z"  // ← All on or after Jan 1, 2024
    },
    // ...
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- Only date_from is provided (date_to is optional)
- Shows posts from Jan 1, 2024 to TODAY
- No upper date limit
- Useful for "show me posts from last month onwards"

---

### Test 14: Feed - Combined Filters
**URL**: `http://localhost:8000/posts/feed/?post_type=text&author_id=1&sort_by=likes_count&page=1&page_size=10`
**Method**: GET
**Parameters**: 
- `post_type=text`
- `author_id=1`
- `sort_by=likes_count`
- `page=1`
- `page_size=10`

**Expected Response**:
```json
{
  "count": 2,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "title": "Popular Text Post",
      "post_type": "text",  // ← Only text
      "author": {
        "username": "john_doe"  // ← Only author_id=1
      },
      "likes_count": 8,  // ← Sorted by likes (highest first)
      "created_at": "2024-12-10T10:00:00Z"
    },
    {
      "id": 7,
      "title": "Another Text Post",
      "post_type": "text",  // ← Only text
      "author": {
        "username": "john_doe"  // ← Same author
      },
      "likes_count": 3,  // ← Lower likes (appears second)
      "created_at": "2024-12-05T10:00:00Z"
    }
  ]
}
```

**Status Code**: 200 OK

**Why This Result:**
- All filters apply simultaneously:
  1. **Filter by type**: Only "text" posts (excludes image, video)
  2. **Filter by author**: Only posts by user 1 (excludes other users)
  3. **Sort by likes**: Ordered by likes count (8 likes before 3 likes)
  4. **Paginate**: page=1, showing 10 per page
- count=2: User 1 has 2 text posts
- Results sorted by popularity within the filtered subset

**How It's Executed:**
1. Click "Feed - Combined Filters"
2. Click "Send"
3. Verify all results are text posts
4. Verify all are from same author
5. Verify they're ordered by likes (descending)

---

## TEST GROUP 6: ERROR HANDLING TESTS

### Test 15: Feed - Invalid Post Type (Error)
**URL**: `http://localhost:8000/posts/feed/?post_type=invalid_type`
**Method**: GET
**Parameters**: `post_type=invalid_type`

**Expected Response**:
```json
{
  "error": "post_type must be one of: text, image, video"
}
```

**Status Code**: 400 Bad Request

**Why This Result:**
- "invalid_type" is not a valid post type
- Valid types are ONLY: text, image, video
- Server rejects the request with clear error message
- NO posts are returned
- Helps prevent invalid data filtering

**How It's Executed:**
1. Click "Feed - Invalid Post Type (Error)"
2. Click "Send"
3. Status shows "400 Bad Request" (red)
4. Response body shows the error message explaining valid values

---

### Test 16: Feed - Invalid Page Size (Error)
**URL**: `http://localhost:8000/posts/feed/?page_size=100`
**Method**: GET
**Parameters**: `page_size=100`

**Expected Response**:
```json
{
  "error": "page_size must be between 1 and 50"
}
```

**Status Code**: 400 Bad Request

**Why This Result:**
- page_size=100 exceeds the maximum of 50
- This limit protects the server from:
  - Queries being too slow
  - Returning too much data
  - Memory being wasted
- Maximum page_size is enforced to 50

**How It's Executed:**
1. Click "Feed - Invalid Page Size (Error)"
2. Click "Send"
3. Status shows "400 Bad Request"
4. Error message shows max is 50

---

### Test 17: Feed - Invalid Author ID (Error)
**URL**: `http://localhost:8000/posts/feed/?author_id=not_a_number`
**Method**: GET
**Parameters**: `author_id=not_a_number`

**Expected Response**:
```json
{
  "error": "author_id must be an integer"
}
```

**Status Code**: 400 Bad Request

**Why This Result:**
- author_id must be a number (integer)
- "not_a_number" is text, not valid
- Server validates data types
- Prevents database errors from bad input

**How It's Executed:**
1. Click "Feed - Invalid Author ID (Error)"
2. Click "Send"
3. Status shows "400 Bad Request"
4. Error explains parameter must be integer

---

### Test 18: Feed - Invalid Sort By (Error)
**URL**: `http://localhost:8000/posts/feed/?sort_by=invalid_sort`
**Method**: GET
**Parameters**: `sort_by=invalid_sort`

**Expected Response**:
```json
{
  "error": "sort_by must be \"created_at\" or \"likes_count\""
}
```

**Status Code**: 400 Bad Request

**Why This Result:**
- Only 2 valid sort options: "created_at" or "likes_count"
- "invalid_sort" is not recognized
- Server only allows safe sorting fields
- Prevents SQL injection and unexpected behaviors

---

### Test 19: Feed - Invalid Date Format (Error)
**URL**: `http://localhost:8000/posts/feed/?date_from=01-01-2024`
**Method**: GET
**Parameters**: `date_from=01-01-2024`

**Expected Response**:
```json
{
  "error": "date_from must be in YYYY-MM-DD format"
}
```

**Status Code**: 400 Bad Request

**Why This Result:**
- Date format must be YYYY-MM-DD (ISO 8601 standard)
- "01-01-2024" uses MM-DD-YYYY format (wrong)
- Server enforces strict date parsing
- Correct format: "2024-01-01"

**How It's Executed:**
1. Click "Feed - Invalid Date Format (Error)"
2. Click "Send"
3. Status shows "400 Bad Request"
4. Error message shows correct format (YYYY-MM-DD)

---

## QUICK REFERENCE TABLE

| Test Name | Method | What It Tests | Expected Status |
|-----------|--------|---------------|-----------------|
| Basic Request | GET | Default pagination | 200 OK |
| Pagination Page 1 | GET | Get first page (5/page) | 200 OK |
| Pagination Page 2 | GET | Get second page (5/page) | 200 OK |
| Filter by Post Type (text) | GET | Show only text posts | 200 OK |
| Filter by Post Type (image) | GET | Show only image posts | 200 OK |
| Multiple Post Types | GET | Show text+video posts | 200 OK |
| Filter by Author | GET | Show one author's posts | 200 OK |
| Search in Title | GET | Find "Python" posts | 200 OK |
| Search in Content | GET | Find "Django" posts | 200 OK |
| Sort by Created At | GET | Newest posts first | 200 OK |
| Sort by Likes Count | GET | Most popular first | 200 OK |
| Date Range Filter | GET | Posts between dates | 200 OK |
| Date From Filter | GET | Posts from date onwards | 200 OK |
| Combined Filters | GET | Multiple filters together | 200 OK |
| Invalid Post Type | GET | Test error handling | 400 Bad Request |
| Invalid Page Size | GET | Test max size limit | 400 Bad Request |
| Invalid Author ID | GET | Test type validation | 400 Bad Request |
| Invalid Sort By | GET | Test allowed values | 400 Bad Request |
| Invalid Date Format | GET | Test date parsing | 400 Bad Request |

---

## How to Run All Tests

1. **Start Django Server**:
   ```bash
   python manage.py runserver
   ```

2. **Open Postman** and import the collection

3. **Run each test**:
   - Click test name
   - Click "Send"
   - Check Status Code (should be 200 or 400)
   - Review Response Body

4. **Success Indicators**:
   - Green status code (200 is green, 400 is orange/red)
   - Response appears immediately
   - JSON is properly formatted
   - Data matches expectations

5. **If Something Fails**:
   - Check server is running
   - Verify database has posts
   - Look at error message
   - Check parameter values

---

This guide shows you exactly what to expect from each Postman test and WHY you get those results! 🚀

