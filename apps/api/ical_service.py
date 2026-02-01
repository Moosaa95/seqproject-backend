"""
iCal Calendar Synchronization Service

This module handles:
1. Exporting bookings as iCal feeds for external platforms
2. Importing iCal feeds from Airbnb, Booking.com, etc.
3. Creating blocked dates from imported events
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from django.utils import timezone
from icalendar import Calendar, Event, vCalAddress, vText
from .models import Property, Booking, ExternalCalendar, BlockedDate


class ICalService:
    """Service for iCal calendar operations"""

    @staticmethod
    def export_property_calendar(property_obj: Property) -> str:
        """
        Export all bookings for a property as an iCal feed.

        Args:
            property_obj: Property instance

        Returns:
            iCal formatted string
        """
        cal = Calendar()

        # Calendar properties
        cal.add('prodid', '-//Sequoia Projects//Apartment Booking//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f'{property_obj.title} - Bookings')
        cal.add('x-wr-timezone', 'UTC')
        cal.add('x-wr-caldesc', f'Booking calendar for {property_obj.title}')

        # Add all confirmed and pending bookings
        bookings = Booking.objects.filter(
            property=property_obj,
            status__in=['pending', 'confirmed', 'completed']
        ).exclude(
            status='cancelled'
        )

        for booking in bookings:
            event = Event()

            # Event UID (unique identifier)
            event.add('uid', f'booking-{booking.booking_id}@sequoiaprojects.com')

            # Summary
            event.add('summary', f'BOOKED - {booking.name}')

            # Description
            description = f"""
