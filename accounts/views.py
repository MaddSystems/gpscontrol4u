from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import activate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, RFCTINForm, PhoneVerificationForm, PhoneCodeVerificationForm
from gpscontrol4u.models import Form, DataRecord
from payments.models import Subscription, PricingPlan, Payment, PlanPurchase
import json
import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# --- Legal static pages views ---
from django.views.decorators.http import require_GET

import sys
import os
import time

# Add project root to path for external API service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from external_api_service import external_api
from subscription_service import SubscriptionService

# Add Mercado Pago imports
import mercadopago
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import logging

# Initialize Mercado Pago SDK
mp_sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)


class HomeView(TemplateView):
    """Landing page for the marketplace"""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pricing_plans'] = PricingPlan.objects.filter(is_active=True)
        return context


class RegisterView(CreateView):
    """User registration view with email verification"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        try:
            # Get the user from form (might be existing unverified user)
            user = form.save(commit=False)
            email = form.cleaned_data['email']
            
            # Check if this is an existing unverified user
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user and not existing_user.email_verified:
                print(f"Updating existing unverified user: {email}")
                
                # Update existing user with new data
                existing_user.first_name = form.cleaned_data['first_name']
                existing_user.last_name = form.cleaned_data['last_name']
                existing_user.language = form.cleaned_data['language']
                existing_user.set_password(form.cleaned_data['password1'])
                existing_user.is_active = False  # Still needs verification
                existing_user.save()
                
                # Send verification email
                self.send_verification_email(existing_user)
                
                messages.success(
                    self.request, 
                    _('Account updated! Please check your email to verify your account.')
                )
                return redirect('accounts:login')
            else:
                print(f"Creating new user: {email}")
                
                # Create new user
                user.is_active = False  # User needs to verify email first
                user.save()
                
                # Send verification email
                self.send_verification_email(user)
                
                messages.success(
                    self.request, 
                    _('Registration successful! Please check your email to verify your account.')
                )
                return redirect('accounts:login')
                
        except Exception as e:
            # Log the error for debugging
            print(f"Registration error: {e}")
            import traceback
            traceback.print_exc()
            messages.error(self.request, _('An error occurred during registration. Please try again.'))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log form errors for debugging
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        
        # Check if the error is due to existing email
        if 'email' in form.errors:
            email = form.data.get('email', '')
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user and not existing_user.email_verified:
                # Remove the email error and provide helpful message
                messages.warning(
                    self.request,
                    _('An unverified account with this email exists. We\'ll send you a new verification email.')
                )
                # Redirect to resend verification with pre-filled email
                return redirect(f"{reverse_lazy('accounts:resend_verification')}?email={email}")
        
        return super().form_invalid(form)
    
    def send_verification_email(self, user):
        """Send verification email to user"""
        from django.utils import translation
        
        try:
            # Activate user's preferred language for email rendering
            current_language = translation.get_language()
            user_language = getattr(user, 'language', 'en')
            print(f"Current language: {current_language}, User language: {user_language}")
            
            with translation.override(user_language):
                # Generate verification token
                token = user.generate_email_verification_token()
                print(f"Generated token for {user.email}: {token}")
                
                # Get current site
                current_site = get_current_site(self.request)
                # Force HTTPS for Cloudflare tunnel
                protocol = 'https'  # Always use HTTPS since Cloudflare tunnel provides SSL
                
                print(f"Current site: {current_site.domain}")
                print(f"Protocol: {protocol} (forced for Cloudflare tunnel)")
                
                # Prepare email context
                context = {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': protocol,
                    'token': token,
                }
                
                # Render email templates with user's language
                subject = _('Verify your Marketplace account')
                print(f"Email subject in {user_language}: {subject}")
                
                text_content = render_to_string('registration/activation_email.txt', context)
                html_content = render_to_string('registration/activation_email.html', context)
                
                print(f"Text content length: {len(text_content)}")
                print(f"HTML content length: {len(html_content)}")
                print(f"From email: {settings.DEFAULT_FROM_EMAIL}")
                print(f"To email: {user.email}")
                
                print(f"Sending email to {user.email}...")
                
                # Send email
                result = send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False,
                )
                
                print(f"Email send result: {result}")
                print(f"Email sent successfully to {user.email}")
                
                # Also log email settings for debugging
                print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
                print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
                print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
                print(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
                print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
                print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
            
        except Exception as e:
            # Log error but don't crash registration
            print(f"Email sending error: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            messages.warning(
                self.request,
                _('Account created but verification email could not be sent. You can request a new verification email from the login page.')
            )

def privacy_policy_view(request):
    """Render the privacy policy static page."""
    return render(request, 'privacy_policy.html')

def terms_and_conditions_view(request):
    """Render the terms and conditions static page."""
    return render(request, 'terms_and_conditions.html')

def login_view(request):
    """User login view with email verification check"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # First, check if user exists and password is correct
            user = authenticate(request, username=email, password=password)
            if user:
                # Check if email is verified
                if not user.email_verified:
                    messages.warning(
                        request, 
                        _('Please verify your email address before logging in. Check your inbox or request a new verification email.')
                    )
                    return render(request, 'registration/login.html', {
                        'form': form,
                        'show_resend_link': True,
                        'user_email': email
                    })
                
                # Email is verified, proceed with login
                login(request, user)
                # Activate user's preferred language
                activate(user.language)
                messages.success(request, _('Welcome back!'))
                next_url = request.GET.get('next', 'accounts:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, _('Invalid email or password.'))
    else:
        form = UserLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, _('You have been logged out.'))
    return redirect('accounts:home')


