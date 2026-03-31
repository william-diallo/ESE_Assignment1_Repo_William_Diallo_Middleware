from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """A custom user model using email as the unique identifier."""

    email = models.EmailField(unique=True)
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")


class PasswordResetCode(models.Model):
    """Stores one-time reset codes sent to users for password reset."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_codes"
    )
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset code for {self.user.email}"

    @property
    def is_expired(self):
        """Convenience property to check if a reset code can still be used."""
        return timezone.now() > self.expires_at
