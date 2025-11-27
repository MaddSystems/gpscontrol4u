from django.conf import settings

def mercado_pago_context(request):
    """Add Mercado Pago settings to template context"""
    return {
        'settings': {
            'MERCADO_PAGO_SANDBOX': settings.MERCADO_PAGO_SANDBOX,
            'MERCADO_PAGO_TEST_BUYER_EMAIL': settings.MERCADO_PAGO_TEST_BUYER_EMAIL,
            'MERCADO_PAGO_TEST_BUYER_PASSWORD': settings.MERCADO_PAGO_TEST_BUYER_PASSWORD,
        }
    }