Booking ID: {booking.booking_id}
Guest: {booking.name}
Email: {booking.email}
Phone: {booking.phone}
Guests: {booking.guests}
Status: {booking.status}
Payment Status: {booking.payment_status}
            """.strip()

            if booking.special_requests:
                description += f"\nSpecial Requests: {booking.special_requests}"

            event.add('description', description)

            # Dates (all-day event)
            event.add('dtstart', booking.check_in)
            event.add('dtend', booking.check_out)

            # Status
            if booking.status == 'confirmed':
                event.add('status', 'CONFIRMED')
            elif booking.status == 'pending':
                event.add('status', 'TENTATIVE')
            else:
                event.add('status', 'CONFIRMED')

            # Organizer
            organizer = vCalAddress(f'MAILTO:admin@sequoiaprojects.com')
            organizer.params['cn'] = vText('Sequoia Projects')
            event.add('organizer', organizer)

            # Attendee
            attendee = vCalAddress(f'MAILTO:{booking.email}')
            attendee.params['cn'] = vText(booking.name)
            attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
            event.add('attendee', attendee)

            # Timestamps
            event.add('created', booking.created_at)
            event.add('last-modified', booking.updated_at)
            event.add('dtstamp', timezone.now())

            # Transparency (show as busy)
            event.add('transp', 'OPAQUE')

            cal.add_component(event)

        # Add blocked dates
        blocked_dates = BlockedDate.objects.filter(property=property_obj)

        for blocked in blocked_dates:
            event = Event()

            # Event UID
            event.add('uid', f'blocked-{blocked.id}@sequoiaprojects.com')

            # Summary
            source = f" ({blocked.external_calendar.get_source_display()})" if blocked.external_calendar else ""
            event.add('summary', f'BLOCKED{source}')

            # Description
            description = f"Property blocked"
            if blocked.notes:
                description += f"\nNotes: {blocked.notes}"
            if blocked.source_booking_id:
                description += f"\nExternal Booking ID: {blocked.source_booking_id}"

            event.add('description', description)

            # Dates (all-day event)
            event.add('dtstart', blocked.start_date)
            event.add('dtend', blocked.end_date)

            # Status
            event.add('status', 'CONFIRMED')

            # Timestamps
            event.add('created', blocked.created_at)
            event.add('last-modified', blocked.updated_at)
            event.add('dtstamp', timezone.now())

            # Transparency (show as busy)
            event.add('transp', 'OPAQUE')

            cal.add_component(event)

        return cal.to_ical().decode('utf-8')

    @staticmethod
    def import_external_calendar(external_calendar: ExternalCalendar) -> Dict:
        """
        Import and parse an external iCal feed.

        Args:
            external_calendar: ExternalCalendar instance

        Returns:
            Dict with status and results
        """
        try:
            # Fetch the iCal feed
            response = requests.get(
                external_calendar.ical_url,
                timeout=30,
                headers={'User-Agent': 'Sequoia-Projects-Calendar-Sync/1.0'}
            )
            response.raise_for_status()

            # Parse the iCal data
            cal = Calendar.from_ical(response.content)

            # Extract events
            events = []
            for component in cal.walk():
                if component.name == "VEVENT":
                    events.append(component)

            # Process events
            blocked_dates_created = 0
            blocked_dates_updated = 0
            errors = []

            for event in events:
                try:
                    # Extract event details
                    summary = str(event.get('summary', ''))
                    dtstart = event.get('dtstart')
                    dtend = event.get('dtend')
                    uid = str(event.get('uid', ''))

                    if not dtstart or not dtend:
                        continue

                    # Convert to date objects
                    if hasattr(dtstart.dt, 'date'):
                        start_date = dtstart.dt.date()
                    else:
                        start_date = dtstart.dt

                    if hasattr(dtend.dt, 'date'):
                        end_date = dtend.dt.date()
                    else:
                        end_date = dtend.dt

                    # Skip past events
                    if end_date < timezone.now().date():
                        continue

                    # Check if this blocked date already exists
                    existing_blocked = BlockedDate.objects.filter(
                        property=external_calendar.property,
                        external_calendar=external_calendar,
                        source_booking_id=uid
                    ).first()

                    if existing_blocked:
                        # Update if dates changed
                        if (existing_blocked.start_date != start_date or
                            existing_blocked.end_date != end_date):
                            existing_blocked.start_date = start_date
                            existing_blocked.end_date = end_date
                            existing_blocked.notes = summary
                            existing_blocked.save()
                            blocked_dates_updated += 1
                    else:
                        # Create new blocked date
                        BlockedDate.objects.create(
                            property=external_calendar.property,
                            external_calendar=external_calendar,
                            start_date=start_date,
                            end_date=end_date,
                            source_booking_id=uid,
                            notes=summary
                        )
                        blocked_dates_created += 1

                except Exception as e:
                    errors.append(f"Error processing event: {str(e)}")
                    continue

            # Update last sync time
            external_calendar.last_synced = timezone.now()
            external_calendar.sync_errors = None
            external_calendar.save()

            return {
                'success': True,
                'created': blocked_dates_created,
                'updated': blocked_dates_updated,
                'total_events': len(events),
                'errors': errors
            }

        except requests.RequestException as e:
            error_msg = f"Failed to fetch calendar: {str(e)}"
            external_calendar.sync_errors = error_msg
            external_calendar.save()

            return {
                'success': False,
                'error': error_msg
            }

        except Exception as e:
            error_msg = f"Failed to parse calendar: {str(e)}"
            external_calendar.sync_errors = error_msg
            external_calendar.save()

            return {
                'success': False,
                'error': error_msg
            }

    @staticmethod
    def sync_all_external_calendars() -> List[Dict]:
        """
        Sync all active external calendars.

        Returns:
            List of sync results for each calendar
        """
        results = []

        external_calendars = ExternalCalendar.objects.filter(is_active=True)

        for ext_cal in external_calendars:
            result = ICalService.import_external_calendar(ext_cal)
            results.append({
                'property': ext_cal.property.title,
                'source': ext_cal.get_source_display(),
                'result': result
            })

        return results

    @staticmethod
    def check_availability_with_blocked_dates(
        property_obj: Property,
        check_in: datetime.date,
        check_out: datetime.date
    ) -> bool:
        """
        Check if property is available considering both bookings and blocked dates.

        Args:
            property_obj: Property instance
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            True if available, False if blocked
        """
        # Check regular bookings
        overlapping_bookings = Booking.objects.filter(
            property=property_obj,
            status__in=['pending', 'confirmed']
        ).filter(
            check_in__lt=check_out,
            check_out__gt=check_in
        )

        if overlapping_bookings.exists():
            return False

        # Check blocked dates
        overlapping_blocked = BlockedDate.objects.filter(
            property=property_obj
        ).filter(
            start_date__lt=check_out,
            end_date__gt=check_in
        )

        if overlapping_blocked.exists():
            return False

        return True
