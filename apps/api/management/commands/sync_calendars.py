"""
Django management command to sync all external calendars.

Usage:
    python manage.py sync_calendars
    python manage.py sync_calendars --verbose
"""

from django.core.management.base import BaseCommand
from api.ical_service import ICalService
from api.models import ExternalCalendar


class Command(BaseCommand):
    help = 'Sync all active external calendars from Airbnb, Booking.com, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed sync results',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING('Starting calendar synchronization...'))

        # Get all active external calendars
        calendars = ExternalCalendar.objects.filter(is_active=True)

        if not calendars.exists():
            self.stdout.write(self.style.WARNING('No active external calendars found.'))
            self.stdout.write('Add calendars via Django Admin or API.')
            return

        self.stdout.write(f'Found {calendars.count()} active calendar(s) to sync\n')

        # Sync all calendars
        results = ICalService.sync_all_external_calendars()

        # Display results
        success_count = 0
        error_count = 0

        for result in results:
            property_name = result['property']
            source = result['source']
            sync_result = result['result']

            if sync_result['success']:
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {property_name} ({source})')
                )

                if verbose:
                    self.stdout.write(
                        f"  - Created: {sync_result.get('created', 0)} blocked dates"
                    )
                    self.stdout.write(
                        f"  - Updated: {sync_result.get('updated', 0)} blocked dates"
                    )
                    self.stdout.write(
                        f"  - Total events: {sync_result.get('total_events', 0)}"
                    )

                    if sync_result.get('errors'):
                        self.stdout.write(
                            self.style.WARNING(f"  - Errors: {len(sync_result['errors'])}")
                        )
                        if verbose:
                            for error in sync_result['errors'][:3]:  # Show first 3 errors
                                self.stdout.write(f"    • {error}")
            else:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ {property_name} ({source})')
                )
                self.stdout.write(
                    f"  Error: {sync_result.get('error', 'Unknown error')}"
                )

            self.stdout.write('')  # Empty line between results

        # Summary
        self.stdout.write('-' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'Sync completed: {success_count} successful, {error_count} failed')
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING('Check sync_errors field in External Calendars for details')
            )
