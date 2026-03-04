from django.urls import path
from . import views
from .views import UserListCreate, PostListCreate, CommentListCreate, CreatePostView, FeedView
from .google_oauth import GoogleOAuthLoginView

urlpatterns = [
    # path('users/', views.get_users, name='get_users'),
    # path('users/create/', views.create_user, name='create_user'),
    # path('posts/', views.get_posts, name='get_posts'),
    # path('posts/create/', views.create_post, name='create_post'),
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('login/', views.verify_password, name='verify_password'),
    path('auth/google/login/', GoogleOAuthLoginView.as_view(), name='google-oauth-login'),
    path('posts/<int:pk>/like/', views.LikePostView.as_view(), name='post-like'),
    path('posts/<int:pk>/comment/', views.CommentCreateView.as_view(), name='post-comment'),
    path('posts/<int:pk>/comments/', views.PostCommentsView.as_view(), name='post-comments'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('protected/', views.ProtectedView.as_view(), name='protected'),
    path('factory/', CreatePostView.as_view(), name='post-factory'),
]
