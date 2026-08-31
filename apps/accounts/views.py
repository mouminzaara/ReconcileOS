"""
API Views for Authentication and User Profile (SimpleJWT & RBAC).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserProfileSerializer
from .models import UserProfile, UserRole


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view returning token + user role profile payload.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
    """
    Returns current authenticated user profile and RBAC role.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = UserRole.ADMIN if user.is_superuser else UserRole.VIEWER
        if hasattr(user, 'profile') and user.profile:
            role = user.profile.role

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": role,
            "is_superuser": user.is_superuser
        })
