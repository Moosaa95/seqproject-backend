# Create your views here.

from rest_framework import status, generics, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from account.serializers import (
    SignupSerializer,
    VerifyEmailSerializer,
    ResendOTPSerializer,
    UserSerializer,
)
from account.models import CustomUser as User
from django.conf import settings

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from account.utils import set_auth_cookies
from account.serializers import CustomTokenObtainPairSerializer


class SignupView(generics.CreateAPIView):
    """
    API endpoint for user signup.
    Creates an inactive user and sends OTP for email verification.
    """

    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def create(self, request):
        """
        Handle user registration.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Signup successful. Please check your email for verification code.",
                "data": {"email": user.email, "user_id": str(user.id)},
            },
            status=status.HTTP_201_CREATED,
        )




class VerifyEmailView(APIView):
    """
    API endpoint to verify email using OTP.
    Activates the user account upon successful verification.
    """

    permission_classes = [AllowAny]
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        """
        Handle email verification.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Email verified successfully. You can now login.",
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    API endpoint to resend OTP for email verification.
    Implements cooldown period to prevent spam.
    """

    permission_classes = [AllowAny]
    serializer_class = ResendOTPSerializer

    def post(self, request):
        """
        Handle OTP resend.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "OTP resent successfully. Please check your email.",
                "data": {},
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            if access_token and refresh_token:
                set_auth_cookies(response, access_token, refresh_token)

            response.data["success"] = True

            
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Handles token refresh by reading the refresh token from cookies if not provided in the request body."""

    def post(self, request, *args, **kwargs):
        """Overrides the default post method to get the refresh token from cookies if not provided."""

        # Fix: Ensure `request.data` is mutable (Django's `QueryDict` may be immutable)
        data = request.data.copy()

        # Fix: Use correct assignment syntax
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_TOKEN_NAME)
        if refresh_token and "refresh" not in data:
            data["refresh"] = refresh_token

        # Call the parent class's `post` method with the modified request data
        request._full_data = data  # Override request data
        response = super().post(request, *args, **kwargs)

        # Fix: Ensure access token is set correctly in cookies
        # if response.status_code == 200:
        #     access_token = response.data.get('access')
        #     if access_token:
        #         set_auth_cookies(response, access_token, refresh_token)  # Fix parameter order
        if response.status_code == 200:
            access_token = response.data.get("access")
            new_refresh_token = response.data.get(
                "refresh"
            )  # May not exist if rotation is disabled

            if access_token:
                if new_refresh_token:
                    set_auth_cookies(response, access_token, new_refresh_token)
                else:
                    set_auth_cookies(
                        response, access_token, refresh_token
                    )  # Keep existing refresh token

        return response


class CustomTokenVerifyView(TokenVerifyView):
    """
    Custom token verification view to handle token verification.
    Supports both GET (for checking current session) and POST (standard JWT verify).
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Handle GET request - verify token from cookies and return user info.
        This is used for checking if the user is still authenticated on page load.
        """
        access_token = request.COOKIES.get(settings.AUTH_ACCESS_TOKEN_NAME)
        
        if not access_token:
            return Response(
                {"authenticated": False, "detail": "No access token found"},
                status=status.HTTP_200_OK
            )
        
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(access_token)
            user = jwt_auth.get_user(validated_token)
            
            return Response({
                "authenticated": True,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError):
            return Response(
                {"authenticated": False, "detail": "Token is invalid or expired"},
                status=status.HTTP_200_OK
            )

    def post(self, request, *args, **kwargs):
        """
        Handle token verification (standard JWT verify).
        """
        access_token = request.COOKIES.get(settings.AUTH_ACCESS_TOKEN_NAME)
        if access_token:
            data = request.data.copy()
            data["access"] = access_token
            request._full_data = data

        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Token is valid, let's get the user
            from rest_framework_simplejwt.authentication import JWTAuthentication
            from rest_framework_simplejwt.exceptions import InvalidToken
            
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(request.data.get("access"))
                user = jwt_auth.get_user(validated_token)
                
                response.data["authenticated"] = True
                response.data["user"] = UserSerializer(user).data
            except Exception as e:
                # Should not happen if super().post() passed, but safety first
                response.data["authenticated"] = False
                
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    # @extend_schema(
    #     summary="Logout user",
    #     description="Logout user by clearing authentication cookies.",
    #     responses={200: drf_serializers.SerializerMessageField(message="Logged out successfully")},
    # )
    def post(self, request):
        """
        Handle user logout.
        """
        response = Response(
            {
                "success": True,
                "message": "Logged out successfully",
                "data": {},
            },
            status=status.HTTP_200_OK,
        )

        # Clear authentication cookies
        response.delete_cookie(settings.AUTH_ACCESS_TOKEN_NAME)
        response.delete_cookie(settings.AUTH_REFRESH_TOKEN_NAME)

        return response


# ============================================================================
# User Management ViewSets
# ============================================================================
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from account.models import UserRole, ActivityLog
from account.serializers import (
    UserRoleSerializer,
    UserRoleListSerializer,
    UserManagementSerializer,
    UserListSerializer,
    ActivityLogSerializer,
)
from apps.api.permissions import IsSuperUser, HasPermission, MethodBasedPermission
from apps.account.permissions import Permissions


class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user roles.
    
    Endpoints:
    - GET /api/account/roles/ - List all roles
    - POST /api/account/roles/ - Create a new role
    - GET /api/account/roles/:id/ - Get role details
    - PUT/PATCH /api/account/roles/:id/ - Update role
    - DELETE /api/account/roles/:id/ - Delete role
    """

    queryset = UserRole.objects.all()
    permission_classes = [IsAuthenticated, MethodBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    # Permission mapping for different HTTP methods
    permission_map = {
        'GET': Permissions.ROLE_READ,
        'POST': Permissions.ROLE_CREATE,
        'PUT': Permissions.ROLE_UPDATE,
        'PATCH': Permissions.ROLE_UPDATE,
        'DELETE': Permissions.ROLE_DELETE,
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return UserRoleListSerializer
        return UserRoleSerializer

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of roles that have users assigned."""
        role = self.get_object()
        if role.users.exists():
            return Response(
                {
                    "success": False,
                    "message": "Cannot delete role with assigned users. Reassign users first.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (admin functionality).
    
    Endpoints:
    - GET /api/account/users/ - List all users
    - POST /api/account/users/ - Create a new user
    - GET /api/account/users/:id/ - Get user details
    - PUT/PATCH /api/account/users/:id/ - Update user
    - DELETE /api/account/users/:id/ - Deactivate user
    """

    queryset = User.objects.select_related('role').all()
    permission_classes = [IsAuthenticated, MethodBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['email', 'first_name', 'last_name']
    filterset_fields = ['is_active', 'is_staff', 'is_superuser', 'role']
    ordering_fields = ['email', 'date_joined', 'first_name', 'last_name']
    ordering = ['-date_joined']

    # Permission mapping for different HTTP methods
    permission_map = {
        'GET': Permissions.USER_READ,
        'POST': Permissions.USER_CREATE,
        'PUT': Permissions.USER_UPDATE,
        'PATCH': Permissions.USER_UPDATE,
        'DELETE': Permissions.USER_DELETE,
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'change_password':
            from .serializers import ChangePasswordSerializer
            return ChangePasswordSerializer
        return UserManagementSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new staff user with auto-generated password.
        Sets must_change_password=True and sends welcome email.
        """
        import secrets
        import string
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Generate a secure 12-character password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Create user with auto-generated password
        user = serializer.save()
        user.set_password(password)
        user.must_change_password = True
        user.is_active = True
        user.is_staff = True
        user.save(update_fields=['password', 'must_change_password', 'is_active', 'is_staff'])
        
        # Send welcome email
        from .services import EmailService
        email_sent = EmailService.send_welcome_email(
            email=user.email,
            first_name=user.first_name,
            password=password
        )
        
        return Response(
            {
                "success": True,
                "message": f"User created successfully. {'Password sent to email.' if email_sent else 'Email could not be sent.'}",
                "user": UserManagementSerializer(user).data,
                "email_sent": email_sent,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change password for the current user (used for first-login password change).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        
        # Send confirmation email
        from .services import EmailService
        EmailService.send_password_changed_email(
            email=user.email,
            first_name=user.first_name
        )
        
        return Response(
            {
                "success": True,
                "message": "Password changed successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """Soft delete - deactivate user instead of deleting."""
        user = self.get_object()
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response(
                {
                    "success": False,
                    "message": "Cannot deactivate your own account.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Soft delete - just deactivate
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        return Response(
            {
                "success": True,
                "message": "User deactivated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing activity logs (read-only).
    
    Endpoints:
    - GET /api/account/activity-logs/ - List all activity logs
    - GET /api/account/activity-logs/:id/ - Get log details
    """

    queryset = ActivityLog.objects.select_related('user').all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, HasPermission.with_permission(Permissions.LOGS_READ)]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['description', 'resource_type', 'endpoint']
    filterset_fields = ['user', 'action', 'resource_type', 'method']
    ordering_fields = ['created_at', 'action', 'resource_type']
    ordering = ['-created_at']


class PermissionsListView(APIView):
    """
    API endpoint to get all available permissions.
    Useful for frontend to display permission checkboxes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": {
                    "permissions": Permissions.all_permissions(),
                    "groups": Permissions.get_permission_groups(),
                },
            },
            status=status.HTTP_200_OK,
        )