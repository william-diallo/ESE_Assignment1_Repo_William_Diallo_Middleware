from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration.


    This serializer validates incoming registration data, hashes the password,
    and creates a new user instance.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("email", "password", "role")

    def create(self, validated_data):
        # Create the user with a hashed password
        user = User.objects.create(
            email=validated_data["email"],
            role=validated_data.get("role", "STAFF"),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user profile data."""

    class Meta:
        model = User
        fields = ("id", "email", "role", "is_active", "is_staff", "date_joined")
        read_only_fields = ("id", "is_active", "is_staff", "date_joined")
