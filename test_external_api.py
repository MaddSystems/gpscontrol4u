#!/usr/bin/env python
"""
Test script to debug external API issues
"""
import os
import sys
import django
import json
import requests
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_backend.settings')
sys.path.insert(0, '/home/systemd/gpscontrol4u')
django.setup()

from django.conf import settings
from external_api_service import ExternalAPIService

print("=" * 80)
print(f"External API Test - {datetime.now()}")
print("=" * 80)

# Initialize service
api_service = ExternalAPIService()

print("\n[1] Testing Authentication...")
print("-" * 80)
auth_url = "https://api2ego.elisasoftware.com.mx/login"
auth_data = {
    "username": api_service.username,
    "password": api_service.password
}

try:
    auth_response = requests.post(auth_url, json=auth_data, timeout=10)
    print(f"Status Code: {auth_response.status_code}")
    print(f"Response Headers: {dict(auth_response.headers)}")
    
    if auth_response.status_code == 200:
        auth_body = auth_response.json()
        print(f"✓ Authentication successful!")
        print(f"Response Body: {json.dumps(auth_body, indent=2)}")
        
        token = auth_body.get('data', {}).get('token')
        if token:
            print(f"\n✓ Token obtained: {token[:50]}...")
            
            print("\n[2] Testing Get Plans Endpoint...")
            print("-" * 80)
            plans_url = "https://api2ego.elisasoftware.com.mx/store/plans"
            plans_params = {"store": api_service.store}
            plans_headers = {
                "Authorization": token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            print(f"URL: {plans_url}")
            print(f"Params: {plans_params}")
            print(f"Headers: {plans_headers}")
            
            plans_response = requests.get(
                plans_url,
                params=plans_params,
                headers=plans_headers,
                timeout=10
            )
            
            print(f"\nStatus Code: {plans_response.status_code}")
            print(f"Response Headers: {dict(plans_response.headers)}")
            
            try:
                plans_body = plans_response.json()
                print(f"Response Body: {json.dumps(plans_body, indent=2)}")
                
                if plans_response.status_code == 200:
                    print("✓ Plans retrieved successfully!")
                else:
                    print(f"✗ Error retrieving plans (status {plans_response.status_code})")
                    if 'data' in plans_body:
                        print(f"Error details: {plans_body.get('data')}")
                        
            except json.JSONDecodeError:
                print(f"✗ Response is not JSON")
                print(f"Raw response: {plans_response.text[:500]}")
        else:
            print("✗ No token in response")
    else:
        print(f"✗ Authentication failed (status {auth_response.status_code})")
        print(f"Response: {auth_response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"✗ Request error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
