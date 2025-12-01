"""
Subscription service for creating external API accounts
"""

import requests
import json
import logging
from django.conf import settings
from accounts.models import User
from payments.models import Subscription

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing external API subscriptions"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://api2ego.elisasoftware.com.mx')
        self.username = getattr(settings, 'EXTERNAL_API_USERNAME', 'AdmGPScontrol4u')
        self.password = getattr(settings, 'EXTERNAL_API_PASSWORD', 'GPSc0ntr0l4u*')
        self.store = getattr(settings, 'EXTERNAL_API_STORE', 'GPScontrol4U')
        self.token = None
    
    def authenticate(self):
        """Authenticate with the external API"""
        try:
            url = f"{self.base_url}/login"
            params = {
                'username': self.username,
                'password': self.password
            }
            
            headers = {
                'accept': 'application/json'
            }
            
            logger.info(f"🔐 [AUTH] Attempting authentication with external API")
            logger.info(f"🔐 [AUTH] URL: {url}")
            logger.info(f"🔐 [AUTH] Username: {self.username}")
            logger.info(f"🔐 [AUTH] Password: {'*' * len(self.password)}")
            
            response = requests.post(url, params=params, headers=headers, timeout=10)
            
            logger.info(f"🔐 [AUTH] Response Status: {response.status_code}")
            logger.info(f"🔐 [AUTH] Response Headers: {dict(response.headers)}")
            logger.info(f"🔐 [AUTH] Response Body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200 and 'data' in data:
                    self.token = data['data'].get('token')
                    logger.info(f"🔐 [AUTH] Authentication successful! Token: {self.token[:20]}...")
                    return True
                else:
                    logger.error(f"🔐 [AUTH] Unexpected response structure: {data}")
            
            logger.error(f"🔐 [AUTH] Authentication failed: {response.status_code} - {response.text}")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"🔐 [AUTH] Authentication request error: {e}")
            return False
    
    def create_subscription(self, user, plan_id, new_client=True, _retry_attempted=False):
        """
        Create a subscription for a user in the external API
        
        Args:
            user: User instance
            plan_id: External plan ID (usually 1 for free plan)
            new_client: Whether this is a new client (True) or updating existing (False)
            _retry_attempted: Internal flag to prevent infinite loops
        
        Returns:
            tuple: (success: bool, data: dict, error_message: str)
        """
        if not self.authenticate():
            return False, None, "Failed to authenticate with external API"
        
        if not user.rfc_tin:
            return False, None, "User must have RFC/TIN to create subscription"
        
        # Use existing password if user already has credentials, otherwise generate new one
        if new_client or not user.external_api_password:
            api_password = User.generate_secure_password()
        else:
            api_password = user.external_api_password
        
        logger.info(f"🚀 [SUBSCRIPTION] Starting subscription creation for user: {user.email}")
        logger.info(f"🚀 [SUBSCRIPTION] User RFC/TIN: {user.rfc_tin}")
        logger.info(f"🚀 [SUBSCRIPTION] Plan ID: {plan_id}")
        logger.info(f"🚀 [SUBSCRIPTION] New Client: {new_client}")
        logger.info(f"🚀 [SUBSCRIPTION] Generated API Password: {api_password}")
        
        # Prepare subscription data
        subscription_data = {
            "rfc": user.rfc_tin,
            "client_info": {
                "name": user.get_full_name(),
                "brand_name": f"{user.get_full_name()} - gpscontrol4u",
                "address": "No address provided",
                "description": f"gpscontrol4u account for {user.email}"
            },
            "username": user.email,
            "user_info": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "password": api_password,
                "phone_number": user.phone_number or ""
            },
            "plan_id": plan_id,
            "new_client": new_client
        }
        
        logger.info(f"🚀 [SUBSCRIPTION] Subscription data prepared:")
        logger.info(f"🚀 [SUBSCRIPTION] RFC: {subscription_data['rfc']}")
        logger.info(f"🚀 [SUBSCRIPTION] Client Name: {subscription_data['client_info']['name']}")
        logger.info(f"🚀 [SUBSCRIPTION] Username: {subscription_data['username']}")
        logger.info(f"🚀 [SUBSCRIPTION] User Password: {subscription_data['user_info']['password']}")
        logger.info(f"🚀 [SUBSCRIPTION] Full payload: {json.dumps(subscription_data, indent=2)}")
        
        try:
            url = f"{self.base_url}/store/subscription"
            params = {
                'store': self.store
            }
            headers = {
                'accept': 'application/json',
                'Authorization': self.token,  # Token already includes "Bearer "
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📡 [API_CALL] ========== EXTERNAL API SUBSCRIPTION CALL ==========")
            logger.info(f"📡 [API_CALL] FULL ENDPOINT URL: POST {url}?store={self.store}")
            logger.info(f"📡 [API_CALL] BASE URL: {self.base_url}")
            logger.info(f"📡 [API_CALL] ENDPOINT: /store/subscription")
            logger.info(f"📡 [API_CALL] QUERY PARAMETER 'store': {self.store}")
            logger.info(f"📡 [API_CALL] REQUEST METHOD: POST")
            logger.info(f"📡 [API_CALL] QUERY PARAMS: {json.dumps(params, indent=2)}")
            logger.info(f"📡 [API_CALL] REQUEST HEADERS: {json.dumps(dict(headers), indent=2)}")
            logger.info(f"📡 [API_CALL] REQUEST BODY (COMPLETE): {json.dumps(subscription_data, indent=2)}")
            logger.info(f"📡 [API_CALL] IMPORTANT DETAILS:")
            logger.info(f"📡 [API_CALL]   - new_client flag: {new_client}")
            logger.info(f"📡 [API_CALL]   - RFC being sent: {subscription_data['rfc']}")
            logger.info(f"📡 [API_CALL]   - Plan ID being sent: {subscription_data['plan_id']}")
            logger.info(f"📡 [API_CALL] ==================================================")
            
            # Build the full URL as it will be sent in the request
            from urllib.parse import urlencode
            full_url = f"{url}?{urlencode(params)}"
            
            logger.info(f"📡 [API_CALL] ACTUAL URL BEING CALLED: {full_url}")
            logger.info(f"📡 [API_CALL] ==================================================")
            
            response = requests.post(url, params=params, headers=headers, json=subscription_data, timeout=30)
            
            logger.info(f"📡 [API_CALL] REQUEST SENT TO: {response.request.url}")
            logger.info(f"📡 [API_CALL] REQUEST METHOD: {response.request.method}")
            logger.info(f"📡 [API_CALL] REQUEST BODY SENT: {response.request.body}")
            
            logger.info(f"📡 [API_RESPONSE] ========== API RESPONSE RECEIVED ==========")
            logger.info(f"📡 [API_RESPONSE] Status Code: {response.status_code}")
            logger.info(f"📡 [API_RESPONSE] Response Headers: {dict(response.headers)}")
            logger.info(f"📡 [API_RESPONSE] Raw Response Body: {response.text}")
            logger.info(f"📡 [API_RESPONSE] ==================================================")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📡 [API_RESPONSE] Parsed JSON: {json.dumps(data, indent=2)}")
                
                if data.get('code') == 200:
                    logger.info(f"✅ [SUCCESS] API call successful!")
                    logger.info(f"✅ [SUCCESS] API Data: {json.dumps(data['data'], indent=2)}")
                    
                    # Extract credentials from API response
                    api_client_id = data['data'].get('client_id')
                    api_user_id = data['data'].get('user_id')
                    api_licenses = data['data'].get('total_licencias', 0)
                    
                    logger.info(f"💾 [CREDENTIALS] Extracting credentials from API response:")
                    logger.info(f"💾 [CREDENTIALS] Username (will be): {user.email}")
                    logger.info(f"💾 [CREDENTIALS] Password (generated): {api_password}")
                    logger.info(f"💾 [CREDENTIALS] Client ID (from API): {api_client_id}")
                    logger.info(f"💾 [CREDENTIALS] User ID (from API): {api_user_id}")
                    logger.info(f"💾 [CREDENTIALS] Licenses (from API): {api_licenses}")
                    
                    # Success - save credentials to user
                    user.set_external_api_credentials(
                        username=user.email,
                        password=api_password,
                        client_id=api_client_id,
                        user_id=api_user_id,
                        licenses=api_licenses
                    )
                    
                    logger.info(f"💾 [DATABASE] Credentials saved to user model")
                    logger.info(f"💾 [DATABASE] User external_api_username: {user.external_api_username}")
                    logger.info(f"💾 [DATABASE] User external_api_password: {user.external_api_password}")
                    logger.info(f"💾 [DATABASE] User external_client_id: {user.external_client_id}")
                    logger.info(f"💾 [DATABASE] User external_user_id: {user.external_user_id}")
                    logger.info(f"💾 [DATABASE] User external_licenses: {user.external_licenses}")
                    
                    # Create or update local subscription
                    subscription, created = Subscription.objects.get_or_create(
                        user=user,
                        defaults={
                            'plan_type': 'free' if plan_id == 1 else 'premium',
                            'status': 'active',
                            'external_plan_id': plan_id
                        }
                    )
                    
                    if not created:
                        subscription.plan_type = 'free' if plan_id == 1 else 'premium'
                        subscription.status = 'active'
                        subscription.external_plan_id = plan_id
                        subscription.save()
                    
                    logger.info(f"💾 [DATABASE] Local subscription {'created' if created else 'updated'}")
                    
                    return_data = {
                        'username': user.email,
                        'password': api_password,
                        'client_id': api_client_id,
                        'user_id': api_user_id,
                        'licenses': api_licenses,
                        'portal_url': 'https://ego.elisasoftware.com.mx/',
                        'message': data.get('message', 'Subscription created successfully')
                    }
                    
                    logger.info(f"🎁 [RETURN] Returning credentials to view:")
                    logger.info(f"🎁 [RETURN] {json.dumps(return_data, indent=2)}")
                    
                    return True, return_data, None
                
                else:
                    error_msg = data.get('message', 'Unknown error from API')
                    logger.error(f"❌ [API_ERROR] API returned error code: {data.get('code')}")
                    logger.error(f"❌ [API_ERROR] Error message: {error_msg}")
                    logger.error(f"❌ [API_ERROR] Full response: {json.dumps(data, indent=2)}")
                    return False, None, error_msg
            
            else:
                logger.error(f"❌ [HTTP_ERROR] HTTP error: {response.status_code}")
                logger.error(f"❌ [HTTP_ERROR] Response body: {response.text}")
                
                try:
                    error_data = response.json()
                    logger.error(f"❌ [HTTP_ERROR] Parsed error: {json.dumps(error_data, indent=2)}")
                    logger.error(f"❌ [HTTP_ERROR] error_data fields: {list(error_data.keys())}")
                    
                    # Extract error message - try multiple possible fields
                    error_msg = None
                    if 'message' in error_data:
                        error_msg = error_data.get('message')
                        logger.error(f"❌ [HTTP_ERROR] Found 'message' field: {error_msg}")
                    elif 'detalle' in error_data:
                        error_msg = error_data.get('detalle')
                        logger.error(f"❌ [HTTP_ERROR] Found 'detalle' field: {error_msg}")
                    elif 'error' in error_data:
                        error_msg = error_data.get('error')
                        logger.error(f"❌ [HTTP_ERROR] Found 'error' field: {error_msg}")
                    else:
                        error_msg = f'HTTP {response.status_code}'
                        logger.error(f"❌ [HTTP_ERROR] No standard error field found, using: {error_msg}")
                    
                    logger.error(f"❌ [HTTP_ERROR] Final error_msg value: {error_msg}")
                    
                    # Handle specific error cases with loop prevention
                    if response.status_code == 503 and not _retry_attempted:
                        if ('no esta disponible' in error_msg.lower() or 
                            'ya se encuentra registrado' in error_msg.lower()) and new_client:
                            # User/client already exists - try with new_client=False
                            logger.info(f"🔄 [RETRY] User/Client {user.email} (RFC: {user.rfc_tin}) already exists, retrying with new_client=False")
                            return self.create_subscription(user, plan_id, new_client=False, _retry_attempted=True)
                        
                        elif 'no se encuentra registrado' in error_msg.lower() and not new_client:
                            # Client (RFC) doesn't exist - try with new_client=True
                            logger.info(f"🔄 [RETRY] Client RFC {user.rfc_tin} not registered, retrying with new_client=True")
                            return self.create_subscription(user, plan_id, new_client=True, _retry_attempted=True)
                    
                    # If retry was already attempted, provide detailed error handling
                    if _retry_attempted:
                        logger.error(f"❌ [RETRY_EXHAUSTED] Both new_client=True and new_client=False failed")
                        
                        # Check if it's a corrupted RFC state
                        if (('no esta disponible' in error_msg.lower() or 
                             'ya se encuentra registrado' in error_msg.lower()) or 
                            'no se encuentra registrado' in error_msg.lower()):
                            
                            corrupted_msg = (
                                f"RFC {user.rfc_tin} appears to be in an inconsistent state in the external API. "
                                f"The RFC cannot be registered as a new client nor accessed as an existing client. "
                                f"Please contact support or try with a different RFC/TIN number."
                            )
                            logger.error(f"❌ [CORRUPTED_RFC] {corrupted_msg}")
                            return False, None, corrupted_msg
                        
                        return False, None, f"Both registration attempts failed: {error_msg}"
                    
                    return False, None, error_msg
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ [JSON_ERROR] Could not parse error response as JSON")
                    return False, None, f"HTTP {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [NETWORK_ERROR] Subscription request error: {e}")
            logger.error(f"❌ [NETWORK_ERROR] Exception type: {type(e)}")
            import traceback
            logger.error(f"❌ [NETWORK_ERROR] Traceback: {traceback.format_exc()}")
            return False, None, f"Connection error: {str(e)}"
    
    def activate_free_plan(self, user):
        """Convenience method to activate free plan for a user"""
        return self.create_subscription(user, plan_id=1, new_client=True)
    
    def get_user_credentials(self, email):
        """Get user credentials from the database - this is a convenience method
        that returns the stored credentials for a user after activation"""
        
        try:
            user = User.objects.get(email=email)
            
            if not user.external_api_registered:
                return False, None, "User not registered with external API"
            
            # Return the stored credentials
            credentials_data = {
                'username': user.external_api_username,
                'password': user.external_api_password,
                'client_id': user.external_client_id,
                'user_id': user.external_user_id,
                'licenses': user.external_licenses,
                'portal_url': 'https://ego.elisasoftware.com.mx/',
            }
            
            return True, credentials_data, "Credentials retrieved successfully"
            
        except User.DoesNotExist:
            return False, None, "User not found"
        except Exception as e:
            logger.error(f"Error retrieving user credentials: {e}")
            return False, None, f"Error retrieving credentials: {str(e)}"
