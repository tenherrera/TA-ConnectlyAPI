from django import views
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Default Path
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),  # DRF login/logout

    # Include posts
    path('posts/', include('posts.urls')),

]


