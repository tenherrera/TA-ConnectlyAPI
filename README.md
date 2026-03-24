# Connectly API

A Django REST Framework-based social media platform API featuring posts, comments, likes, Google OAuth authentication, and an advanced news feed with pagination, filtering, and search.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation / Setup](#installation--setup)
- [Project Structure](#project-structure)
- [Directory Guide](#directory-guide)
- [Where to Find Specific Implementations](#where-to-find-specific-implementations)
- [Usage](#usage)
- [Documentation](#documentation)
- [Additional Notes](#additional-notes)

## Project Overview

Connectly API is a REST API for a social media-style platform. It provides **posts** (text, image, video), **comments**, **likes**, **token-based and Google OAuth authentication**, and a **news feed** with pagination, filtering, sorting, and search. The API is backend-only (no UI); clients use the HTTP API to create users, publish posts, and consume the feed.

## Features

- **Posts**: Create, read, update posts with support for text, image, and video types
- **Comments**: Add and retrieve comments on posts
- **Likes**: Like posts (idempotent; unique constraint per user/post)
- **News feed**: Pagination (page size 1-50), filtering (post type, author, date range), search (title and content), sorting (`created_at` or `likes_count`)
- **Authentication**: DRF token auth and Google OAuth (`id_token`); role-based permissions (post author can update/delete own posts)

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Python**: 3.12+
- **Database**: SQLite (development)
- **Authentication**: `django-allauth`, `PyJWT`, `google-auth-oauthlib`, `rest_framework.authtoken`

## Installation / Setup

### Prerequisites

- Python 3.12 or higher
- pip

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TA-ConnectlyAPI
   ```
2. **Go to the Django project**
   ```bash
   cd connectly_project
   ```
3. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
5. **Run migrations**
   ```bash
   python manage.py migrate
   ```
6. **Optional: create a superuser**
   ```bash
   python manage.py createsuperuser
   ```
7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

API base URL: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

For production, configure environment variables (e.g. `SECRET_KEY`, `DEBUG`, `GOOGLE_OAUTH_CLIENT_ID`) and use a production database and HTTPS.

## Project Structure

```text
project-root/
├── connectly_project/            # Django application root
│   ├── connectly_project/        # Project package (settings, root URLs)
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── posts/                    # Main application
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   ├── google_oauth.py
│   │   ├── tests.py
│   │   └── migrations/
│   ├── factories/
│   ├── singletons/
│   ├── docs/                     # Project markdown documentation
│   ├── manage.py
│   ├── requirements.txt
│   └── postman_*.json
├── README.md
└── LICENSE
```

## Directory Guide

| What you need                  | Where to look                                     |
| ------------------------------ | ------------------------------------------------- |
| Core API and business logic    | `connectly_project/posts/views.py`                |
| Google OAuth login             | `connectly_project/posts/google_oauth.py`         |
| API routes (app)               | `connectly_project/posts/urls.py`                 |
| Root URL configuration         | `connectly_project/connectly_project/urls.py`     |
| Configuration (settings)       | `connectly_project/connectly_project/settings.py` |
| Database models / schema       | `connectly_project/posts/models.py`               |
| Request/response serialization | `connectly_project/posts/serializers.py`          |
| Permission rules               | `connectly_project/posts/permissions.py`          |
| Tests                          | `connectly_project/posts/tests.py`                |
| Migrations                     | `connectly_project/posts/migrations/`             |

There is no UI layer; this is an API-only project.

## Where to Find Specific Implementations

- **Authentication**
  - Token login: `posts/views.verify_password` (login endpoint)
  - Google OAuth: `posts/google_oauth.GoogleOAuthLoginView` (`POST` with `id_token`)
  - Token check: `posts/views.ProtectedView`
- **Business logic**
  - Posts CRUD, likes, comments, and feed: `posts/views.py` (e.g. `PostListCreate`, `PostDetailView`, `LikePostView`, `CommentCreateView`, `FeedView`)
- **API endpoints**
  - App routes: `posts/urls.py`
  - Root include: `connectly_project/connectly_project/urls.py` (prefix `posts/`)
- **Database interaction**
  - Models: `posts/models.py` (`Post`, `Comment`, `Like`; `User` from Django)
  - Query/annotation logic: `posts/views.py` (`annotate`, `select_related`, `prefetch_related` for feed optimizations)

## Usage

### Quick start

1. Create a user: `POST /posts/users/` with `username`, `email`, `password`
2. Login: `POST /posts/login/` with `username`, `password` (returns token)
3. Create a post: `POST /posts/posts/` with `Authorization: Token <token>` and body (`title`, `content`, `post_type`)
4. Get feed: `GET /posts/feed/`

### API endpoints (summary)

| Group            | Method           | Path                                          |
| ---------------- | ---------------- | --------------------------------------------- |
| **Auth**         | POST             | `/posts/users/` - register                    |
|                  | POST             | `/posts/login/` - token login                 |
|                  | POST             | `/posts/auth/google/login/` - Google OAuth    |
|                  | GET              | `/posts/protected/` - verify token            |
| **Users**        | GET              | `/posts/users/` - list users                  |
| **Posts**        | GET, POST        | `/posts/posts/` - list, create                |
|                  | GET, PUT, DELETE | `/posts/posts/{id}/` - detail, update, delete |
| **Interactions** | POST             | `/posts/posts/{id}/like/` - like              |
|                  | POST             | `/posts/posts/{id}/comment/` - comment        |
|                  | GET              | `/posts/posts/{id}/comments/` - list comments |
|                  | GET              | `/posts/comments/` - list all comments        |
| **Feed**         | GET              | `/posts/feed/` - paginated feed               |
| **Other**        | POST             | `/posts/factory/` - create test posts (auth)  |

### News feed (`GET /posts/feed/`)

Public endpoint (no authentication required). Common query parameters:

| Parameter   | Type   | Default    | Description                                                     |
| ----------- | ------ | ---------- | --------------------------------------------------------------- |
| `page`      | int    | 1          | Page number                                                     |
| `page_size` | int    | 10         | Items per page (max 50)                                         |
| `post_type` | string | -          | Filter: `text`, `image`, `video` (comma-separated for multiple) |
| `author_id` | int    | -          | Filter by author ID                                             |
| `date_from` | date   | -          | From date (`YYYY-MM-DD`)                                        |
| `date_to`   | date   | -          | To date (`YYYY-MM-DD`)                                          |
| `search`    | string | -          | Search in title and content                                     |
| `sort_by`   | string | created_at | `created_at` or `likes_count`                                   |

### Google OAuth (`POST /posts/auth/google/login/`)

Send JSON body with `id_token` (JWT from Google). Success response includes `token`, `user` (`id`, `username`, `email`), and `created`.

## Documentation

Detailed project documents are centralized under `connectly_project/docs/`:

- `connectly_project/docs/DELIVERABLES.md`
- `connectly_project/docs/GOOGLE_OAUTH_DOCUMENTATION.md`
- `connectly_project/docs/IMPLEMENTATION_SUMMARY.md`
- `connectly_project/docs/TEST_RESULTS_REPORT.md`
- `connectly_project/docs/POSTMAN_TESTING_GUIDE.md`
- `connectly_project/docs/NEWS_FEED_PLAN.md`
- `connectly_project/docs/NEWS_FEED_DOCUMENTATION.md`
- `connectly_project/docs/PAGINATION_CACHING_TESTING.md`
- `connectly_project/docs/RBAC_PRIVACY_TEST_REPORT.md`

## Additional Notes

- **License**: MIT (see [LICENSE](LICENSE))
- **Production**: Set `DEBUG=False`, use a production database, keep secrets in environment variables, and enforce HTTPS
- **AI Disclosure**: AI tools were used as assistive tooling for portions of code and documentation, with all outputs reviewed and edited by developers
