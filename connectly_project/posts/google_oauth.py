import json
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()


class GoogleOAuthLoginView(APIView):
    """
    Handle Google OAuth token exchange.
    Expects JSON POST: {"id_token": "<Google ID Token>"}
    Returns: {"token": "<DRF Token>", "user": {...}, "created": bool}
    """
    csrf_classes = []
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        try:
            id_token_str = request.data.get('id_token')
            if not id_token_str:
                return Response(
                    {'error': 'id_token required in request body'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse and decode JWT payload
            parts = id_token_str.split('.')
            if len(parts) != 3:
                return Response(
                    {'error': 'Invalid token format (not a valid JWT)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Decode payload with proper padding
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            try:
                payload_json = json.loads(base64.urlsafe_b64decode(payload))
            except Exception as e:
                return Response(
                    {'error': f'Failed to decode token payload: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = payload_json.get('email')
            name = payload_json.get('name', 'GoogleUser')
            
            if not email:
                return Response(
                    {'error': 'Email not found in token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user with email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email.split('@')[0]}
            )
            
            # Get or create token
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'created': created,
                'message': 'Login successful' if not created else 'Account created and logged in'
            }, status=status.HTTP_200_OK)
        
        except json.JSONDecodeError as e:
            return Response(
                {'error': f'Invalid JSON in request: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
