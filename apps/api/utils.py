from django.conf import settings

def set_auth_cookies(response, access_token, refresh_token):
    cookie_common = {
        "path": settings.AUTH_COOKIE_PATH,
        "secure": settings.AUTH_COOKIE_SECURE,
        "httponly": settings.AUTH_COOKIE_HTTP_ONLY,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }

    response.set_cookie(
        settings.AUTH_ACCESS_TOKEN_NAME,
        access_token,
        max_age=settings.AUTH_COOKIE_ACCESS_TOKEN_MAX_AGE,
        **cookie_common
    )
    response.set_cookie(
        settings.AUTH_REFRESH_TOKEN_NAME,
        refresh_token,
        max_age=settings.AUTH_COOKIE_REFRESH_TOKEN_MAX_AGE,
        **cookie_common
    )
    return response