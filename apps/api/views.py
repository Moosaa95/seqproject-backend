from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import (
    Property, Booking, Payment, ContactInquiry, PropertyInquiry, Agent,
    ExternalCalendar, BlockedDate, Location, InventoryItem, LocationInventory,
    PropertyInventory, InventoryMovement, BookingDispute,
    Country, State,
)
from .serializers import (
    PropertySerializer,
    PropertyListSerializer,
    BookingSerializer,
    PaymentSerializer,
    ContactInquirySerializer,
    PropertyInquirySerializer,
    AgentSerializer,
    ExternalCalendarSerializer,
    BlockedDateSerializer,
    LocationSerializer,
    InventoryItemSerializer,
    LocationInventorySerializer,
    PropertyInventorySerializer,
    InventoryMovementSerializer,
    BookingDisputeSerializer,
    CountrySerializer,
    StateSerializer,
)
from .pagination import StandardResultsSetPagination
from .paystack import get_paystack_service, PaystackService
from .notifications import EmailNotificationService
from .permissions import IsAdminOrStaff, IsAdminOrReadOnly
from .authentication import CsrfExemptSessionAuthentication
from .ical_service import ICalService
from django.http import HttpResponse


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify API is running.
    """
    return Response(
        {
            "status": "healthy",
            "message": "Sequoia Projects API is running successfully",
            "timestamp": timezone.now(),
        },
        status=status.HTTP_200_OK,
    )


class CountryViewSet(viewsets.ModelViewSet):
    """Manage Countries"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "code"]


class StateViewSet(viewsets.ModelViewSet):
    """Manage States"""
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ["country"]
    search_fields = ["name"]


