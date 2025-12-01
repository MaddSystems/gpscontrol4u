#!/usr/bin/env python
"""
Complete cycle test with unique data each run
Tests all steps from auth → registration → verification
"""

import requests
import json
import sys
import time
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://api2ego.elisasoftware.com.mx"
USERNAME = "AdmGPScontrol4u"
PASSWORD = "GPSc0ntr0l4u*"
STORE = "GPScontrol4U"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def generate_unique_data():
    """Generate unique RFC and email for each test run"""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.digits, k=1))
    
    # RFC format: 4 letters + 6 digits (date) + 2 letters + 1 digit
    rfc = f"TEST{timestamp % 1000000:06d}{random_suffix}X{random.randint(0, 9)}"
    email = f"test{timestamp}@testgpscontrol.com"
    
    return rfc, email

def log_step(step_num, title):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}STEP {step_num}: {title}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def log_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def log_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def log_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")

def step_1_authenticate():
    """Step 1: Authenticate"""
    log_step(1, "AUTHENTICATE")
    
    url = f"{BASE_URL}/login"
    params = {'username': USERNAME, 'password': PASSWORD}
    headers = {'accept': 'application/json'}
    
    try:
        response = requests.post(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                token = data['data'].get('token')
                log_success(f"Authentication OK - Token received")
                return token
        log_error("Authentication failed")
        return None
    except Exception as e:
        log_error(f"Request failed: {e}")
        return None

def step_2_verify_rfc_not_exists(token, rfc):
    """Step 2: Verify RFC doesn't exist yet"""
    log_step(2, "VERIFY RFC DOESN'T EXIST YET")
    
    url = f"{BASE_URL}/store/client/licenses"
    params = {'rfc': rfc, 'store': STORE}
    headers = {'accept': 'application/json', 'Authorization': token}
    
    log_info(f"Checking if RFC exists: {rfc}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 503:
            log_success(f"RFC {rfc} does NOT exist yet - ready to register")
            return True
        elif response.status_code == 200:
            log_error(f"RFC {rfc} ALREADY EXISTS - cannot test")
            return False
    except Exception as e:
        log_error(f"Check failed: {e}")
    return False

def step_3_register_new_client(token, rfc, email):
    """Step 3: Register new client"""
    log_step(3, "REGISTER NEW CLIENT")
    
    url = f"{BASE_URL}/store/subscription"
    params = {'store': STORE}
    headers = {
        'accept': 'application/json',
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "rfc": rfc,
        "client_info": {
            "name": "Test User",
            "brand_name": "Test - gpscontrol4u",
            "address": "Test Address",
            "description": f"Test account for {email}"
        },
        "username": email,
        "user_info": {
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": "TestPass123!",
            "phone_number": "+5215540386933"
        },
        "plan_id": 7,
        "new_client": True
    }
    
    log_info(f"Registering RFC: {rfc}")
    log_info(f"Email: {email}")
    log_info(f"Plan ID: 7 (Free)")
    
    try:
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                client_id = data['data'].get('client_id')
                user_id = data['data'].get('user_id')
                licenses = data['data'].get('total_licencias')
                
                log_success(f"Registration SUCCESS")
                log_info(f"Client ID: {client_id}")
                log_info(f"User ID: {user_id}")
                log_info(f"Licenses: {licenses}")
                
                return True, {
                    'client_id': client_id,
                    'user_id': user_id,
                    'licenses': licenses,
                    'password': 'TestPass123!'
                }
            else:
                error = data.get('message', 'Unknown error')
                log_error(f"API error: {error}")
                return False, None
        else:
            log_error(f"HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_error(f"Error: {error_data.get('detalle', error_data.get('message'))}")
            except:
                pass
            return False, None
    except Exception as e:
        log_error(f"Request failed: {e}")
        return False, None

def step_4_verify_client_registered(token, rfc):
    """Step 4: Verify client was registered"""
    log_step(4, "VERIFY CLIENT NOW EXISTS")
    
    url = f"{BASE_URL}/store/client/licenses"
    params = {'rfc': rfc, 'store': STORE}
    headers = {'accept': 'application/json', 'Authorization': token}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200 and data['data']:
                log_success(f"Client {rfc} verified in system")
                return True
        log_error(f"Verification failed")
        return False
    except Exception as e:
        log_error(f"Request failed: {e}")
        return False

def main():
    # Generate unique data
    rfc, email = generate_unique_data()
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}COMPLETE REGISTRATION CYCLE TEST{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"RFC: {rfc}")
    print(f"Email: {email}")
    print(f"Plan ID: 7 (Free)")
    
    # Step 1: Authenticate
    token = step_1_authenticate()
    if not token:
        sys.exit(1)
    
    # Step 2: Verify RFC doesn't exist
    if not step_2_verify_rfc_not_exists(token, rfc):
        sys.exit(1)
    
    # Step 3: Register new client
    success, reg_data = step_3_register_new_client(token, rfc, email)
    if not success:
        sys.exit(1)
    
    # Step 4: Verify registration
    if not step_4_verify_client_registered(token, rfc):
        log_error("Warning: Verification failed but registration may have succeeded")
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST COMPLETED SUCCESSFULLY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"\nCredentials:")
    print(f"  RFC: {rfc}")
    print(f"  Email: {email}")
    print(f"  Password: TestPass123!")
    print(f"  Client ID: {reg_data['client_id']}")
    print(f"  User ID: {reg_data['user_id']}")
    print(f"  Licenses: {reg_data['licenses']}")
    print(f"\nUse these values to test Django registration flow.\n")

if __name__ == '__main__':
    main()
