from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, UserProfile
from gpscontrol4u.models import Form, FormTemplate, DataRecord
from payments.models import Subscription, PricingPlan, Payment
import json


class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create pricing plans
        self.create_pricing_plans()
        
        # Create form templates
        self.create_form_templates()
        
        # Create sample users
        self.create_sample_users()
        
        # Create sample forms and data
        self.create_sample_forms_and_data()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
    
    def create_pricing_plans(self):
        """Create pricing plans for USD and MXN"""
        self.stdout.write('Creating pricing plans...')
        
        # Free plan (USD)
        PricingPlan.objects.get_or_create(
            plan_type='free',
            currency='USD',
            defaults={
                'plan_name': 'Free Plan',
                'amount': 0.00,
                'max_forms': 0,
                'max_records_per_form': 100,
                'analytics_enabled': False,
                'export_enabled': False,
                'priority_support': False,
            }
        )
        
        # Premium plan (USD)
        PricingPlan.objects.get_or_create(
            plan_type='premium_monthly',
            currency='USD',
            defaults={
                'plan_name': 'Premium Monthly (USD)',
                'amount': 9.99,
                'max_forms': 0,  # 0 means unlimited
                'max_records_per_form': 10000,
                'analytics_enabled': True,
                'export_enabled': True,
                'priority_support': True,
            }
        )
        
        # Premium plan (MXN)
        PricingPlan.objects.get_or_create(
            plan_type='premium_monthly',
            currency='MXN',
            defaults={
                'plan_name': 'Premium Mensual (MXN)',
                'amount': 199.00,
                'max_forms': 0,  # 0 means unlimited
                'max_records_per_form': 10000,
                'analytics_enabled': True,
                'export_enabled': True,
                'priority_support': True,
            }
        )
    
    def create_form_templates(self):
        """Create predefined form templates"""
        self.stdout.write('Creating form templates...')
        
        # Customer Survey (English)
        survey_structure = {
            "fields": [
                {"type": "text", "name": "customer_name", "label": "Customer Name", "required": True},
                {"type": "email", "name": "email", "label": "Email Address", "required": True},
                {"type": "select", "name": "satisfaction", "label": "How satisfied are you?", 
                 "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"], "required": True},
                {"type": "textarea", "name": "comments", "label": "Additional Comments", "required": False},
                {"type": "number", "name": "rating", "label": "Rate us (1-10)", "min": 1, "max": 10, "required": True}
            ]
        }
        
        FormTemplate.objects.get_or_create(
            name='Customer Survey',
            language='en',
            defaults={
                'description': 'A comprehensive customer satisfaction survey',
                'category': 'survey',
                'template_structure': survey_structure,
                'is_premium_only': False,
            }
        )
        
        # Encuesta de Cliente (Spanish)
        survey_structure_es = {
            "fields": [
                {"type": "text", "name": "nombre_cliente", "label": "Nombre del Cliente", "required": True},
                {"type": "email", "name": "email", "label": "Correo Electrónico", "required": True},
                {"type": "select", "name": "satisfaccion", "label": "¿Qué tan satisfecho está?", 
                 "options": ["Muy Satisfecho", "Satisfecho", "Neutral", "Insatisfecho", "Muy Insatisfecho"], "required": True},
                {"type": "textarea", "name": "comentarios", "label": "Comentarios Adicionales", "required": False},
                {"type": "number", "name": "calificacion", "label": "Califíquenos (1-10)", "min": 1, "max": 10, "required": True}
            ]
        }
        
        FormTemplate.objects.get_or_create(
            name='Encuesta de Cliente',
            language='es',
            defaults={
                'description': 'Una encuesta completa de satisfacción del cliente',
                'category': 'survey',
                'template_structure': survey_structure_es,
                'is_premium_only': False,
            }
        )
        
        # Inspection Form (Premium)
        inspection_structure = {
            "fields": [
                {"type": "text", "name": "inspector_name", "label": "Inspector Name", "required": True},
                {"type": "date", "name": "inspection_date", "label": "Inspection Date", "required": True},
                {"type": "text", "name": "location", "label": "Location", "required": True},
                {"type": "select", "name": "status", "label": "Overall Status", 
                 "options": ["Pass", "Fail", "Conditional Pass"], "required": True},
                {"type": "checkbox", "name": "safety_items", "label": "Safety Items Checked", 
                 "options": ["Fire Extinguisher", "Emergency Exits", "First Aid Kit", "Safety Signs"], "required": False},
                {"type": "textarea", "name": "notes", "label": "Inspector Notes", "required": False},
                {"type": "file", "name": "photos", "label": "Photos", "required": False}
            ]
        }
        
        FormTemplate.objects.get_or_create(
            name='Safety Inspection',
            language='en',
            defaults={
                'description': 'Comprehensive safety inspection checklist',
                'category': 'inspection',
                'template_structure': inspection_structure,
                'is_premium_only': True,
            }
        )
    
    def create_sample_users(self):
        """Create sample users for testing"""
        self.stdout.write('Creating sample users...')
        
        # Free user (USA)
        free_user, created = User.objects.get_or_create(
            email='free@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'language': 'en',
                'role': 'free',
            }
        )
        if created:
            free_user.set_password('password123')
            free_user.save()
            UserProfile.objects.create(user=free_user, country='US')
            Subscription.objects.create(
                user=free_user,
                plan_type='free',
                status='active',
                currency='USD'
            )
        
        # Premium user (USA)
        premium_user, created = User.objects.get_or_create(
            email='premium@example.com',
            defaults={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'language': 'en',
                'role': 'premium',
            }
        )
        if created:
            premium_user.set_password('password123')
            premium_user.save()
            UserProfile.objects.create(user=premium_user, country='US')
            Subscription.objects.create(
                user=premium_user,
                plan_type='premium_monthly',
                status='active',
                currency='USD',
                amount=9.99,
                start_date=timezone.now(),
            )
        
        # Premium user (Mexico)
        premium_user_mx, created = User.objects.get_or_create(
            email='premium@ejemplo.com',
            defaults={
                'first_name': 'Carlos',
                'last_name': 'González',
                'language': 'es',
                'role': 'premium',
            }
        )
        if created:
            premium_user_mx.set_password('password123')
            premium_user_mx.save()
            UserProfile.objects.create(user=premium_user_mx, country='MX')
            Subscription.objects.create(
                user=premium_user_mx,
                plan_type='premium_monthly',
                status='active',
                currency='MXN',
                amount=199.00,
                start_date=timezone.now(),
            )
    
    def create_sample_forms_and_data(self):
        """Create sample forms and data records"""
        self.stdout.write('Creating sample forms and data...')
        
        # Create predefined forms from templates
        templates = FormTemplate.objects.all()
        for template in templates:
            Form.objects.get_or_create(
                form_name=template.name,
                language=template.language,
                is_predefined=True,
                defaults={
                    'user_id': 1,  # Use admin user as owner
                    'form_structure': template.template_structure,
                }
            )
        
        # Create custom forms for premium users
        premium_users = User.objects.filter(role='premium')
        for user in premium_users:
            custom_form_structure = {
                "fields": [
                    {"type": "text", "name": "project_name", "label": "Project Name", "required": True},
                    {"type": "date", "name": "start_date", "label": "Start Date", "required": True},
                    {"type": "select", "name": "priority", "label": "Priority", 
                     "options": ["Low", "Medium", "High", "Critical"], "required": True},
                    {"type": "textarea", "name": "description", "label": "Description", "required": False}
                ]
            }
            
            Form.objects.get_or_create(
                user=user,
                form_name=f"Project Tracker - {user.first_name}",
                language=user.language,
                defaults={
                    'form_structure': custom_form_structure,
                    'is_predefined': False,
                }
            )
        
        # Create sample data records
        forms = Form.objects.all()[:3]  # Get first 3 forms
        users = User.objects.filter(role__in=['free', 'premium'])
        
        for form in forms:
            for user in users:
                if form.can_user_access(user):
                    sample_data = {
                        "responses": {
                            "customer_name": f"Sample Customer {user.id}",
                            "email": f"customer{user.id}@example.com",
                            "satisfaction": "Satisfied",
                            "rating": 8,
                            "comments": "Great service!"
                        }
                    }
                    
                    DataRecord.objects.get_or_create(
                        user=user,
                        form=form,
                        defaults={
                            'data_content': sample_data,
                            'language': form.language,
                        }
                    )
