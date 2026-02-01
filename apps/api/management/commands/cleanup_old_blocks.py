"""
Django management command to clean up old blocked dates.

Usage:
    python manage.py cleanup_old_blocks
    python manage.py cleanup_old_blocks --days 30
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import BlockedDate


class Command(BaseCommand):
    help = 'Delete blocked dates that have ended (past dates)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Delete blocks older than N days ago (default: 0 = delete all past dates)',
        )

    def handle(self, *args, **options):
        days = options['days']

        # Calculate cutoff date
        cutoff_date = timezone.now().date() - timedelta(days=days)

        self.stdout.write(f'Deleting blocked dates that ended before {cutoff_date}...')

        # Find old blocked dates
        old_blocks = BlockedDate.objects.filter(end_date__lt=cutoff_date)
        count = old_blocks.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No old blocked dates found.'))
            return

        # Delete them
        old_blocks.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} old blocked date(s)')
        )
