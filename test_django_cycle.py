#!/usr/bin/env python
"""
Complete Django cycle test - simulating browser interaction
"""

import os
import django
import json
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_backend.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User
from django.test import Client
from subscription_service import SubscriptionService
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

email = "fullcycletest@gpscontrol.com"
password = "TestPassword123!"

print(f"\n{'='*80}")
print(f"DJANGO FULL CYCLE TEST")
print(f"{'='*80}\n")

# Get the user
user = User.objects.get(email=email)

print(f"[STEP 1] User State Before Plan Activation:")
print(f"  Email: {user.email}")
print(f"  RFC: {user.rfc_tin}")
print(f"  Phone Verified: {user.phone_verified}")
print(f"  External API Registered: {user.external_api_registered}")
print(f"  External Client ID: {user.external_client_id}")
print(f"  External User ID: {user.external_user_id}")

print(f"\n[STEP 2] Calling activate_plan_for_user (like clicking the button):")
print(f"  Plan ID: 7 (Free Plan de prueba)")

# Import the function
from accounts.views import activate_plan_for_user

# Call it exactly as the view would
success = activate_plan_for_user(user, payment_id=None, external_reference=None, plan_id=7)

print(f"\n[STEP 3] Result:")
print(f"  Success: {success}")

# Refresh user
user.refresh_from_db()

print(f"\n[STEP 4] User State After Plan Activation:")
print(f"  External API Registered: {user.external_api_registered}")
print(f"  External API Username: {user.external_api_username}")
print(f"  External API Password: {user.external_api_password}")
print(f"  External Client ID: {user.external_client_id}")
print(f"  External User ID: {user.external_user_id}")
print(f"  External Licenses: {user.external_licenses}")
print(f"  Role: {user.role}")

print(f"\n[STEP 5] Verification:")
if user.external_client_id and user.external_user_id:
    print(f"  ✅ CREDENTIALS SAVED - Plan activation SUCCESSFUL")
else:
    print(f"  ❌ CREDENTIALS NOT SAVED - Plan activation FAILED")

print(f"\n{'='*80}\n")
