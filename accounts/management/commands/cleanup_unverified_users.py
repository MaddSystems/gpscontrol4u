from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


class Command(BaseCommand):
    help = 'Clean up unverified user accounts older than specified days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Remove unverified accounts older than this many days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find unverified users older than cutoff date
        unverified_users = User.objects.filter(
            email_verified=False,
            date_joined__lt=cutoff_date
        )
        
        count = unverified_users.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} unverified accounts older than {days} days')
            )
            
            if count > 0:
                self.stdout.write('Accounts that would be deleted:')
                for user in unverified_users:
                    self.stdout.write(f'  - {user.email} (created: {user.date_joined})')
        else:
            if count > 0:
                unverified_users.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {count} unverified accounts older than {days} days')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'No unverified accounts older than {days} days found')
                )
