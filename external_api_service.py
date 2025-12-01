"""
External API service for integrating with the DataCollect API
"""

import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service class for interacting with the external DataCollect API"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://api2ego.elisasoftware.com.mx')
        self.username = getattr(settings, 'EXTERNAL_API_USERNAME', 'AdmGPScontrol4u')
        self.password = getattr(settings, 'EXTERNAL_API_PASSWORD', 'GPSc0ntr0l4u*')
        self.store = getattr(settings, 'EXTERNAL_API_STORE', 'GPScontrol4U')
        self.token = None
        self.session = requests.Session()
        
        # Debug: Log the credentials being used
        logger.info(f"External API Config - URL: {self.base_url}, Username: {self.username}, Store: {self.store}")
    
    def authenticate(self):
        """
        Authenticate with the external API and get Bearer token
        Returns True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/login"
            params = {
                'username': self.username,
                'password': self.password
            }
            
            headers = {
                'accept': 'application/json'
            }
            
            response = self.session.post(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200 and 'data' in data:
                    self.token = data['data'].get('token')
                    if self.token:
                        # Set authorization header for future requests
                        self.session.headers.update({
                            'Authorization': self.token,
                            'accept': 'application/json',
                            'Content-Type': 'application/json'
                        })
                        
                        logger.info("External API authentication successful")
                        return True
                        
            logger.error(f"External API authentication failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"External API authentication error: {e}")
            return False
    
    def get_available_plans(self):
        """
        Get available subscription plans from the external API
        Returns list of plans or None if error
        """
        # Check cache first
        cache_key = 'external_api_plans'
        cached_plans = cache.get(cache_key)
        if cached_plans:
            logger.info("Returning cached external API plans")
            return cached_plans
        
        # Authenticate if not already done
        if not self.token:
            if not self.authenticate():
                return None
        
        try:
            url = f"{self.base_url}/store/plans"
            params = {
                'store': self.store
            }
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200 and 'data' in data:
                    plans = data['data']
                    
                    # Process plans to make them more usable
                    processed_plans = []
                    for plan in plans:
                        plan_name = plan.get('name', '').lower()
                        processed_plan = {
                            'id': plan.get('id'),
                            'name': plan.get('name', 'Unknown Plan'),
                            'description': plan.get('description', ''),
                            'price': float(plan.get('price', 0)),
                            'billing_cycle': plan.get('billing_cycle', 'Unknown'),
                            'months': plan.get('months', 12),
                            'admin_users_quantity': plan.get('admin_users_quantity', 0),
                            'subscribed_users_quantity': plan.get('subscribed_users_quantity', 0),
                            'status': plan.get('status', 'Unknown'),
                            'client': plan.get('client', ''),
                            'is_free': 'gratuito' in plan_name or 'free' in plan_name,
                            # Only mark as premium if it's the main team plan, not additional licenses
                            'is_premium': ('equipo' in plan_name or 'premium' in plan_name or 'anual' in plan_name) and 'licencia' not in plan_name and 'adicional' not in plan_name
                        }
                        processed_plans.append(processed_plan)
                    
                    # Cache for 30 minutes
                    cache.set(cache_key, processed_plans, 30 * 60)
                    
                    logger.info(f"Retrieved {len(processed_plans)} plans from external API")
                    return processed_plans
                    
            logger.error(f"Failed to get plans from external API: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting plans from external API: {e}")
            return None
    
    def register_user_rfc(self, rfc_tin, user_data):
        """
        Register user RFC/TIN with external API
        This is a placeholder - will implement when endpoint is provided
        """
        # TODO: Implement when registration endpoint is provided
        logger.info(f"RFC registration placeholder called for: {rfc_tin}")
        return {'success': True, 'message': 'RFC registration simulated'}


# Global instance
external_api = ExternalAPIService()