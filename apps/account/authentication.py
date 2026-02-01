from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that reads tokens from HttpOnly cookies.
    
    Falls back to Authorization header if no cookie is present.
    """
    
    def authenticate(self, request):
        # First, try the standard Authorization header
        header = self.get_header(request)

        if header is not None:
            # Standard JWT authentication from header
            raw_token = self.get_raw_token(header)
        else:
            # Fallback: Try to get token from cookie
            raw_token = request.COOKIES.get(settings.AUTH_ACCESS_TOKEN_NAME)

            if raw_token is None:
                # No token in header or cookie - return None to allow AllowAny views
                return None

            # Convert to bytes if it's a string
            if isinstance(raw_token, str):
                raw_token = raw_token.encode('utf-8')

        if raw_token is None:
            return None

        # Validate the token
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            # Return None instead of raising AuthenticationFailed
            # This allows views with AllowAny permission to work
            # Views requiring authentication will still fail at permission check
            return None

        # Return user and validated token
        return self.get_user(validated_token), validated_token