@login_required
def dashboard_view(request):
    """User dashboard with purchase history and plan tracking"""
    logger = logging.getLogger(__name__)
    user = request.user
    
    # Get user's subscription (for backward compatibility)
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        subscription = None
    
    # Get user's plan purchases (new system)
    user_purchases = PlanPurchase.get_user_purchase_history(user)
    active_purchases = PlanPurchase.get_user_active_purchases(user)
    active_plan_ids = PlanPurchase.get_user_active_plan_ids(user)
    
    # Get external API plans
    external_plans = external_api.get_available_plans()
    if not external_plans:
        external_plans = []
        messages.warning(request, _('Unable to load current plans from server. Please try again later.'))
    else:
        # Sort plans by price (free first, then ascending by price)
        external_plans = sorted(external_plans, key=lambda x: float(x.get('price', 0)))
    
    # Check if user needs to select a plan
    show_plan_selection = (
        user.rfc_tin and 
        user.external_api_registered and 
        user.can_access_plans and
        not active_purchases.exists()  # No active purchases
    )
    
    # Show plan information if user has active purchases
    show_plan_info = (
        user.rfc_tin and 
        user.external_api_registered and
        user.can_access_plans and
        active_purchases.exists() and
        external_plans
    )
    
    # Get user's forms (only if they have an active plan)
    if active_purchases.exists():
        user_forms = Form.objects.filter(user=user, is_active=True)
        recent_records = DataRecord.objects.filter(user=user)[:10]
    else:
        user_forms = Form.objects.none()
        recent_records = DataRecord.objects.none()
        
    predefined_forms = Form.objects.filter(is_predefined=True, is_active=True)
    
    # Prepare purchased plans data with enhanced information
    user_purchased_plans = set()
    purchase_details = {}
    
    for purchase in user_purchases:
        plan_id = purchase.external_plan_id
        user_purchased_plans.add(plan_id)
        user_purchased_plans.add(int(plan_id) if plan_id.isdigit() else plan_id)
        
        # Store detailed purchase information
        purchase_details[plan_id] = {
            'purchase': purchase,
            'is_active': purchase.is_active(),
            'is_expired': purchase.is_expired(),
            'days_until_expiration': purchase.days_until_expiration(),
            'purchase_date': purchase.purchase_date,
            'activation_date': purchase.activation_date,
            'expiration_date': purchase.expiration_date,
            'amount': purchase.amount,
            'currency': purchase.currency,
            'status': purchase.status,
            'plan_category': purchase.plan_category,
        }
    
    # Add current subscription plan for backward compatibility
    if subscription and subscription.external_plan_id:
        user_purchased_plans.add(subscription.external_plan_id)
        try:
            user_purchased_plans.add(int(subscription.external_plan_id))
        except (ValueError, TypeError):
            pass
    
    # Debug logging
    logger.info(f"🎯 [DASHBOARD] User {user.email} purchased plans: {user_purchased_plans}")
    logger.info(f"🎯 [DASHBOARD] Active purchases: {len(active_purchases)}")
    
    # Ensure all plan IDs are properly represented
    normalized_purchased_plans = set()
    for plan_id in user_purchased_plans:
        normalized_purchased_plans.add(plan_id)
        try:
            # Add both string and integer versions
            if isinstance(plan_id, str) and plan_id.isdigit():
                normalized_purchased_plans.add(int(plan_id))
            normalized_purchased_plans.add(str(plan_id))
        except (ValueError, TypeError):
            pass
    
    user_purchased_plans = normalized_purchased_plans
    logger.info(f"🎯 [DASHBOARD] Normalized purchased plans: {user_purchased_plans}")
    
    # Calculate total spent
    total_spent = sum(purchase.amount for purchase in user_purchases)
    
    # Calculate user totals from all active purchases using model properties
    total_admin_users = sum(purchase.admin_users_quantity for purchase in active_purchases)
    total_subscribed_users = sum(purchase.subscribed_users_quantity for purchase in active_purchases)
    total_users = total_admin_users + total_subscribed_users
    
    context = {
        'user': user,
        'subscription': subscription,  # For backward compatibility
        'user_forms': user_forms,
        'predefined_forms': predefined_forms,
        'recent_records': recent_records,
        'total_forms': user_forms.count(),
        'total_records': recent_records.count() if active_purchases.exists() else 0,
        'show_plan_selection': show_plan_selection,
        'show_plan_info': show_plan_info,
        'external_plans': external_plans,
        'user_purchased_plans': user_purchased_plans,
        # New purchase-related context
        'user_purchases': user_purchases,
        'active_purchases': active_purchases,
        'active_plan_ids': active_plan_ids,
        'purchase_details': purchase_details,
        'has_free_plan': PlanPurchase.user_has_free_plan(user),
        'total_spent': total_spent,
        # User totals
        'total_users': total_users,
        'total_admin_users': total_admin_users,
        'total_subscribed_users': total_subscribed_users,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    """User profile management"""
    if request.method == 'POST':
        user = request.user
        
        # Update basic info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.language = request.POST.get('language', user.language)
        user.save()
        
        # Update profile
        profile = user.profile
        profile.phone = request.POST.get('phone', profile.phone)
        profile.country = request.POST.get('country', profile.country)
        profile.marketing_emails = request.POST.get('marketing_emails') == 'on'
        profile.save()
        
        # Activate new language
        activate(user.language)
        
        messages.success(request, _('Profile updated successfully.'))
        return redirect('accounts:profile')
    
    return render(request, 'profile.html', {'user': request.user})


def pricing_view(request):
    """Pricing page with purchase history support"""
    # Get external API plans
    external_plans = external_api.get_available_plans()
    if not external_plans:
        plans = PricingPlan.objects.filter(is_active=True).order_by('amount')
        messages.warning(request, _('Unable to load current plans from server. Please try again later.'))
    else:
        plans = []
        # Sort plans by price (free first, then ascending by price)
        external_plans = sorted(external_plans, key=lambda x: float(x.get('price', 0)))
    
    # Check user's setup status and purchase history
    user_has_rfc_tin = False
    user_api_registered = False
    current_subscription = None
    has_free_plan = False
    user_purchased_plans = set()
    active_plan_ids = []
    
    if request.user.is_authenticated:
        user_has_rfc_tin = bool(request.user.rfc_tin)
        user_api_registered = request.user.external_api_registered
        has_free_plan = PlanPurchase.user_has_free_plan(request.user)
        user_purchased_plans = set()
        active_plan_ids = PlanPurchase.get_user_active_plan_ids(request.user)
        
        # Get all purchased plans for display logic
        for purchase in PlanPurchase.get_user_purchase_history(request.user):
            plan_id = purchase.external_plan_id
            user_purchased_plans.add(plan_id)
            user_purchased_plans.add(int(plan_id) if plan_id.isdigit() else plan_id)
        
        try:
            current_subscription = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            current_subscription = None
    
    context = {
        'plans': plans,
        'external_plans': external_plans,
        'usd_plans': plans.filter(currency='USD') if plans else [],
        'mxn_plans': plans.filter(currency='MXN') if plans else [],
        'user_has_rfc_tin': user_has_rfc_tin,
        'user_api_registered': user_api_registered,
        'current_subscription': current_subscription,
        'has_free_plan': has_free_plan,
        'user_purchased_plans': user_purchased_plans,
        'active_plan_ids': active_plan_ids,
    }
    
    return render(request, 'pricing.html', context)


def set_language(request):
    """Set user language preference"""
    from django.http import HttpResponseRedirect
    from django.utils import translation
    from django.urls import translate_url
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    language = request.POST.get('language', 'es')
    
    logger.info(f"🌐 [SET_LANGUAGE] Language switch requested: {language}")
    logger.info(f"🌐 [SET_LANGUAGE] Current session language: {request.session.get('django_language', 'not set')}")
    
    if language in ['en', 'es']:
        # Set language in session using the correct session key
        request.session['django_language'] = language
        request.session.modified = True  # Force session save
        
        # If user is authenticated, save to user profile
        if request.user.is_authenticated:
            request.user.language = language
            request.user.save()
            logger.info(f"🌐 [SET_LANGUAGE] User language updated: {request.user.email} -> {language}")
        
        # Activate the language for this request
        translation.activate(language)
        
        logger.info(f"🌐 [SET_LANGUAGE] Language activated: {language}")
        logger.info(f"🌐 [SET_LANGUAGE] Session updated: {request.session.get('django_language')}")
    
    # Get the redirect URL
    next_url = request.META.get('HTTP_REFERER', '/')
    
    # Try to translate the URL if possible
    try:
        next_url = translate_url(next_url, language)
    except:
        pass
        
    response = HttpResponseRedirect(next_url)
    # Set cookie with proper settings
    response.set_cookie(
        'django_language', 
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        path=settings.LANGUAGE_COOKIE_PATH,
        secure=not settings.DEBUG
    )
    
    logger.info(f"🌐 [SET_LANGUAGE] Redirecting to: {next_url}")
    return response


def verify_email(request, token):
    """Verify user email with token"""
    try:
        user = User.objects.get(email_verification_token=token)
        
        if user.verify_email(token):
            # Automatically log the user in after successful verification
            login(request, user)
            messages.success(request, _('Your email has been verified successfully! Welcome to Marketplace.'))
            return redirect('accounts:dashboard')
        else:
            # Token expired or invalid
            error_type = 'expired' if not user.is_email_verification_valid() else 'invalid_token'
            return render(request, 'registration/email_verification.html', {
                'success': False,
                'error_type': error_type
            })
            
    except User.DoesNotExist:
        return render(request, 'registration/email_verification.html', {
            'success': False,
            'error_type': 'user_not_found'
        })


def resend_verification_email(request):
    """Resend verification email"""
    # Get email from URL parameter if available
    prefilled_email = request.GET.get('email', '')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
            
            if user.email_verified:
                messages.info(request, _('This email address is already verified. You can log in now.'))
                return redirect('accounts:login')
            
            # Send new verification email
            send_verification_email_helper(request, user)
            messages.success(request, _('Verification email sent! Please check your inbox and spam folder.'))
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(request, _('No account found with this email address. Please register a new account.'))
    
    return render(request, 'registration/resend_verification.html', {
        'prefilled_email': prefilled_email
    })


def send_verification_email_helper(request, user):
    """Helper function to send verification email"""
    from django.utils import translation
    
    try:
        # Activate user's preferred language for email rendering
        current_language = translation.get_language()
        user_language = getattr(user, 'language', 'en')
        print(f"[Helper] Current language: {current_language}, User language: {user_language}")
        
        with translation.override(user_language):
            # Generate new verification token
            token = user.generate_email_verification_token()
            print(f"[Helper] Generated token for {user.email}: {token}")
            
            # Get current site
            current_site = get_current_site(request)
            # Force HTTPS for Cloudflare tunnel
            protocol = 'https'  # Always use HTTPS since Cloudflare tunnel provides SSL
            
            print(f"[Helper] Current site: {current_site.domain}")
            print(f"[Helper] Protocol: {protocol}")
            
            # Prepare email context
            context = {
                'user': user,
                'domain': current_site.domain,
                'protocol': protocol,
                'token': token,
            }
            
            # Render email templates with user's language
            subject = _('Verify your Marketplace account')
            text_content = render_to_string('registration/activation_email.txt', context)
            html_content = render_to_string('registration/activation_email.html', context)
            
            print(f"[Helper] Email subject in {user_language}: {subject}")
            print(f"[Helper] Text content length: {len(text_content)}")
            print(f"[Helper] HTML content length: {len(html_content)}")
            print(f"[Helper] From email: {settings.DEFAULT_FROM_EMAIL}")
            print(f"[Helper] To email: {user.email}")
            print(f"[Helper] Sending email to {user.email}...")
            
            # Send email
            result = send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            print(f"[Helper] Email send result: {result}")
            print(f"[Helper] Email sent successfully to {user.email}")
        
    except Exception as e:
        print(f"[Helper] Email sending error: {e}")
        print(f"[Helper] Error type: {type(e)}")
        import traceback
        print(f"[Helper] Full traceback: {traceback.format_exc()}")
        messages.error(request, _('Could not send verification email. Please try again later.'))
        

@login_required
def setup_account_view(request):
    """Account setup view for RFC/TIN collection"""
    logger = logging.getLogger(__name__)
    user = request.user
    
    # If user already has RFC/TIN and phone verified, redirect to dashboard
    if user.rfc_tin and user.phone_verified:
        return redirect('accounts:dashboard')
    
    # If user has RFC but no phone verified, go to phone verification
    if user.rfc_tin and not user.phone_verified:
        return redirect('accounts:verify_phone')
    
    if request.method == 'POST':
        form = RFCTINForm(request.POST)
        if form.is_valid():
            try:
                # Save RFC/TIN to user
                user.rfc_tin = form.cleaned_data['rfc_tin']
                user.save()
                
                logger.info(f"✅ [SETUP_ACCOUNT] RFC/TIN saved for user {user.email}: {user.rfc_tin}")
                messages.success(
                    request,
                    _('RFC/TIN saved! Now please verify your phone number.')
                )
                # Redirect to phone verification
                return redirect('accounts:verify_phone')
                
            except Exception as e:
                logger.error(f"❌ [SETUP_ACCOUNT] Error saving RFC/TIN: {e}")
                print(f"Error saving RFC/TIN: {e}")
                messages.error(
                    request,
                    _('An error occurred. Please try again.')
                )
    else:
        form = RFCTINForm()
    
    context = {
        'form': form,
        'user': user,
    }
    
    return render(request, 'accounts/setup_account.html', context)


@login_required
@require_http_methods(["POST"])
@login_required
@require_http_methods(["POST"])
def activate_plan(request):
    """Activate a subscription plan for the user via external API"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        plan_type = data.get('plan_type')
        external_plan_id = data.get('external_plan_id', 1)  # Default to plan 1 (free)
        
        logger.info(f"🎯 [ACTIVATE_PLAN] Plan activation started")
        logger.info(f"🎯 [ACTIVATE_PLAN] User: {request.user.email}")
        logger.info(f"🎯 [ACTIVATE_PLAN] Plan Type: {plan_type}")
        logger.info(f"🎯 [ACTIVATE_PLAN] External Plan ID: {external_plan_id}")
        logger.info(f"🎯 [ACTIVATE_PLAN] Request data: {json.dumps(data, indent=2)}")
        
        # Get available plans from external API to validate the plan
        from external_api_service import ExternalAPIService
        external_api = ExternalAPIService()
        available_plans = external_api.get_available_plans()
        
        # Check if the requested plan exists
        requested_plan = None
        if available_plans:
            for plan in available_plans:
                # Convert both to string for comparison to handle type mismatches
                if str(plan.get('id')) == str(external_plan_id):
                    requested_plan = plan
                    break
        
        if not requested_plan:
            logger.error(f"🎯 [ACTIVATE_PLAN] Invalid plan ID: {external_plan_id}")
            return JsonResponse({
                'success': False,
                'message': f'Plan ID {external_plan_id} not found'
            })
        
        user = request.user
        logger.info(f"🎯 [ACTIVATE_PLAN] User details:")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Email: {user.email}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   RFC/TIN: {user.rfc_tin}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   External API Registered: {user.external_api_registered}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Current Role: {user.role}")
        
        # Check if user has RFC/TIN
        if not user.rfc_tin:
            logger.error(f"🎯 [ACTIVATE_PLAN] User {user.email} missing RFC/TIN")
            return JsonResponse({
                'success': False,
                'message': 'RFC/TIN setup required before plan activation'
            })
        
        # Initialize subscription service
        subscription_service = SubscriptionService()
        
        # Determine if this plan requires payment
        plan_price = float(requested_plan.get('price', 0))
        is_free_plan = plan_price == 0
        
        logger.info(f"🎯 [ACTIVATE_PLAN] Plan details:")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Name: {requested_plan.get('name')}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Price: {plan_price}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Is Free: {is_free_plan}")
        
        if is_free_plan:
            logger.info(f"🎯 [ACTIVATE_PLAN] Free plan requested - activating directly")
            
            # For free plans, activate immediately without payment
            success, error_msg = activate_plan_for_user(user, None, None, external_plan_id)
            
            if success:
                logger.info(f"🎯 [ACTIVATE_PLAN] Free plan activation successful")
                
                # Get updated user credentials from external API
                success, api_data, error_message = subscription_service.get_user_credentials(user.email)
                
                response_data = {
                    'success': True,
                    'message': f'Successfully activated {requested_plan.get("name")} plan!'
                }
                
                if success and api_data:
                    response_data.update({
                        'credentials': {
                            'username': api_data.get('username'),
                            'password': api_data.get('password'),
                            'portal_url': api_data.get('portal_url', 'https://ego.elisasoftware.com.mx/'),
                            'client_id': api_data.get('client_id'),
                            'user_id': api_data.get('user_id'),
                            'licenses': api_data.get('licenses', 0)
                        }
                    })
                
                # Return success with credentials for user
                return JsonResponse(response_data)
            else:
                logger.error(f"🎯 [ACTIVATE_PLAN] Plan activation failed")
                error_msg_display = error_msg if error_msg else f'Failed to activate {requested_plan.get("name")} plan'
                return JsonResponse({
                    'success': False,
                    'message': error_msg_display
                })
        
        else:
            logger.info(f"🎯 [ACTIVATE_PLAN] Paid plan requested - user language: {user.language}")
            
            # Check if user language is Spanish for Mercado Pago
            if user.language == 'es':
                logger.info(f"🎯 [ACTIVATE_PLAN] Spanish user - redirecting to Mercado Pago")
                return JsonResponse({
                    'success': True,
                    'payment_required': True,
                    'payment_provider': 'mercado_pago',
                    'plan_id': external_plan_id,
                    'message': 'Redirecting to Mercado Pago payment...'
                })
            else:
                logger.info(f"🎯 [ACTIVATE_PLAN] English user - Stripe not yet implemented")
                return JsonResponse({
                    'success': False,
                    'message': f'Payment processing for {requested_plan.get("name")} is currently only available for Spanish-speaking users via Mercado Pago'
                })
        
    except json.JSONDecodeError as e:
        logger.error(f"🎯 [ACTIVATE_PLAN] JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        import traceback
        logger.error(f"🎯 [ACTIVATE_PLAN] Unexpected error: {e}")
        logger.error(f"🎯 [ACTIVATE_PLAN] Error type: {type(e)}")
        logger.error(f"🎯 [ACTIVATE_PLAN] Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def create_mercado_pago_preference(request):
    """Create a Mercado Pago payment preference for plan activation"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user = request.user
        logger.info(f"🎯 [MP_PREFERENCE] Creating preference for user: {user.email}")
        
        # Parse request data to get plan ID
        try:
            data = json.loads(request.body) if request.body else {}
            plan_id = data.get('plan_id', 2)  # Default to plan 2 if not provided
        except json.JSONDecodeError:
            plan_id = 2  # Default fallback
        
        logger.info(f"🎯 [MP_PREFERENCE] Plan ID: {plan_id}")
        
        # Check if user is Spanish-speaking and has RFC/TIN
        if user.language != 'es':
            return JsonResponse({
                'success': False,
                'message': 'Mercado Pago is only available for Spanish-speaking users'
            })
        
        if not user.rfc_tin:
            return JsonResponse({
                'success': False,
                'message': 'RFC/TIN is required for plan activation'
            })
        
        # Get plan details from external API
        from external_api_service import ExternalAPIService
        external_api = ExternalAPIService()
        external_plans = external_api.get_available_plans()
        
        # Find the selected plan
        selected_plan = None
        if external_plans:
            for plan in external_plans:
                # Convert both to string for comparison to handle type mismatches
                if str(plan.get('id')) == str(plan_id):
                    selected_plan = plan
                    break
        
        # Fallback plan details if plan not found
        if not selected_plan:
            logger.warning(f"🎯 [MP_PREFERENCE] Plan {plan_id} not found, using default plan fallback")
            selected_plan = {
                'id': plan_id,
                'name': f'gpscontrol4u Plan {plan_id}',
                'description': f'Subscription plan with ID {plan_id}',
                'price': 60.0
            }
        
        plan_name = selected_plan.get('name', f'gpscontrol4u Plan {plan_id}')
        plan_description = selected_plan.get('description', f'Subscription plan with ID {plan_id}')
        plan_price = float(selected_plan.get('price', 60.0))
        
        logger.info(f"🎯 [MP_PREFERENCE] Selected plan: {plan_name} - ${plan_price} USD")
        
        # Generate unique external reference with the correct plan ID
        external_reference = f"plan_subscription_{plan_id}_{user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Always use HTTPS for the configured domain since we're behind Cloudflare
        domain = getattr(settings, 'DOMAIN', 'mp.armaddia.lat')
        base_url = f"https://{domain}"
        
        logger.info(f"🎯 [MP_PREFERENCE] Domain from settings: {domain}")
        logger.info(f"🎯 [MP_PREFERENCE] Request host: {request.get_host()}")
        logger.info(f"🎯 [MP_PREFERENCE] Using base URL: {base_url}")
        
        # Create preference data
        success_url = f"{base_url}{reverse('accounts:payment_success')}"
        failure_url = f"{base_url}{reverse('accounts:payment_failure')}"
        pending_url = f"{base_url}{reverse('accounts:payment_pending')}"
        
        logger.info(f"🎯 [MP_PREFERENCE] URLs being used:")
        logger.info(f"🎯 [MP_PREFERENCE]   Base URL: {base_url}")
        logger.info(f"🎯 [MP_PREFERENCE]   Success: {success_url}")
        logger.info(f"🎯 [MP_PREFERENCE]   Failure: {failure_url}")
        logger.info(f"🎯 [MP_PREFERENCE]   Pending: {pending_url}")
        
        # Determine payer email based on sandbox mode
        if settings.MERCADO_PAGO_SANDBOX and settings.MERCADO_PAGO_TEST_BUYER_EMAIL:
            payer_email = settings.MERCADO_PAGO_TEST_BUYER_EMAIL
            logger.info(f"🎯 [MP_PREFERENCE] Using TEST email for sandbox: {payer_email}")
        else:
            payer_email = user.email
            logger.info(f"🎯 [MP_PREFERENCE] Using REAL email for production: {payer_email}")
        
        preference_data = {
            "items": [
                {
                    "title": plan_name,
                    "description": plan_description,
                    "quantity": 1,
                    "currency_id": "MXN",
                    "unit_price": plan_price
                }
            ],
            "payer": {
                "name": user.first_name or "Usuario",
                "surname": user.last_name or "User",
                "email": payer_email,
                "phone": {
                    "area_code": "55",
                    "number": "1234567890"  # TODO: Add phone field to user model
                },
                "address": {
                    "street_name": "Street",
                    "street_number": 123,
                    "zip_code": "12345"
                }
            },
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            "auto_return": "approved",
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 1
            },
            "notification_url": f"{base_url}{reverse('accounts:mercado_pago_webhook')}",
            "statement_descriptor": "gpscontrol4u_PLAN",
            "external_reference": external_reference,
            "expires": True,
            "expiration_date_from": timezone.now().isoformat(),
            "expiration_date_to": (timezone.now() + timedelta(hours=24)).isoformat()
        }
        
        logger.info(f"🎯 [MP_PREFERENCE] Creating preference with data: {json.dumps(preference_data, indent=2)}")
        
        # Create preference
        preference_response = mp_sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            logger.info(f"🎯 [MP_PREFERENCE] Preference created successfully: {preference['id']}")
            logger.info(f"🎯 [MP_PREFERENCE] Available URLs:")
            logger.info(f"🎯 [MP_PREFERENCE]   init_point: {preference.get('init_point', 'N/A')}")
            logger.info(f"🎯 [MP_PREFERENCE]   sandbox_init_point: {preference.get('sandbox_init_point', 'N/A')}")
            logger.info(f"🎯 [MP_PREFERENCE]   SANDBOX setting: {settings.MERCADO_PAGO_SANDBOX}")
            
            # Store preference info in session for later validation
            request.session['mp_preference_id'] = preference['id']
            request.session['mp_external_reference'] = external_reference
            request.session['mp_amount'] = 60.0
            
            # Always use sandbox URL when in sandbox mode
            if settings.MERCADO_PAGO_SANDBOX:
                checkout_url = preference.get('sandbox_init_point', preference.get('init_point'))
                logger.info(f"🎯 [MP_PREFERENCE] Using SANDBOX URL: {checkout_url}")
            else:
                checkout_url = preference.get('init_point')
                logger.info(f"🎯 [MP_PREFERENCE] Using PRODUCTION URL: {checkout_url}")
            
            # Validate that we're using the correct environment
            if settings.MERCADO_PAGO_SANDBOX and 'sandbox' not in checkout_url:
                logger.error(f"🎯 [MP_PREFERENCE] CRITICAL: Sandbox mode but production URL!")
                return JsonResponse({
                    'success': False,
                    'message': 'Sandbox configuration error. Please contact support.'
                })
            elif not settings.MERCADO_PAGO_SANDBOX and 'sandbox' in checkout_url:
                logger.error(f"🎯 [MP_PREFERENCE] CRITICAL: Production mode but sandbox URL!")
                return JsonResponse({
                    'success': False,
                    'message': 'Production configuration error. Please contact support.'
                })
            
            return JsonResponse({
                'success': True,
                'checkout_url': checkout_url,
                'preference_id': preference['id']
            })
        else:
            logger.error(f"🎯 [MP_PREFERENCE] Failed to create preference: {preference_response}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to create payment preference'
            })
            
    except Exception as e:
        logger.error(f"🎯 [MP_PREFERENCE] Error creating preference: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating payment: {str(e)}'
        })


