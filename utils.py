import requests
import json
import re
import config

def format_phone_for_api(phone):
    """Format phone number to 07XXXXXXXX format required by API"""
    # Ensure phone is a string
    phone = str(phone)

    # Remove any spaces, quotes or special characters
    phone = ''.join(c for c in phone if c.isdigit())

    # If it starts with 254, convert to local format
    if phone.startswith('254'):
        phone = '0' + phone[3:]

    # Make sure it starts with 0
    if not phone.startswith('0'):
        phone = '0' + phone

    # Ensure it's exactly 10 digits (07XXXXXXXX)
    if len(phone) > 10:
        phone = phone[:10]
    elif len(phone) < 10:
        print(f"Warning: Phone number {phone} is shorter than expected")

    print(f"Original phone: {phone} -> Formatted for API: {phone}")
    return phone

def make_payment_request(phone, amount, callback_url=None):
    """Make a payment request to the payment API"""
    try:
        # Format phone number for API
        formatted_phone = format_phone_for_api(phone)
        
        # Prepare API request
        headers = {
            'Authorization': f'Bearer {config.API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'phone': formatted_phone,
            'amount': str(amount)
        }
        
        # Add callback URL if provided
        if callback_url:
            payload['callback_url'] = callback_url
            
        print(f"Sending payment request with phone: {formatted_phone}, amount: {amount}")

        # Send payment request to API
        response = requests.post(
            f"{config.BASE_URL}/request/stk",
            headers=headers,
            json=payload,
            timeout=30  # Timeout after 30 seconds
        )

        print(f"API Response: {response.status_code} - {response.text}")
        
        return response.status_code, response.json() if response.status_code == 200 else response.text
        
    except requests.exceptions.Timeout:
        return 408, "Request timed out"
    
    except Exception as e:
        return 500, str(e)

def validate_phone_number(phone):
    """Validate phone number format"""
    # Remove any non-digit characters
    phone = re.sub(r'\\D', '', phone)
    
    # Check if the phone number is a valid Kenyan format
    kenyan_pattern = r'^(?:\+?254|0)[17]\d{8}$'
    return re.match(kenyan_pattern, phone) is not None

def validate_pin(pin):
    """Validate PIN format (4 digits)"""
    return pin.isdigit() and len(pin) == 4

def get_subscription_plan(plan_type='basic'):
    """Get subscription plan details"""
    plan_type = plan_type.lower()
    if plan_type in config.SUBSCRIPTION_PLANS:
        return config.SUBSCRIPTION_PLANS[plan_type]
    return config.SUBSCRIPTION_PLANS['basic']  # Default to basic plan

def get_words_for_plan(plan_type='basic'):
    """Get word count for a subscription plan"""
    plan = get_subscription_plan(plan_type)
    return plan.get('words', 100)  # Default to 100 words if not found
