from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from posts.models import Post
import json
import base64


class LikesCommentsAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.username = 'apitest'
        self.password = 'pass1234'
        self.user = User.objects.create_user(username=self.username, email='api@test', password=self.password)
        # create a post
        self.post = Post.objects.create(title='API Test', content='API content', author=self.user)
        self.client = APIClient()

    def test_like_comment_and_get_comments(self):
        # get token via login endpoint
        resp = self.client.post('/posts/login/', {'username': self.username, 'password': self.password}, format='json')
        self.assertEqual(resp.status_code, 200)
        # verify_password returns a Django JsonResponse; parse JSON
        token = resp.json().get('token')
        self.assertTrue(token)
        # set auth
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # like post
        like_resp = self.client.post(f'/posts/posts/{self.post.id}/like/')
        self.assertIn(like_resp.status_code, (200, 201))

        # comment on post
        comment_resp = self.client.post(f'/posts/posts/{self.post.id}/comment/', {'text': 'Nice post!'}, format='json')
        self.assertEqual(comment_resp.status_code, 201)
        # comment_resp is a DRF Response in this view, so data should be available
        self.assertEqual(comment_resp.data.get('text'), 'Nice post!')

        # get comments
        get_resp = self.client.get(f'/posts/posts/{self.post.id}/comments/')
        self.assertEqual(get_resp.status_code, 200)
        self.assertTrue(isinstance(get_resp.data, list))
        self.assertTrue(any(c.get('text') == 'Nice post!' for c in get_resp.data))

    def test_like_post_multiple_times(self):
        """Test that liking a post multiple times returns the same like (idempotent)"""
        resp = self.client.post('/posts/login/', {'username': self.username, 'password': self.password}, format='json')
        token = resp.json().get('token')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # First like should return 201 Created
        like_resp1 = self.client.post(f'/posts/posts/{self.post.id}/like/')
        self.assertEqual(like_resp1.status_code, 201)

        # Second like should return 200 OK (already liked, not created again)
        like_resp2 = self.client.post(f'/posts/posts/{self.post.id}/like/')
        self.assertEqual(like_resp2.status_code, 200)
        self.assertIn('Already liked', like_resp2.data.get('message'))

    def test_comment_on_nonexistent_post(self):
        """Test that commenting on a post that doesn't exist returns 404"""
        resp = self.client.post('/posts/login/', {'username': self.username, 'password': self.password}, format='json')
        token = resp.json().get('token')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # Try to comment on non-existent post id 99999
        comment_resp = self.client.post('/posts/posts/99999/comment/', {'text': 'Comment on ghost'}, format='json')
        self.assertEqual(comment_resp.status_code, 404)
        self.assertIn('Post not found', comment_resp.data.get('error'))

    def test_get_comments_from_nonexistent_post(self):
        """Test that getting comments from a non-existent post returns 404"""
        # No auth needed for GET
        get_resp = self.client.get('/posts/posts/99999/comments/')
        self.assertEqual(get_resp.status_code, 404)
        self.assertIn('Post not found', get_resp.data.get('error'))


class GoogleOAuthTest(TestCase):
    """Test Google OAuth login endpoint"""
    
    def setUp(self):
        self.client = APIClient()
    
    def create_mock_id_token(self, email='testuser@gmail.com', name='Test User'):
        """
        Create a mock Google ID token (JWT format) for testing.
        Real tokens would be signed by Google, but for testing we create an unsigned one.
        """
        header = {'alg': 'RS256', 'typ': 'JWT'}
        payload = {
            'iss': 'https://accounts.google.com',
            'sub': '123456789',
            'email': email,
            'name': name,
            'email_verified': True,
            'aud': 'YOUR_GOOGLE_CLIENT_ID_HERE',
            'iat': 1234567890,
            'exp': 9999999999
        }
        
        # Encode as JWT (without real signature for testing)
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signature_b64 = base64.urlsafe_b64encode(b'fake_signature').decode().rstrip('=')
        
        return f'{header_b64}.{payload_b64}.{signature_b64}'
    
    def test_google_oauth_new_user(self):
        """Test Google OAuth login creates a new user"""
        mock_token = self.create_mock_id_token(email='newgoogleuser@gmail.com', name='New Google User')
        
        resp = self.client.post('/posts/auth/google/login/', {'id_token': mock_token}, format='json')
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)
        self.assertIn('user', resp.data)
        self.assertTrue(resp.data['created'])
        self.assertEqual(resp.data['user']['email'], 'newgoogleuser@gmail.com')
    
    def test_google_oauth_existing_user(self):
        """Test Google OAuth login with existing user (returns existing token)"""
        User = get_user_model()
        User.objects.create_user(username='existinguser', email='existing@gmail.com')
        
        mock_token = self.create_mock_id_token(email='existing@gmail.com')
        
        resp = self.client.post('/posts/auth/google/login/', {'id_token': mock_token}, format='json')
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)
        self.assertFalse(resp.data['created'])
        self.assertEqual(resp.data['user']['email'], 'existing@gmail.com')
    
    def test_google_oauth_missing_id_token(self):
        """Test Google OAuth without id_token returns 400"""
        resp = self.client.post('/posts/auth/google/login/', {}, format='json')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
        self.assertIn('id_token required', resp.data['error'])
    
    def test_google_oauth_invalid_token_format(self):
        """Test Google OAuth with malformed token returns 400"""
        invalid_token = 'not.a.valid.token.format'
        
        resp = self.client.post('/posts/auth/google/login/', {'id_token': invalid_token}, format='json')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_google_oauth_missing_email_in_token(self):
        """Test Google OAuth token without email returns 400"""
        header = {'alg': 'RS256', 'typ': 'JWT'}
        payload = {
            'iss': 'https://accounts.google.com',
            'sub': '123456789',
            # No email field!
            'aud': 'YOUR_GOOGLE_CLIENT_ID_HERE',
        }
        
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signature_b64 = 'fake'
        
        invalid_token = f'{header_b64}.{payload_b64}.{signature_b64}'
        
        resp = self.client.post('/posts/auth/google/login/', {'id_token': invalid_token}, format='json')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Email not found', resp.data['error'])