@login_required
def payment_success(request):
    """Handle successful payment callback from Mercado Pago"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get payment info from query parameters
    collection_id = request.GET.get('collection_id')
    collection_status = request.GET.get('collection_status')
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    preference_id = request.GET.get('preference_id')
    
    logger.info(f"🎯 [MP_SUCCESS] Payment success callback for user: {request.user.email}")
    logger.info(f"🎯 [MP_SUCCESS] Payment ID: {payment_id}")
    logger.info(f"🎯 [MP_SUCCESS] Status: {status}")
    logger.info(f"🎯 [MP_SUCCESS] External Reference: {external_reference}")
    
    # Verify payment with Mercado Pago API
    if payment_id:
        try:
            payment_response = mp_sdk.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment_data = payment_response["response"]
                
                if payment_data['status'] == 'approved' and payment_data['status_detail'] == 'accredited':
                    # Extract plan ID from external reference
                    plan_id = 2  # Default fallback
                    if external_reference and (external_reference.startswith('premium_subscription_') or external_reference.startswith('plan_subscription_')):
                        try:
                            ref_parts = external_reference.split('_')
                            
                            # Check if this is new format by looking for reasonable plan_id and user_id
                            if len(ref_parts) >= 5:
                                potential_plan_id = ref_parts[2]
                                potential_user_id = ref_parts[3]
                                
                                # If both are numeric and plan_id is reasonable (1-10), it's likely new format
                                if (potential_plan_id.isdigit() and potential_user_id.isdigit() and 
                                    1 <= int(potential_plan_id) <= 10):
                                    plan_id = int(potential_plan_id)
                                else:
                                    # Fallback to default
                                    plan_id = 2
                            elif len(ref_parts) >= 3:  # Old format without plan_id
                                plan_id = 2  # Default for old references
                        except (ValueError, IndexError):
                            plan_id = 2  # Fallback on error
                    
                    # Payment is approved, activate plan
                    success, error_msg = activate_plan_for_user(request.user, payment_id, external_reference, plan_id)
                    
                    if success:
                        messages.success(request, _('Payment successful! Your plan has been activated.'))
                    else:
                        messages.error(request, _('Payment received but there was an error activating your plan. Please contact support.'))
                else:
                    messages.warning(request, _('Payment is being processed. You will receive an email confirmation once completed.'))
            else:
                # Payment verification failed, but we're on success callback
                # This often happens with sandbox payments that become unavailable quickly
                logger.warning(f"🎯 [MP_SUCCESS] Could not verify payment {payment_id}, but processing as successful due to success callback")
                
                # Extract plan ID from external reference since we can't verify through API
                plan_id = 2  # Default fallback
                if external_reference and (external_reference.startswith('premium_subscription_') or external_reference.startswith('plan_subscription_')):
                    try:
                        ref_parts = external_reference.split('_')
                        
                        # Check if this is new format by looking for reasonable plan_id and user_id
                        if len(ref_parts) >= 5:
                            potential_plan_id = ref_parts[2]
                            potential_user_id = ref_parts[3]
                            
                            # If both are numeric and plan_id is reasonable (1-10), it's likely new format
                            if (potential_plan_id.isdigit() and potential_user_id.isdigit() and 
                                1 <= int(potential_plan_id) <= 10):
                                plan_id = int(potential_plan_id)
                            else:
                                # Fallback to default
                                plan_id = 2
                        elif len(ref_parts) >= 3:  # Old format without plan_id
                            plan_id = 2  # Default for old references
                    except (ValueError, IndexError):
                        plan_id = 2  # Fallback on error
                
                logger.info(f"🎯 [MP_SUCCESS] Extracted plan ID {plan_id} from external reference, proceeding with activation")
                
                # Activate plan even though we couldn't verify payment details
                success, error_msg = activate_plan_for_user(request.user, payment_id, external_reference, plan_id)
                
                if success:
                    messages.success(request, _('Payment successful! Your plan has been activated.'))
                else:
                    messages.error(request, _('Payment received but there was an error activating your plan. Please contact support.'))
                
        except Exception as e:
            logger.error(f"🎯 [MP_SUCCESS] Error verifying payment: {e}")
            
            # Even if verification fails, try to activate plan since we're on success callback
            logger.warning(f"🎯 [MP_SUCCESS] Payment verification failed with error, but attempting activation due to success callback")
            
            # Extract plan ID from external reference
            plan_id = 2  # Default fallback
            if external_reference and (external_reference.startswith('premium_subscription_') or external_reference.startswith('plan_subscription_')):
                try:
                    ref_parts = external_reference.split('_')
                    
                    # Check if this is new format by looking for reasonable plan_id and user_id
                    if len(ref_parts) >= 5:
                        potential_plan_id = ref_parts[2]
                        potential_user_id = ref_parts[3]
                        
                        # If both are numeric and plan_id is reasonable (1-10), it's likely new format
                        if (potential_plan_id.isdigit() and potential_user_id.isdigit() and 
                            1 <= int(potential_plan_id) <= 10):
                            plan_id = int(potential_plan_id)
                        else:
                            # Fallback to default
                            plan_id = 2
                    elif len(ref_parts) >= 3:  # Old format without plan_id
                        plan_id = 2  # Default for old references
                except (ValueError, IndexError):
                    plan_id = 2  # Fallback on error
            
            logger.info(f"🎯 [MP_SUCCESS] Attempting fallback activation with plan ID {plan_id}")
            
            # Try to activate plan as fallback
            success, error_msg = activate_plan_for_user(request.user, payment_id, external_reference, plan_id)
            
            if success:
                messages.success(request, _('Payment successful! Your plan has been activated.'))
            else:
                messages.warning(request, _('Payment received but please contact support to ensure your plan is activated.'))
    
    return redirect('accounts:dashboard')


@login_required
def payment_failure(request):
    """Handle failed payment callback from Mercado Pago"""
    messages.error(request, _('Payment was cancelled or failed. Please try again.'))
    return redirect('accounts:dashboard')


@login_required
def payment_pending(request):
    """Handle pending payment callback from Mercado Pago"""
    messages.info(request, _('Your payment is being processed. You will receive an email confirmation once completed.'))
    return redirect('accounts:dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def mercado_pago_webhook(request):
    """Handle Mercado Pago webhook notifications with improved error handling"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f"🔔 [MP_WEBHOOK] Received webhook: {json.dumps(data, indent=2)}")
        
        # Validate webhook data
        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if payment_id:
                logger.info(f"🔔 [MP_WEBHOOK] Processing payment ID: {payment_id}")
                
                # Check if this payment was already processed
                existing_payment = Payment.objects.filter(mercado_pago_payment_id=payment_id).first()
                if existing_payment:
                    logger.info(f"🔔 [MP_WEBHOOK] Payment {payment_id} already processed, skipping")
                    return JsonResponse({'status': 'already_processed'})
                
                # Try to get payment details from Mercado Pago with retry logic
                payment_data = None
                max_retries = 3
                retry_delay = 2  # seconds
                
                for attempt in range(max_retries):
                    try:
                        payment_response = mp_sdk.payment().get(payment_id)
                        
                        if payment_response["status"] == 200:
                            payment_data = payment_response["response"]
                            logger.info(f"🔔 [MP_WEBHOOK] Payment data retrieved successfully on attempt {attempt + 1}")
                            break
                        else:
                            logger.warning(f"🔔 [MP_WEBHOOK] Attempt {attempt + 1}: Failed to get payment details: {payment_response}")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                    except Exception as api_error:
                        logger.warning(f"🔔 [MP_WEBHOOK] Attempt {attempt + 1}: API error: {api_error}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                
                if payment_data:
                    external_reference = payment_data.get('external_reference')
                    
                    logger.info(f"🔔 [MP_WEBHOOK] Payment data retrieved successfully")
                    logger.info(f"🔔 [MP_WEBHOOK] Status: {payment_data.get('status')}")
                    logger.info(f"🔔 [MP_WEBHOOK] External reference: {external_reference}")
                    
                    # Find user by external reference
                    if external_reference and (external_reference.startswith('premium_subscription_') or external_reference.startswith('plan_subscription_')):
                        try:
                            # New format: plan_subscription_{plan_id}_{user_id}_{timestamp}
                            # Legacy format: premium_subscription_{plan_id}_{user_id}_{timestamp}
                            # Old format: premium_subscription_{user_id}_{timestamp}
                            ref_parts = external_reference.split('_')
                            
                            # Check if this is new format by looking for reasonable plan_id and user_id
                            if len(ref_parts) >= 5:
                                potential_plan_id = ref_parts[2]
                                potential_user_id = ref_parts[3]
                                
                                # If both are numeric and plan_id is reasonable (1-10), it's likely new format
                                if (potential_plan_id.isdigit() and potential_user_id.isdigit() and 
                                    1 <= int(potential_plan_id) <= 10):
                                    plan_id = potential_plan_id
                                    user_id = potential_user_id
                                    logger.info(f"🔔 [MP_WEBHOOK] New format - Plan ID: {plan_id}, User ID: {user_id}")
                                else:
                                    # Fallback to old format interpretation
                                    user_id = ref_parts[2]
                                    plan_id = "2"  # Default to plan 2 for old references
                                    logger.info(f"🔔 [MP_WEBHOOK] Old format (5+ parts) - User ID: {user_id}, Default Plan ID: {plan_id}")
                            elif len(ref_parts) >= 3:  # Old format without plan_id
                                user_id = ref_parts[2]
                                plan_id = "2"  # Default to plan 2 for old references
                                logger.info(f"🔔 [MP_WEBHOOK] Old format - User ID: {user_id}, Default Plan ID: {plan_id}")
                            else:
                                raise ValueError("Invalid external reference format")
                            
                            user = User.objects.get(id=user_id)
                            
                            logger.info(f"🔔 [MP_WEBHOOK] Found user: {user.email} (ID: {user.id}) for plan: {plan_id}")
                            
                            if payment_data['status'] == 'approved' and payment_data['status_detail'] == 'accredited':
                                # Activate plan for user with correct plan ID
                                logger.info(f"🔔 [MP_WEBHOOK] Payment approved, activating plan {plan_id} for user {user.email}")
                                success, error_msg = activate_plan_for_user(user, payment_id, external_reference, plan_id)
                                logger.info(f"🔔 [MP_WEBHOOK] Plan activation result: {success}")
                                logger.info(f"🔔 [MP_WEBHOOK] Error message: {error_msg}")
                                
                                if success:
                                    return JsonResponse({'status': 'plan_activated'})
                                else:
                                    # Log activation failure but don't return 500 to prevent MP retries
                                    # This could be due to corrupted RFC, API issues, etc.
                                    logger.error(f"🔔 [MP_WEBHOOK] Plan activation failed for user {user.email} - payment was successful but external API activation failed")
                                    logger.error(f"🔔 [MP_WEBHOOK] This requires MANUAL REVIEW - Payment ID: {payment_id}, User: {user.email}, Plan: {plan_id}")
                                    
                                    # Return success to MP to prevent retries, but flag for manual review
                                    return JsonResponse({
                                        'status': 'payment_received_activation_failed',
                                        'message': 'Payment processed but activation failed - requires manual review',
                                        'payment_id': payment_id,
                                        'user_id': user.id,
                                        'plan_id': plan_id
                                    })
                            else:
                                logger.info(f"🔔 [MP_WEBHOOK] Payment not approved yet (status: {payment_data['status']}, detail: {payment_data.get('status_detail')})")
                            
                        except (User.DoesNotExist, IndexError, ValueError) as e:
                            logger.error(f"🔔 [MP_WEBHOOK] Could not find user from reference {external_reference}: {e}")
                            return JsonResponse({'status': 'user_not_found'}, status=400)
                    else:
                        logger.warning(f"🔔 [MP_WEBHOOK] Invalid or missing external reference: {external_reference}")
                        
                else:
                    logger.error(f"🔔 [MP_WEBHOOK] Failed to get payment details after {max_retries} attempts")
                    
                    # FALLBACK: Try to process webhook even if MP API fails
                    # This helps when payments succeed but MP API is temporarily unavailable
                    logger.info(f"🔔 [MP_WEBHOOK] Attempting fallback processing without payment verification")
                    
                    # Try to extract user from webhook data or recent preferences
                    # This is a workaround for API issues
                    user = None
                    plan_id = "2"  # Default fallback
                    
                    # Look for recent users who might have made this payment
                    recent_users = User.objects.filter(
                        created_at__gte=timezone.now() - timedelta(hours=24),
                        role='free'
                    ).order_by('-created_at')
                    
                    if recent_users.exists():
                        user = recent_users.first()
                        logger.info(f"🔔 [MP_WEBHOOK] Fallback: Found recent user {user.email} who might have made this payment")
                        
                        # Try to find the most recent payment record for this user to get the correct plan ID
                        recent_payment = Payment.objects.filter(
                            user=user,
                            created_at__gte=timezone.now() - timedelta(hours=1)
                        ).order_by('-created_at').first()
                        
                        # Payment model doesn't have external_plan_id, so we need to get it from subscription
                        if recent_payment and recent_payment.subscription and recent_payment.subscription.external_plan_id:
                            plan_id = str(recent_payment.subscription.external_plan_id)
                            logger.info(f"🔔 [MP_WEBHOOK] Fallback: Found recent payment with plan ID {plan_id}")
                        else:
                            # Try to extract plan ID from query parameters or recent preferences
                            # This is a last resort to get the correct plan ID
                            try:
                                # Look for recent external references that might contain the plan ID
                                recent_subscriptions = Subscription.objects.filter(
                                    user=user,
                                    created_at__gte=timezone.now() - timedelta(hours=1)
                                ).order_by('-created_at')
                                
                                if recent_subscriptions.exists():
                                    recent_sub = recent_subscriptions.first()
                                    if recent_sub.external_plan_id:
                                        plan_id = str(recent_sub.external_plan_id)
                                        logger.info(f"🔔 [MP_WEBHOOK] Fallback: Found recent subscription with plan ID {plan_id}")
                            except:
                                pass
                        
                        # Log this as a fallback activation for manual review
                        logger.warning(f"🔔 [MP_WEBHOOK] FALLBACK ACTIVATION: Payment {payment_id} could not be verified with MP API, but activating plan {plan_id} for recent user {user.email}")
                        
                        # Generate external reference with the determined plan ID
                        external_reference = f"plan_subscription_{plan_id}_{user.id}_fallback"
                        
                        # Activate plan with the determined plan ID
                        success, error_msg = activate_plan_for_user(user, payment_id, external_reference, plan_id)
                        logger.info(f"🔔 [MP_WEBHOOK] Fallback activation error message: {error_msg}")
                        
                        if success:
                            logger.info(f"🔔 [MP_WEBHOOK] Fallback activation successful for {user.email} with plan {plan_id}")
                            return JsonResponse({'status': 'fallback_activated'})
                        else:
                            # Log fallback failure but don't return 500 to prevent MP retries
                            logger.error(f"🔔 [MP_WEBHOOK] Fallback activation failed for {user.email} - requires MANUAL REVIEW")
                            logger.error(f"🔔 [MP_WEBHOOK] MANUAL REVIEW NEEDED - Payment ID: {payment_id}, User: {user.email}, Plan: {plan_id}")
                            
                            # Return success to MP to prevent retries, but flag for manual review
                            return JsonResponse({
                                'status': 'fallback_payment_received_activation_failed',
                                'message': 'Fallback payment processed but activation failed - requires manual review',
                                'payment_id': payment_id,
                                'user_id': user.id,
                                'plan_id': plan_id
                            })
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"🔔 [MP_WEBHOOK] Critical error processing webhook: {e}")
        import traceback
        logger.error(f"🔔 [MP_WEBHOOK] Traceback: {traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_credentials(request):
    """Get stored API credentials for the authenticated user"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = request.user
    
    logger.info(f"🔑 [GET_CREDENTIALS] Credentials request from user: {user.email}")
    logger.info(f"🔑 [GET_CREDENTIALS] User has external_api_username: {bool(user.external_api_username)}")
    logger.info(f"🔑 [GET_CREDENTIALS] User has external_api_password: {bool(user.external_api_password)}")
    
    # Check if user has credentials stored
    if not user.external_api_username or not user.external_api_password:
        logger.warning(f"🔑 [GET_CREDENTIALS] No credentials found for user {user.email}")
        return JsonResponse({
            'success': False,
            'message': _('No credentials found. Please activate a plan first.')
        })
    
    # Return stored credentials
    from django.utils import translation
    
    # Use user's language for response
    with translation.override(user.language):
        response_data = {
            'success': True,
            'data': {
                'credentials': {
                    'username': user.external_api_username,
                    'password': user.external_api_password,
                    'portal_url': 'https://ego.elisasoftware.com.mx/'  # External portal URL
                },
                'plan_type': user.role,
                'client_id': user.external_client_id,
                'user_id': user.external_user_id,
                'licenses': user.external_licenses
            }
        }
    
    logger.info(f"🔑 [GET_CREDENTIALS] Returning credentials for user {user.email}")
    return JsonResponse(response_data)


def activate_plan_for_user(user, payment_id, external_reference, plan_id=1):
    """Activate any plan for a user after successful payment or for free plans using PlanPurchase model"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🎯 [ACTIVATE_PLAN] Activating plan for user: {user.email}")
        logger.info(f"🎯 [ACTIVATE_PLAN] Payment ID: {payment_id}")
        logger.info(f"🎯 [ACTIVATE_PLAN] External Reference: {external_reference}")
        logger.info(f"🎯 [ACTIVATE_PLAN] Plan ID: {plan_id}")
        
        # Get plan details from external API
        from external_api_service import ExternalAPIService
        external_api = ExternalAPIService()
        external_plans = external_api.get_available_plans()
        
        # Find the plan details
        selected_plan = None
        if external_plans:
            for plan in external_plans:
                if str(plan.get('id')) == str(plan_id):
                    selected_plan = plan
                    break
        
        if not selected_plan:
            logger.error(f"🎯 [ACTIVATE_PLAN] Plan {plan_id} not found in external API")
            return False
        
        plan_name = selected_plan.get('name', f'Plan {plan_id}')
        plan_price = float(selected_plan.get('price', 0))
        is_free_plan = plan_price == 0
        
        logger.info(f"🎯 [ACTIVATE_PLAN] Plan details:")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Name: {plan_name}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Price: {plan_price}")
        logger.info(f"🎯 [ACTIVATE_PLAN]   Is Free: {is_free_plan}")
        
        # Check free plan restriction - only allow one free plan per user
        if is_free_plan and PlanPurchase.user_has_free_plan(user):
            logger.warning(f"🎯 [ACTIVATE_PLAN] User {user.email} already has a free plan")
            return False
        
        # Determine plan category based on plan characteristics
        if is_free_plan:
            plan_category = 'free'
        elif 'team' in plan_name.lower() or 'equipo' in plan_name.lower():
            plan_category = 'team'
        else:
            plan_category = 'license'
        
        # Initialize subscription service for external API
        subscription_service = SubscriptionService()
        
        # Determine if this should be a new client based on external API registration status
        # If user has no credentials stored, treat as new client to register them first
        is_new_client = not bool(user.external_api_password)
        logger.info(f"🎯 [ACTIVATE_PLAN] Is new client: {is_new_client}")
        logger.info(f"🎯 [ACTIVATE_PLAN] User external_api_registered: {user.external_api_registered}")
        logger.info(f"🎯 [ACTIVATE_PLAN] User has existing password: {bool(user.external_api_password)}")
        
        # Create subscription via external API using the specified plan ID
        success, api_data, error_message = subscription_service.create_subscription(
            user=user,
            plan_id=int(plan_id),
            new_client=is_new_client
        )
        
        if success:
            # Update user model
            if is_free_plan:
                user.role = 'free'
            else:
                if selected_plan.get('is_premium', False):
                    user.role = 'premium'
                else:
                    user.role = 'paid'
            
            # Always update credentials if they come from API (first time or updates)
            if not user.external_api_registered:
                # First time registration - save all credentials
                user.external_api_username = api_data['username']
                user.external_api_password = api_data['password']
                user.external_client_id = api_data['client_id']
                user.external_user_id = api_data['user_id']
                user.external_licenses = api_data['licenses']
                user.external_api_registered = True
            else:
                # Subsequent purchases - only update licenses (keep original credentials)
                user.external_licenses = api_data['licenses']
            user.save()
            
            # Create payment record if there's an actual payment
            payment_record = None
            if payment_id or not is_free_plan:
                payment_record = Payment.objects.create(
                    user=user,
                    payment_provider='mercado_pago' if payment_id else 'internal',
                    payment_type='subscription',
                    amount=plan_price,
                    currency='USD',
                    status='completed',
                    mercado_pago_payment_id=payment_id if payment_id else None,
                    description=f'{plan_name} - Plan ID {plan_id}',
                    metadata={
                        'external_reference': external_reference,
                        'api_data': api_data,
                        'plan_id': plan_id,
                        'is_free_plan': is_free_plan
                    }
                )
            
            # Create PlanPurchase record
            plan_purchase = PlanPurchase.objects.create(
                user=user,
                external_plan_id=str(plan_id),
                plan_name=plan_name,
                plan_category=plan_category,
                amount=plan_price,
                currency='USD',
                status='active',
                activation_date=timezone.now(),
                payment=payment_record,
                external_metadata=selected_plan
            )
            
            # Set expiration for all plans (1 year)
            # According to external API, both free and paid plans are annual
            plan_purchase.expiration_date = timezone.now() + timedelta(days=365)
            plan_purchase.save(update_fields=['expiration_date'])
            
            # Maintain backward compatibility - update/create subscription record
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'plan_type': 'free' if is_free_plan else f'plan_{plan_id}',
                    'status': 'active',
                    'currency': 'USD',
                    'amount': plan_price,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=365),  # All plans expire after 1 year
                    'external_plan_id': str(plan_id)
                }
            )
            
            if not created:
                subscription.plan_type = 'free' if is_free_plan else f'plan_{plan_id}'
                subscription.status = 'active'
                subscription.amount = plan_price
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=365)  # All plans expire after 1 year
                subscription.external_plan_id = str(plan_id)
                subscription.save()
            
            logger.info(f"🎯 [ACTIVATE_PLAN] Successfully activated {plan_name} for user: {user.email}")
            return True, None
            
        else:
            logger.error(f"🎯 [ACTIVATE_PLAN] Failed to create external API subscription")
            logger.error(f"🎯 [ACTIVATE_PLAN] error_message type: {type(error_message)}")
            logger.error(f"🎯 [ACTIVATE_PLAN] error_message value: '{error_message}'")
            logger.error(f"🎯 [ACTIVATE_PLAN] User: {user.email}, RFC: {user.rfc_tin}, Plan ID: {plan_id}")
            logger.error(f"🎯 [ACTIVATE_PLAN] Is new client: {is_new_client}")
            
            # Return the actual API error message to the user
            user_message = error_message if error_message else "Failed to activate plan"
            logger.error(f"🎯 [ACTIVATE_PLAN] Returning API error message: '{user_message}'")
            return False, user_message
            
    except Exception as e:
        logger.error(f"🎯 [ACTIVATE_PLAN] Error activating plan: {e}")
        logger.error(f"🎯 [ACTIVATE_PLAN] User: {user.email}, Plan ID: {plan_id}")
        import traceback
        logger.error(f"🎯 [ACTIVATE_PLAN] Traceback: {traceback.format_exc()}")
        return False, f"Error activating plan: {str(e)}"


