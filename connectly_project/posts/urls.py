from django.urls import path
from . import views
from .views import UserListCreate, PostListCreate, CommentListCreate, CreatePostView

urlpatterns = [
    # path('users/', views.get_users, name='get_users'),
    # path('users/create/', views.create_user, name='create_user'),
    # path('posts/', views.get_posts, name='get_posts'),
    # path('posts/create/', views.create_post, name='create_post'),
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('login/', views.verify_password, name='verify_password'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('protected/', views.ProtectedView.as_view(), name='protected'),
    path('factory/', CreatePostView.as_view(), name='post-factory'),
]
