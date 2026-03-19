from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """Permission class that allows read-only access to authenticated users,
    while restricting write access to staff and admins.

    * Any authenticated user can list/retrieve inventory data.
    * Only users with role 'ADMIN' or 'STAFF' can create/update/delete.
    """

    def has_permission(self, request, view):
        # Require authentication for all inventory endpoints.
        if not request.user or not request.user.is_authenticated:
            return False

        # Safe methods (GET, HEAD, OPTIONS) are allowed for authenticated users.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access only for staff/admin roles.
        return getattr(request.user, "role", "") in {"ADMIN", "STAFF"}


class AllowAnonymousCreate(permissions.BasePermission):
    """Allow anonymous users to create resources (POST) but require authentication for reading.

    This mirrors the common pattern where user registration is open (anyone can POST to create a user),
    but reading/listing requires authentication.
    """

    def has_permission(self, request, view):
        # Allow anyone to create data.
        if request.method == "POST":
            return True

        # For non-POST requests, require authentication.
        return bool(request.user and request.user.is_authenticated)
