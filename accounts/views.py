from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serialisers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """API endpoint for registering a new user."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    """API endpoint to return the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
