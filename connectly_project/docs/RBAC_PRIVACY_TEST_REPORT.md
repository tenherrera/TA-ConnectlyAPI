# Connectly API RBAC and Privacy Test Report

## Scope

This report covers:
- Role-based access control using `admin` and `user` roles stored in `UserProfile`
- Post privacy enforcement using `public` and `private`
- Guest behavior for unauthenticated requests

## Endpoints Covered

- `POST /posts/users/`
- `POST /posts/login/`
- `POST /posts/factory/`
- `GET /posts/posts/{id}/`
- `GET /posts/feed/`
- `DELETE /posts/posts/{id}/`
- `DELETE /posts/comments/{id}/`

## Successful Test Cases

| Scenario | Request | Expected Status | Expected Result |
|---|---|---:|---|
| Create admin user | `POST /posts/users/` with `"role": "admin"` | 201 | User created and linked `UserProfile.role=admin` |
| Create regular user | `POST /posts/users/` with `"role": "user"` | 201 | User created and linked `UserProfile.role=user` |
| Owner views private post | `GET /posts/posts/{private_id}/` with owner token | 200 | Private post payload returned |
| Owner sees private post in feed | `GET /posts/feed/` with owner token | 200 | Owner feed includes own private post |
| Other user sees only public posts in feed | `GET /posts/feed/` with non-owner token | 200 | Feed excludes another user's private post |
| Admin deletes post | `DELETE /posts/posts/{id}/` with admin token | 200 | Post deleted successfully |
| Admin deletes comment | `DELETE /posts/comments/{id}/` with admin token | 200 | Comment deleted successfully |
| Create private post | `POST /posts/factory/` with `"privacy": "private"` | 201 | Stored post privacy is `private` |

## Failed Permission Test Cases

| Scenario | Request | Expected Status | Expected Result |
|---|---|---:|---|
| Other user views private post | `GET /posts/posts/{private_id}/` with non-owner token | 403 | Access denied |
| Guest views private post | `GET /posts/posts/{private_id}/` without token | 403 | Access denied |
| Non-admin deletes post | `DELETE /posts/posts/{id}/` with regular user token | 403 | Admin role required |
| Guest deletes post | `DELETE /posts/posts/{id}/` without token | 401 | Authentication required |
| Non-admin deletes comment | `DELETE /posts/comments/{id}/` with regular user token | 403 | Admin role required |

## Edge Cases

| Scenario | Request | Expected Status | Expected Result |
|---|---|---:|---|
| Delete non-existent post as admin | `DELETE /posts/posts/99999/` | 404 | Post not found |
| Delete non-existent comment as admin | `DELETE /posts/comments/99999/` | 404 | Comment not found |
| Create user without role | `POST /posts/users/` without `role` | 201 | Role defaults to `user` |
| Create post without privacy | `POST /posts/factory/` without `privacy` | 201 | Privacy defaults to `public` |
| Guest feed request | `GET /posts/feed/` without token | 200 | Only public posts returned |

## Postman Validation Flow

1. Import [`postman_collection.json`](c:\Users\masof\Downloads\MO-IT152-main\MO-IT152-main\connectly_project\postman_collection.json).
2. Create an admin user and a regular user.
3. Log in and store the tokens in `adminToken`, `userToken`, and `ownerToken`.
4. Create one `public` post and one `private` post as the owner.
5. Run the read-access requests:
   - owner should get `200` for the private post
   - non-owner should get `403`
   - guest should get `403`
6. Run the feed requests:
   - owner feed should include the private post
   - other user feed should exclude it
7. Run the delete requests:
   - admin delete should return `200`
   - non-admin delete should return `403`

## Automated Coverage Added

Automated Django tests were added for:
- private post visibility
- feed privacy filtering
- admin-only post deletion
- admin-only comment deletion
- role assignment on user creation
- privacy assignment on post creation

## Execution Notes

Run these commands after migrations are applied:

```bash
python manage.py migrate
python manage.py test posts.tests -v 2
```

If your local Python launcher is unavailable, use the interpreter configured for the project virtual environment from your IDE terminal.