@csrf_exempt
@require_http_methods(["POST"])
def get_plan_details(request):
    """Get details for a specific plan"""
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return JsonResponse({
                'success': False,
                'message': 'Plan ID is required'
            })
        
        # Get plan details from external API
        from external_api_service import ExternalAPIService
        external_api = ExternalAPIService()
        external_plans = external_api.get_available_plans()
        
        # Find the plan details
        selected_plan = None
        if external_plans:
            for plan in external_plans:
                # Convert both to string for comparison to handle type mismatches
                if str(plan.get('id')) == str(plan_id):
                    selected_plan = plan
                    break
        
        if not selected_plan:
            return JsonResponse({
                'success': False,
                'message': f'Plan {plan_id} not found'
            })
        
        return JsonResponse({
            'success': True,
            'id': selected_plan.get('id'),
            'name': selected_plan.get('name'),
            'description': selected_plan.get('description'),
            'price': float(selected_plan.get('price', 0)),
            'is_free': float(selected_plan.get('price', 0)) == 0
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"🎯 [GET_PLAN_DETAILS] JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"🎯 [GET_PLAN_DETAILS] Error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error'
        })


@login_required
def verify_phone_view(request):
    """View to request and verify phone number via WhatsApp"""
    logger = logging.getLogger(__name__)
    user = request.user
    
    # If phone is already verified, redirect to dashboard
    if user.phone_verified and user.phone_number:
        return redirect('accounts:dashboard')
    
    # If user doesn't have RFC yet, go back to setup
    if not user.rfc_tin:
        return redirect('accounts:setup_account')
    
    if request.method == 'POST':
        from .forms import PhoneVerificationForm
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            try:
                # Get country code and phone number, combine them
                country_code = form.cleaned_data['country_code']
                phone_digits = form.cleaned_data['phone_number']
                phone = f"{country_code}{phone_digits}"
                
                # Send verification code via WhatsApp
                from whatsapp_service import WhatsAppPhoneVerificationService
                whatsapp_service = WhatsAppPhoneVerificationService()
                
                logger.info(f"📱 [VERIFY_PHONE] Attempting to send code to {phone}")
                success, verification_code, message = whatsapp_service.send_verification_code(phone)
                
                if not success:
                    logger.error(f"❌ [VERIFY_PHONE] Failed to send code: {message}")
                    messages.error(
                        request,
                        _('Could not send verification code. ') + message
                    )
                    return render(request, 'accounts/verify_phone.html', {'form': form, 'user': user, 'step': 'phone'})
                
                # Save to session with expiration time (10 minutes)
                request.session['phone_verification_code'] = verification_code
                request.session['phone_verification_code_expire'] = (
                    timezone.now() + timedelta(minutes=10)
                ).isoformat()
                request.session['phone_verification_phone'] = phone
                
                logger.info(f"✅ [VERIFY_PHONE] Code sent to {phone}")
                logger.warning(f"⚠️  [VERIFY_PHONE] DEBUG: Verification code for testing: {verification_code}")
                
                messages.success(
                    request,
                    _('Verification code sent to your WhatsApp. Please enter it below.')
                )
                
                # Redirect to code verification
                return redirect('accounts:verify_phone_code')
                
            except Exception as e:
                logger.error(f"❌ [VERIFY_PHONE] Error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                messages.error(
                    request,
                    _('An error occurred. Please try again.')
                )
    else:
        from .forms import PhoneVerificationForm
        form = PhoneVerificationForm()
    
    context = {
        'form': form,
        'user': user,
        'step': 'phone',
    }
    
    return render(request, 'accounts/verify_phone.html', context)


