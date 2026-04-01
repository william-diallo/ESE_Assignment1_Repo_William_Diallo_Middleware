"""Common helpers shared across test modules."""

from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_user(email: str, password: str, role: str = "STAFF"):
    """Create a user without relying on a custom manager signature."""

    user = User.objects.create(email=email, role=role)
    user.set_password(password)
    user.save(update_fields=["password"])
    return user