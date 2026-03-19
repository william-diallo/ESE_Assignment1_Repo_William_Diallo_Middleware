from django.contrib.auth.models import AbstractUser
from django.db import models


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
