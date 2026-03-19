from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views import ProfileView, RegisterView




urlpatterns = [
    # User registration
    path("register/", RegisterView.as_view(), name="register"),


    # JWT authentication endpoints
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # Profile endpoint (requires a valid access token)
    path("me/", ProfileView.as_view(), name="profile"),
]