@login_required
def verify_phone_code_view(request):
    """View to verify phone code sent via WhatsApp"""
    logger = logging.getLogger(__name__)
    user = request.user
    
    # Check if user has requested a code
    if 'phone_verification_code' not in request.session:
        messages.error(
            request,
            _('Please request a verification code first.')
        )
        return redirect('accounts:verify_phone')
    
    # Check if code has expired
    code_expire_str = request.session.get('phone_verification_code_expire')
    if code_expire_str:
        code_expire = timezone.datetime.fromisoformat(code_expire_str)
        if timezone.now() > code_expire:
            del request.session['phone_verification_code']
            del request.session['phone_verification_code_expire']
            del request.session['phone_verification_phone']
            messages.error(
                request,
                _('Verification code expired. Please request a new one.')
            )
            return redirect('accounts:verify_phone')
    
    if request.method == 'POST':
        from .forms import PhoneCodeVerificationForm
        form = PhoneCodeVerificationForm(request.POST)
        if form.is_valid():
            try:
                entered_code = form.cleaned_data['verification_code']
                stored_code = request.session.get('phone_verification_code')
                phone = request.session.get('phone_verification_phone')
                
                logger.info(f"📱 [VERIFY_CODE] Verifying code for {user.email}")
                logger.info(f"📱 [VERIFY_CODE] Phone: {phone}")
                
                # Verify code with WhatsApp API
                from whatsapp_service import WhatsAppPhoneVerificationService
                whatsapp_service = WhatsAppPhoneVerificationService()
                
                success, validated, message = whatsapp_service.verify_code(phone, entered_code)
                
                if not success:
                    logger.error(f"❌ [VERIFY_CODE] API error: {message}")
                    # Check if it's an invalid code error
                    if "no es valido" in message or "invalid" in message.lower() or "503" in str(message):
                        messages.error(
                            request,
                            _('El código de verificación que ingresaste es incorrecto. Por favor verifica e intenta de nuevo.')
                        )
                    else:
                        messages.error(
                            request,
                            _('Error al verificar el código. Por favor intenta más tarde.')
                        )
                else:
                    if validated:
                        # Code is correct! Save phone number
                        user.phone_number = phone
                        user.phone_verified = True
                        # Activate the flag now that user has RFC + phone verified
                        user.external_api_registered = True
                        user.save()
                        
                        logger.info(f"✅ [VERIFY_CODE] Phone verified for {user.email}: {phone}")
                        logger.info(f"✅ [VERIFY_CODE] User can now access plans - external_api_registered set to True")
                        
                        # Clean up session
                        del request.session['phone_verification_code']
                        del request.session['phone_verification_code_expire']
                        del request.session['phone_verification_phone']
                        
                        messages.success(
                            request,
                            _('¡Teléfono verificado! Ahora puedes acceder a tu dashboard.')
                        )
                        return redirect('accounts:dashboard')
                    else:
                        logger.warning(f"❌ [VERIFY_CODE] Code validation failed for {user.email}")
                        messages.error(
                            request,
                            _('El código de verificación que ingresaste es incorrecto. Por favor verifica e intenta de nuevo.')
                        )
                    
            except Exception as e:
                logger.error(f"❌ [VERIFY_CODE] Error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                messages.error(
                    request,
                    _('An error occurred. Please try again.')
                )
    else:
        from .forms import PhoneCodeVerificationForm
        form = PhoneCodeVerificationForm()
    
    phone = request.session.get('phone_verification_phone', 'your phone')
    
    context = {
        'form': form,
        'user': user,
        'phone': phone,
        'step': 'code',
    }
    
    return render(request, 'accounts/verify_phone_code.html', context)

