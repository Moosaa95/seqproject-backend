from rest_framework import serializers
from django.utils import timezone
from .models import (
    Agent,
    Property,
    PropertyImage,
    Booking,
    Payment,
    ContactInquiry,
    PropertyInquiry,
    ExternalCalendar,
    BlockedDate,
    Location,
    InventoryItem,
    LocationInventory,
    PropertyInventory,
    InventoryMovement,
    BookingDispute,
    Country,
    State,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class StateSerializer(serializers.ModelSerializer):
    country_details = CountrySerializer(source="country", read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = State
        fields = [
            "id",
            "name",
            "country_id",
            "country_details",
            "created_at",
            "updated_at",
        ]


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""

    inventory_count = serializers.SerializerMethodField()
    state_details = StateSerializer(source="state", read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source="state", write_only=True, required=False, allow_null=True
    )
    # Helper fields to flatten the response for simpler frontend consumption
    state_name = serializers.CharField(source="state.name", read_only=True)
    country_name = serializers.CharField(source="state.country.name", read_only=True)

    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "address",
            "state_id",
            "state_details",
            "state_name",
            "country_name",
            "is_active",
            "inventory_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_inventory_count(self, obj):
        """Get total number of inventory items at this location"""
        return obj.inventory_stock.count()


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model"""

    class Meta:
        model = Agent
        fields = ["id", "name", "phone", "mobile", "email", "skype"]


class PropertyImageSerializer(serializers.ModelSerializer):
    """Serializer for Property Images"""

    # Return full URL for images
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "image_url", "category", "order", "is_primary"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PropertySerializer(serializers.ModelSerializer):
    """
    Property serializer matching frontend TypeScript interface
    """

    agent = AgentSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source="agent", write_only=True, required=False
    )

    # Write-only fields for creating agent inline
    agent_name = serializers.CharField(write_only=True, required=False)
    agent_phone = serializers.CharField(write_only=True, required=False)
    agent_mobile = serializers.CharField(write_only=True, required=False)
    agent_email = serializers.EmailField(write_only=True, required=False)

    # Images serialization
    images = serializers.SerializerMethodField()
    categorized_images = serializers.SerializerMethodField()

    # Additional computed fields
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "location",
            "price",
            "currency",
            "status",
            "type",
            "area",
            "guests",
            "bedrooms",
            "bathrooms",
            "living_rooms",
            "garages",
            "units",
            "description",
            "amenities",
            "entity",
            "agent",
            "agent_id",
            "agent_name",
            "agent_phone",
            "agent_mobile",
            "agent_email",
            "featured",
            "is_active",
            "available_from",
            "is_available",
            "images",
            "categorized_images",
            "created_at",
            "updated_at",
            "location_data",
            "location_id_val",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_available"]

    # Add location_id_val field for write (since location_id is reserved/ambiguous in some contexts, actually generic FK usage is fine but let's be explicit)
    location_id_val = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location_data", write_only=True, required=False, allow_null=True
    )
    location_data = LocationSerializer(read_only=True)

    def get_images(self, obj):
        """Return list of image URLs matching frontend format"""
        request = self.context.get("request")
        property_images = obj.images.all()

        image_urls = []
        for img in property_images:
            if img.image and hasattr(img.image, "url"):
                if request is not None:
                    image_urls.append(request.build_absolute_uri(img.image.url))
                else:
                    image_urls.append(img.image.url)

        return image_urls

    def get_categorized_images(self, obj):
        """
        Return categorized images matching frontend format:
        [{ category: "Living Room", images: [...] }, ...]
        """
        request = self.context.get("request")
        property_images = obj.images.exclude(category__isnull=True).exclude(category="")

        # Group images by category
        categorized = {}
        for img in property_images:
            if img.category not in categorized:
                categorized[img.category] = []

            if img.image and hasattr(img.image, "url"):
                if request is not None:
                    categorized[img.category].append(
                        request.build_absolute_uri(img.image.url)
                    )
                else:
                    categorized[img.category].append(img.image.url)

        # Convert to list format
        return [{"category": cat, "images": imgs} for cat, imgs in categorized.items()]

    def create(self, validated_data):
        """Create property with optional inline agent creation and image uploads"""
        # Extract agent-related fields
        agent_name = validated_data.pop("agent_name", None)
        agent_phone = validated_data.pop("agent_phone", None)
        agent_mobile = validated_data.pop("agent_mobile", None)
        agent_email = validated_data.pop("agent_email", None)
        
        # If location_data is present, sync the char field 'location'
        if validated_data.get('location_data'):
             validated_data['location'] = validated_data['location_data'].name

        # If inline agent data is provided, create or get agent
        if agent_name or agent_email:
            # Check if required fields are present
            if not all([agent_name, agent_phone, agent_mobile, agent_email]):
                raise serializers.ValidationError(
                    {
                        "agent": "All agent fields (name, phone, mobile, email) are required when creating an agent inline"
                    }
                )

            # Get or create agent
            agent, created = Agent.objects.get_or_create(
                email=agent_email,
                defaults={
                    "name": agent_name,
                    "phone": agent_phone,
                    "mobile": agent_mobile,
                },
            )

            # Update existing agent if needed
            if not created:
                agent.name = agent_name
                agent.phone = agent_phone
                agent.mobile = agent_mobile
                agent.save()

            # Set the agent on validated_data (it's already mapped to 'agent' via agent_id source)
            if "agent" not in validated_data:
                validated_data["agent"] = agent

        # Create the property
        property_obj = Property.objects.create(**validated_data)
        print("Created Property:", property_obj)

        # Handle image uploads
        request = self.context.get("request")
        if request and request.FILES:
            images = request.FILES.getlist("images")
            for index, image_file in enumerate(images):
                # Get image metadata from request data
                category = request.data.get(f"image_{index}_category", "")
                order = int(request.data.get(f"image_{index}_order", index))
                is_primary = (
                    request.data.get(f"image_{index}_is_primary", "false").lower()
                    == "true"
                )

                # Create PropertyImage
                PropertyImage.objects.create(
                    property=property_obj,
                    image=image_file,
                    category=category,
                    order=order,
                    is_primary=is_primary,
                )

        return property_obj

    def update(self, instance, validated_data):
        """Update property with optional inline agent creation/update and image uploads"""
        # Extract agent-related fields
        agent_name = validated_data.pop("agent_name", None)
        agent_phone = validated_data.pop("agent_phone", None)
        agent_mobile = validated_data.pop("agent_mobile", None)
        agent_email = validated_data.pop("agent_email", None)

        # Sync location char field if location_data updated
        if 'location_data' in validated_data and validated_data['location_data']:
             validated_data['location'] = validated_data['location_data'].name

        # If inline agent data is provided, create or update agent
        if agent_name or agent_email:
            # Check if required fields are present
            if not all([agent_name, agent_phone, agent_mobile, agent_email]):
                raise serializers.ValidationError(
                    {
                        "agent": "All agent fields (name, phone, mobile, email) are required when creating/updating an agent inline"
                    }
                )

            # Get or create agent
            agent, created = Agent.objects.get_or_create(
                email=agent_email,
                defaults={
                    "name": agent_name,
                    "phone": agent_phone,
                    "mobile": agent_mobile,
                },
            )

            # Update existing agent if needed
            if not created:
                agent.name = agent_name
                agent.phone = agent_phone
                agent.mobile = agent_mobile
                agent.save()

            # Set the agent on validated_data
            if "agent" not in validated_data:
                validated_data["agent"] = agent

        # Update the property
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle image uploads
        request = self.context.get("request")
        if request and request.FILES:
            images = request.FILES.getlist("images")
            for index, image_file in enumerate(images):
                # Get image metadata from request data
                category = request.data.get(f"image_{index}_category", "")
                order = int(request.data.get(f"image_{index}_order", index))
                is_primary = (
                    request.data.get(f"image_{index}_is_primary", "false").lower()
                    == "true"
                )

                # Create PropertyImage
                PropertyImage.objects.create(
                    property=instance,
                    image=image_file,
                    category=category,
                    order=order,
                    is_primary=is_primary,
                )

        return instance


class PropertyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for property listings"""

    agent = AgentSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    location_data = LocationSerializer(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "location",
            "location_data",
            "price",
            "currency",
            "status",
            "type",
            "bedrooms",
            "bathrooms",
            "guests",
            "featured",
            "primary_image",
            "agent",
        ]

    def get_primary_image(self, obj):
        """Get the primary/first image for the property"""
        request = self.context.get("request")
        primary_img = obj.images.filter(is_primary=True).first() or obj.images.first()

        if primary_img and primary_img.image and hasattr(primary_img.image, "url"):
            if request is not None:
                return request.build_absolute_uri(primary_img.image.url)
            return primary_img.image.url
        return None


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""

    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.CharField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            "booking_id",
            "property",
            "property_id",
            "property_details",
            "name",
            "email",
            "phone",
            "check_in",
            "check_out",
            "guests",
            "nights",
            "total_amount",
            "currency",
            "status",
            "payment_status",
            "special_requests",
            "cancellation_reason",
            "checked_in_at",
            "checked_out_at",
            "occupancy_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "booking_id",
            "property",
            "nights",
            "total_amount",
            "currency",
            "checked_in_at",
            "checked_out_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate booking data"""
        check_in = data.get("check_in")
        check_out = data.get("check_out")

        # Validate dates
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError(
                    {"check_out": "Check-out date must be after check-in date"}
                )

            if check_in < timezone.now().date():
                raise serializers.ValidationError(
                    {"check_in": "Check-in date cannot be in the past"}
                )

        # Check property availability
        property_id = data.get("property_id")
        if property_id:
            try:
                property_obj = Property.objects.get(id=property_id)
                if not property_obj.is_available:
                    raise serializers.ValidationError(
                        {"property_id": "This property is not currently available"}
                    )

                # Check availability (includes both bookings and blocked dates)
                from .ical_service import ICalService

                is_available = ICalService.check_availability_with_blocked_dates(
                    property_obj, check_in, check_out
                )

                # When updating, exclude current booking from check
                if self.instance:
                    # Check if current booking overlaps
                    if self.instance.property_id == property_id:
                        # Re-check excluding this booking
                        other_bookings = Booking.objects.filter(
                            property_id=property_id, status__in=["pending", "confirmed"]
                        ).filter(check_in__lt=check_out, check_out__gt=check_in).exclude(pk=self.instance.pk)

                        # Check blocked dates
                        from .models import BlockedDate
                        blocked = BlockedDate.objects.filter(
                            property_id=property_id
                        ).filter(start_date__lt=check_out, end_date__gt=check_in)

                        is_available = not other_bookings.exists() and not blocked.exists()

                if not is_available:
                    raise serializers.ValidationError(
                        {"check_in": "Property is not available for selected dates (may be booked or blocked from external calendars)"}
                    )

            except Property.DoesNotExist:
                raise serializers.ValidationError({"property_id": "Property not found"})

        return data

    def create(self, validated_data):
        """Create booking with property assignment and pending payment transaction"""
        property_id = validated_data.pop("property_id")
        property_obj = Property.objects.get(id=property_id)

        # Calculate total amount based on property price and nights
        nights = (validated_data["check_out"] - validated_data["check_in"]).days
        total_amount = property_obj.price * nights

        booking = Booking.objects.create(
            property=property_obj,
            total_amount=total_amount,
            currency=property_obj.currency,
            **validated_data,
        )

        # Automatically create a pending payment transaction
        from .models import PAYMENT_STATUS_CHOICES, PAYMENT_METHOD_CHOICES

        Payment.objects.create(
            booking=booking,
            amount=total_amount,
            currency=property_obj.currency,
            payment_method=PAYMENT_METHOD_CHOICES.PAYSTACK,
            status=PAYMENT_STATUS_CHOICES.PENDING,
        )

        return booking


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""

    booking_details = BookingSerializer(source="booking", read_only=True)
    booking_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "booking_id",
            "booking_details",
            "amount",
            "currency",
            "payment_method",
            "transaction_reference",
            "gateway_response",
            "status",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "paid_at", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create payment with booking assignment"""
        booking_id = validated_data.pop("booking_id")
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            raise serializers.ValidationError({"booking_id": "Booking not found"})

        payment = Payment.objects.create(booking=booking, **validated_data)

        return payment


class ContactInquirySerializer(serializers.ModelSerializer):
    """Serializer for Contact Inquiries"""

    class Meta:
        model = ContactInquiry
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "subject",
            "message",
            "is_read",
            "responded",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_read", "responded", "created_at", "updated_at"]


class PropertyInquirySerializer(serializers.ModelSerializer):
    """Serializer for Property-specific Inquiries"""

    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.CharField(write_only=True)

    class Meta:
        model = PropertyInquiry
        fields = [
            "id",
            "property",
            "property_id",
            "property_details",
            "name",
            "email",
            "phone",
            "message",
            "is_read",
            "responded",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "property", "is_read", "responded", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create inquiry with property assignment"""
        property_id = validated_data.pop("property_id")
        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise serializers.ValidationError({"property_id": "Property not found"})

        inquiry = PropertyInquiry.objects.create(
            property=property_obj, **validated_data
        )

        return inquiry


class ExternalCalendarSerializer(serializers.ModelSerializer):
    """Serializer for External Calendar feeds"""

    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.CharField(write_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = ExternalCalendar
        fields = [
            "id",
            "property",
            "property_id",
            "property_details",
            "source",
            "source_display",
            "ical_url",
            "is_active",
            "last_synced",
            "sync_errors",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "property", "last_synced", "sync_errors", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create external calendar with property assignment"""
        property_id = validated_data.pop("property_id")
        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise serializers.ValidationError({"property_id": "Property not found"})

        external_calendar = ExternalCalendar.objects.create(
            property=property_obj, **validated_data
        )

        return external_calendar


class BlockedDateSerializer(serializers.ModelSerializer):
    """Serializer for Blocked Dates"""

    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.CharField(write_only=True)
    external_calendar_details = ExternalCalendarSerializer(source="external_calendar", read_only=True)

    class Meta:
        model = BlockedDate
        fields = [
            "id",
            "property",
            "property_id",
            "property_details",
            "external_calendar",
            "external_calendar_details",
            "start_date",
            "end_date",
            "source_booking_id",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate blocked date data"""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date:
            if end_date <= start_date:
                raise serializers.ValidationError(
                    {"end_date": "End date must be after start date"}
                )

        return data

    def create(self, validated_data):
        """Create blocked date with property assignment"""
        property_id = validated_data.pop("property_id")
        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise serializers.ValidationError({"property_id": "Property not found"})

        blocked_date = BlockedDate.objects.create(
            property=property_obj, **validated_data
        )

        return blocked_date


# =============================================================================
# INVENTORY MANAGEMENT SERIALIZERS
# =============================================================================





class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for InventoryItem model"""

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "name",
            "description",
            "category",
            "unit",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LocationInventorySerializer(serializers.ModelSerializer):
    """Serializer for LocationInventory model"""

    location_details = LocationSerializer(source="location", read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", write_only=True
    )
    item_details = InventoryItemSerializer(source="item", read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem.objects.all(), source="item", write_only=True
    )
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = LocationInventory
        fields = [
            "id",
            "location",
            "location_id",
            "location_details",
            "item",
            "item_id",
            "item_details",
            "quantity",
            "min_threshold",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "location", "item", "created_at", "updated_at"]


class PropertyInventorySerializer(serializers.ModelSerializer):
    """Serializer for PropertyInventory model"""

    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all(), source="property", write_only=True
    )
    item_details = InventoryItemSerializer(source="item", read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem.objects.all(), source="item", write_only=True
    )

    class Meta:
        model = PropertyInventory
        fields = [
            "id",
            "property",
            "property_id",
            "property_details",
            "item",
            "item_id",
            "item_details",
            "quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "property", "item", "created_at", "updated_at"]


class InventoryMovementSerializer(serializers.ModelSerializer):
    """Serializer for InventoryMovement model"""

    location_details = LocationSerializer(source="location", read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", write_only=True
    )
    item_details = InventoryItemSerializer(source="item", read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem.objects.all(), source="item", write_only=True
    )
    property_details = PropertyListSerializer(source="property", read_only=True)
    property_id = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all(),
        source="property",
        write_only=True,
        required=False,
        allow_null=True,
    )
    booking_details = BookingSerializer(source="booking", read_only=True)
    booking_ref = serializers.UUIDField(write_only=True, required=False)
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True
    )

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "location",
            "location_id",
            "location_details",
            "item",
            "item_id",
            "item_details",
            "property",
            "property_id",
            "property_details",
            "booking",
            "booking_ref",
            "booking_details",
            "movement_type",
            "movement_type_display",
            "quantity",
            "reason",
            "performed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "location",
            "item",
            "property",
            "booking",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create inventory movement and update location inventory"""
        booking_ref = validated_data.pop("booking_ref", None)

        # If booking reference is provided, look up the booking
        if booking_ref:
            try:
                booking = Booking.objects.get(booking_id=booking_ref)
                validated_data["booking"] = booking
            except Booking.DoesNotExist:
                raise serializers.ValidationError({"booking_ref": "Booking not found"})

        # Create the movement record
        movement = InventoryMovement.objects.create(**validated_data)

        # Update location inventory
        location = validated_data["location"]
        item = validated_data["item"]
        quantity_change = validated_data["quantity"]

        location_inv, created = LocationInventory.objects.get_or_create(
            location=location, item=item, defaults={"quantity": 0}
        )
        location_inv.quantity += quantity_change
        if location_inv.quantity < 0:
            location_inv.quantity = 0  # Prevent negative inventory
        location_inv.save()

        return movement


# =============================================================================
# DISPUTE RESOLUTION SERIALIZERS
# =============================================================================


class BookingDisputeSerializer(serializers.ModelSerializer):
    """Serializer for BookingDispute model"""

    booking_details = BookingSerializer(source="booking", read_only=True)
    booking_ref = serializers.UUIDField(write_only=True)
    dispute_type_display = serializers.CharField(
        source="get_dispute_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BookingDispute
        fields = [
            "id",
            "booking",
            "booking_ref",
            "booking_details",
            "dispute_type",
            "dispute_type_display",
            "status",
            "status_display",
            "description",
            "resolution",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "booking", "resolved_at", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create dispute with booking assignment"""
        booking_ref = validated_data.pop("booking_ref")
        try:
            booking = Booking.objects.get(booking_id=booking_ref)
        except Booking.DoesNotExist:
            raise serializers.ValidationError({"booking_ref": "Booking not found"})

        dispute = BookingDispute.objects.create(booking=booking, **validated_data)
        return dispute

    def update(self, instance, validated_data):
        """Update dispute with optional resolution timestamp"""
        # If status is being changed to resolved/closed and resolution is provided
        new_status = validated_data.get("status")
        resolution = validated_data.get("resolution")

        if new_status in ["resolved", "closed"] and resolution and not instance.resolved_at:
            validated_data["resolved_at"] = timezone.now()

        return super().update(instance, validated_data)
