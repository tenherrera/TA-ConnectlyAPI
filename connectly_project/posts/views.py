import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Post
from .models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPostAuthor
from rest_framework.views import APIView       
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from .serializers import UserSerializer, PostSerializer, CommentSerializer
from django.contrib.auth import login


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
        
# New Function: Verify Passwords (Fixed Indentation)
@csrf_exempt
def verify_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            # INSTRUCTION: Use the authenticate method to validate credentials
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse({'message': 'Authentication successful!'})
            else:
                return JsonResponse({'error': 'Invalid credentials.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# --- Class-Based Views ---

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
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    def get(self, request):
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

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