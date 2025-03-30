# Lipia Backend

MongoDB-backed backend for the Lipia subscription service.

## Overview

This is a Python Flask REST API that provides backend services for the Lipia subscription system. It stores user data, payments, and transactions in MongoDB and integrates with payment services.

Key features:
- User registration and authentication
- Subscription management
- Payment processing with callbacks
- Word count tracking and consumption
- MongoDB database integration

## Requirements

- Python 3.8+
- MongoDB
- Flask
- PyMongo

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/granitevolition/lipia-backend.git
   cd lipia-backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and configure it:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file with your MongoDB connection details and other settings.

## Configuration

The following environment variables can be configured:

### MongoDB Connection
- `MONGO_PUBLIC_URL`: MongoDB connection string
- `MONGO_DB_NAME`: Database name

### API Settings
- `API_KEY`: API key for authentication

### Service Configuration
- `BASE_URL`: Base URL for the payment API
- `PAYMENT_URL`: Payment URL for the frontend
- `CALLBACK_HOST`: Callback server host
- `CALLBACK_PORT`: Callback server port

### Application Settings
- `DEBUG`: Enable debug mode (True/False)
- `PORT`: Application port

## Running the Server

Start the application:

```
python server.py
```

For production deployment, use gunicorn:

```
gunicorn server:app
```

## API Endpoints

### User Management
- `POST /api/users/register`: Register a new user
- `POST /api/users/login`: Login a user
- `GET /api/users/<username>`: Get user information
- `GET /api/users/<username>/payments`: Get user payments

### Payment Processing
- `POST /api/payments/initiate`: Initiate a payment
- `GET /api/payments/<checkout_id>/status`: Check payment status
- `POST /api/payments/callback`: Payment callback endpoint

### Word Management
- `POST /api/words/consume`: Consume words from a user's account

### System
- `GET /api/health`: Health check endpoint

## Integration with Frontend

The Python client (`client.py`) provides an easy way to integrate with the frontend. Example usage:

```python
from client import LipiaClient

client = LipiaClient()

# Register a user
status, data = client.register_user('username', '1234', '0712345678')

# Login a user
status, data = client.login_user('username', '1234')

# Initiate payment
status, data = client.initiate_payment('username', '0712345678', 'premium')
```

## Deployment

This application can be deployed on Railway, Heroku, or any other platform that supports Python applications. The included Procfile is configured for such deployments.

## MongoDB Schema

### Users Collection
- `username`: Unique identifier
- `pin`: Authentication PIN
- `words_remaining`: Number of words remaining
- `phone_number`: User's phone number
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### Payments Collection
- `username`: User who made the payment
- `amount`: Payment amount
- `reference`: Payment reference number
- `checkout_id`: Payment checkout ID
- `subscription_type`: Subscription plan type
- `timestamp`: Payment timestamp
- `status`: Payment status (pending, completed, failed)

### Transactions Collection
- `transaction_id`: Unique transaction identifier
- `username`: User who initiated the transaction
- `amount`: Transaction amount
- `phone`: Phone used for payment
- `subscription_type`: Subscription plan type
- `timestamp`: Transaction timestamp
- `status`: Transaction status
- `reference`: Payment reference (when completed)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

## License

MIT
