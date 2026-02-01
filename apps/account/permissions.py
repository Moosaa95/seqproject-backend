"""
Permission constants for the application.
These define all available permissions that can be assigned to roles.
"""


class Permissions:
    """
    All available permissions in the system.
    Format: RESOURCE_ACTION
    """

    # Property permissions
    PROPERTY_READ = "property:read"
    PROPERTY_CREATE = "property:create"
    PROPERTY_UPDATE = "property:update"
    PROPERTY_DELETE = "property:delete"

    # Booking permissions
    BOOKING_READ = "booking:read"
    BOOKING_CREATE = "booking:create"
    BOOKING_UPDATE = "booking:update"
    BOOKING_DELETE = "booking:delete"

    # Payment permissions
    PAYMENT_READ = "payment:read"
    PAYMENT_CREATE = "payment:create"
    PAYMENT_REFUND = "payment:refund"

    # User management permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Role management permissions
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    # Activity logs permissions
    LOGS_READ = "logs:read"

    # Inventory permissions
    INVENTORY_READ = "inventory:read"
    INVENTORY_CREATE = "inventory:create"
    INVENTORY_UPDATE = "inventory:update"
    INVENTORY_DELETE = "inventory:delete"

    # Location permissions
    LOCATION_READ = "location:read"
    LOCATION_CREATE = "location:create"
    LOCATION_UPDATE = "location:update"
    LOCATION_DELETE = "location:delete"

    # Contact inquiry permissions
    INQUIRY_READ = "inquiry:read"
    INQUIRY_UPDATE = "inquiry:update"
    INQUIRY_DELETE = "inquiry:delete"

    @classmethod
    def all_permissions(cls):
        """Return a list of all permission strings."""
        return [
            value
            for key, value in vars(cls).items()
            if isinstance(value, str) and ":" in value
        ]

    @classmethod
    def permission_choices(cls):
        """Return permissions as choices for forms/admin."""
        permissions = cls.all_permissions()
        return [(p, p.replace(":", " - ").title()) for p in permissions]

    @classmethod
    def get_permission_groups(cls):
        """Return permissions grouped by resource."""
        groups = {}
        for perm in cls.all_permissions():
            resource, action = perm.split(":")
            if resource not in groups:
                groups[resource] = []
            groups[resource].append(perm)
        return groups
