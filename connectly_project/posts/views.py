import json
import hashlib
from singletons.logger_singleton import LoggerSingleton
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Like, UserProfile
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPostAuthor, IsAdminRole, can_view_post
from rest_framework.views import APIView       
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from .serializers import UserSerializer, PostSerializer, CommentSerializer, FeedSerializer
from django.contrib.auth import login
from factories.post_factory import PostFactory
from rest_framework.authtoken.models import Token
from django.db.models import Count, Q
from django.utils.dateparse import parse_date


FEED_CACHE_VERSION_KEY = 'feed_cache_version'
FEED_CACHE_TIMEOUT = 60


def get_feed_cache_version():
    version = cache.get(FEED_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(FEED_CACHE_VERSION_KEY, version, None)
    return version


def invalidate_feed_cache():
    try:
        cache.incr(FEED_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(FEED_CACHE_VERSION_KEY, 2, None)


def build_feed_cache_key(request):
    visibility_scope = f"user:{request.user.id}" if request.user.is_authenticated else 'guest'
    raw_key = f"feed:{get_feed_cache_version()}:{visibility_scope}:{request.get_full_path()}"
    return f"feed:{hashlib.md5(raw_key.encode('utf-8')).hexdigest()}"


# Function 1: To get users
def get_users(request):
    try:
        users = list(User.objects.values('id', 'username', 'email', 'created_at'))
        return JsonResponse(users, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Function 2: To create a new user (UPDATED)
@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return JsonResponse(
                {'id': user.id, 'role': serializer.data['role'], 'message': 'User created successfully'},
                status=201
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# Function 3: Retrieve All Posts
def get_posts(request):
    try:
        posts = list(Post.objects.values('id', 'content', 'author', 'created_at'))
        return JsonResponse(posts, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Function 4: To Create a Post
@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            author = User.objects.get(id=data['author'])
            post = Post.objects.create(
                title=data.get('title', 'Untitled'),
                content=data['content'],
                author=author,
                post_type=data.get('post_type', 'text'),
                metadata=data.get('metadata', {}),
                privacy=data.get('privacy', Post.PRIVACY_PUBLIC)
            )
            invalidate_feed_cache()
            return JsonResponse({'id': post.id, 'message': 'Post created successfully'}, status=201)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Author not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
# New Function: Verify Passwords
@csrf_exempt
def verify_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                
                token, _ = Token.objects.get_or_create(user=user)
                profile, _ = UserProfile.objects.get_or_create(user=user)

                return JsonResponse({
                    'token': token.key,
                    'role': profile.role,
                    'message': 'Authentication successful!'
                })
            else:
                return JsonResponse({'error': 'Invalid credentials.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class UserListCreate(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        # Initialize the logger
        logger = LoggerSingleton().get_logger()
        logger.info("User requested the list of posts!")
        
        if request.user.is_authenticated:
            posts = Post.objects.filter(
                Q(privacy=Post.PRIVACY_PUBLIC) | Q(author=request.user)
            )
        else:
            posts = Post.objects.filter(privacy=Post.PRIVACY_PUBLIC)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Call the Factory to handle the heavy lifting
            new_post = PostFactory.create_post(
                post_type=request.data.get('post_type'),
                title=request.data.get('title'),
                author=request.user, # The logged-in user
                content=request.data.get('content'),
                metadata=request.data.get('metadata')
            )
            new_post.privacy = request.data.get('privacy', Post.PRIVACY_PUBLIC)
            new_post.save()
            invalidate_feed_cache()

            # Serialize the result to return it to the user
            return Response(PostSerializer(new_post).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # This catches our Factory errors (like missing video duration)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CommentListCreate(APIView):
    def get(self, request):
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)



# News Feed endpoint with pagination and filtering
class FeedView(APIView):
    authentication_classes = [TokenAuthentication]
    """
    GET /feed/ - News feed with pagination, sorting, and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Results per page (default: 10, max: 50)
    - sort_by: Sorting field (created_at or likes_count, default: created_at)
    - post_type: Filter by post type (text, image, video)
    - author_id: Filter by author ID
    - search: Search in title and content
    - date_from: Posts from this date (YYYY-MM-DD)
    - date_to: Posts until this date (YYYY-MM-DD)
    """
    
    def get(self, request):
        try:
            cache_key = build_feed_cache_key(request)
            cached_payload = cache.get(cache_key)
            if cached_payload is not None:
                response = Response(cached_payload, status=status.HTTP_200_OK)
                response['X-Cache'] = 'HIT'
                return response

            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            
            if page < 1:
                return Response(
                    {'error': 'page must be a positive integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if page_size < 1 or page_size > 50:
                return Response(
                    {'error': 'page_size must be between 1 and 50'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start with all posts, optimized with annotations
            queryset = Post.objects.annotate(
                likes_count=Count('likes'),
                comments_count=Count('comments')
            ).select_related('author').prefetch_related('likes')

            if request.user.is_authenticated:
                queryset = queryset.filter(
                    Q(privacy=Post.PRIVACY_PUBLIC) | Q(author=request.user)
                )
            else:
                queryset = queryset.filter(privacy=Post.PRIVACY_PUBLIC)
            
            # Apply filters
            # Filter by post_type
            post_type = request.query_params.get('post_type')
            if post_type:
                post_types = [t.strip() for t in post_type.split(',')]
                valid_types = ['text', 'image', 'video']
                for pt in post_types:
                    if pt not in valid_types:
                        return Response(
                            {'error': f'post_type must be one of: {", ".join(valid_types)}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                queryset = queryset.filter(post_type__in=post_types)
            
            # Filter by author_id
            author_id = request.query_params.get('author_id')
            if author_id:
                try:
                    queryset = queryset.filter(author_id=int(author_id))
                except ValueError:
                    return Response(
                        {'error': 'author_id must be an integer'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Search filter (title and content)
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(content__icontains=search)
                )
            
            # Date range filters
            date_from = request.query_params.get('date_from')
            if date_from:
                from_date = parse_date(date_from)
                if from_date is None:
                    return Response(
                        {'error': 'date_from must be in YYYY-MM-DD format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(created_at__date__gte=from_date)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                to_date = parse_date(date_to)
                if to_date is None:
                    return Response(
                        {'error': 'date_to must be in YYYY-MM-DD format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(created_at__date__lte=to_date)
            
            # Apply sorting
            sort_by = request.query_params.get('sort_by', 'created_at')
            if sort_by == 'created_at':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'likes_count':
                queryset = queryset.order_by('-likes_count', '-created_at')
            else:
                return Response(
                    {'error': 'sort_by must be "created_at" or "likes_count"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get total count before pagination
            total_count = queryset.count()

            paginator = Paginator(queryset, page_size)
            total_pages = paginator.num_pages

            try:
                paginated_posts = paginator.page(page)
            except EmptyPage:
                return Response(
                    {'error': 'page exceeds available results'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Serialize
            serializer = FeedSerializer(
                paginated_posts.object_list,
                many=True,
                context={'request': request}
            )
            
            # Build pagination links
            next_page = None
            prev_page = None
            
            if paginated_posts.has_next():
                next_page = request.build_absolute_uri(
                    f'?page={page + 1}&page_size={page_size}&sort_by={sort_by}'
                )
            
            if paginated_posts.has_previous():
                prev_page = request.build_absolute_uri(
                    f'?page={page - 1}&page_size={page_size}&sort_by={sort_by}'
                )
            
            payload = {
                'count': total_count,
                'next': next_page,
                'previous': prev_page,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'results': serializer.data
            }
            cache.set(cache_key, payload, FEED_CACHE_TIMEOUT)
            response = Response(payload, status=status.HTTP_200_OK)
            response['X-Cache'] = 'MISS'
            return response
        
        except ValueError as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Feed retrieval failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PostDetailView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        if not can_view_post(request.user, post):
            return Response({"error": "You do not have permission to view this post."}, status=403)
        return Response(PostSerializer(post).data)

    # (Optional) Adding PUT to test editing permissions later
    def put(self, request, pk):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            post = Post.objects.get(pk=pk)
            if not IsPostAuthor().has_object_permission(request, self, post):
                return Response({'error': 'You do not have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)

            post.content = request.data.get("content", post.content)
            post.title = request.data.get("title", post.title)
            post.privacy = request.data.get("privacy", post.privacy)
            post.save()
            invalidate_feed_cache()
            return Response({"message": "Post updated successfully", "post": PostSerializer(post).data})
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        if not IsAdminRole().has_permission(request, self):
            if request.user.is_authenticated:
                return Response({'error': 'Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        post.delete()
        invalidate_feed_cache()
        return Response({'message': 'Post deleted successfully.'}, status=status.HTTP_200_OK)

class ProtectedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authenticated!"})
    
class CreatePostView(APIView):
    # Ensure only logged-in users can create posts
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        data = request.data
        try:
            post = PostFactory.create_post(
                post_type=data['post_type'],
                title=data['title'],
                author=request.user,  # We use the logged-in user as the author
                content=data.get('content', ''),
                metadata=data.get('metadata', {})
            )
            post.privacy = data.get('privacy', Post.PRIVACY_PUBLIC)
            post.save()
            invalidate_feed_cache()
            return Response({'message': 'Post created successfully!', 'post_id': post.id}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# new endpoints for like/comment operations
class LikePostView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)

        if not can_view_post(request.user, post):
            return Response({'error': 'You do not have permission to interact with this post.'}, status=status.HTTP_403_FORBIDDEN)

        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            invalidate_feed_cache()
            return Response({'message': 'Post liked'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already liked'}, status=status.HTTP_200_OK)


class CommentCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)

        if not can_view_post(request.user, post):
            return Response({'error': 'You do not have permission to interact with this post.'}, status=status.HTTP_403_FORBIDDEN)

        text = request.data.get('text') or request.data.get('content')
        if not text:
            return Response({'error': 'No comment text provided'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(post=post, author=request.user, text=text)
        invalidate_feed_cache()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class PostCommentsView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)
        if not can_view_post(request.user, post):
            return Response({'error': 'You do not have permission to view comments for this post.'}, status=status.HTTP_403_FORBIDDEN)
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentDetailView(APIView):
    authentication_classes = [TokenAuthentication]

    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if not IsAdminRole().has_permission(request, self):
            if request.user.is_authenticated:
                return Response({'error': 'Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        comment.delete()
        invalidate_feed_cache()
        return Response({'message': 'Comment deleted successfully.'}, status=status.HTTP_200_OK)
