from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from payments.models import Payment
from .models import User, UserProfile
class MarketplaceAdminSite(admin.AdminSite):
    site_header = "Marketplace Administration"
    site_title = "Marketplace Admin"
    index_title = "Welcome to Marketplace Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-summary/', self.admin_view(self.dashboard_view), name='dashboard-summary'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_users = User.objects.count()
        # Get completed payments
        completed_payments = Payment.objects.filter(status='completed').select_related('user')
        # Collect buyers and their products
        buyers_products = {}
        for payment in completed_payments:
            user = payment.user
            email = user.email
            # Try to get product info from payment metadata or description
            product = payment.metadata.get('product', None) if hasattr(payment, 'metadata') else None
            if not product:
                product = payment.description if payment.description else 'Unknown Product'
            if email not in buyers_products:
                buyers_products[email] = []
            buyers_products[email].append(product)

        total_buyers = len(buyers_products)
        context = dict(
            self.each_context(request),
            total_users=total_users,
            total_buyers=total_buyers,
            buyers_products=buyers_products,
        )
        return render(request, 'admin/dashboard_summary.html', context)

    
    readonly_fields = ('email_verification_token', 'email_verification_sent_at')
    
    def email_verification_status(self, obj):
        """Display email verification status with color coding"""
        if obj.email_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        elif obj.email_verification_token:
            if obj.is_email_verification_valid():
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">❌ Expired</span>'
                )
        else:
            return format_html(
                '<span style="color: gray;">No verification sent</span>'
            )
    
    email_verification_status.short_description = _('Email Status')
    
    
    def send_verification_email(self, request, queryset):
        """Admin action to send verification email"""
        from django.contrib import messages
        from accounts.views import send_verification_email_helper
        
        count = 0
        for user in queryset:
            if not user.email_verified:
                try:
                    send_verification_email_helper(request, user)
                    count += 1
                except Exception as e:
                    messages.error(request, f'Failed to send email to {user.email}: {str(e)}')
        
        if count > 0:
            messages.success(request, f'Verification emails sent to {count} users.')
        else:
            messages.warning(request, 'No verification emails were sent.')
    
    send_verification_email.short_description = _('Send verification email to selected users')
    
    def mark_email_verified(self, request, queryset):
        """Admin action to manually verify emails"""
        count = queryset.filter(email_verified=False).update(
            email_verified=True,
            email_verification_token='',
            email_verification_sent_at=None,
            is_active=True
        )
        
        if count > 0:
            self.message_user(request, f'{count} users marked as email verified.')
        else:
            self.message_user(request, 'No users were updated.')
    
    mark_email_verified.short_description = _('Mark selected users as email verified')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'country', 'timezone', 'marketing_emails')
    list_filter = ('country', 'marketing_emails')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone')
    raw_id_fields = ('user',)


# Instantiate the custom admin site for import
marketplace_admin_site = MarketplaceAdminSite(name='marketplace_admin')


# Register User and UserProfile with the custom admin site
marketplace_admin_site.register(User, UserAdmin)
marketplace_admin_site.register(UserProfile, UserProfileAdmin)
