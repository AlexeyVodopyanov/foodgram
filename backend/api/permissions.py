from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class OnlyReadAuthorAdmin(permissions.BasePermission):
    """Чтение или доступно только админ и автор."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user == obj.author or request.user.is_staff:
            return True
        raise PermissionDenied('Вы не являетесь автором этого рецепта')
