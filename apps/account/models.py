from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from commons.mixins import ModelMixins
from apps.account.managers import CustomUserManager


class UserRole(ModelMixins):
    """
    Role model for role-based access control.
    Roles contain a list of permissions that define what users can do.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=list,
        help_text="List of permission strings e.g., ['property:read', 'booking:create']",
    )
    is_superuser_role = models.BooleanField(
        default=False, help_text="If true, this role grants all permissions"
    )
    is_default = models.BooleanField(
        default=False, help_text="If true, this role is assigned to new users by default"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def __str__(self):
        return self.name

    def has_permission(self, permission):
        """Check if this role has a specific permission."""
        if self.is_superuser_role:
            return True
        return permission in self.permissions

    def has_any_permission(self, permissions):
        """Check if this role has any of the given permissions."""
        if self.is_superuser_role:
            return True
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions):
        """Check if this role has all of the given permissions."""
        if self.is_superuser_role:
            return True
        return all(p in self.permissions for p in permissions)


class CustomUser(AbstractBaseUser, PermissionsMixin, ModelMixins):

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.ForeignKey(
        UserRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="The role that defines this user's permissions",
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="If true, user must change password on next login",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.email}"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def get_short_name(self):
        """
        Return the short name for the user (first name).
        """
        return self.first_name if self.first_name else self.email

    def has_permission(self, permission):
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.has_permission(permission)

    def has_any_permission(self, permissions):
        """Check if user has any of the given permissions."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.has_any_permission(permissions)

    def get_permissions(self):
        """Get list of all permissions for this user."""
        if self.is_superuser:
            from apps.account.permissions import Permissions
            return Permissions.all_permissions()
        if not self.role:
            return []
        return self.role.permissions


class EmailOTP(ModelMixins):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="email_otps"
    )
    code = models.CharField(max_length=6, blank=True, null=True)
    purpose = models.CharField(max_length=50)  # signup, login, reset
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def get_user_otp(cls, email, purpose):
        """
        Get the OTP for a given user and purpose.
        """
        try:
            user = EmailOTP.objects.select_related("user").get(
                user__email=email, purpose=purpose, is_used=False, is_verified=True
            )
            return user

        except cls.DoesNotExist:
            return None

    @classmethod
    def generate_otp(cls, user, purpose):
        """
        Generate a new OTP for a given user and purpose. If an OTP already exists, update it.
        """
        import random

        otp_code = str(random.randint(100000, 999999))
        otp_instance, created = cls.objects.update_or_create(
            user=user,
            purpose=purpose,
            is_used=False,
            defaults={"code": otp_code, "last_sent_at": timezone.now()},
        )
        return otp_instance

    @classmethod
    def is_expired(cls, otp_instance, expiry_minutes=10):
        """
        Check if the OTP is expired based on the last_sent_at timestamp.
        """
        if not otp_instance.last_sent_at:
            return True

        expiry_time = otp_instance.last_sent_at + timedelta(minutes=expiry_minutes)
        return timezone.now() > expiry_time

    @classmethod
    def verify_otp(cls, email, purpose, code):
        """
        Verify the OTP for a given user and purpose.
        """
        try:
            user = CustomUser.objects.get(email=email)
            otp_instance = cls.objects.get(user=user, purpose=purpose, is_used=False)

            if cls.is_expired(otp_instance):
                return False, "OTP has expired."

            if otp_instance.code != code:
                return False, "Invalid OTP."

            otp_instance.is_used = True
            otp_instance.is_verified = True
            otp_instance.code = None  # Clear OTP after successful verification
            otp_instance.save(update_fields=["is_used", "is_verified", "code"])

            user.is_active = True  # Update user verification status
            user.save(update_fields=["is_active"])

            return True, "OTP verified successfully."

        except cls.DoesNotExist:
            return False, "OTP not found. Please request a new OTP."
        except CustomUser.DoesNotExist:
            return False, "User not found."

    @classmethod
    def can_resend_otp(cls, email, purpose, cooldown_minutes=2):
        """
        Check if enough time has passed to resend the OTP.
        """
        otp_instance = cls.get_user_otp(email, purpose)
        if not otp_instance:
            return True  # No existing OTP, can send new one

        if not otp_instance.last_sent_at:
            return True

        next_allowed_time = otp_instance.last_sent_at + timedelta(
            minutes=cooldown_minutes
        )
        return timezone.now() >= next_allowed_time

    def __str__(self):
        return f"OTP for {self.user.email} - Purpose: {self.purpose}"


class ActivityLog(ModelMixins):
    """
    Log of all user activities in the system.
    Used for auditing and monitoring user actions.
    """

    class ActionType(models.TextChoices):
        CREATE = "create", "Create"
        READ = "read", "Read"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        EXPORT = "export", "Export"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        default=ActionType.OTHER,
    )
    resource_type = models.CharField(
        max_length=100, help_text="e.g., Property, Booking, User"
    )
    resource_id = models.CharField(
        max_length=100, blank=True, help_text="ID of the affected resource"
    )
    description = models.TextField(blank=True, help_text="Human-readable description")
    details = models.JSONField(
        default=dict, help_text="Additional context data (changes, old values, etc.)"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    endpoint = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=10, blank=True)  # GET, POST, etc.
    status_code = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["resource_type", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Anonymous"
        return f"{user_str} - {self.action} {self.resource_type} at {self.created_at}"

    @classmethod
    def log_action(
        cls,
        user,
        action,
        resource_type,
        resource_id="",
        description="",
        details=None,
        request=None,
    ):
        """
        Convenience method to create an activity log entry.
        """
        log_entry = cls(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else "",
            description=description,
            details=details or {},
        )

        if request:
            log_entry.ip_address = cls._get_client_ip(request)
            log_entry.user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            log_entry.endpoint = request.path[:500]
            log_entry.method = request.method

        log_entry.save()
        return log_entry

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request, handling proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
