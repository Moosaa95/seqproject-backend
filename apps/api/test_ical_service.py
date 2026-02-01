"""
Tests for iCal Calendar Synchronization Service.

Tests cover:
1. iCal export functionality
2. iCal import functionality (with mocked HTTP)
3. Availability checking with blocked dates
"""

from datetime import date, timedelta
from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils import timezone
from api.models import Property, Booking, ExternalCalendar, BlockedDate, Agent
from api.ical_service import ICalService


class ICalExportTestCase(TestCase):
    """Tests for iCal export functionality."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        # Create agent
        cls.agent = Agent.objects.create(
            name="Test Agent",
            phone="1234567890",
            email="agent@test.com"
        )

        # Create property
        cls.property = Property.objects.create(
            title="Test Apartment",
            location="Lagos, Nigeria",
            price=50000,
            currency="₦",
            status="rent",
            type="apartment",
            bedrooms=2,
            bathrooms=1,
            living_rooms=1,
            description="A test apartment",
            agent=cls.agent,
            is_active=True
        )

    def test_export_empty_calendar(self):
        """Test exporting calendar with no bookings."""
        ical_data = ICalService.export_property_calendar(self.property)

        self.assertIn("BEGIN:VCALENDAR", ical_data)
        self.assertIn("END:VCALENDAR", ical_data)
        self.assertIn("PRODID:-//Sequoia Projects//Apartment Booking//EN", ical_data)
        self.assertIn(self.property.title, ical_data)

    def test_export_with_booking(self):
        """Test exporting calendar with bookings."""
        # Create a booking
        check_in = date.today() + timedelta(days=5)
        check_out = date.today() + timedelta(days=10)

        booking = Booking.objects.create(
            property=self.property,
            name="John Doe",
            email="john@test.com",
            phone="1234567890",
            check_in=check_in,
            check_out=check_out,
            guests=2,
            total_amount=250000,
            status="confirmed"
        )

        ical_data = ICalService.export_property_calendar(self.property)

        self.assertIn("BEGIN:VEVENT", ical_data)
        self.assertIn("END:VEVENT", ical_data)
        self.assertIn(f"booking-{booking.booking_id}", ical_data)
        self.assertIn("BOOKED - John Doe", ical_data)

    def test_export_with_blocked_date(self):
        """Test exporting calendar with blocked dates."""
        # Create a blocked date
        start_date = date.today() + timedelta(days=15)
        end_date = date.today() + timedelta(days=18)

        blocked = BlockedDate.objects.create(
            property=self.property,
            start_date=start_date,
            end_date=end_date,
            notes="Manual block"
        )

        ical_data = ICalService.export_property_calendar(self.property)

        self.assertIn("BLOCKED", ical_data)
        self.assertIn(f"blocked-{blocked.id}", ical_data)


class ICalImportTestCase(TestCase):
    """Tests for iCal import functionality."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        cls.agent = Agent.objects.create(
            name="Test Agent",
            phone="1234567890",
            email="agent@test.com"
        )

        cls.property = Property.objects.create(
            title="Test Apartment",
            location="Lagos, Nigeria",
            price=50000,
            currency="₦",
            status="rent",
            type="apartment",
            bedrooms=2,
            bathrooms=1,
            living_rooms=1,
            description="A test apartment",
            agent=cls.agent,
            is_active=True
        )

        cls.external_calendar = ExternalCalendar.objects.create(
            property=cls.property,
            source="airbnb",
            ical_url="https://example.com/calendar.ics",
            is_active=True
        )

    @patch('api.ical_service.requests.get')
    def test_import_valid_ical(self, mock_get):
        """Test importing a valid iCal feed."""
        # Create mock iCal data with future event
        future_date = date.today() + timedelta(days=30)
        end_date = future_date + timedelta(days=3)

        mock_ical_data = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Airbnb Inc//Hosting Calendar//EN
BEGIN:VEVENT
UID:airbnb-12345@airbnb.com
DTSTART;VALUE=DATE:{future_date.strftime('%Y%m%d')}
DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}
SUMMARY:Reserved
END:VEVENT
END:VCALENDAR"""

        mock_response = Mock()
        mock_response.content = mock_ical_data.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = ICalService.import_external_calendar(self.external_calendar)

        self.assertTrue(result['success'])
        self.assertEqual(result['created'], 1)

        # Verify blocked date was created
        blocked = BlockedDate.objects.filter(
            property=self.property,
            external_calendar=self.external_calendar
        ).first()

        self.assertIsNotNone(blocked)
        self.assertEqual(blocked.start_date, future_date)
        self.assertEqual(blocked.source_booking_id, "airbnb-12345@airbnb.com")

    @patch('api.ical_service.requests.get')
    def test_import_network_error(self, mock_get):
        """Test handling network errors during import."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        result = ICalService.import_external_calendar(self.external_calendar)

        self.assertFalse(result['success'])
        self.assertIn("Failed to fetch calendar", result['error'])

        # Verify sync_errors was set
        self.external_calendar.refresh_from_db()
        self.assertIsNotNone(self.external_calendar.sync_errors)


class AvailabilityCheckTestCase(TestCase):
    """Tests for availability checking with blocked dates."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        cls.agent = Agent.objects.create(
            name="Test Agent",
            phone="1234567890",
            email="agent@test.com"
        )

        cls.property = Property.objects.create(
            title="Test Apartment",
            location="Lagos, Nigeria",
            price=50000,
            currency="₦",
            status="rent",
            type="apartment",
            bedrooms=2,
            bathrooms=1,
            living_rooms=1,
            description="A test apartment",
            agent=cls.agent,
            is_active=True
        )

    def test_available_with_no_conflicts(self):
        """Test property is available when no conflicts."""
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=15)

        is_available = ICalService.check_availability_with_blocked_dates(
            self.property, check_in, check_out
        )

        self.assertTrue(is_available)

    def test_not_available_with_booking_conflict(self):
        """Test property is not available when booking conflicts."""
        # Create conflicting booking
        Booking.objects.create(
            property=self.property,
            name="Jane Doe",
            email="jane@test.com",
            phone="1234567890",
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=15),
            guests=2,
            total_amount=250000,
            status="confirmed"
        )

        # Try to book overlapping dates
        check_in = date.today() + timedelta(days=12)
        check_out = date.today() + timedelta(days=17)

        is_available = ICalService.check_availability_with_blocked_dates(
            self.property, check_in, check_out
        )

        self.assertFalse(is_available)

    def test_not_available_with_blocked_dates(self):
        """Test property is not available when blocked dates conflict."""
        # Create blocked date
        BlockedDate.objects.create(
            property=self.property,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=25),
            notes="Airbnb booking"
        )

        # Try to book overlapping dates
        check_in = date.today() + timedelta(days=22)
        check_out = date.today() + timedelta(days=27)

        is_available = ICalService.check_availability_with_blocked_dates(
            self.property, check_in, check_out
        )

        self.assertFalse(is_available)

    def test_available_before_blocked_dates(self):
        """Test property is available before blocked dates."""
        # Create blocked date
        BlockedDate.objects.create(
            property=self.property,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            notes="Blocked"
        )

        # Try to book dates before the block
        check_in = date.today() + timedelta(days=25)
        check_out = date.today() + timedelta(days=28)

        is_available = ICalService.check_availability_with_blocked_dates(
            self.property, check_in, check_out
        )

        self.assertTrue(is_available)
