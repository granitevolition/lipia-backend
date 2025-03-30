from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import threading
import socket
from datetime import datetime
import queue

import config
import database as db
import utils

app = Flask(__name__)
CORS(app)

# Callback queue for payment notifications
CALLBACK_QUEUE = queue.Queue()

# Find an available port for the callback server
def find_available_port():
    global config
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in range(8000, 9000):
        try:
            s.bind((config.CALLBACK_HOST, port))
            config.CALLBACK_PORT = port
            s.close()
            return port
        except:
            continue
    s.close()
    return None

# Routes
@app.route('/')
def index():
    return jsonify({
        'service': 'Lipia Subscription Service API',
        'version': '1.0.0',
        'status': 'active'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'mongodb': 'connected' if db.db.command('ping').get('ok') == 1.0 else 'error',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    username = data.get('username')
    pin = data.get('pin')
    phone_number = data.get('phone_number')
    
    if not username or not pin:
        return jsonify({'error': 'Username and PIN are required'}), 400
    
    # Validate PIN (4 digits)
    if not utils.validate_pin(pin):
        return jsonify({'error': 'PIN must be 4 digits'}), 400
    
    # Check if user already exists
    if db.user_exists(username):
        return jsonify({'error': 'Username already exists'}), 409
    
    # Create user
    success = db.create_user(username, pin, phone_number)
    
    if success:
        return jsonify({'message': 'User registered successfully', 'username': username}), 201
    else:
        return jsonify({'error': 'Failed to register user'}), 500

@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    username = data.get('username')
    pin = data.get('pin')
    
    if not username or not pin:
        return jsonify({'error': 'Username and PIN are required'}), 400
    
    # Get user data
    user = db.get_user_data(username)
    
    # Check if user exists and PIN matches
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.get('pin') != pin:
        return jsonify({'error': 'Invalid PIN'}), 401
    
    # Return user data (excluding PIN)
    user.pop('pin', None)
    return jsonify({'message': 'Login successful', 'user': user}), 200

@app.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    # Get user data
    user = db.get_user_data(username)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove sensitive information
    user.pop('pin', None)
    
    return jsonify(user), 200

@app.route('/api/users/<username>/payments', methods=['GET'])
def get_user_payments(username):
    # Check if user exists
    if not db.user_exists(username):
        return jsonify({'error': 'User not found'}), 404
    
    # Get user payments
    payments = db.get_payments_by_username(username)
    
    return jsonify(payments), 200

@app.route('/api/payments/initiate', methods=['POST'])
def initiate_payment():
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    username = data.get('username')
    phone = data.get('phone')
    plan_type = data.get('plan_type', 'basic')
    
    if not username or not phone:
        return jsonify({'error': 'Username and phone are required'}), 400
    
    # Check if user exists
    if not db.user_exists(username):
        return jsonify({'error': 'User not found'}), 404
    
    # Get subscription plan details
    plan = utils.get_subscription_plan(plan_type)
    amount = plan.get('amount')
    
    # Build callback URL
    callback_url = f"http://{config.CALLBACK_HOST}:{config.CALLBACK_PORT}/api/payments/callback"
    
    # Make payment request
    status_code, response_data = utils.make_payment_request(phone, amount, callback_url)
    
    if status_code != 200:
        return jsonify({'error': 'Payment initiation failed', 'details': response_data}), status_code
    
    # Handle successful response
    response_json = response_data if isinstance(response_data, dict) else json.loads(response_data)
    
    if 'message' in response_json and response_json['message'] == 'callback received successfully' and 'data' in response_json:
        data = response_json['data']
        checkout_id = data.get('CheckoutRequestID')
        reference = data.get('refference')  # Note: API uses "refference" with two f's
        
        # Record payment as completed
        db.record_payment(
            username,
            amount,
            plan_type,
            'completed',
            reference,
            checkout_id
        )
        
        # Save transaction
        transaction_data = {
            'checkout_id': checkout_id,
            'username': username,
            'amount': amount,
            'phone': phone,
            'subscription_type': plan_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed',
            'reference': reference
        }
        db.save_transaction(checkout_id, transaction_data)
        
        # Update word count
        words_to_add = utils.get_words_for_plan(plan_type)
        new_word_count = db.update_word_count(username, words_to_add)
        
        return jsonify({
            'message': 'Payment processed successfully',
            'checkout_id': checkout_id,
            'reference': reference,
            'words_added': words_to_add,
            'new_word_count': new_word_count
        }), 200
    
    elif 'data' in response_json and 'CheckoutRequestID' in response_json['data']:
        # Payment pending callback
        checkout_id = response_json['data']['CheckoutRequestID']
        
        # Record pending payment
        db.record_payment(
            username,
            amount,
            plan_type,
            'pending',
            'N/A',
            checkout_id
        )
        
        # Save transaction
        transaction_data = {
            'checkout_id': checkout_id,
            'username': username,
            'amount': amount,
            'phone': phone,
            'subscription_type': plan_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }
        db.save_transaction(checkout_id, transaction_data)
        
        return jsonify({
            'message': 'Payment initiated',
            'checkout_id': checkout_id,
            'status': 'pending'
        }), 202
    
    else:
        # Handle error message from API
        error_msg = response_json.get('message', 'Unknown error')
        
        # Record failed payment
        db.record_payment(username, amount, plan_type, 'failed')
        
        return jsonify({'error': error_msg}), 400

@app.route('/api/payments/callback', methods=['POST'])
def payment_callback():
    # Get callback data
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid callback data'}), 400
    
    # Put callback data in queue for processing
    CALLBACK_QUEUE.put(data)
    
    # Process the callback data
    checkout_id = data.get('CheckoutRequestID')
    
    if not checkout_id:
        return jsonify({'error': 'Invalid checkout ID'}), 400
    
    # Get transaction data
    transaction = db.get_transaction(checkout_id)
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    # Update transaction status
    reference = data.get('reference')
    db.update_transaction_status(checkout_id, 'completed', reference)
    
    # Update payment record
    username = transaction['username']
    amount = transaction['amount']
    subscription_type = transaction['subscription_type']
    
    # Record completed payment
    db.record_payment(
        username,
        amount,
        subscription_type,
        'completed',
        reference,
        checkout_id
    )
    
    # Update word count
    words_to_add = utils.get_words_for_plan(subscription_type)
    new_word_count = db.update_word_count(username, words_to_add)
    
    return jsonify({
        'message': 'Callback processed successfully',
        'checkout_id': checkout_id,
        'reference': reference,
        'words_added': words_to_add,
        'new_word_count': new_word_count
    }), 200

@app.route('/api/payments/<checkout_id>/status', methods=['GET'])
def payment_status(checkout_id):
    # Get transaction data
    transaction = db.get_transaction(checkout_id)
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    return jsonify({
        'checkout_id': checkout_id,
        'status': transaction.get('status', 'unknown'),
        'reference': transaction.get('reference', 'N/A'),
        'timestamp': transaction.get('timestamp'),
        'amount': transaction.get('amount'),
        'subscription_type': transaction.get('subscription_type')
    }), 200

@app.route('/api/words/consume', methods=['POST'])
def consume_words():
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    username = data.get('username')
    words = data.get('words')
    
    if not username or not words:
        return jsonify({'error': 'Username and word count are required'}), 400
    
    try:
        words = int(words)
        if words <= 0:
            return jsonify({'error': 'Word count must be a positive number'}), 400
    except ValueError:
        return jsonify({'error': 'Word count must be a number'}), 400
    
    # Consume words
    success, remaining = db.consume_words(username, words)
    
    if success:
        return jsonify({
            'message': f'Successfully consumed {words} words',
            'words_used': words,
            'words_remaining': remaining
        }), 200
    else:
        return jsonify({
            'error': 'Insufficient words',
            'words_requested': words,
            'words_available': remaining
        }), 400

if __name__ == '__main__':
    # Find available port for callback server and start app
    port = find_available_port() or config.CALLBACK_PORT
    print(f"Using callback port: {port}")
    
    # Start Flask application
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)
