#!/usr/bin/env python
"""
Complete API cycle test for ElizaSoftware external API
Tests: Authentication → Plans → New Client Registration → License Check → Subscription Check
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://api2ego.elisasoftware.com"
USERNAME = "AdmGPScontrol4u"
PASSWORD = "GPSc0ntr0l4u*"
STORE = "GPScontrol4U"

# Test data - completely new RFC
TEST_RFC = "TEST660529FD9"
TEST_EMAIL = "testcycle9@gmail.com"
TEST_PLAN_ID = 7  # Free plan

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log_step(step_num, title):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}STEP {step_num}: {title}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def log_success(msg):
    print(f"{GREEN}✅ SUCCESS: {msg}{RESET}")

def log_error(msg):
    print(f"{RED}❌ ERROR: {msg}{RESET}")

def log_info(msg):
    print(f"{YELLOW}ℹ️  INFO: {msg}{RESET}")

def log_response(response, title=""):
    if title:
        print(f"\n{title}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def step_1_authenticate():
    """Step 1: Authenticate with API"""
    log_step(1, "AUTHENTICATE")
    
    url = f"{BASE_URL}/login"
    params = {
        'username': USERNAME,
        'password': PASSWORD
    }
    headers = {'accept': 'application/json'}
    
    log_info(f"POST {url}")
    log_info(f"Params: username={USERNAME}")
    
    try:
        response = requests.post(url, params=params, headers=headers, timeout=10)
        data = log_response(response, "Authentication Response:")
        
        if response.status_code == 200 and data.get('code') == 200:
            token = data['data'].get('token')
            log_success(f"Authentication successful. Token received: {token[:50]}...")
            return token
        else:
            log_error("Authentication failed")
            return None
    except Exception as e:
        log_error(f"Authentication request failed: {e}")
        return None

def step_2_get_plans(token):
    """Step 2: Get available plans"""
    log_step(2, "GET AVAILABLE PLANS")
    
    url = f"{BASE_URL}/store/plans"
    params = {'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token
    }
    
    log_info(f"GET {url}?store={STORE}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = log_response(response, "Plans Response:")
        
        if response.status_code == 200 and data.get('code') == 200:
            plans = data['data']
            log_success(f"Retrieved {len(plans)} plans")
            for plan in plans:
                print(f"  - ID: {plan['id']}, Name: {plan['name']}, Price: {plan['price']}")
            return plans
        else:
            log_error("Failed to get plans")
            return None
    except Exception as e:
        log_error(f"Get plans request failed: {e}")
        return None

def step_3_check_client_exists(token):
    """Step 3: Check if client (RFC) already exists"""
    log_step(3, "CHECK IF CLIENT EXISTS (using licenses endpoint)")
    
    url = f"{BASE_URL}/store/client/licenses"
    params = {'rfc': TEST_RFC, 'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token
    }
    
    log_info(f"GET {url}?rfc={TEST_RFC}&store={STORE}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = log_response(response, "Client Check Response:")
        
        if response.status_code == 200:
            if data.get('code') == 200 and data['data'].get('id'):
                log_error(f"RFC {TEST_RFC} ALREADY EXISTS in API")
                return True
            else:
                log_success(f"RFC {TEST_RFC} does NOT exist - ready for registration")
                return False
        else:
            # 503 = not found
            log_success(f"RFC {TEST_RFC} does NOT exist (expected 503 error) - ready for registration")
            return False
    except Exception as e:
        log_error(f"Client check request failed: {e}")
        return False

def step_4_register_new_client(token):
    """Step 4: Register new client with subscription"""
    log_step(4, "REGISTER NEW CLIENT (with subscription)")
    
    url = f"{BASE_URL}/store/subscription"
    params = {'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "rfc": TEST_RFC,
        "client_info": {
            "name": "Test User Cycle",
            "brand_name": "Test Cycle - gpscontrol4u",
            "address": "Test Address",
            "description": f"Test cycle account for {TEST_EMAIL}"
        },
        "username": TEST_EMAIL,
        "user_info": {
            "first_name": "Test",
            "last_name": "Cycle",
            "email": TEST_EMAIL,
            "password": "TestPassword123!",
            "phone_number": "+5215540386932"
        },
        "plan_id": TEST_PLAN_ID,
        "new_client": True
    }
    
    log_info(f"POST {url}?store={STORE}")
    log_info(f"Payload: RFC={TEST_RFC}, Email={TEST_EMAIL}, Plan={TEST_PLAN_ID}, new_client=True")
    print(f"Full payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        data = log_response(response, "Registration Response:")
        
        if response.status_code == 200 and data.get('code') == 200:
            log_success(f"New client registered successfully")
            client_id = data['data'].get('client_id')
            user_id = data['data'].get('user_id')
            log_info(f"Client ID: {client_id}, User ID: {user_id}")
            return True, data['data']
        else:
            log_error(f"Registration failed with code {data.get('code') if data else response.status_code}")
            return False, data if data else None
    except Exception as e:
        log_error(f"Registration request failed: {e}")
        return False, None

def step_5_verify_client_exists(token):
    """Step 5: Verify client now exists"""
    log_step(5, "VERIFY CLIENT NOW EXISTS")
    
    url = f"{BASE_URL}/store/client/licenses"
    params = {'rfc': TEST_RFC, 'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token
    }
    
    log_info(f"GET {url}?rfc={TEST_RFC}&store={STORE}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = log_response(response, "Client Verification Response:")
        
        if response.status_code == 200 and data.get('code') == 200:
            if data['data'].get('id'):
                log_success(f"Client {TEST_RFC} now exists in API")
                log_info(f"Client ID: {data['data'].get('client_id')}")
                log_info(f"User ID: {data['data'].get('user_id')}")
                return True
            else:
                log_error("Client verified but no ID returned")
                return False
        else:
            log_error("Client verification failed")
            return False
    except Exception as e:
        log_error(f"Client verification request failed: {e}")
        return False

def step_6_check_subscription(token):
    """Step 6: Check subscription status"""
    log_step(6, "CHECK SUBSCRIPTION STATUS")
    
    url = f"{BASE_URL}/store/client/subscription"
    params = {'rfc': TEST_RFC, 'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token
    }
    
    log_info(f"GET {url}?rfc={TEST_RFC}&store={STORE}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = log_response(response, "Subscription Status Response:")
        
        if response.status_code == 200 and data.get('code') == 200:
            log_success(f"Subscription found for RFC {TEST_RFC}")
            subscription = data['data'][0] if data['data'] else None
            if subscription:
                log_info(f"Subscription ID: {subscription.get('subscription_id')}")
                log_info(f"Plan ID: {subscription.get('plan_id')}")
                log_info(f"Status: {subscription.get('status')}")
            return True
        else:
            log_error("Subscription check failed or no subscription found")
            return False
    except Exception as e:
        log_error(f"Subscription check request failed: {e}")
        return False

def main():
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}ELIZA SOFTWARE API - COMPLETE REGISTRATION CYCLE TEST{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"Store: {STORE}")
    print(f"Test RFC: {TEST_RFC}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Test Plan ID: {TEST_PLAN_ID}")
    
    # Step 1: Authenticate
    token = step_1_authenticate()
    if not token:
        log_error("Cannot proceed without authentication")
        sys.exit(1)
    
    # Step 2: Get plans
    plans = step_2_get_plans(token)
    if not plans:
        log_error("Cannot proceed without plans info")
        sys.exit(1)
    
    # Step 3: Check if client exists (should NOT exist)
    exists = step_3_check_client_exists(token)
    if exists:
        log_error("RFC already exists - cannot test new registration. Please use a different RFC.")
        sys.exit(1)
    
    # Step 4: Register new client
    success, reg_data = step_4_register_new_client(token)
    if not success:
        log_error("Registration failed - cannot proceed")
        sys.exit(1)
    
    # Step 5: Verify client now exists
    verified = step_5_verify_client_exists(token)
    if not verified:
        log_error("Verification failed - client may not be properly registered")
        # Continue anyway to see what happened
    
    # Step 6: Check subscription
    has_subscription = step_6_check_subscription(token)
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"RFC: {TEST_RFC}")
    print(f"Email: {TEST_EMAIL}")
    print(f"Registration: {GREEN}✅ SUCCESS{RESET if success else RED}❌ FAILED{RESET}")
    print(f"Verification: {GREEN}✅ SUCCESS{RESET if verified else RED}❌ FAILED{RESET}")
    print(f"Subscription: {GREEN}✅ SUCCESS{RESET if has_subscription else RED}❌ FAILED{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

if __name__ == '__main__':
    main()
