from django.db import models
from django.conf import settings
import json


class Form(models.Model):
    """gpscontrol4u form definitions"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Español'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forms')
    form_name = models.CharField(max_length=200)
    form_structure = models.JSONField(help_text="JSON structure defining form fields and validation")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    is_predefined = models.BooleanField(default=False, help_text="True for default forms available to free users")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'form_name', 'language']
    
    def __str__(self):
        return f"{self.form_name} ({self.language}) - {self.user.email}"
    
    def get_form_structure(self):
        """Return parsed JSON structure"""
        if isinstance(self.form_structure, str):
            return json.loads(self.form_structure)
        return self.form_structure
    
    def can_user_access(self, user):
        """Check if user can access this form"""
        if self.is_predefined:
            return True  # Predefined forms available to all users
        if self.user == user:
            return True  # User's own forms
        return False


class DataRecord(models.Model):
    """User-submitted data records"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_records')
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='data_records')
    data_content = models.JSONField(help_text="JSON data submitted by user")
    language = models.CharField(max_length=2, choices=Form.LANGUAGE_CHOICES, default='en')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Location data (optional)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Data for {self.form.form_name} by {self.user.email}"
    
    def get_data_content(self):
        """Return parsed JSON data"""
        if isinstance(self.data_content, str):
            return json.loads(self.data_content)
        return self.data_content


class FormTemplate(models.Model):
    """Predefined form templates"""
    
    CATEGORY_CHOICES = [
        ('survey', 'Survey'),
        ('inspection', 'Inspection'),
        ('feedback', 'Feedback'),
        ('registration', 'Registration'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    template_structure = models.JSONField(help_text="JSON template structure")
    language = models.CharField(max_length=2, choices=Form.LANGUAGE_CHOICES, default='en')
    is_premium_only = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        unique_together = ['name', 'language']
    
    def __str__(self):
        return f"{self.name} ({self.language})"
    
    def can_user_access(self, user):
        """Check if user can access this template"""
        if not self.is_premium_only:
            return True
        return user.is_premium()
