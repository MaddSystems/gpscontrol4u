from django import template

register = template.Library()

@register.filter
def sum_amount(purchases):
    """Calculate the total amount from a queryset of purchases"""
    try:
        return sum(purchase.amount for purchase in purchases)
    except (TypeError, AttributeError):
        return 0
