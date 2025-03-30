import threading
import json
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler

import config
import database as db
import utils

# Global queue for callback data
CALLBACK_QUEUE = queue.Queue()

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Lipia Callback Server')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            # Parse the JSON data from the callback
            callback_data = json.loads(post_data.decode('utf-8'))

            # Put the callback data in the queue for processing
            CALLBACK_QUEUE.put(callback_data)

            # Process the callback data
            self.process_callback(callback_data)

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
    
    def process_callback(self, callback_data):
        """Process payment callback data"""
        try:
            checkout_id = callback_data.get('CheckoutRequestID')
            if not checkout_id:
                print("No checkout ID in callback data")
                return

            # Look up transaction
            transaction = db.get_transaction(checkout_id)
            if not transaction:
                print(f"Transaction {checkout_id} not found")
                return

            # Update transaction status
            reference = callback_data.get('reference')
            db.update_transaction_status(checkout_id, 'completed', reference)

            # Update payment record
            username = transaction['username']
            amount = transaction['amount']
            subscription_type = transaction['subscription_type']

            # Record payment
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
            
            print(f"Payment processed successfully for {username}: {words_to_add} words added")
        
        except Exception as e:
            print(f"Error processing callback: {e}")

def run_callback_server():
    """Start callback server in a separate thread"""
    server = HTTPServer((config.CALLBACK_HOST, config.CALLBACK_PORT), CallbackHandler)
    print(f"Starting callback server on {config.CALLBACK_HOST}:{config.CALLBACK_PORT}")
    server.serve_forever()

def start_callback_server():
    """Start the callback server in a background thread"""
    callback_thread = threading.Thread(target=run_callback_server, daemon=True)
    callback_thread.start()
    return callback_thread

def check_callbacks():
    """Check for callbacks in the queue and process them"""
    while not CALLBACK_QUEUE.empty():
        callback_data = CALLBACK_QUEUE.get_nowait()
        process_callback(callback_data)

def process_callback(callback_data):
    """Process payment callback data"""
    try:
        checkout_id = callback_data.get('CheckoutRequestID')
        if not checkout_id:
            print("No checkout ID in callback data")
            return

        # Look up transaction
        transaction = db.get_transaction(checkout_id)
        if not transaction:
            print(f"Transaction {checkout_id} not found")
            return

        # Update transaction status
        reference = callback_data.get('reference')
        db.update_transaction_status(checkout_id, 'completed', reference)

        # Update payment record
        username = transaction['username']
        amount = transaction['amount']
        subscription_type = transaction['subscription_type']

        # Record payment
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
        
        print(f"Payment processed successfully for {username}: {words_to_add} words added")
    
    except Exception as e:
        print(f"Error processing callback: {e}")
