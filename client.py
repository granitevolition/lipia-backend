import os
import requests
import json
from datetime import datetime

class LipiaClient:
    """Client for interacting with the Lipia API"""
    
    def __init__(self, base_url=None, api_key=None):
        """Initialize the client with API settings"""
        self.base_url = base_url or os.environ.get('LIPIA_API_URL', 'http://localhost:5000/api')
        self.api_key = api_key or os.environ.get('LIPIA_API_KEY', '')
        self.timeout = 30  # Request timeout in seconds
    
    def register_user(self, username, pin, phone_number=None):
        """Register a new user"""
        try:
            payload = {
                'username': username,
                'pin': pin
            }
            
            if phone_number:
                payload['phone_number'] = phone_number
            
            response = requests.post(
                f"{self.base_url}/users/register",
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 201 else response.text
        except Exception as e:
            return 500, str(e)
    
    def login_user(self, username, pin):
        """Login a user"""
        try:
            payload = {
                'username': username,
                'pin': pin
            }
            
            response = requests.post(
                f"{self.base_url}/users/login",
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)
    
    def get_user(self, username):
        """Get user data"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}",
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)
    
    def get_user_payments(self, username):
        """Get user payments"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}/payments",
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)
    
    def initiate_payment(self, username, phone, plan_type='basic'):
        """Initiate a payment"""
        try:
            payload = {
                'username': username,
                'phone': phone,
                'plan_type': plan_type
            }
            
            response = requests.post(
                f"{self.base_url}/payments/initiate",
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code in [200, 202] else response.text
        except Exception as e:
            return 500, str(e)
    
    def get_payment_status(self, checkout_id):
        """Get payment status"""
        try:
            response = requests.get(
                f"{self.base_url}/payments/{checkout_id}/status",
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)
    
    def consume_words(self, username, words):
        """Consume words from a user's account"""
        try:
            payload = {
                'username': username,
                'words': words
            }
            
            response = requests.post(
                f"{self.base_url}/words/consume",
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)
    
    def health_check(self):
        """Check API health"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            
            return response.status_code, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return 500, str(e)

# Example usage
if __name__ == '__main__':
    client = LipiaClient()
    
    # Check API health
    status, data = client.health_check()
    print(f"API Health: {status}")
    print(json.dumps(data, indent=2) if isinstance(data, dict) else data)
