#!/usr/bin/env python3
"""
Test script for WhatsApp phone verification endpoints
Tests the ElizaSoftware API phone authentication endpoints
"""

import requests
import json
import urllib.parse
from datetime import datetime

# Configuration
BASE_URL = "https://api2ego.elisasoftware.com"
APPLICATION = "GPScontrol4U"
KEYCODE = "25360C4R105"
TOKEN = "No token"  # As per the example
TYPE = "web"

# Test phone number (with +52 for Mexico)
PHONE_NUMBER = "+525540386931"  # Your phone number with country code (+52 Mexico prefix)

class WhatsAppPhoneVerifier:
    """Class to interact with ElizaSoftware WhatsApp phone verification API"""
    
    def __init__(self, base_url=BASE_URL, application=APPLICATION, keycode=KEYCODE):
        self.base_url = base_url
        self.application = application
        self.keycode = keycode
        self.token = TOKEN
        self.type = TYPE
        self.verification_code = None
        
    def send_verification_code(self, phone_number):
        """
        Send verification code to phone via WhatsApp
        
        POST /phone/autenticate?token=No%20token&type=web&phone=%2B525527866324&application=GPScontrol4U&keycode=25360C4R105
        """
        url = f"{self.base_url}/phone/autenticate"
        
        # Build query parameters
        params = {
            'token': self.token,
            'type': self.type,
            'phone': phone_number,
            'application': self.application,
            'keycode': self.keycode
        }
        
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        print(f"\n{'='*80}")
        print(f"📱 STEP 1: SENDING VERIFICATION CODE")
        print(f"{'='*80}")
        print(f"URL: POST {url}")
        print(f"Query Params: {json.dumps(params, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
        
        try:
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data='',
                timeout=30,
                verify=True
            )
            
            print(f"\n✅ Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body:\n{response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n📦 Parsed JSON:")
                    print(json.dumps(data, indent=2))
                    
                    if data.get('code') == 200:
                        print(f"\n✅ Success! Message: {data.get('message')}")
                        return True, data
                    else:
                        print(f"\n❌ API returned error: {data.get('message')}")
                        return False, data
                except json.JSONDecodeError:
                    print(f"\n❌ Could not parse response as JSON")
                    return False, response.text
            else:
                print(f"\n❌ HTTP Error {response.status_code}")
                return False, response.text
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request Error: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def verify_code(self, phone_number, verification_code):
        """
        Verify the code sent to phone
        
        GET /phone/autenticate?code=610224&phone=%2B525527866324&application=GPScontrol4U&keycode=25360C4R105
        """
        url = f"{self.base_url}/phone/autenticate"
        
        # Build query parameters
        params = {
            'code': verification_code,
            'phone': phone_number,
            'application': self.application,
            'keycode': self.keycode
        }
        
        headers = {
            'accept': 'application/json'
        }
        
        print(f"\n{'='*80}")
        print(f"✅ STEP 2: VERIFYING CODE")
        print(f"{'='*80}")
        print(f"URL: GET {url}")
        print(f"Query Params: {json.dumps(params, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
                verify=True
            )
            
            print(f"\n✅ Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body:\n{response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n📦 Parsed JSON:")
                    print(json.dumps(data, indent=2))
                    
                    if data.get('code') == 200:
                        print(f"\n✅ Code verified! Message: {data.get('message')}")
                        return True, data
                    else:
                        print(f"\n❌ API returned error: {data.get('message')}")
                        return False, data
                except json.JSONDecodeError:
                    print(f"\n❌ Could not parse response as JSON")
                    return False, response.text
            else:
                print(f"\n❌ HTTP Error {response.status_code}")
                return False, response.text
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request Error: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)


def main():
    """Main test function"""
    print(f"\n{'='*80}")
    print(f"🔐 WHATSAPP PHONE VERIFICATION API TEST")
    print(f"{'='*80}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Application: {APPLICATION}")
    print(f"Phone: {PHONE_NUMBER}")
    
    # Initialize verifier
    verifier = WhatsAppPhoneVerifier()
    
    # Step 1: Send verification code
    print(f"\n\n🚀 Attempting to send verification code...")
    success, response = verifier.send_verification_code(PHONE_NUMBER)
    
    if not success:
        print(f"\n⚠️  El envío retornó un estado que no es 200.")
        print(f"Verificando si el código anterior aún es válido...")
        
        # Si no es éxito pero got code 201 (token aún vigente), usar ese código
        if isinstance(response, dict) and response.get('code') == 201:
            print(f"\n✅ El API dice que el código anterior aún es válido.")
            verification_code = response.get('data', {}).get('code')
            if verification_code:
                print(f"Usando código anterior: {verification_code}")
            else:
                print(f"No se encontró código en respuesta.")
                return
        else:
            print(f"No se pudo obtener código válido. Deteniendo test.")
            return
    else:
        # Obtener el código de la respuesta (en caso de que sea necesario)
        api_code = response.get('data', {}).get('code')
        if api_code:
            print(f"\n✅ Código generado por API: {api_code}")
            print(f"Esperando que llegue a tu WhatsApp...")
    
    # Step 2: Ask user for code
    print(f"\n\n⏳ PAUSA - Esperando código de WhatsApp...")
    print(f"{'='*80}")
    print(f"✅ Se envió un código de verificación a tu WhatsApp: {PHONE_NUMBER}")
    print(f"{'='*80}")
    print(f"\n📱 Por favor revisa tu WhatsApp y copia el código de 6 dígitos que recibiste.")
    print(f"\n⏸️  PRESIONA ENTER CUANDO ESTÉS LISTO, LUEGO INGRESA EL CÓDIGO:\n")
    
    input("Presiona ENTER para continuar...")
    
    verification_code = input("📝 Ingresa el código de 6 dígitos: ").strip()
    
    if not verification_code or len(verification_code) != 6:
        print(f"\n❌ Invalid code format. Must be 6 digits.")
        return
    
    # Step 3: Verify the code
    print(f"\n🔍 Verifying code: {verification_code}")
    success, response = verifier.verify_code(PHONE_NUMBER, verification_code)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    if success:
        print(f"✅ Phone verification completed successfully!")
        print(f"Response: {json.dumps(response, indent=2)}")
    else:
        print(f"❌ Phone verification failed!")
        print(f"Response: {response}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
