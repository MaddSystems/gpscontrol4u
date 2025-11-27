from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
import hashlib
import random
import string


class CustomUserManager(UserManager):
    """Custom user manager to handle email as username"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model for the marketplace"""
    
    ROLE_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Español'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='free')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    ios_app_user_id = models.CharField(max_length=255, blank=True, null=True, 
                                      help_text="ID to link with gpscontrol4u iOS app")
    phone_number = models.CharField(max_length=20, blank=True, null=True,
                                   help_text="Phone number for the user account")
    phone_verified = models.BooleanField(default=False,
                                        help_text="Whether phone number has been verified")
    
    # RFC/TIN for external API integration
    rfc_tin = models.CharField(max_length=20, blank=True, null=True,
                              help_text="RFC (Mexico) or TIN number for API registration")
    external_api_registered = models.BooleanField(default=False,
                                                 help_text="Whether user is registered with external API")
    can_access_plans = models.BooleanField(default=False,
                                          help_text="Whether user can subscribe to plans")
    
    # External API credentials for mobile app and web portal login
    external_api_username = models.CharField(max_length=255, blank=True, null=True,
                                           help_text="Username for external API (usually email)")
    external_api_password = models.CharField(max_length=255, blank=True, null=True,
                                           help_text="Password for external API login")
    external_client_id = models.IntegerField(blank=True, null=True,
                                           help_text="Client ID from external API")
    external_user_id = models.IntegerField(blank=True, null=True,
                                         help_text="User ID from external API")
    external_licenses = models.IntegerField(default=0,
                                          help_text="Number of licenses assigned")
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username requirement
    username = models.CharField(max_length=150, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
    
    def is_premium(self):
        return self.role == 'premium'
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def generate_email_verification_token(self):
        """Generate a unique email verification token"""
        token = get_random_string(50)
        # Create a hash to ensure uniqueness
        hash_source = f"{self.email}{token}{timezone.now().isoformat()}"
        self.email_verification_token = hashlib.sha256(hash_source.encode()).hexdigest()[:100]
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token
    
    def is_email_verification_valid(self):
        """Check if email verification token is still valid"""
        if not self.email_verification_sent_at:
            return False
        
        from django.conf import settings
        timeout = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 86400)  # 24 hours
        expiry_time = self.email_verification_sent_at + timezone.timedelta(seconds=timeout)
        return timezone.now() < expiry_time
    
    def verify_email(self, token):
        """Verify email with given token"""
        if self.email_verification_token == token and self.is_email_verification_valid():
            self.email_verified = True
            self.email_verification_token = ''
            self.email_verification_sent_at = None
            self.is_active = True
            self.save()
            return True
        return False
    
    @staticmethod
    def generate_secure_password():
        """
        Generate a secure but memorable password for external API
        Format: Word + Numbers (e.g., Apple123)
        Note: Removed special characters to avoid API compatibility issues
        """
        # List of common, easy-to-remember words
        words = [
            'Apple', 'Ocean', 'Tiger', 'Moon', 'River', 'Eagle', 'Storm', 'Fire',
            'Star', 'Cloud', 'Rock', 'Wave', 'Wind', 'Sun', 'Tree', 'Sky',
            'Bird', 'Fish', 'Bear', 'Wolf', 'Lion', 'Rose', 'Gold', 'Blue'
        ]
        
        # Generate password components (no special characters for API compatibility)
        word = random.choice(words)
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        
        # Combine components
        password = f"{word}{numbers}"
        return password
    
    def set_external_api_credentials(self, username, password, client_id=None, user_id=None, licenses=0):
        """Set external API credentials for the user"""
        self.external_api_username = username
        self.external_api_password = password
        self.external_client_id = client_id
        self.external_user_id = user_id
        self.external_licenses = licenses
        self.external_api_registered = True
        self.save()
    
    def get_external_api_credentials(self):
        """Get external API credentials as a dictionary"""
        return {
            'username': self.external_api_username,
            'password': self.external_api_password,
            'client_id': self.external_client_id,
            'user_id': self.external_user_id,
            'licenses': self.external_licenses
        }


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, choices=[('US', 'United States'), ('MX', 'Mexico')], default='US')
    timezone = models.CharField(max_length=50, default='UTC')
    marketing_emails = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Profile for {self.user.email}"
