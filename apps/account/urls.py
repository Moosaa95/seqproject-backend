from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView,
    VerifyEmailView,
    ResendOTPView,
    CustomTokenObtainView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    UserRoleViewSet,
    UserManagementViewSet,
    ActivityLogViewSet,
    PermissionsListView,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'roles', UserRoleViewSet, basename='roles')
router.register(r'users', UserManagementViewSet, basename='users')
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-logs')

urlpatterns = [
    # Authentication endpoints
    path("jwt/signup/", SignupView.as_view(), name="signup"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("jwt/create/", CustomTokenObtainView.as_view(), name="login"),
    path("jwt/refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("jwt/verify/", CustomTokenVerifyView.as_view(), name="verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # Permissions list endpoint
    path("permissions/", PermissionsListView.as_view(), name="permissions-list"),
    
    # ViewSet routes
    path("", include(router.urls)),
]