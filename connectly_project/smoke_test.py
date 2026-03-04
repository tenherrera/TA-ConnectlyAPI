#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectly_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from posts.models import Post, Like, Comment

def run():
    User = get_user_model()
    try:
        user, created = User.objects.get_or_create(username='smoketest', defaults={'email':'smoke@example.com'})
        if created and hasattr(user, 'set_password'):
            user.set_password('password')
            user.save()

        post = Post.objects.create(title='Smoke Test', content='Smoke test content', author=user)
        like, lcreated = Like.objects.get_or_create(user=user, post=post)
        comment = Comment.objects.create(author=user, post=post, text='Looks good')

        print('SMOKE_OK', {
            'user_id': user.id,
            'post_id': post.id,
            'like_id': like.id,
            'comment_id': comment.id,
        })
    except Exception as e:
        print('SMOKE_ERROR', str(e))

if __name__ == '__main__':
    run()
