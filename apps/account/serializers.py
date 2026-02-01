from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from .models import EmailOTP, UserRole, ActivityLog
from apps.account.services import EmailService
from apps.account.permissions import Permissions

User = get_user_model()


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for user roles with permissions."""
    
    user_count = serializers.SerializerMethodField()
    available_permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = [
            'id', 'name', 'description', 'permissions', 
            'is_superuser_role', 'is_default', 'user_count',
            'available_permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_count(self, obj):
        return obj.users.count()

    def get_available_permissions(self, obj):
        """Return all available permissions for the frontend to display."""
        return Permissions.get_permission_groups()


class UserRoleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for role listings."""
    
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description', 'is_superuser_role', 'is_default', 'user_count']

    def get_user_count(self, obj):
        return obj.users.count()


class ActivityLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for activity logs."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_email', 'user_name', 'action', 
            'resource_type', 'resource_id', 'description', 'details',
            'ip_address', 'user_agent', 'endpoint', 'method',
            'status_code', 'created_at'
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return "Anonymous"


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        return value

    def create(self, validated_data):
        """
        Create user, generate OTP, and send verification email.
        """
        with transaction.atomic():
            # Get default role if exists
            default_role = UserRole.objects.filter(is_default=True).first()
            
            # Create inactive user
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                is_active=False,
                role=default_role  # Assign default role
            )

            # Generate OTP
            otp_instance = EmailOTP.generate_otp(user, purpose='signup')

            # Send verification email
            email_sent = EmailService.send_otp_email(
                email=user.email,
                otp_code=otp_instance.code,
                purpose='signup'
            )

            if not email_sent:
                raise serializers.ValidationError("Failed to send verification email")

            return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be a 6-digit number")
        return value

    def validate(self, attrs):
        """
        Verify OTP and return user if valid.
        """
        email = attrs.get('email')
        otp_code = attrs.get('otp')

        # Verify OTP
        is_valid = EmailOTP.verify_otp(email=email, purpose='signup', code=otp_code)

        if not is_valid:
            raise serializers.ValidationError("Invalid or expired OTP")

        # Get user
        try:
            user = User.objects.get(email=email)
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        return attrs

    def save(self):
        """
        Activate the user account.
        """
        user = self.validated_data['user']
        user.is_active = True
        user.save(update_fields=['is_active'])
        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['signup', 'login', 'reset'])

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist")
        return value

    def validate(self, attrs):
        """
        Check cooldown period before allowing resend.
        """
        email = attrs.get('email')
        purpose = attrs.get('purpose')

        # Check if can resend OTP (cooldown check)
        can_resend = EmailOTP.can_resend_otp(
            email=email,
            purpose=purpose,
            cooldown_minutes=2
        )

        if not can_resend:
            raise serializers.ValidationError(
                "Please wait 2 minutes before requesting another OTP"
            )

        return attrs

    def save(self):
        """
        Generate new OTP and send email.
        """
        email = self.validated_data['email']
        purpose = self.validated_data['purpose']

        # Get user
        user = User.objects.get(email=email)

        # Generate new OTP
        otp_instance = EmailOTP.generate_otp(user, purpose=purpose)

        # Send email
        email_sent = EmailService.send_otp_email(
            email=user.email,
            otp_code=otp_instance.code,
            purpose=purpose
        )

        if not email_sent:
            raise serializers.ValidationError("Failed to send verification email")

        return otp_instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details with role info."""
    
    role_details = UserRoleListSerializer(source='role', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'date_joined', 
            'is_active', 'is_staff', 'is_superuser', 'role', 'role_details',
            'permissions', 'must_change_password'
        ]
        read_only_fields = ['id', 'date_joined', 'permissions', 'must_change_password']

    def get_permissions(self, obj):
        return obj.get_permissions()


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for admin user management - full CRUD."""
    
    role_details = UserRoleListSerializer(source='role', read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'date_joined',
            'is_active', 'is_staff', 'is_superuser', 'role', 'role_details',
            'password', 'must_change_password'
        ]
        read_only_fields = ['id', 'date_joined', 'must_change_password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user listings."""
    
    role_name = serializers.CharField(source='role.name', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff', 'is_superuser', 'role', 'role_name',
            'date_joined'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change (used for first-login password change)."""
    
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for JWT token authentication.
    Adds custom claims to the token.
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom claims including role and permissions
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'must_change_password': self.user.must_change_password,
            'role': {
                'id': str(self.user.role.id) if self.user.role else None,
                'name': self.user.role.name if self.user.role else None,
            } if self.user.role else None,
            'permissions': self.user.get_permissions(),
        }

        return data


class UserMembershipSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()