"""
Custom permission classes for API views
"""
from rest_framework import permissions


class IsAdminOrStaff(permissions.BasePermission):
    """
    Permission class to check if user is authenticated staff/superuser
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and is staff or superuser"""
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow read-only access to everyone,
    but write access only to admin users
    """

    def has_permission(self, request, view):
        """Allow safe methods for everyone, write methods for admins only"""
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsSuperUser(permissions.BasePermission):
    """
    Permission class to check if user is a superuser.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class HasPermission(permissions.BasePermission):
    """
    Permission class that checks if user has a specific permission.
    
    Usage in views:
        permission_classes = [HasPermission]
        required_permission = 'property:read'
        
    Or use the factory method:
        permission_classes = [HasPermission.with_permission('property:read')]
    """

    required_permission = None

    def __init__(self, permission=None):
        self.required_permission = permission or self.required_permission

    def has_permission(self, request, view):
        # Get permission from view if not set on class
        permission = self.required_permission or getattr(view, 'required_permission', None)
        
        if not permission:
            return True  # No permission required
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser:
            return True
        
        return request.user.has_permission(permission)

    @classmethod
    def with_permission(cls, permission):
        """Factory method to create a permission class with a specific permission."""
        class PermissionWithValue(cls):
            required_permission = permission
        PermissionWithValue.__name__ = f"HasPermission_{permission.replace(':', '_')}"
        return PermissionWithValue


class HasAnyPermission(permissions.BasePermission):
    """
    Permission class that checks if user has any of the specified permissions.
    
    Usage:
        permission_classes = [HasAnyPermission.with_permissions(['property:read', 'property:update'])]
    """

    required_permissions = []

    def has_permission(self, request, view):
        perms = self.required_permissions or getattr(view, 'required_permissions', [])
        
        if not perms:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.has_any_permission(perms)

    @classmethod
    def with_permissions(cls, permissions_list):
        """Factory method to create a permission class with specific permissions."""
        class PermissionsWithValue(cls):
            required_permissions = permissions_list
        return PermissionsWithValue


class MethodBasedPermission(permissions.BasePermission):
    """
    Permission class that maps HTTP methods to required permissions.
    
    Usage:
        permission_classes = [MethodBasedPermission]
        permission_map = {
            'GET': 'property:read',
            'POST': 'property:create',
            'PUT': 'property:update',
            'PATCH': 'property:update',
            'DELETE': 'property:delete',
        }
    """

    def has_permission(self, request, view):
        permission_map = getattr(view, 'permission_map', {})
        required_permission = permission_map.get(request.method)
        
        if not required_permission:
            return True  # No permission required for this method
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return request.user.has_permission(required_permission)

