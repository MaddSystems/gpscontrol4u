from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class Subscription(models.Model):
    """Track user subscriptions for gpscontrol4u premium features"""
    
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('premium_monthly', 'Premium Monthly'),
        ('premium_yearly', 'Premium Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('MXN', 'Mexican Peso'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='inactive')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Stripe fields
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Mercado Pago fields
    mercado_pago_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    mercado_pago_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # External API fields
    external_plan_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from external API plan system")
    
    # Reference to current active purchase (for backward compatibility)
    current_plan_purchase = models.ForeignKey(
        'PlanPurchase', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Currently active plan purchase"
    )
    
    # Subscription dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan_type} ({self.status})"
    
    def is_active(self):
        return self.status == 'active'
    
    def is_premium(self):
        return self.plan_type in ['premium_monthly', 'premium_yearly'] and self.is_active()


class Payment(models.Model):
    """Log payment transactions"""
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('mercado_pago', 'Mercado Pago'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('one_time', 'One Time'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    payment_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES, default='subscription')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Subscription.CURRENCY_CHOICES, default='USD')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Provider-specific IDs
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    mercado_pago_payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} ({self.status})"


class PricingPlan(models.Model):
    """Define pricing plans for different markets"""
    
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=Subscription.PLAN_CHOICES)
    currency = models.CharField(max_length=3, choices=Subscription.CURRENCY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Features
    max_forms = models.IntegerField(default=0, help_text="0 means unlimited")
    max_records_per_form = models.IntegerField(default=100)
    analytics_enabled = models.BooleanField(default=False)
    export_enabled = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    
    # Stripe product IDs
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Mercado Pago plan ID
    mercado_pago_plan_id = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['plan_type', 'currency']
        ordering = ['currency', 'amount']
    
    def __str__(self):
        return f"{self.plan_name} - {self.amount} {self.currency}"


class PlanPurchase(models.Model):
    """Track all plan purchases with history, restrictions, and expiration"""
    
    PLAN_CATEGORY_CHOICES = [
        ('free', 'Free Plan'),
        ('team', 'Team Plan'),
        ('license', 'License'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('MXN', 'Mexican Peso'),
    ]
    
    # Core fields
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plan_purchases')
    external_plan_id = models.CharField(max_length=255, help_text="ID from external API plan system")
    plan_name = models.CharField(max_length=255)
    plan_category = models.CharField(max_length=20, choices=PLAN_CATEGORY_CHOICES)
    
    # Purchase details
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    purchase_date = models.DateTimeField(auto_now_add=True)
    activation_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    
    # Payment tracking
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Provider-specific IDs
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    mercado_pago_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata from external API
    external_metadata = models.JSONField(default=dict, blank=True, help_text="Data from external API")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-purchase_date']
        # Ensure only one free plan per user
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'plan_category'],
                condition=models.Q(plan_category='free'),
                name='unique_free_plan_per_user'
            )
        ]
    
    @property
    def admin_users_quantity(self):
        """Get admin users quantity from external metadata"""
        return self.external_metadata.get('admin_users_quantity', 0) or 0
    
    @property
    def subscribed_users_quantity(self):
        """Get subscribed users quantity from external metadata"""
        return self.external_metadata.get('subscribed_users_quantity', 0) or 0
    
    @property
    def total_users_quantity(self):
        """Get total users quantity (admin + subscribed)"""
        return self.admin_users_quantity + self.subscribed_users_quantity

    def __str__(self):
        return f"{self.user.email} - {self.plan_name} ({self.status})"
    
    def is_active(self):
        """Check if the purchase is currently active"""
        if self.status != 'active':
            return False
        
        # Check expiration for non-free plans
        if self.expiration_date and timezone.now() > self.expiration_date:
            # Auto-expire if past expiration date
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])
            return False
        
        return True
    
    def is_expired(self):
        """Check if the purchase has expired"""
        if self.expiration_date and timezone.now() > self.expiration_date:
            return True
        return False
    
    def days_until_expiration(self):
        """Get days until expiration, None if no expiration date"""
        if not self.expiration_date:
            return None
        
        days = (self.expiration_date - timezone.now()).days
        return max(0, days)
    
    def activate(self, expiration_days=None):
        """Activate the purchase with optional expiration"""
        self.status = 'active'
        self.activation_date = timezone.now()
        
        if expiration_days:
            self.expiration_date = timezone.now() + timedelta(days=expiration_days)
        
        self.save(update_fields=['status', 'activation_date', 'expiration_date', 'updated_at'])
    
    def expire(self):
        """Mark the purchase as expired"""
        self.status = 'expired'
        self.save(update_fields=['status', 'updated_at'])
    
    def cancel(self):
        """Cancel the purchase"""
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])
    
    @classmethod
    def get_user_active_purchases(cls, user):
        """Get all active purchases for a user"""
        return cls.objects.filter(user=user, status='active').order_by('-purchase_date')
    
    @classmethod
    def get_user_purchase_history(cls, user):
        """Get complete purchase history for a user"""
        return cls.objects.filter(user=user).order_by('-purchase_date')
    
    @classmethod
    def user_has_free_plan(cls, user):
        """Check if user has already activated the free plan"""
        return cls.objects.filter(user=user, plan_category='free').exists()
    
    @classmethod
    def get_user_active_plan_ids(cls, user):
        """Get list of active external plan IDs for a user"""
        active_purchases = cls.get_user_active_purchases(user)
        return [purchase.external_plan_id for purchase in active_purchases]
