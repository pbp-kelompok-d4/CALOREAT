from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffOrReadOnly(BasePermission):
    """Allow public reads while reserving guide management for staff users."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsReviewCreatorOrSuperuserDeleteOrReadOnly(BasePermission):
    message = "You do not have permission to perform this action on this review."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.method == "POST":
            return not request.user.is_superuser

        if request.method in ("PUT", "PATCH", "DELETE"):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        is_creator = (
            obj.created_by_id is not None and obj.created_by_id == request.user.id
        )

        if request.method in ("PUT", "PATCH"):
            return is_creator

        if request.method == "DELETE":
            return request.user.is_superuser or is_creator

        return False
