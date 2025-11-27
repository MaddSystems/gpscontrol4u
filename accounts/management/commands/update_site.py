from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Update the default site domain from .env DOMAIN variable'

    def handle(self, *args, **options):
        # Get domain from Django settings (which reads from .env via decouple)
        domain = getattr(settings, 'DOMAIN', 'localhost')
        
        if not domain or domain == 'localhost':
            self.stdout.write(
                self.style.WARNING(
                    'Warning: DOMAIN not set in .env file. Using localhost as fallback.\n'
                    'Please set DOMAIN=your-domain.com in your .env file for production.'
                )
            )
            domain = 'localhost'
        
        # Remove protocol if present (sites framework expects domain only)
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        
        try:
            # Get or create the default site
            site = Site.objects.get(pk=1)
            old_domain = site.domain
            old_name = site.name
            
            # Update to the correct domain from .env
            site.domain = domain
            site.name = 'Marketplace'
            site.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Site updated successfully:\n'
                    f'  Domain: {old_domain} → {site.domain}\n'
                    f'  Name: {old_name} → {site.name}\n'
                    f'  Source: DOMAIN from Django settings (.env file)'
                )
            )
            
        except Site.DoesNotExist:
            # Create the site if it doesn't exist
            site = Site.objects.create(
                pk=1,
                domain=domain,
                name='Marketplace'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Site created successfully:\n'
                    f'  Domain: {site.domain}\n'
                    f'  Name: {site.name}\n'
                    f'  Source: DOMAIN from Django settings (.env file)'
                )
            )
