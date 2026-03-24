from rest_framework import permissions
from .models import Post, UserProfile

class IsPostAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author.username == request.user.username


class IsAdminRole(permissions.BasePermission):
    message = 'Admin role required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return profile.role == UserProfile.ROLE_ADMIN


def can_view_post(user, post):
    if post.privacy == Post.PRIVACY_PUBLIC:
        return True
    return bool(user and user.is_authenticated and post.author_id == user.id)
