from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from cloudinary.models import CloudinaryField
import cloudinary
from commons.mixins import ModelMixins


class PROPERTY_STATUS_CHOICES(models.TextChoices):
    RENT = "rent", "For Rent"
    SALE = "sale", "For Sale"


class CURRENCY_CHOICES(models.TextChoices):
    NGN = "₦", "Nigerian Naira"
    USD = "$", "US Dollar"
    GBP = "£", "British Pound"
    EUR = "€", "Euro"


class BOOKING_STATUS_CHOICES(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class PAYMENT_STATUS_CHOICES(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PAYMENT_METHOD_CHOICES(models.TextChoices):
    PAYSTACK = "paystack", "Paystack"
    FLUTTERWAVE = "flutterwave", "Flutterwave"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CASH = "cash", "Cash"
    CARD = "card", "Card"


class CONTACT_SUBJECT_CHOICES(models.TextChoices):
    PROPERTY_INQUIRY = "property", "Property Inquiry"
    PROPERTY_MANAGEMENT = "management", "Property Management"
    CONSTRUCTION = "construction", "Construction"
    PROJECT_CONSULTANCY = "consultancy", "Project Consultancy"
    AIRBNB_SERVICES = "airbnb", "Airbnb & Short-Let Services"
    OTHER = "other", "Other"





class Agent(ModelMixins):
    """Agent/Contact person for properties"""

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    mobile = models.CharField(max_length=50)
    email = models.EmailField()
    skype = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Property(ModelMixins):
    """Property/Apartment model matching frontend structure"""

    # Basic Information
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    location_data = models.ForeignKey(
        "Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="properties"
    )
    price = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCY_CHOICES.choices, default=CURRENCY_CHOICES.NGN
    )
    status = models.CharField(
        max_length=10,
        choices=PROPERTY_STATUS_CHOICES.choices,
        default=PROPERTY_STATUS_CHOICES.RENT,
    )
    type = models.CharField(max_length=100)

    # Property Details
    area = models.IntegerField(null=True, blank=True, help_text="Area in square meters")
    guests = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    bedrooms = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    bathrooms = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    living_rooms = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    garages = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    units = models.IntegerField(
        null=True, blank=True, help_text="Number of similar units available"
    )

    # Description & Features
    description = models.TextField()
    amenities = models.JSONField(default=list, help_text="List of amenities")

    # Management
    entity = models.CharField(
        max_length=255, null=True, blank=True, help_text="Property owner/manager entity"
    )
    agent = models.ForeignKey(
        Agent, on_delete=models.SET_NULL, null=True, related_name="properties"
    )

    # Status & Visibility
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    available_from = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-featured", "-created_at"]
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.title} - {self.location}"

    @property
    def is_available(self):
        """Check if property is currently available"""
        if not self.is_active:
            return False
        if self.available_from and self.available_from > timezone.now().date():
            return False
        return True


class PropertyImage(ModelMixins):
    """Property images with optional categorization"""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = CloudinaryField(
        "image",
        folder="property_images/",
        transformation=[{"width": 800, "height": 600, "crop": "limit"}],
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., Living Room, Kitchen, Bedroom, Bathroom",
    )
    order = models.IntegerField(default=0, help_text="Display order")
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.property.title} - Image {self.order}"


class Booking(ModelMixins):
    """Booking/Reservation model"""

    # Unique identifier
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Property & Customer Info
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="bookings"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)

    # Booking Details
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    nights = models.IntegerField(editable=False)

    # Pricing
    total_amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=10, default="₦")

    # Status
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES.choices,
        default=BOOKING_STATUS_CHOICES.PENDING,
    )
    payment_status = models.CharField(max_length=20, default="unpaid")

    # Additional Info
    special_requests = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    # Occupancy Tracking
    checked_in_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when client arrived"
    )
    checked_out_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when client departed"
    )
    occupancy_status = models.CharField(
        max_length=20,
        default="booked",
        help_text="Current occupancy state: booked/occupied/departed"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.booking_id} - {self.property.title}"

    def save(self, *args, **kwargs):
        # Calculate nights automatically
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.nights = delta.days
        super().save(*args, **kwargs)

    def clean(self):
        """Validate booking dates"""
        from django.core.exceptions import ValidationError

        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                raise ValidationError("Check-out date must be after check-in date")

            if self.check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")