class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property management.

    Endpoints:
    - GET /api/properties/ - List all properties
    - GET /api/properties/:id/ - Get property details
    - POST /api/properties/ - Create property (admin only)
    - PUT/PATCH /api/properties/:id/ - Update property (admin only)
    - DELETE /api/properties/:id/ - Delete property (admin only)

    Filters:
    - status: 'rent' or 'sale'
    - type: property type
    - entity: property owner/manager
    - featured: true/false
    - search: search in title, location, description
    - min_price, max_price: price range
    - bedrooms, bathrooms: exact match
    """

    queryset = Property.objects.filter(is_active=True)
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["title", "location", "description", "type", "entity"]
    ordering_fields = ["price", "created_at", "bedrooms", "bathrooms"]
    ordering = ["-featured", "-created_at"]

    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for details"""
        if self.action == "list":
            return PropertyListSerializer
        return PropertySerializer

    def get_queryset(self):
        """Filter properties based on query parameters"""
        queryset = super().get_queryset()

        # Filter by status (rent/sale)
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by type
        type_filter = self.request.query_params.get("type", None)
        if type_filter:
            queryset = queryset.filter(type__icontains=type_filter)

        # Filter by entity
        entity_filter = self.request.query_params.get("entity", None)
        if entity_filter:
            queryset = queryset.filter(entity__icontains=entity_filter)

        # Filter by featured
        featured_filter = self.request.query_params.get("featured", None)
        if featured_filter is not None:
            queryset = queryset.filter(featured=featured_filter.lower() == "true")

        # Filter by price range
        min_price = self.request.query_params.get("min_price", None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get("max_price", None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by bedrooms/bathrooms
        bedrooms = self.request.query_params.get("bedrooms", None)
        if bedrooms:
            queryset = queryset.filter(bedrooms__gte=bedrooms)

        bathrooms = self.request.query_params.get("bathrooms", None)
        if bathrooms:
            queryset = queryset.filter(bathrooms__gte=bathrooms)

        return queryset

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def booked_dates(self, request, pk=None):
        """
        Get list of booked/blocked dates for the property.
        Returns array of { start: 'YYYY-MM-DD', end: 'YYYY-MM-DD' }
        """
        property_obj = self.get_object()
        
        # Get confirmed bookings
        bookings = Booking.objects.filter(
            property=property_obj,
            status__in=["confirmed", "pending", "completed"]
        ).values("check_in", "check_out")

        # Get blocked dates
        blocked = BlockedDate.objects.filter(
            property=property_obj
        ).values("start_date", "end_date")

        ranges = []
        for b in bookings:
            ranges.append({
                "start": b["check_in"],
                "end": b["check_out"]
            })
            
        for b in blocked:
            ranges.append({
                "start": b["start_date"],
                "end": b["end_date"]
            })

        return Response(ranges)

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """
        Check property availability for given dates
        Query params: check_in, check_out
        """
        property_obj = self.get_object()
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")

        if not check_in or not check_out:
            return Response(
                {"error": "check_in and check_out dates are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from datetime import datetime

            check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()

            # Use ICalService to check availability (includes both bookings and blocked dates)
            is_available = ICalService.check_availability_with_blocked_dates(
                property_obj, check_in_date, check_out_date
            ) and property_obj.is_available

            return Response(
                {
                    "available": is_available,
                    "property_id": property_obj.id,
                    "check_in": check_in,
                    "check_out": check_out,
                }
            )

        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking management.

    Endpoints:
    - GET /api/bookings/ - List all bookings (admin only)
    - GET /api/bookings/:id/ - Get booking details
    - POST /api/bookings/ - Create new booking
    - PATCH /api/bookings/:id/ - Update booking status (admin only)
    """

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "payment_status"]
    ordering_fields = ["created_at", "check_in", "check_out"]
    ordering = ["-created_at"]
    lookup_field = "booking_id"

    def get_permissions(self):
        """Allow anyone to create, admin to list/update"""
        if self.action in ["list", "update", "partial_update", "destroy"]:
            return [IsAdminOrStaff()]
        return [AllowAny()]

    def get_queryset(self):
        """Filter bookings by property or email"""
        queryset = super().get_queryset()

        # Filter by property ID
        property_id = self.request.query_params.get("property_id", None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        # Filter by email (for user to check their bookings)
        email = self.request.query_params.get("email", None)
        if email:
            queryset = queryset.filter(email__iexact=email)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create booking and return booking details"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        # Send booking confirmation emails
        try:
            # Send confirmation to customer
            EmailNotificationService.send_booking_confirmation(booking)
            # Send notification to admin
            EmailNotificationService.send_booking_admin_notification(booking)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send booking notifications: {str(e)}")

        return Response(
            {
                "success": True,
                "message": "Booking created successfully",
                "booking": BookingSerializer(
                    booking, context={"request": request}
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()

        if booking.status == "cancelled":
            return Response(
                {"error": "Booking is already cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.status == "completed":
            return Response(
                {"error": "Cannot cancel completed booking"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "cancelled"
        booking.save()

        return Response(
            {
                "success": True,
                "message": "Booking cancelled successfully",
                "booking": BookingSerializer(
                    booking, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        """Record client check-in for a booking"""
        booking = self.get_object()

        if booking.status == "cancelled":
            return Response(
                {"error": "Cannot check in to a cancelled booking"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.checked_in_at:
            return Response(
                {"error": "Client has already checked in"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.status != "confirmed":
            return Response(
                {"error": "Booking must be confirmed before check-in"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.checked_in_at = timezone.now()
        booking.occupancy_status = "occupied"
        booking.save()

        return Response(
            {
                "success": True,
                "message": "Client checked in successfully",
                "booking": BookingSerializer(
                    booking, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        """Record client check-out for a booking"""
        booking = self.get_object()

        if not booking.checked_in_at:
            return Response(
                {"error": "Client has not checked in yet"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.checked_out_at:
            return Response(
                {"error": "Client has already checked out"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.checked_out_at = timezone.now()
        booking.occupancy_status = "departed"
        booking.status = "completed"
        booking.save()

        return Response(
            {
                "success": True,
                "message": "Client checked out successfully",
                "booking": BookingSerializer(
                    booking, context={"request": request}
                ).data,
            }
        )


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment management.

    Endpoints:
    - GET /api/payments/ - List all payments (admin only)
    - GET /api/payments/:id/ - Get payment details
    - POST /api/payments/initialize/ - Initialize payment with Paystack
    - POST /api/payments/verify/ - Verify payment status
    - GET /api/payments/config/ - Get Paystack public key
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Allow anyone to create, admin to list"""
        if self.action == "list":
            return [IsAdminOrStaff()]
        return [AllowAny()]

    @action(detail=False, methods=["post"])
    def initialize(self, request):
        """Initialize a payment with Paystack"""
        booking_id = request.data.get("booking_id")

        if not booking_id:
            return Response(
                {"success": False, "message": "booking_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {"success": False, "message": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if booking already has a successful payment
        if booking.payment_status == "paid":
            return Response(
                {"success": False, "message": "Booking has already been paid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            paystack_service = get_paystack_service()
            result = paystack_service.initialize_payment(
                booking=booking, metadata=request.data.get("metadata", {})
            )

            if result["success"]:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def verify(self, request):
        """Verify a payment transaction"""
        reference = request.data.get("reference")

        if not reference:
            return Response(
                {"success": False, "message": "reference is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            paystack_service = get_paystack_service()
            result = paystack_service.verify_payment(reference)

            if result["success"]:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def config(self, request):
        """Get Paystack public key for frontend"""
        try:
            paystack_service = get_paystack_service()
            return Response(
                {
                    "public_key": paystack_service.get_public_key(),
                    "callback_url": paystack_service.callback_url,
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContactInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contact Inquiry management.

    Endpoints:
    - GET /api/contact-inquiries/ - List all inquiries (admin only)
    - POST /api/contact-inquiries/ - Submit contact form
    """

    queryset = ContactInquiry.objects.all()
    serializer_class = ContactInquirySerializer
    permission_classes = [AllowAny]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Allow anyone to create, admin to list/view"""
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            return [IsAdminOrStaff()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        """Submit contact inquiry"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = serializer.save()

        # Send email notification to admin
        try:
            EmailNotificationService.send_contact_inquiry_notification(inquiry)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send contact inquiry notification: {str(e)}")

        return Response(
            {
                "success": True,
                "message": "Thank you for contacting us. We will get back to you soon.",
                "inquiry_id": inquiry.id,
            },
            status=status.HTTP_201_CREATED,
        )


class PropertyInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Inquiry management.

    Endpoints:
    - GET /api/property-inquiries/ - List all inquiries (admin only)
    - POST /api/property-inquiries/ - Submit property inquiry
    """

    queryset = PropertyInquiry.objects.all()
    serializer_class = PropertyInquirySerializer
    permission_classes = [AllowAny]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Allow anyone to create, admin to list/view"""
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            return [IsAdminOrStaff()]
        return [AllowAny()]

    def get_queryset(self):
        """Filter by property ID"""
        queryset = super().get_queryset()

        property_id = self.request.query_params.get("property_id", None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Submit property inquiry"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = serializer.save()

        # Send email notification to agent/admin
        try:
            EmailNotificationService.send_property_inquiry_notification(inquiry)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send property inquiry notification: {str(e)}")

        return Response(
            {
                "success": True,
                "message": "Thank you for your inquiry. Our agent will contact you soon.",
                "inquiry_id": inquiry.id,
            },
            status=status.HTTP_201_CREATED,
        )


class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Agent management (read-only for public).

    Endpoints:
    - GET /api/agents/ - List all agents
    - GET /api/agents/:id/ - Get agent details
    """

    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [AllowAny]


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    """
    Webhook endpoint for Paystack payment notifications.

    Endpoint: POST /api/payments/webhook/

    This endpoint receives and processes payment event notifications from Paystack.
    The webhook signature is verified to ensure the request is from Paystack.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle Paystack webhook events"""
        # Get the signature from headers
        signature = request.headers.get("X-Paystack-Signature")

        if not signature:
            return Response(
                {"error": "Missing signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get raw request body
            payload = request.body

            # Verify webhook signature
            paystack_service = get_paystack_service()
            if not paystack_service.verify_webhook_signature(payload, signature):
                return Response(
                    {"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED
                )

            # Parse event data
            event_data = json.loads(payload.decode("utf-8"))

            # Process the webhook event
            result = paystack_service.process_webhook_event(event_data)

            return Response(result, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExternalCalendarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for External Calendar management.

    Endpoints:
    - GET /api/external-calendars/ - List all external calendars (admin only)
    - POST /api/external-calendars/ - Add external calendar (admin only)
    - PATCH /api/external-calendars/:id/ - Update external calendar (admin only)
    - DELETE /api/external-calendars/:id/ - Delete external calendar (admin only)
    - POST /api/external-calendars/:id/sync/ - Manually trigger sync (admin only)
    """

    queryset = ExternalCalendar.objects.all()
    serializer_class = ExternalCalendarSerializer
    permission_classes = [IsAuthenticated]  # Allow any authenticated user
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by property ID (accepts both 'property' and 'property_id' params)"""
        queryset = super().get_queryset()

        # Accept both property_id and property as filter params for flexibility
        property_id = self.request.query_params.get("property_id") or \
                      self.request.query_params.get("property")
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Manually trigger calendar sync"""
        external_calendar = self.get_object()

        try:
            result = ICalService.import_external_calendar(external_calendar)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BlockedDateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Blocked Date management.

    Endpoints:
    - GET /api/blocked-dates/ - List all blocked dates (admin only)
    - POST /api/blocked-dates/ - Create manual block (admin only)
    - PATCH /api/blocked-dates/:id/ - Update blocked date (admin only)
    - DELETE /api/blocked-dates/:id/ - Delete blocked date (admin only)
    """

    queryset = BlockedDate.objects.all()
    serializer_class = BlockedDateSerializer
    permission_classes = [IsAdminOrStaff]
    ordering = ["start_date"]

    def get_queryset(self):
        """Filter by property ID"""
        queryset = super().get_queryset()

        property_id = self.request.query_params.get("property_id", None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset


@api_view(["GET"])
@permission_classes([AllowAny])
def export_property_ical(request, property_id):
    """
    Export property bookings as iCal feed.

    Endpoint: GET /api/properties/:property_id/ical/

    This endpoint generates an iCal feed containing all confirmed and pending
    bookings for a property, which can be imported into Airbnb, Booking.com, etc.
    """
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND
        )

    try:
        ical_data = ICalService.export_property_calendar(property_obj)

        response = HttpResponse(ical_data, content_type="text/calendar; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{property_obj.title.replace(" ", "_")}_calendar.ics"'
        )
        return response

    except Exception as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAdminOrStaff])
def sync_all_calendars(request):
    """
    Manually trigger sync for all active external calendars.

    Endpoint: POST /api/calendars/sync-all/

    Admin only endpoint to sync all calendars at once.
    """
    try:
        results = ICalService.sync_all_external_calendars()
        return Response(
            {"success": True, "results": results}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# =============================================================================
# INVENTORY MANAGEMENT VIEWSETS
# =============================================================================


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Location management.

    Endpoints:
    - GET /api/locations/ - List all locations
    - POST /api/locations/ - Create location (admin only)
    - GET /api/locations/:id/ - Get location details
    - PUT/PATCH /api/locations/:id/ - Update location (admin only)
    - DELETE /api/locations/:id/ - Delete location (admin only)
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "address"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Filter by active status"""
        queryset = super().get_queryset()

        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset


class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InventoryItem management.

    Endpoints:
    - GET /api/inventory-items/ - List all inventory items
    - POST /api/inventory-items/ - Create inventory item (admin only)
    - GET /api/inventory-items/:id/ - Get inventory item details
    - PUT/PATCH /api/inventory-items/:id/ - Update inventory item (admin only)
    - DELETE /api/inventory-items/:id/ - Delete inventory item (admin only)
    """

    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category"]
    ordering_fields = ["name", "category", "created_at"]
    ordering = ["category", "name"]

    def get_queryset(self):
        """Filter by category and active status"""
        queryset = super().get_queryset()

        category = self.request.query_params.get("category", None)
        if category:
            queryset = queryset.filter(category__icontains=category)

        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset


class LocationInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LocationInventory management.

    Endpoints:
    - GET /api/location-inventory/ - List inventory stock by location
    - POST /api/location-inventory/ - Add inventory to location (admin only)
    - PUT/PATCH /api/location-inventory/:id/ - Update inventory stock (admin only)
    - DELETE /api/location-inventory/:id/ - Remove inventory entry (admin only)
    """

    queryset = LocationInventory.objects.all()
    serializer_class = LocationInventorySerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["quantity", "created_at"]
    ordering = ["location", "item"]

    def get_queryset(self):
        """Filter by location and item"""
        queryset = super().get_queryset()

        location_id = self.request.query_params.get("location_id", None)
        if location_id:
            queryset = queryset.filter(location_id=location_id)

        item_id = self.request.query_params.get("item_id", None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        low_stock = self.request.query_params.get("low_stock", None)
        if low_stock and low_stock.lower() == "true":
            from django.db.models import F
            queryset = queryset.filter(quantity__lte=F("min_threshold"))

        return queryset


class PropertyInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PropertyInventory management.

    Endpoints:
    - GET /api/property-inventory/ - List inventory assigned to properties
    - POST /api/property-inventory/ - Assign inventory to property (admin only)
    - PUT/PATCH /api/property-inventory/:id/ - Update assignment (admin only)
    - DELETE /api/property-inventory/:id/ - Remove assignment (admin only)
    """

    queryset = PropertyInventory.objects.all()
    serializer_class = PropertyInventorySerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["quantity", "created_at"]
    ordering = ["property", "item"]

    def get_queryset(self):
        """Filter by property and item"""
        queryset = super().get_queryset()

        property_id = self.request.query_params.get("property_id", None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        item_id = self.request.query_params.get("item_id", None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset


class InventoryMovementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InventoryMovement management (audit trail).

    Endpoints:
    - GET /api/inventory-movements/ - List all movements (admin only)
    - POST /api/inventory-movements/ - Record movement (admin only)
    - GET /api/inventory-movements/:id/ - Get movement details (admin only)
    """

    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["movement_type"]
    ordering_fields = ["created_at", "quantity"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]  # No update/delete for audit trail

    def get_queryset(self):
        """Filter by location, item, property, and booking"""
        queryset = super().get_queryset()

        location_id = self.request.query_params.get("location_id", None)
        if location_id:
            queryset = queryset.filter(location_id=location_id)

        item_id = self.request.query_params.get("item_id", None)
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        property_id = self.request.query_params.get("property_id", None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        booking_id = self.request.query_params.get("booking_id", None)
        if booking_id:
            queryset = queryset.filter(booking__booking_id=booking_id)

        return queryset


# =============================================================================
# DISPUTE RESOLUTION VIEWSET
# =============================================================================


class BookingDisputeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BookingDispute management.

    Endpoints:
    - GET /api/disputes/ - List all disputes (admin only)
    - POST /api/disputes/ - Create dispute (admin only)
    - GET /api/disputes/:id/ - Get dispute details (admin only)
    - PUT/PATCH /api/disputes/:id/ - Update/resolve dispute (admin only)
    - DELETE /api/disputes/:id/ - Delete dispute (admin only)
    """

    queryset = BookingDispute.objects.all()
    serializer_class = BookingDisputeSerializer
    permission_classes = [IsAdminOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["dispute_type", "status"]
    ordering_fields = ["created_at", "resolved_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by booking"""
        queryset = super().get_queryset()

        booking_id = self.request.query_params.get("booking_id", None)
        if booking_id:
            queryset = queryset.filter(booking__booking_id=booking_id)

        return queryset

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Quick resolve action for a dispute"""
        dispute = self.get_object()

        resolution = request.data.get("resolution")
        resolved_by = request.data.get("resolved_by")

        if not resolution:
            return Response(
                {"error": "resolution is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dispute.resolution = resolution
        dispute.resolved_by = resolved_by
        dispute.resolved_at = timezone.now()
        dispute.status = "resolved"
        dispute.save()

        return Response(
            {
                "success": True,
                "message": "Dispute resolved successfully",
                "dispute": BookingDisputeSerializer(dispute).data,
            }
        )
