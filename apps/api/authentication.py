"""
Custom authentication classes for API
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF checks.
    Use this for endpoints that need session auth but can't use CSRF tokens.
    """

    def enforce_csrf(self, request):
        """
        Skip CSRF check
        """
        return  # Do nothing, effectively disabling CSRF
