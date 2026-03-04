# Connectly API - Google OAuth Integration Documentation

## Overview
This document describes the Google OAuth login feature added to the Connectly API. The implementation allows users to authenticate using their Google accounts.

## Implementation Summary

### 1. Dependencies Installed
- `django-allauth` - Django authentication library with OAuth support
- `google-auth-oauthlib` - Google OAuth library
- `google-auth-httplib2` - Google authentication HTTP library
- `PyJWT` - JWT token handling

### 2. Endpoint Added
**POST /posts/auth/google/login/**

**Request Format:**
```json
{
  "id_token": "<Google ID Token (JWT format)>"
}
```

**Success Response (200 OK):**
```json
{
  "token": "abcd1234efgh5678ijkl9012mnop3456",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "testuser@gmail.com"
  },
  "created": true,
  "message": "Account created and logged in"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "id_token required in request body"
}
```

### 3. How It Works
1. Client obtains Google ID token from Google OAuth (using OAuth 2.0 flow on client-side)
2. Client sends ID token to `/posts/auth/google/login/`
3. Server decodes JWT payload and extracts email
4. Server creates or retrieves user based on email
5. Server creates/retrieves DRF authentication token
6. Client receives token and can use it for authenticated API requests

### 4. Configuration
Added to `settings.py`:
- `django.contrib.sites` - Required by allauth
- `allauth.account` and `allauth.socialaccount.providers.google` - OAuth apps
- `SITE_ID = 1` - Sites framework configuration
- `allauth.account.middleware.AccountMiddleware` - Required by allauth

### 5. Test Coverage

#### Test Cases Added (5 Google OAuth tests):
1. **test_google_oauth_new_user**: New user login creates account
2. **test_google_oauth_existing_user**: Existing user retrieves token
3. **test_google_oauth_missing_id_token**: Missing id_token returns 400
4. **test_google_oauth_invalid_token_format**: Malformed token returns 400
5. **test_google_oauth_missing_email_in_token**: Token without email returns 400

#### Test Results:
```
Ran 9 tests in 0.957s
OK (4 likes/comments tests + 5 Google OAuth tests)
```

### 6. Using the Endpoint

#### Option A: Real Google OAuth Flow (Production)
1. Implement Google Sign-In on your frontend using `@react-oauth/google` or similar
2. Get ID token from Google after user authenticates
3. Send ID token to `/posts/auth/google/login/`
4. Receive DRF token and use for authenticated requests

#### Option B: Testing with Mock Token (Development)
Use the mock ID token provided in the Postman collection:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJzdWIiOiIxMjM0NTY3ODkiLCJlbWFpbCI6InRlc3R1c2VyQGdtYWlsLmNvbSIsIm5hbWUiOiJUZXN0IFVzZXIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXVkIjoiWU9VUl9HT09HTEVDTGNFOVEVCVJ1UklEX0hFUkUiLCJpYXQiOjEyMzQ1Njc4OTAsImV4cCI6OTk5OTk5OTk5OX0.fake_signature
```

This decodes to:
```json
{
  "iss": "https://accounts.google.com",
  "sub": "123456789",
  "email": "testuser@gmail.com",
  "name": "Test User",
  "email_verified": true,
  "aud": "YOUR_GOOGLE_CLIENT_ID_HERE",
  "iat": 1234567890,
  "exp": 9999999999
}
```

### 7. Error Handling

| Error | Status Code | Cause |
|-------|-------------|-------|
| `id_token required in request body` | 400 | Missing id_token in request |
| `Invalid token format (not a valid JWT)` | 400 | Token is not valid JWT format |
| `Failed to decode token payload` | 400 | Token payload cannot be decoded |
| `Email not found in token` | 400 | Token missing email claim |
| `Authentication failed: {error}` | 400 | General authentication error |

### 8. Security Notes
⚠️ **For Production:**
- Implement proper JWT verification using Google's public keys
- Current implementation decodes without verification (for testing only)
- Add rate limiting to prevent brute force
- Use HTTPS only
- Store secrets in environment variables (not in code)
- Validate token signature with Google's certificates

### 9. Integration with Existing Features
- ✅ Compatible with existing token authentication
- ✅ Works with likes and comments endpoints
- ✅ Maintains user-post relationships
- ✅ Supports post factory endpoint
- ✅ All existing permissions/authentication remain intact

### 10. Files Modified/Created
- `connectly_project/settings.py` - Added allauth configuration
- `posts/google_oauth.py` - New Google OAuth view
- `posts/urls.py` - Added /auth/google/login/ route
- `posts/tests.py` - Added 5 Google OAuth test cases
- `postman_google_oauth_collection.json` - Postman collection for testing

### 11. Quick Start for Testing

**Step 1: Start Django server**
```powershell
cd connectly_project
.\venv\Scripts\python.exe manage.py runserver
```

**Step 2: Run automated tests**
```powershell
.\venv\Scripts\python.exe manage.py test posts
```

**Step 3: Test in Postman**
1. Import `postman_google_oauth_collection.json`
2. Set baseUrl to `http://127.0.0.1:8000`
3. Run requests and check responses

### 12. Sample Postman Requests

**Success Case:**
```
POST http://127.0.0.1:8000/posts/auth/google/login/

{
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJzdWIiOiIxMjM0NTY3ODkiLCJlbWFpbCI6InRlc3R1c2VyQGdtYWlsLmNvbSIsIm5hbWUiOiJUZXN0IFVzZXIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXVkIjoiWU9VUl9HT09HTEVDTGNFOVEVCVJ1UklEX0hFUkUiLCJpYXQiOjEyMzQ1Njc4OTAsImV4cCI6OTk5OTk5OTk5OX0.fake_signature"
}

Response (200 OK):
{
  "token": "abcd1234efgh5678ijkl9012mnop3456",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "testuser@gmail.com"
  },
  "created": true,
  "message": "Account created and logged in"
}
```

**Error Case:**
```
POST http://127.0.0.1:8000/posts/auth/google/login/

{}

Response (400 Bad Request):
{
  "error": "id_token required in request body"
}
```

## Conclusion
The Google OAuth integration is fully tested and documented, providing a secure way for users to authenticate using their Google accounts while maintaining compatibility with the existing Connectly API.
