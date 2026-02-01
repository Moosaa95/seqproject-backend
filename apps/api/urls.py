from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()

# Register all ViewSets
router.register(r'properties', views.PropertyViewSet, basename='property')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'contact-inquiries', views.ContactInquiryViewSet, basename='contact-inquiry')
router.register(r'property-inquiries', views.PropertyInquiryViewSet, basename='property-inquiry')
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'external-calendars', views.ExternalCalendarViewSet, basename='external-calendar')
router.register(r'blocked-dates', views.BlockedDateViewSet, basename='blocked-date')

# Inventory management
router.register(r"locations", views.LocationViewSet)
router.register(r"countries", views.CountryViewSet)
router.register(r"states", views.StateViewSet)
router.register(r"inventory-items", views.InventoryItemViewSet, basename='inventory-item')
router.register(r'location-inventory', views.LocationInventoryViewSet, basename='location-inventory')
router.register(r'property-inventory', views.PropertyInventoryViewSet, basename='property-inventory')
router.register(r'inventory-movements', views.InventoryMovementViewSet, basename='inventory-movement')

# Dispute management
router.register(r'disputes', views.BookingDisputeViewSet, basename='dispute')

app_name = 'api'

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='health-check'),

    # # Legacy session-based authentication endpoints
    # path('auth/login/', jwt_auth.login_view, name='login'),
    # path('auth/logout/', jwt_auth.logout_view, name='logout'),
    # path('auth/check/', jwt_auth.check_auth, name='check-auth'),
    # path('auth/csrf/', jwt_auth.get_csrf_token, name='csrf-token'),

    # # JWT Authentication endpoints
    # path('auth/jwt/signup/', jwt_auth.SignupView.as_view(), name='jwt-signup'),
    # path('auth/jwt/create/', jwt_auth.LoginView.as_view(), name='jwt-create'),
    # path('auth/jwt/refresh/', jwt_auth.CookieTokenRefreshView.as_view(), name='jwt-refresh'),
    # path('auth/jwt/logout/', jwt_auth.LogoutView.as_view(), name='jwt-logout'),
    # path('auth/jwt/verify/', jwt_auth.VerifyView.as_view(), name='jwt-verify'),
    # path('auth/me/', jwt_auth.MeView.as_view(), name='auth-me'),

    # Paystack webhook endpoint
    path('payments/webhook/', views.PaystackWebhookView.as_view(), name='paystack-webhook'),

    # iCal export endpoint
    path('properties/<uuid:property_id>/ical/', views.export_property_ical, name='property-ical-export'),

    # Calendar sync endpoint
    path('calendars/sync-all/', views.sync_all_calendars, name='sync-all-calendars'),

    # Router URLs (all ViewSets)
    path('', include(router.urls)),
]

