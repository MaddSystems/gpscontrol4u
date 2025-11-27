from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Public pages
    path('', views.HomeView.as_view(), name='home'),
    path('pricing/', views.pricing_view, name='pricing'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # User dashboard and profile
    path('setup/', views.setup_account_view, name='setup_account'),
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    path('verify-phone-code/', views.verify_phone_code_view, name='verify_phone_code'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('activate-plan/', views.activate_plan, name='activate_plan'),
    path('get-credentials/', views.get_credentials, name='get_credentials'),
    path('get-plan-details/', views.get_plan_details, name='get_plan_details'),
    
    # Payment processing
    path('create-mercado-pago-preference/', views.create_mercado_pago_preference, name='create_mercado_pago_preference'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('payment/pending/', views.payment_pending, name='payment_pending'),
    path('webhooks/mercadopago/', views.mercado_pago_webhook, name='mercado_pago_webhook'),
    
    # Language setting
    path('set-language/', views.set_language, name='set-language'),

    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-and-conditions/', views.terms_and_conditions_view, name='terms_and_conditions'),
]
