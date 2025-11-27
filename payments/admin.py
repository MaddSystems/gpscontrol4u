from django.contrib import admin
from .models import Subscription, Payment, PricingPlan


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'status', 'currency', 'amount', 'start_date', 'end_date')
    list_filter = ('plan_type', 'status', 'currency', 'created_at')
    search_fields = ('user__email', 'stripe_subscription_id', 'mercado_pago_subscription_id')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'plan_type', 'status', 'currency', 'amount')}),
        ('Stripe', {'fields': ('stripe_subscription_id', 'stripe_customer_id')}),
        ('Mercado Pago', {'fields': ('mercado_pago_subscription_id', 'mercado_pago_customer_id')}),
        ('Dates', {'fields': ('start_date', 'end_date', 'trial_end_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'payment_provider', 'payment_type', 'status', 'created_at')
    list_filter = ('payment_provider', 'payment_type', 'status', 'currency', 'created_at')
    search_fields = ('user__email', 'stripe_payment_intent_id', 'mercado_pago_payment_id', 'description')
    raw_id_fields = ('user', 'subscription')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'subscription', 'payment_provider', 'payment_type')}),
        ('Payment Details', {'fields': ('amount', 'currency', 'status', 'description')}),
        ('Provider IDs', {'fields': ('stripe_payment_intent_id', 'mercado_pago_payment_id')}),
        ('Metadata', {'fields': ('metadata',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'plan_type', 'amount', 'currency', 'max_forms', 'is_active')
    list_filter = ('plan_type', 'currency', 'is_active', 'analytics_enabled', 'export_enabled')
    search_fields = ('plan_name', 'stripe_price_id', 'mercado_pago_plan_id')
    
    fieldsets = (
        (None, {'fields': ('plan_name', 'plan_type', 'currency', 'amount')}),
        ('Features', {'fields': ('max_forms', 'max_records_per_form', 'analytics_enabled', 'export_enabled', 'priority_support')}),
        ('Stripe', {'fields': ('stripe_price_id', 'stripe_product_id')}),
        ('Mercado Pago', {'fields': ('mercado_pago_plan_id',)}),
        ('Status', {'fields': ('is_active',)}),
    )
