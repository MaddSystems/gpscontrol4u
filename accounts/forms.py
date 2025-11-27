from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile
import re


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email address')
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First name'),
            'autofocus': True
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last name')
        })
    )
    language = forms.ChoiceField(
        choices=User.LANGUAGE_CHOICES,
        required=True,
        initial='es',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    accepted_terms = forms.BooleanField(
        required=True,
        label=_('I have read and accept the Terms and Conditions'),
        error_messages={'required': _('You must accept the Terms and Conditions to register.')}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'language', 'password1', 'password2', 'accepted_terms')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Password')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirm password')
        })
    
    def clean_email(self):
        """Custom email validation that allows unverified users to re-register"""
        email = self.cleaned_data.get('email')
        
        if email:
            existing_user = User.objects.filter(email=email).first()
            
            # Only raise validation error if user exists AND is verified
            if existing_user and existing_user.email_verified:
                raise forms.ValidationError(
                    _('A verified account with this email already exists. Please use the login form.')
                )
        
        return email
    
    def clean(self):
        """Override clean to handle unique email constraint for unverified users"""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        if email:
            existing_user = User.objects.filter(email=email).first()
            
            # If user exists but is not verified, we'll handle this in the view
            # Don't raise validation error here for unverified users
            if existing_user and not existing_user.email_verified:
                # Remove any unique constraint errors for email
                if 'email' in self._errors:
                    del self._errors['email']
        
        return cleaned_data
    
    def save(self, commit=True):
        # Don't save if user already exists (will be handled in view)
        email = self.cleaned_data.get('email')
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user and not existing_user.email_verified:
            # Return the existing user, will be updated in the view
            return existing_user
        
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create user profile if it doesn't exist
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user)
        return user


class UserLoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email address'),
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password'),
            'required': True
        })
    )


class UserProfileForm(forms.ModelForm):
    """User profile edit form"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'language')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
        }


class UserProfileDetailsForm(forms.ModelForm):
    """Extended user profile form"""
    
    class Meta:
        model = UserProfile
        fields = ('phone', 'country', 'timezone', 'marketing_emails')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'marketing_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RFCTINForm(forms.Form):
    """Form to collect RFC/TIN for external API registration"""
    rfc_tin = forms.CharField(
        max_length=20,
        required=True,
        label=_('RFC/TIN Number'),
        help_text=_('Enter your RFC (Mexico) or TIN number to enable app access'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('RFC/TIN number'),
            'pattern': '[A-Za-z0-9]+',
        })
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        label=_('I accept the terms and conditions'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_rfc_tin(self):
        rfc_tin = self.cleaned_data.get('rfc_tin', '').upper().strip()
        # Basic validation - only alphanumeric characters
        if not re.match(r'^[A-Z0-9]+$', rfc_tin):
            raise forms.ValidationError(_('RFC/TIN must contain only letters and numbers'))
        # Length validation
        if len(rfc_tin) < 8 or len(rfc_tin) > 20:
            raise forms.ValidationError(_('RFC/TIN must be between 8 and 20 characters'))

        # External API validation
        from accounts.rfc_validator import RFCValidatorService
        validator = RFCValidatorService()
        is_valid, error = validator.validate_rfc(rfc_tin)
        if not is_valid:
            raise forms.ValidationError(error)

        return rfc_tin


class PhoneVerificationForm(forms.Form):
    """Form to collect and verify phone number with country code"""
    
    COUNTRY_CODES = [
        ('+52', '🇲🇽 Mexico (+52)'),
        ('+1', '🇺🇸 United States (+1)'),
        ('+1', '🇨🇦 Canada (+1)'),
        ('+34', '🇪🇸 Spain (+34)'),
        ('+55', '🇧🇷 Brazil (+55)'),
        ('+56', '🇨🇱 Chile (+56)'),
        ('+57', '🇨🇴 Colombia (+57)'),
        ('+54', '🇦🇷 Argentina (+54)'),
    ]
    
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        required=True,
        initial='+52',
        label=_('Country Code'),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        label=_('Phone number'),
        help_text='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '',
            'type': 'tel',
            'pattern': '[0-9]{10}',
            'maxlength': '10',
        })
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        # Only allow 10 digits
        if not phone.isdigit():
            raise forms.ValidationError(_('Phone number must contain only digits'))
        if len(phone) != 10:
            raise forms.ValidationError(_('Phone number must be exactly 10 digits'))
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get('country_code')
        phone_number = cleaned_data.get('phone_number')
        
        if country_code and phone_number:
            # Combine for validation
            full_phone = f'{country_code}{phone_number}'
            cleaned_data['full_phone'] = full_phone
        
        return cleaned_data


class PhoneCodeVerificationForm(forms.Form):
    """Form to verify phone code sent via WhatsApp"""
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        label=_('Verification code'),
        help_text=_('Ingresa el código de 6 dígitos enviado a tu WhatsApp'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('000000'),
            'maxlength': '6',
            'pattern': '[0-9]{6}',
        })
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code', '').strip()
        if not re.match(r'^[0-9]{6}$', code):
            raise forms.ValidationError(_('Verification code must be 6 digits'))
        return code
