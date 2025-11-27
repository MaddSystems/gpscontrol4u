#!/usr/bin/env python
"""
Check if a specific RFC exists in the external API
"""

import requests
import json

BASE_URL = "https://api2ego.elisasoftware.com"
USERNAME = "AdmGPScontrol4u"
PASSWORD = "GPSc0ntr0l4u*"
STORE = "GPScontrol4U"

# The RFC that was failing
TEST_RFC = "GEOR660529FD2"

print(f"\n{'='*80}")
print(f"CHECKING IF RFC EXISTS IN EXTERNAL API")
print(f"{'='*80}\n")

# Step 1: Authenticate
print(f"[1] Authenticating...")
url = f"{BASE_URL}/login"
params = {'username': USERNAME, 'password': PASSWORD}
headers = {'accept': 'application/json'}

response = requests.post(url, params=params, headers=headers, timeout=10)
if response.status_code == 200:
    data = response.json()
    if data.get('code') == 200:
        token = data['data'].get('token')
        print(f"✅ Authentication OK\n")
    else:
        print(f"❌ Authentication failed")
        exit(1)
else:
    print(f"❌ Authentication request failed")
    exit(1)

# Step 2: Check if RFC exists using licenses endpoint
print(f"[2] Checking if RFC '{TEST_RFC}' exists...")
url = f"{BASE_URL}/store/client/licenses"
params = {'rfc': TEST_RFC, 'store': STORE}
headers = {'accept': 'application/json', 'Authorization': token}

response = requests.get(url, params=params, headers=headers, timeout=10)

print(f"\nResponse Status: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    data = response.json()
    if data.get('code') == 200:
        print(f"\n✅ RFC '{TEST_RFC}' EXISTS IN API")
        if data['data']:
            print(f"   Client Info: {json.dumps(data['data'], indent=2)}")
    else:
        print(f"\n❌ RFC '{TEST_RFC}' NOT FOUND (Code: {data.get('code')})")
elif response.status_code == 503:
    print(f"\n❌ RFC '{TEST_RFC}' NOT FOUND (503 Error)")
else:
    print(f"\n❓ Unexpected status code: {response.status_code}")

print(f"\n{'='*80}\n")