class Payment(ModelMixins):
    """Payment transactions"""

    # Booking reference
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="payments"
    )

    # Payment Details
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=10, default="₦")
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES.choices,
        default=PAYMENT_METHOD_CHOICES.PAYSTACK,
    )

    # Transaction Info
    transaction_reference = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
    gateway_response = models.JSONField(
        null=True, blank=True, help_text="Response from payment gateway"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES.choices,
        default=PAYMENT_STATUS_CHOICES.PENDING,
    )

    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} - {self.booking.booking_id}"


class ContactInquiry(ModelMixins):
    """General contact form submissions"""

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    subject = models.CharField(
        max_length=50,
        choices=CONTACT_SUBJECT_CHOICES.choices,
        default=CONTACT_SUBJECT_CHOICES.OTHER,
    )
    message = models.TextField()

    # Status
    is_read = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"{self.name} - {self.subject}"


class PropertyInquiry(ModelMixins):
    """Property-specific inquiries"""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="inquiries"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    message = models.TextField()

    # Status
    is_read = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)

    # Timestamps

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Property Inquiries"

    def __str__(self):
        return f"{self.name} - {self.property.title}"


class CALENDAR_SOURCE_CHOICES(models.TextChoices):
    AIRBNB = "airbnb", "Airbnb"
    BOOKING_COM = "booking_com", "Booking.com"
    VRBO = "vrbo", "VRBO"
    OTHER = "other", "Other"


class ExternalCalendar(ModelMixins):
    """External calendar feeds for property synchronization"""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="external_calendars"
    )
    source = models.CharField(
        max_length=50,
        choices=CALENDAR_SOURCE_CHOICES.choices,
        help_text="Calendar source platform"
    )
    ical_url = models.URLField(
        max_length=500,
        help_text="iCal feed URL from external platform"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable calendar sync"
    )
    last_synced = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync timestamp"
    )
    sync_errors = models.TextField(
        blank=True,
        null=True,
        help_text="Last sync error message"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "External Calendars"
        unique_together = ["property", "source"]

    def __str__(self):
        return f"{self.property.title} - {self.get_source_display()}"


class BlockedDate(ModelMixins):
    """Dates blocked from external calendars"""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="blocked_dates"
    )
    external_calendar = models.ForeignKey(
        ExternalCalendar,
        on_delete=models.CASCADE,
        related_name="blocked_dates",
        null=True,
        blank=True,
        help_text="Source calendar (if from external sync)"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    source_booking_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="External booking reference"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the block"
    )

    class Meta:
        ordering = ["start_date"]
        verbose_name_plural = "Blocked Dates"

    def __str__(self):
        return f"{self.property.title} - {self.start_date} to {self.end_date}"

    def clean(self):
        """Validate blocked dates"""
        from django.core.exceptions import ValidationError

        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError("End date must be after start date")


# =============================================================================
# INVENTORY MANAGEMENT MODELS
# =============================================================================


