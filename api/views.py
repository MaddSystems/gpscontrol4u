from django.shortcuts import render
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import Q

from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserProfileSerializer,
    LoginSerializer, FormSerializer, DataRecordSerializer, 
    FormTemplateSerializer, SubscriptionSerializer, PaymentSerializer,
    PricingPlanSerializer
)
from accounts.models import User, UserProfile
from gpscontrol4u.models import Form, DataRecord, FormTemplate
from payments.models import Subscription, Payment, PricingPlan


class UserRegistrationView(generics.CreateAPIView):
    """Register a new user"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """Get and update extended user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class FormViewSet(viewsets.ModelViewSet):
    """CRUD operations for gpscontrol4u forms"""
    serializer_class = FormSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Free users can only see predefined forms and their own forms
        if user.role == 'free':
            return Form.objects.filter(
                Q(is_predefined=True) | Q(user=user)
            ).filter(is_active=True)
        
        # Premium users can see all their forms and predefined forms
        return Form.objects.filter(
            Q(user=user) | Q(is_predefined=True)
        ).filter(is_active=True)
    
    def perform_create(self, serializer):
        # Check if user can create forms
        if self.request.user.role == 'free':
            # Free users cannot create custom forms
            raise permissions.PermissionDenied("Upgrade to Premium to create custom forms")
        
        serializer.save(user=self.request.user)


class DataRecordViewSet(viewsets.ModelViewSet):
    """CRUD operations for data records"""
    serializer_class = DataRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DataRecord.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if user can access the form
        form = serializer.validated_data['form']
        if not form.can_user_access(self.request.user):
            raise permissions.PermissionDenied("You don't have access to this form")
        
        serializer.save(user=self.request.user)


class FormTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to form templates"""
    serializer_class = FormTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = FormTemplate.objects.filter(is_active=True)
        
        # Filter based on user's subscription level
        if user.role == 'free':
            queryset = queryset.filter(is_premium_only=False)
        
        return queryset


class SubscriptionView(generics.RetrieveAPIView):
    """Get user's subscription status"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        subscription, created = Subscription.objects.get_or_create(
            user=self.request.user,
            defaults={'plan_type': 'free', 'status': 'active'}
        )
        return subscription


class PaymentHistoryView(generics.ListAPIView):
    """Get user's payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PricingPlansView(generics.ListAPIView):
    """Get available pricing plans"""
    serializer_class = PricingPlanSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return PricingPlan.objects.filter(is_active=True)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_language(request):
    """Update user's language preference"""
    language = request.data.get('language')
    
    if language not in ['en', 'es']:
        return Response({'error': 'Invalid language'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.language = language
    user.save()
    
    return Response({'message': 'Language updated successfully', 'language': language})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def link_ios_app(request):
    """Link user account with gpscontrol4u iOS app"""
    ios_user_id = request.data.get('ios_user_id')
    
    if not ios_user_id:
        return Response({'error': 'iOS user ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.ios_app_user_id = ios_user_id
    user.save()
    
    return Response({'message': 'iOS app linked successfully'})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """API health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'Marketplace API is running',
        'version': '1.0.0'
    })
