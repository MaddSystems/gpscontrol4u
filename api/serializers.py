from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User, UserProfile
from gpscontrol4u.models import Form, DataRecord, FormTemplate
from payments.models import Subscription, Payment, PricingPlan


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm', 'language')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserSerializer(serializers.ModelSerializer):
    is_premium = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'language', 
                 'ios_app_user_id', 'is_premium', 'created_at')
        read_only_fields = ('id', 'role', 'created_at')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('phone', 'country', 'timezone', 'marketing_emails')


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class FormSerializer(serializers.ModelSerializer):
    can_user_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Form
        fields = ('id', 'form_name', 'form_structure', 'language', 'is_predefined', 
                 'is_active', 'created_at', 'updated_at', 'can_user_access')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_predefined')
    
    def get_can_user_access(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_user_access(request.user)
        return False
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DataRecordSerializer(serializers.ModelSerializer):
    form_name = serializers.CharField(source='form.form_name', read_only=True)
    
    class Meta:
        model = DataRecord
        fields = ('id', 'form', 'form_name', 'data_content', 'language', 
                 'latitude', 'longitude', 'submitted_at', 'updated_at')
        read_only_fields = ('id', 'submitted_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FormTemplateSerializer(serializers.ModelSerializer):
    can_user_access = serializers.SerializerMethodField()
    
    class Meta:
        model = FormTemplate
        fields = ('id', 'name', 'description', 'category', 'template_structure', 
                 'language', 'is_premium_only', 'can_user_access')
    
    def get_can_user_access(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_user_access(request.user)
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'plan_type', 'status', 'currency', 'amount', 
                 'start_date', 'end_date', 'created_at')
        read_only_fields = ('id', 'created_at')


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_provider', 'payment_type', 'amount', 'currency', 
                 'status', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class PricingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = ('id', 'plan_name', 'plan_type', 'currency', 'amount', 
                 'max_forms', 'max_records_per_form', 'analytics_enabled', 
                 'export_enabled', 'priority_support')
