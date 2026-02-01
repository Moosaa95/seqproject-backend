from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Agent,
    Property,
    PropertyImage,
    Booking,
    Payment,
    ContactInquiry,
    PropertyInquiry,
    Location,
    InventoryItem,
    LocationInventory,
    PropertyInventory,
    InventoryMovement,
    BookingDispute,
)


class PropertyImageInline(admin.TabularInline):
    """Inline admin for Property Images"""

    model = PropertyImage
    extra = 1
    fields = ["image", "category", "order", "is_primary"]


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin for Agent model"""

    list_display = ["name", "email", "phone", "mobile", "created_at"]
    search_fields = ["name", "email", "phone", "mobile"]
    list_filter = ["created_at"]
    ordering = ["name"]


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property model"""

    list_display = [
        "id",
        "title",
        "location",
        "price",
        "currency",
        "status",
        "type",
        "bedrooms",
        "bathrooms",
        "featured",
        "is_active",
    ]
    list_filter = ["status", "type", "featured", "is_active", "entity", "created_at"]
    search_fields = ["id", "title", "location", "description", "entity"]
    list_editable = ["featured", "is_active"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [PropertyImageInline]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    # "id",
                    "title",
                    "location",
                    "price",
                    "currency",
                    "status",
                    "type",
                )
            },
        ),
        (
            "Property Details",
            {
                "fields": (
                    "area",
                    "guests",
                    "bedrooms",
                    "bathrooms",
                    "living_rooms",
                    "garages",
                    "units",
                )
            },
        ),
        ("Description & Features", {"fields": ("description", "amenities")}),
        ("Management", {"fields": ("entity", "agent")}),
        (
            "Status & Visibility",
            {"fields": ("featured", "is_active", "available_from")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("agent")


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    """Admin for Property Images"""

    list_display = [
        "property",
        "category",
        "order",
        "is_primary",
        "image_preview",
        "created_at",
    ]
    list_filter = ["category", "is_primary", "created_at"]
    search_fields = ["property__title", "category"]
    list_editable = ["order", "is_primary"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Preview"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin for Booking model"""

    list_display = [
        "booking_id",
        "property",
        "name",
        "email",
        "phone",
        "check_in",
        "check_out",
        "nights",
        "guests",
        "total_amount",
        "status",
        "payment_status",
        "occupancy_status",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "occupancy_status", "check_in", "check_out", "created_at"]
    search_fields = ["booking_id", "name", "email", "phone", "property__title"]
    readonly_fields = ["booking_id", "nights", "checked_in_at", "checked_out_at", "created_at", "updated_at"]
    list_editable = ["status", "payment_status", "occupancy_status"]

    fieldsets = (
        (
            "Booking Information",
            {"fields": ("booking_id", "property", "status", "payment_status")},
        ),
        ("Customer Information", {"fields": ("name", "email", "phone")}),
        (
            "Booking Details",
            {
                "fields": (
                    "check_in",
                    "check_out",
                    "guests",
                    "nights",
                    "special_requests",
                )
            },
        ),
        ("Pricing", {"fields": ("total_amount", "currency")}),
        (
            "Occupancy Tracking",
            {"fields": ("occupancy_status", "checked_in_at", "checked_out_at")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("property")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model"""

    list_display = [
        "id",
        "booking",
        "amount",
        "currency",
        "payment_method",
        "status",
        "transaction_reference",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "paid_at", "created_at"]
    search_fields = ["id", "transaction_reference", "booking__booking_id"]
    readonly_fields = ["id", "paid_at", "created_at", "updated_at"]
    list_editable = ["status"]

    fieldsets = (
        ("Payment Information", {"fields": ("id", "booking", "status")}),
        ("Payment Details", {"fields": ("amount", "currency", "payment_method")}),
        (
            "Transaction Information",
            {"fields": ("transaction_reference", "gateway_response", "paid_at")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("booking")


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    """Admin for Contact Inquiries"""

    list_display = [
        "id",
        "name",
        "email",
        "phone",
        "subject",
        "is_read",
        "responded",
        "created_at",
    ]
    list_filter = ["subject", "is_read", "responded", "created_at"]
    search_fields = ["name", "email", "phone", "message"]
    list_editable = ["is_read", "responded"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Inquiry Information", {"fields": ("name", "email", "phone", "subject")}),
        ("Message", {"fields": ("message",)}),
        ("Status", {"fields": ("is_read", "responded")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    """Admin for Property Inquiries"""

    list_display = [
        "id",
        "property",
        "name",
        "email",
        "phone",
        "is_read",
        "responded",
        "created_at",
    ]
    list_filter = ["is_read", "responded", "created_at"]
    search_fields = ["name", "email", "phone", "property__title", "message"]
    list_editable = ["is_read", "responded"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Property & Contact Information",
            {"fields": ("property", "name", "email", "phone")},
        ),
        ("Message", {"fields": ("message",)}),
        ("Status", {"fields": ("is_read", "responded")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("property")


# =============================================================================
# INVENTORY MANAGEMENT ADMIN
# =============================================================================


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin for Location model"""

    list_display = ["name", "address", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "address"]
    list_editable = ["is_active"]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    """Admin for InventoryItem model"""

    list_display = ["name", "category", "unit", "is_active", "created_at"]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "description", "category"]
    list_editable = ["is_active"]


@admin.register(LocationInventory)
class LocationInventoryAdmin(admin.ModelAdmin):
    """Admin for LocationInventory model"""

    list_display = ["location", "item", "quantity", "min_threshold", "is_low_stock", "created_at"]
    list_filter = ["location", "item__category", "created_at"]
    search_fields = ["location__name", "item__name"]
    list_editable = ["quantity", "min_threshold"]

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = "Low Stock?"


@admin.register(PropertyInventory)
class PropertyInventoryAdmin(admin.ModelAdmin):
    """Admin for PropertyInventory model"""

    list_display = ["property", "item", "quantity", "created_at"]
    list_filter = ["property", "item__category", "created_at"]
    search_fields = ["property__title", "item__name"]
    list_editable = ["quantity"]


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    """Admin for InventoryMovement model (audit trail)"""

    list_display = [
        "created_at",
        "location",
        "item",
        "movement_type",
        "quantity",
        "property",
        "performed_by",
    ]
    list_filter = ["movement_type", "location", "item__category", "created_at"]
    search_fields = ["location__name", "item__name", "property__title", "reason", "performed_by"]
    readonly_fields = ["created_at", "updated_at"]  # Audit trail shouldn't be edited

    ordering = ["-created_at"]


# =============================================================================
# DISPUTE RESOLUTION ADMIN
# =============================================================================


@admin.register(BookingDispute)
class BookingDisputeAdmin(admin.ModelAdmin):
    """Admin for BookingDispute model"""

    list_display = [
        "id",
        "booking",
        "dispute_type",
        "status",
        "resolved_at",
        "resolved_by",
        "created_at",
    ]
    list_filter = ["dispute_type", "status", "created_at", "resolved_at"]
    search_fields = ["booking__booking_id", "description", "resolution", "resolved_by"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Dispute Information", {"fields": ("booking", "dispute_type", "status")}),
        ("Description", {"fields": ("description",)}),
        ("Resolution", {"fields": ("resolution", "resolved_at", "resolved_by")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# Customize admin site headers
admin.site.site_header = "Sequoia Projects Administration"
admin.site.site_title = "Sequoia Projects Admin"
admin.site.index_title = "Welcome to Sequoia Projects Admin Panel"
