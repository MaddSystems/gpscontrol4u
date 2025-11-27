#!/usr/bin/env python
"""
Test Django user registration flow with the working RFC from test_api_cycle.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_backend.settings')
django.setup()

from accounts.models import User
from subscription_service import SubscriptionService
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the RFC that worked in the API test
TEST_RFC = "TEST660529FD9"
TEST_EMAIL = "testcycle9@gmail.com"
TEST_PLAN_ID = 7

print("\n" + "="*80)
print("DJANGO USER REGISTRATION TEST")
print("="*80)

# Step 1: Check if user already exists
print("\n[STEP 1] Checking if user exists...")
try:
    user = User.objects.get(email=TEST_EMAIL)
    print(f"✅ User exists: {user.email}")
    print(f"  - RFC: {user.rfc_tin}")
    print(f"  - Phone Verified: {user.phone_verified}")
    print(f"  - External API Registered: {user.external_api_registered}")
    print(f"  - External Client ID: {user.external_client_id}")
    print(f"  - External User ID: {user.external_user_id}")
    print(f"  - External Licenses: {user.external_licenses}")
except User.DoesNotExist:
    print(f"❌ User does not exist, need to create first")
    sys.exit(1)

# Step 2: Verify user has all required fields
print("\n[STEP 2] Verifying user has required fields...")
if not user.rfc_tin:
    print(f"❌ User missing RFC/TIN")
    sys.exit(1)
print(f"✅ User has RFC: {user.rfc_tin}")

if not user.phone_verified:
    print(f"❌ User phone not verified")
    sys.exit(1)
print(f"✅ User phone verified")

# Step 3: Try to create subscription via Django service
print("\n[STEP 3] Creating subscription via SubscriptionService...")
subscription_service = SubscriptionService()

is_new_client = not bool(user.external_api_password)
print(f"  - Is new client: {is_new_client}")
print(f"  - Plan ID: {TEST_PLAN_ID}")
print(f"  - New Client flag: True")

success, api_data, error_message = subscription_service.create_subscription(
    user=user,
    plan_id=TEST_PLAN_ID,
    new_client=True
)

print(f"\n[RESULT]")
print(f"  - Success: {success}")
print(f"  - Error: {error_message}")
if api_data:
    print(f"  - API Data: {json.dumps(api_data, indent=2)}")

# Step 4: Check if user was updated
if success:
    user.refresh_from_db()
    print(f"\n[STEP 4] Checking user after subscription...")
    print(f"  - External API Registered: {user.external_api_registered}")
    print(f"  - External API Username: {user.external_api_username}")
    print(f"  - External API Password: {user.external_api_password}")
    print(f"  - External Client ID: {user.external_client_id}")
    print(f"  - External User ID: {user.external_user_id}")
    print(f"  - External Licenses: {user.external_licenses}")
    
    if user.external_client_id and user.external_user_id:
        print(f"\n✅ SUCCESS: User credentials saved correctly!")
    else:
        print(f"\n❌ ERROR: Credentials not saved properly!")
else:
    print(f"\n❌ FAILED: Subscription creation failed")
    print(f"Error: {error_message}")

print("\n" + "="*80 + "\n")
