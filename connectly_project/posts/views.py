import json
from singletons.logger_singleton import LoggerSingleton
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Post, User, Comment, Like  # Added Comment here; like model added
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPostAuthor
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

            # INSTRUCTION: Update user creation to use Django's create_user method
            user = User.objects.create_user(
                username=data['username'], 
                email=data['email'], 
                password=data['password'] # Added password field
            )

            return JsonResponse({'id': user.id, 'message': 'User created successfully'}, status=201)
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
            post = Post.objects.create(content=data['content'], author=author)
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

                return JsonResponse({'token': token.key, 'message': 'Authentication successful!'})
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
    def get(self, request):
        # Initialize the logger
        logger = LoggerSingleton().get_logger()
        logger.info("User requested the list of posts!")
        
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            # Call the Factory to handle the heavy lifting
            new_post = PostFactory.create_post(
                post_type=request.data.get('post_type'),
                title=request.data.get('title'),
                author=request.user, # The logged-in user
                content=request.data.get('content'),
                metadata=request.data.get('metadata')
            )

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
            
            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            paginated_posts = queryset[start:end]
            
            # Serialize
            serializer = FeedSerializer(
                paginated_posts, 
                many=True,
                context={'request': request}
            )
            
            # Build pagination links
            next_page = None
            prev_page = None
            
            if page < total_pages:
                next_page = request.build_absolute_uri(
                    f'?page={page + 1}&page_size={page_size}&sort_by={sort_by}'
                )
            
            if page > 1:
                prev_page = request.build_absolute_uri(
                    f'?page={page - 1}&page_size={page_size}&sort_by={sort_by}'
                )
            
            return Response({
                'count': total_count,
                'next': next_page,
                'previous': prev_page,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
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
    # Instruction: Enforce role-based permissions
    permission_classes = [IsAuthenticated, IsPostAuthor]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)

            # Instruction: Check object permissions manually for the object
            self.check_object_permissions(request, post)

            return Response({"content": post.content, "author": post.author.username})
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

    # (Optional) Adding PUT to test editing permissions later
    def put(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post) # This triggers IsPostAuthor

            post.content = request.data.get("content", post.content)
            post.save()
            return Response({"message": "Post updated successfully", "content": post.content})
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

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

        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
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

        text = request.data.get('text') or request.data.get('content')
        if not text:
            return Response({'error': 'No comment text provided'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(post=post, author=request.user, text=text)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class PostCommentsView(APIView):
    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)