class Country(ModelMixins):
    """Country model for location scalability"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO code e.g., NG, US

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(ModelMixins):
    """State/Region model"""
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")

    class Meta:
        verbose_name_plural = "States"
        unique_together = ["name", "country"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.country.code}"


class Location(ModelMixins):
    """Physical location/warehouse for inventory management"""

    name = models.CharField(max_length=255, unique=True)  # e.g., "Wuse", "Maitama"
    address = models.TextField(blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, related_name="locations")
    # Removed direct country field as it's derived from state
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryItem(ModelMixins):
    """Inventory item type definition"""

    name = models.CharField(max_length=255)  # e.g., "Towel", "Bedsheet"
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)  # e.g., "Linens", "Kitchenware"
    unit = models.CharField(max_length=50, default="piece")  # e.g., "piece", "set"
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class LocationInventory(ModelMixins):
    """Inventory stock at a specific location/warehouse"""

    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="inventory_stock"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="location_stock"
    )
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    min_threshold = models.IntegerField(
        default=5, help_text="Alert when stock falls below this level"
    )

    class Meta:
        ordering = ["location", "item"]
        unique_together = ["location", "item"]
        verbose_name_plural = "Location Inventory"

    def __str__(self):
        return f"{self.location.name} - {self.item.name}: {self.quantity}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_threshold


class PropertyInventory(ModelMixins):
    """Inventory assigned to a specific property/apartment"""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="inventory"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="property_assignments"
    )
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["property", "item"]
        unique_together = ["property", "item"]
        verbose_name_plural = "Property Inventory"

    def __str__(self):
        return f"{self.property.title} - {self.item.name}: {self.quantity}"


class MOVEMENT_TYPE_CHOICES(models.TextChoices):
    INITIAL = "initial", "Initial Stock"
    RESTOCK = "restock", "Restock"
    ASSIGN_TO_PROPERTY = "assign", "Assigned to Property"
    RETURN_FROM_PROPERTY = "return", "Returned from Property"
    CLIENT_REQUEST = "client_request", "Client Request (Extra)"
    DISPOSED = "disposed", "Disposed/Written Off"
    DAMAGED = "damaged", "Damaged"
    TRANSFERRED = "transferred", "Transferred Between Locations"


class InventoryMovement(ModelMixins):
    """Tracks all inventory movements for audit trail"""

    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="movements"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="movements"
    )
    property = models.ForeignKey(
        Property,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_movements",
    )
    booking = models.ForeignKey(
        Booking,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_movements",
    )
    movement_type = models.CharField(
        max_length=50, choices=MOVEMENT_TYPE_CHOICES.choices
    )
    quantity = models.IntegerField()  # Positive for in, negative for out
    reason = models.TextField(help_text="Required for audit trail")
    performed_by = models.CharField(max_length=255)  # Staff name who did this

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inventory Movements"

    def __str__(self):
        direction = "+" if self.quantity > 0 else ""
        return f"{self.location.name} - {self.item.name}: {direction}{self.quantity} ({self.get_movement_type_display()})"


# =============================================================================
# DISPUTE RESOLUTION MODELS
# =============================================================================


class DISPUTE_TYPE_CHOICES(models.TextChoices):
    NO_SHOW = "no_show", "Client No-Show"
    CANCELLATION = "cancellation", "Client Cancellation"
    EARLY_CHECKOUT = "early_checkout", "Early Checkout"
    DAMAGE = "damage", "Property Damage"
    REFUND_REQUEST = "refund", "Refund Request"
    OTHER = "other", "Other"


class DISPUTE_STATUS_CHOICES(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class BookingDispute(ModelMixins):
    """Dispute/conflict resolution for bookings"""

    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="disputes"
    )
    dispute_type = models.CharField(
        max_length=50, choices=DISPUTE_TYPE_CHOICES.choices
    )
    status = models.CharField(
        max_length=50,
        choices=DISPUTE_STATUS_CHOICES.choices,
        default=DISPUTE_STATUS_CHOICES.OPEN,
    )
    description = models.TextField()
    resolution = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Booking Disputes"

    def __str__(self):
        return f"Dispute: {self.booking.booking_id} - {self.get_dispute_type_display()}"


# =============================================================================
# OCCUPANCY STATUS CHOICES (for Booking enhancement)
# =============================================================================


class OCCUPANCY_STATUS_CHOICES(models.TextChoices):
    BOOKED = "booked", "Booked (Awaiting Arrival)"
    OCCUPIED = "occupied", "Occupied (Client Inside)"
    DEPARTED = "departed", "Departed (Client Left)"
