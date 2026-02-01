"""
Activity Logging Middleware for automatic request tracking.
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ActivityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user activities.
    Only logs write operations (POST, PUT, PATCH, DELETE) by default.
    """

    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        "/api/account/token/",
        "/api/account/token/refresh/",
        "/api/account/token/verify/",
        "/admin/jsi18n/",
        "/static/",
        "/media/",
        "/health/",
        "/__debug__/",
    ]

    # HTTP methods to log (write operations)
    LOGGED_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    # Map HTTP methods to action types
    METHOD_ACTION_MAP = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }

    def process_response(self, request, response):
        """Log activity after response is generated."""
        try:
            # Skip if not a logged method
            if request.method not in self.LOGGED_METHODS:
                return response

            # Skip excluded paths
            if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
                return response

            # Skip if user is not authenticated
            if not hasattr(request, "user") or not request.user.is_authenticated:
                return response

            # Only log successful operations
            if response.status_code >= 400:
                return response

            # Create activity log
            self._create_log(request, response)

        except Exception as e:
            # Don't let logging errors break the request
            logger.error(f"Error logging activity: {e}")

        return response

    def _create_log(self, request, response):
        """Create an activity log entry."""
        from apps.account.models import ActivityLog

        # Extract resource type from path
        resource_type = self._extract_resource_type(request.path)
        action = self.METHOD_ACTION_MAP.get(request.method, "other")
        
        # Try to extract resource ID from response or path
        resource_id = self._extract_resource_id(request, response)

        # Build description
        description = f"{request.user.email} {action}d {resource_type}"
        if resource_id:
            description += f" (ID: {resource_id})"

        ActivityLog.log_action(
            user=request.user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            request=request,
        )
        
        # Add status code after creation
        # (done separately since log_action creates the entry)

    def _extract_resource_type(self, path):
        """Extract resource type from URL path."""
        # Remove /api/ prefix and trailing slashes
        cleaned = path.strip("/")
        if cleaned.startswith("api/"):
            cleaned = cleaned[4:]
        
        # Get the first segment as resource type
        parts = cleaned.split("/")
        if parts:
            # Handle common API patterns
            resource = parts[0].replace("-", "_").title().replace("_", "")
            return resource
        return "Unknown"

    def _extract_resource_id(self, request, response):
        """Extract resource ID from response or path."""
        # Try from response data (for creates)
        if hasattr(response, "data") and isinstance(response.data, dict):
            if "id" in response.data:
                return str(response.data["id"])
            if "data" in response.data and isinstance(response.data["data"], dict):
                if "id" in response.data["data"]:
                    return str(response.data["data"]["id"])

        # Try from URL path (for updates/deletes)
        path_parts = request.path.strip("/").split("/")
        if len(path_parts) >= 2:
            # Check if last part looks like an ID (UUID or number)
            last_part = path_parts[-1] if path_parts[-1] else path_parts[-2] if len(path_parts) > 1 else None
            if last_part:
                # UUID pattern or numeric ID
                import re
                if re.match(r'^[0-9a-f-]{36}$', last_part, re.I) or last_part.isdigit():
                    return last_part

        return ""
