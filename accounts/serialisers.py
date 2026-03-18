from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('email', 'password', 'role')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            role=validated_data.get('role', 'STAFF')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