class FeedAPITest(TestCase):
    """Test the news feed endpoint with pagination, sorting, and filtering"""
    
    def setUp(self):
        User = get_user_model()
        # Create test users
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com')
        
        # Create posts with different types and timestamps
        self.post1 = Post.objects.create(
            title='First Post',
            content='Content 1',
            author=self.user1,
            post_type='text'
        )
        
        self.post2 = Post.objects.create(
            title='Image Post',
            content='Check out this image',
            author=self.user2,
            post_type='image'
        )
        
        self.post3 = Post.objects.create(
            title='Video Post',
            content='Watch this video',
            author=self.user1,
            post_type='video'
        )
        
        self.client = APIClient()
    
    def test_feed_basic_request(self):
        """Test basic feed request returns all posts"""
        resp = self.client.get('/posts/feed/')
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)
        self.assertIn('count', resp.data)
        self.assertEqual(resp.data['count'], 3)
        self.assertEqual(len(resp.data['results']), 3)
    
    def test_feed_pagination_first_page(self):
        """Test feed pagination first page"""
        resp = self.client.get('/posts/feed/?page=1&page_size=2')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 3)
        self.assertEqual(resp.data['page'], 1)
        self.assertEqual(resp.data['page_size'], 2)
        self.assertEqual(resp.data['total_pages'], 2)
        self.assertEqual(len(resp.data['results']), 2)
        self.assertIsNotNone(resp.data['next'])
    
    def test_feed_pagination_second_page(self):
        """Test feed pagination second page"""
        resp = self.client.get('/posts/feed/?page=2&page_size=2')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertIsNotNone(resp.data['previous'])
        self.assertIsNone(resp.data['next'])
    
    def test_feed_pagination_invalid_page(self):
        """Test feed with invalid page number"""
        resp = self.client.get('/posts/feed/?page=-1')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_pagination_invalid_page_size(self):
        """Test feed with invalid page size (exceeds max)"""
        resp = self.client.get('/posts/feed/?page_size=100')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_filter_by_post_type(self):
        """Test feed filtering by post_type"""
        resp = self.client.get('/posts/feed/?post_type=image')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Image Post')
        self.assertEqual(resp.data['results'][0]['post_type'], 'image')
    
    def test_feed_filter_by_multiple_post_types(self):
        """Test feed filtering by multiple post_types"""
        resp = self.client.get('/posts/feed/?post_type=text,video')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 2)
    
    def test_feed_filter_by_invalid_post_type(self):
        """Test feed with invalid post_type"""
        resp = self.client.get('/posts/feed/?post_type=invalid_type')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_filter_by_author(self):
        """Test feed filtering by author_id"""
        resp = self.client.get(f'/posts/feed/?author_id={self.user1.id}')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 2)
        for post in resp.data['results']:
            self.assertEqual(post['author']['username'], 'user1')
    
    def test_feed_filter_by_invalid_author(self):
        """Test feed with invalid author_id"""
        resp = self.client.get('/posts/feed/?author_id=invalid')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_search_in_title(self):
        """Test feed search in title"""
        resp = self.client.get('/posts/feed/?search=Image')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Image Post')
    
    def test_feed_search_in_content(self):
        """Test feed search in content"""
        resp = self.client.get('/posts/feed/?search=video')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Video Post')
    
    def test_feed_sorting_by_created_at_default(self):
        """Test feed sorting by created_at (most recent first)"""
        resp = self.client.get('/posts/feed/?sort_by=created_at')
        
        self.assertEqual(resp.status_code, 200)
        # Most recent post should be first
        self.assertEqual(resp.data['results'][0]['id'], self.post3.id)
    
    def test_feed_sorting_invalid(self):
        """Test feed with invalid sort_by parameter"""
        resp = self.client.get('/posts/feed/?sort_by=invalid_sort')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_with_like_counts(self):
        """Test that feed includes like counts"""
        resp = self.client.get('/posts/feed/')
        
        self.assertEqual(resp.status_code, 200)
        for post in resp.data['results']:
            self.assertIn('likes_count', post)
            self.assertEqual(post['likes_count'], 0)
    
    def test_feed_with_comment_counts(self):
        """Test that feed includes comment counts"""
        resp = self.client.get('/posts/feed/')
        
        self.assertEqual(resp.status_code, 200)
        for post in resp.data['results']:
            self.assertIn('comments_count', post)
    
    def test_feed_user_liked_field_unauthenticated(self):
        """Test that user_liked field is false for unauthenticated users"""
        resp = self.client.get('/posts/feed/')
        
        self.assertEqual(resp.status_code, 200)
        for post in resp.data['results']:
            self.assertIn('user_liked', post)
            self.assertFalse(post['user_liked'])
    
    def test_feed_combined_filters(self):
        """Test feed with multiple filters combined"""
        resp = self.client.get(f'/posts/feed/?post_type=text&author_id={self.user1.id}')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'First Post')
    
    def test_feed_pagination_max_page_size(self):
        """Test that page_size cannot exceed maximum of 50"""
        resp = self.client.get('/posts/feed/?page_size=51')
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)
    
    def test_feed_default_pagination_values(self):
        """Test that default pagination uses page=1 and page_size=10"""
        resp = self.client.get('/posts/feed/')
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['page'], 1)
        self.assertEqual(resp.data['page_size'], 10)
