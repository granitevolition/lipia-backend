import socket
import threading
from http.server import HTTPServer
from flask import Flask

import config
import database as db
from app import app
from callback_server import CallbackHandler, start_callback_server

def find_available_port():
    """Find an available port for the callback server"""
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

def main():
    """Main entry point for the application"""
    print(f"Starting Lipia Subscription Service")
    print(f"MongoDB URI: {config.MONGO_URI}")
    
    # Initialize database
    try:
        db.init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    
    # Find available port for callback server
    port = find_available_port()
    if port:
        print(f"Using callback port: {port}")
        
        # Start callback server in background thread
        callback_thread = start_callback_server()
        print("Callback server started")
    else:
        print("Could not find available port for callback server")
    
    # Start Flask application
    print(f"Starting Flask server on port {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)

if __name__ == '__main__':
    main()
