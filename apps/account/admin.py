from django.contrib import admin
from .models import CustomUser, EmailOTP, UserRole, ActivityLog


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'is_used', 'is_verified', 'last_sent_at')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_superuser_role', 'is_default', 'user_count', 'created_at')
    list_filter = ('is_superuser_role', 'is_default')
    search_fields = ('name', 'description')

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'ip_address', 'created_at')
    list_filter = ('action', 'resource_type', 'method')
    search_fields = ('user__email', 'resource_type', 'description', 'endpoint')
    readonly_fields = ('user', 'action', 'resource_type', 'resource_id', 'description', 
                      'details', 'ip_address', 'user_agent', 'endpoint', 'method', 
                      'status_code', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False  # Logs should not be created manually

    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be edited

