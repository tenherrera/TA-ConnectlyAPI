from django.db import models
from django.conf import settings
from django.contrib.auth.models import User  # <--- The Real Django User

class Post(models.Model):
    # Factory Pattern Requirements
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    title = models.CharField(max_length=255, default="Untitled")
    content = models.TextField()
    # Link to the Real User
    author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    metadata = models.JSONField(default=dict, blank=True) 

    def __str__(self):
        return f"{self.title} by {self.author.username}"

class Comment(models.Model):
    text = models.TextField()
    # Link to the Real User
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"