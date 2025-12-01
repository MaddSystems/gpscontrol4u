"""
WhatsApp Phone Verification Service
Integrates with ElizaSoftware API for phone verification via WhatsApp
"""

import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class WhatsAppPhoneVerificationService:
    """Service to handle WhatsApp phone verification"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://api2ego.elisasoftware.com.mx')
        self.application = getattr(settings, 'EXTERNAL_API_STORE', 'GPScontrol4U')
        self.keycode = getattr(settings, 'WHATSAPP_KEYCODE', '25360C4R105')
        self.token = getattr(settings, 'WHATSAPP_TOKEN', 'No token')
        self.type = 'web'
    
    def normalize_phone(self, phone_number):
        """
        Normalize phone number to +52XXXXXXXXXX format (Mexico)
        Removes spaces, dashes, parentheses, and ensures proper format
        """
        # Remove common formatting characters
        phone = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # If it starts with +52, keep it
        if phone.startswith('+52'):
            return phone
        
        # If it's 10 digits (Mexico local), add +52
        if len(phone) == 10 and phone.isdigit():
            return f'+52{phone}'
        
        # If it's 10 digits starting with 52, add +
        if len(phone) == 12 and phone.startswith('52') and phone[2:].isdigit():
            return f'+{phone}'
        
        # Otherwise return as is with + if needed
        if not phone.startswith('+'):
            return f'+{phone}'
        
        return phone
    
    def send_verification_code(self, phone_number):
        """
        Send verification code to phone via WhatsApp
        
        Returns:
            tuple: (success: bool, code: str or None, message: str)
        """
        try:
            # Normalize phone number
            normalized_phone = self.normalize_phone(phone_number)
            
            url = f"{self.base_url}/phone/autenticate"
            
            params = {
                'token': self.token,
                'type': self.type,
                'phone': normalized_phone,
                'application': self.application,
                'keycode': self.keycode
            }
            
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📱 [WHATSAPP_SEND] Sending verification code to {normalized_phone}")
            logger.info(f"📱 [WHATSAPP_SEND] URL: POST {url}")
            logger.info(f"📱 [WHATSAPP_SEND] Params: {json.dumps(params, indent=2)}")
            
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data='',
                timeout=30,
                verify=True
            )
            
            logger.info(f"📱 [WHATSAPP_SEND] Status: {response.status_code}")
            logger.info(f"📱 [WHATSAPP_SEND] Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # code 200 = new code sent, code 201 = reusing existing code (both valid)
                if data.get('code') in [200, 201]:
                    verification_code = data.get('data', {}).get('code')
                    message = data.get('message', 'Code sent successfully')
                    
                    logger.info(f"✅ [WHATSAPP_SEND] Code sent: {verification_code}")
                    logger.info(f"✅ [WHATSAPP_SEND] Message: {message}")
                    
                    return True, verification_code, message
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logger.error(f"❌ [WHATSAPP_SEND] API error: {error_msg}")
                    return False, None, error_msg
            else:
                logger.error(f"❌ [WHATSAPP_SEND] HTTP {response.status_code}: {response.text}")
                return False, None, f"HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [WHATSAPP_SEND] Request error: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"❌ [WHATSAPP_SEND] Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, None, str(e)
    
    def verify_code(self, phone_number, verification_code):
        """
        Verify the code sent via WhatsApp
        
        Returns:
            tuple: (success: bool, validated: bool, message: str)
        """
        try:
            # Normalize phone number
            normalized_phone = self.normalize_phone(phone_number)
            
            url = f"{self.base_url}/phone/autenticate"
            
            params = {
                'code': verification_code,
                'phone': normalized_phone,
                'application': self.application,
                'keycode': self.keycode
            }
            
            headers = {
                'accept': 'application/json'
            }
            
            logger.info(f"📱 [WHATSAPP_VERIFY] Verifying code for {normalized_phone}")
            logger.info(f"📱 [WHATSAPP_VERIFY] URL: GET {url}")
            logger.info(f"📱 [WHATSAPP_VERIFY] Params: {json.dumps(params, indent=2)}")
            
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
                verify=True
            )
            
            logger.info(f"📱 [WHATSAPP_VERIFY] Status: {response.status_code}")
            logger.info(f"📱 [WHATSAPP_VERIFY] Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200:
                    validated = data.get('data', {}).get('validated', False)
                    message = data.get('message', 'Code verified')
                    
                    if validated:
                        logger.info(f"✅ [WHATSAPP_VERIFY] Code verified successfully")
                        return True, True, message
                    else:
                        logger.error(f"❌ [WHATSAPP_VERIFY] Code not validated")
                        return True, False, message
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logger.error(f"❌ [WHATSAPP_VERIFY] API error: {error_msg}")
                    return False, False, error_msg
            else:
                logger.error(f"❌ [WHATSAPP_VERIFY] HTTP {response.status_code}: {response.text}")
                return False, False, f"HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [WHATSAPP_VERIFY] Request error: {e}")
            return False, False, str(e)
        except Exception as e:
            logger.error(f"❌ [WHATSAPP_VERIFY] Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, False, str(e)
