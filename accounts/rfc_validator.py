import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class RFCValidatorService:
    """Service to validate RFC/TIN against external API"""
    def __init__(self):
        self.base_url = getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://api2ego.elisasoftware.com.mx')
        self.username = getattr(settings, 'EXTERNAL_API_USERNAME', 'AdmGPScontrol4u')
        self.password = getattr(settings, 'EXTERNAL_API_PASSWORD', 'GPSc0ntr0l4u*')
        self.store = getattr(settings, 'EXTERNAL_API_STORE', 'GPScontrol4U')
        self.token = None
        self.session = requests.Session()

    def authenticate(self):
        url = f"{self.base_url}/login"
        params = {
            'username': self.username,
            'password': self.password
        }
        headers = {'accept': 'application/json'}
        response = self.session.post(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200 and 'data' in data:
                self.token = data['data'].get('token')
                return True
        return False

    def validate_rfc(self, rfc_tin):
        if not self.token:
            if not self.authenticate():
                return False, _('No se pudo autenticar con la API externa')

        url = f"{self.base_url}/store/client/subscription"
        params = {
            'rfc': rfc_tin,
            'store': self.store
        }
        headers = {
            'accept': 'application/json',
            'Authorization': self.token
        }
        response = self.session.get(url, params=params, headers=headers, timeout=10)
        #print(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            # If code 200 and data is empty → RFC already exists → deny
            if data.get('code') == 200 and data.get('data') == []:
                return False, _('El RFC/TIN ya existe en el sistema')
            
            # If code 200 and data has subscriptions → RFC already exists → deny
            if data.get('code') == 200 and isinstance(data.get('data'), list) and len(data.get('data', [])) > 0:
                return False, _('El RFC/TIN ya existe en el sistema')

        if response.status_code == 503:
            data = response.json()
            # If code 503 and message matches "no corresponde..." → RFC does not exist → allow
            if data.get('code') == 503 and "no corresponde" in data.get('message', ''):
                return True, None

        # Fallback → unexpected error
        return False, _('No se pudo validar el RFC/TIN en este momento, intente más tarde')