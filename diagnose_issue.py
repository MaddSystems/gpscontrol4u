#!/usr/bin/env python
"""
Diagnose the exact issue with email registration
"""

import requests
import json
import sys

BASE_URL = "https://api2ego.elisasoftware.com"
STORE = "GPScontrol4U"

# Use the token from your curl examples
TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjMyLCJ1c2VybmFtZSI6IkFkbUdQU2NvbnRyb2w0dSIsImlhdCI6MTc2NDE5NTEzNiwiZXhwIjoxNzY2Nzg3MTM2LCJlbWFpbCI6Im9yZGVyc0BncHNjb250cm9sLmNvbS5teCIsIm5hbWUiOiJUaWVuZGEgR1BTY29udHJvbDR1IiwiYXBwbGljYXRpb25faWQiOjN9.vR564nTeE-UGDF33i6lXdmfnnmZ4lbVNJrMJ3b-ud4ZTYb0GKQCwKe6YTDArk6XOkdalT5pWioDW9vuH7DciILchHGcP6UeZf3OKJeh_noCS4CmNyrAmrloOHv1H2ErA8Rk0D_BRGjvmW4_r20cWrSudGD2k2iLvqCZXDQJddnuIw1nU_Iu5_Fck2F49bOR4r4cRXhFzG8-yH7tD5-Tfefs0lluCHJRHdYWbE-mMIZ4uq8lPgfd2urZ5ZROBXZQwNLh59pLhqTnajKV4niUXpvkiks1P5XeG-sTo4r0Ym2swibjkxSsQ8u5r6nfMHskP2x97FOwNUJN6cbBTHYLsIw"

headers = {
    'accept': 'application/json',
    'Authorization': TOKEN,
    'Content-Type': 'application/json'
}

print("\n" + "="*80)
print("DIAGNOSING EMAIL REGISTRATION ISSUE")
print("="*80 + "\n")

print("🔍 QUESTION: Which RFC is tearlipiz@gmail.com registered with?")
print("-"*80)

# Test RFC 1 (original)
rfc1 = "TEAR660529FD2"
print(f"\n[TEST 1] Checking RFC: {rfc1}")
response1 = requests.get(
    f"{BASE_URL}/store/client/subscription",
    params={"rfc": rfc1, "store": STORE},
    headers=headers,
    timeout=10
)
print(f"Status: {response1.status_code}")
data1 = response1.json()
print(f"Response: {json.dumps(data1, indent=2)}")

if response1.status_code == 200 and data1.get('data'):
    print(f"✅ RFC {rfc1} EXISTS in API")
    print(f"   Data: {data1['data']}")
else:
    print(f"❌ RFC {rfc1} NOT found")

# Test RFC 2 (new)
rfc2 = "TEAR660529FD6"
print(f"\n[TEST 2] Checking RFC: {rfc2}")
response2 = requests.get(
    f"{BASE_URL}/store/client/subscription",
    params={"rfc": rfc2, "store": STORE},
    headers=headers,
    timeout=10
)
print(f"Status: {response2.status_code}")
data2 = response2.json()
print(f"Response: {json.dumps(data2, indent=2)}")

if response2.status_code == 200 and data2.get('data'):
    print(f"✅ RFC {rfc2} EXISTS in API")
    print(f"   Data: {data2['data']}")
else:
    print(f"❌ RFC {rfc2} NOT found")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

if response1.status_code == 200 and data1.get('data'):
    print(f"\n✅ RFC {rfc1} (TEAR660529FD2) is the ORIGINAL RFC for tearlipiz@gmail.com")
    print(f"\nThe problem:")
    print(f"  - Email tearlipiz@gmail.com is registered with RFC {rfc1}")
    print(f"  - You changed the RFC in the system to {rfc2}")
    print(f"  - When trying to activate with new RFC {rfc2}, API rejects because:")
    print(f"    * Email already exists (with old RFC {rfc1})")
    print(f"    * API doesn't allow same email with different RFC simultaneously")
    print(f"\nSolution:")
    print(f"  - Use a DIFFERENT EMAIL when changing RFC")
    print(f"  - OR delete/unregister the old RFC first")
    print(f"  - OR use new_client=False to UPDATE the existing registration")
else:
    print(f"\n❓ RFC {rfc1} not found, so tearlipiz@gmail.com might be with RFC {rfc2}")

print("\n" + "="*80 + "\n")
