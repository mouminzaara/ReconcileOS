"""
Serializers for accounts, SimpleJWT auth, and UserProfile.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom SimpleJWT serializer enriching token payload and login response JSON
    with user profile details, email, and assigned RBAC role.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Retrieve profile role
        role = UserRole.ADMIN if user.is_superuser else UserRole.VIEWER
        if hasattr(user, 'profile') and user.profile:
            role = user.profile.role

        token['username'] = user.username
        token['email'] = user.email
        token['role'] = role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Enrich login response payload
        role = UserRole.ADMIN if self.user.is_superuser else UserRole.VIEWER
        if hasattr(self.user, 'profile') and self.user.profile:
            role = self.user.profile.role

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': role,
            'is_superuser': self.user.is_superuser
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile details.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'created_at', 'updated_at']
