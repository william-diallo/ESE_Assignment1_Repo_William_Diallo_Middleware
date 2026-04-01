"""Recipient lookup helpers for notification workflows."""

from django.contrib.auth import get_user_model
from django.db.models import Q

from accounts.roles import PRIVILEGED_ROLES

User = get_user_model()


def get_admin_emails() -> list[str]:
    """Return unique email addresses for privileged admin/staff recipients."""

    admin_users = (
        User.objects.filter(
            Q(role__in=tuple(PRIVILEGED_ROLES))
            | Q(is_staff=True)
            | Q(is_superuser=True)
        )
        .exclude(email="")
        .values_list("email", flat=True)
        .distinct()
    )
    return list(admin_users)