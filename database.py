from pymongo import MongoClient
from datetime import datetime
import os
import config

# Get MongoDB connection string
mongo_uri = os.environ.get('MONGO_URL', config.MONGO_URI)

# Create MongoDB client
try:
    print(f"Connecting to MongoDB at: {mongo_uri}")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful")
    
    # Set database
    db = client[config.MONGO_DB_NAME]
    
    # Collection references
    users_collection = db['users']
    payments_collection = db['payments']
    transactions_collection = db['transactions']
    
except Exception as e:
    print(f"MongoDB connection error: {e}")
    # Create fallback in-memory collections for development
    print("Using in-memory collections for development")
    from pymongo.collection import Collection
    
    class InMemoryCollection:
        def __init__(self, name):
            self.name = name
            self.data = []
            self._id_counter = 1
            
        def insert_one(self, document):
            document['_id'] = self._id_counter
            self._id_counter += 1
            self.data.append(document)
            return type('obj', (object,), {'inserted_id': document['_id']})
            
        def find_one(self, query):
            for doc in self.data:
                match = True
                for k, v in query.items():
                    if k not in doc or doc[k] != v:
                        match = False
                        break
                if match:
                    return doc
            return None
            
        def find(self, query=None):
            if query is None:
                return self.data
            results = []
            for doc in self.data:
                match = True
                for k, v in query.items():
                    if k not in doc or doc[k] != v:
                        match = False
                        break
                if match:
                    results.append(doc)
            return results
            
        def update_one(self, query, update):
            doc = self.find_one(query)
            if doc:
                for k, v in update.get('$set', {}).items():
                    doc[k] = v
                return type('obj', (object,), {'modified_count': 1})
            return type('obj', (object,), {'modified_count': 0})
            
        def create_index(self, key, **kwargs):
            pass
            
        def count_documents(self, query):
            return len(self.find(query))
            
    users_collection = InMemoryCollection('users')
    payments_collection = InMemoryCollection('payments')
    transactions_collection = InMemoryCollection('transactions')
    
    # Add a default admin user
    users_collection.insert_one({
        'username': 'admin',
        'pin': '1234',
        'words_remaining': 1000,
        'phone_number': '0712345678',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })

# Initialize collections with indexes
def init_db():
    """Initialize the database with required indexes"""
    try:
        # Create indexes for users collection
        users_collection.create_index("username", unique=True)
        users_collection.create_index("phone_number")
        
        # Create indexes for payments collection
        payments_collection.create_index("username")
        payments_collection.create_index("checkout_id")
        payments_collection.create_index("reference")
        
        # Create indexes for transactions collection
        transactions_collection.create_index("transaction_id", unique=True)
        transactions_collection.create_index("username")
        
        print("Database indexes created successfully")
        return True
    except Exception as e:
        print(f"Error creating database indexes: {e}")
        return False

# User functions
def user_exists(username):
    """Check if a user exists in the database"""
    return users_collection.count_documents({"username": username}) > 0

def get_user_data(username):
    """Get user data from the database"""
    user = users_collection.find_one({"username": username})
    if user:
        # Convert ObjectId to string for JSON serialization
        user['_id'] = str(user['_id'])
        # Ensure phone_number is a string
        if 'phone_number' in user:
            user['phone_number'] = str(user['phone_number'])
        return user
    return None

def create_user(username, pin, phone_number=None):
    """Create a new user in the database"""
    new_user = {
        "username": username,
        "pin": pin,
        "words_remaining": 0,
        "phone_number": phone_number,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = users_collection.insert_one(new_user)
    return result.inserted_id is not None

def update_word_count(username, words_to_add):
    """Update a user's word count"""
    user = users_collection.find_one({"username": username})
    if not user:
        return None
    
    current_words = int(user.get('words_remaining', 0))
    new_word_count = current_words + words_to_add
    
    result = users_collection.update_one(
        {"username": username},
        {
            "$set": {
                "words_remaining": new_word_count,
                "updated_at": datetime.now()
            }
        }
    )
    
    return new_word_count if result.modified_count > 0 else None

def consume_words(username, words_to_use):
    """Deduct words from a user's account"""
    user = users_collection.find_one({"username": username})
    if not user:
        return False, 0
    
    current_words = int(user.get('words_remaining', 0))
    
    if current_words < words_to_use:
        return False, current_words
    
    new_word_count = current_words - words_to_use
    
    result = users_collection.update_one(
        {"username": username},
        {
            "$set": {
                "words_remaining": new_word_count,
                "updated_at": datetime.now()
            }
        }
    )
    
    return result.modified_count > 0, new_word_count

# Payment and transaction functions
def record_payment(username, amount, subscription_type, status='pending', reference='N/A', checkout_id='N/A'):
    """Record a payment in the database"""
    payment = {
        "username": username,
        "amount": amount,
        "reference": reference,
        "checkout_id": checkout_id,
        "subscription_type": subscription_type,
        "timestamp": datetime.now(),
        "status": status
    }
    
    result = payments_collection.insert_one(payment)
    return result.inserted_id is not None

def get_payments_by_username(username):
    """Get all payments for a user"""
    payments = list(payments_collection.find({"username": username}))
    for payment in payments:
        payment['_id'] = str(payment['_id'])
        # Ensure timestamp is properly serialized
        if isinstance(payment.get('timestamp'), datetime):
            payment['timestamp'] = payment['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    return payments

def save_transaction(transaction_id, data):
    """Save transaction data to the database"""
    # Ensure timestamp is a datetime object
    if 'timestamp' in data and isinstance(data['timestamp'], str):
        try:
            data['timestamp'] = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            data['timestamp'] = datetime.now()
    
    data['transaction_id'] = transaction_id
    data['created_at'] = datetime.now()
    data['updated_at'] = datetime.now()
    
    # Use upsert to create or update
    result = transactions_collection.update_one(
        {"transaction_id": transaction_id},
        {"$set": data},
        upsert=True
    )
    
    return result.upserted_id is not None or result.modified_count > 0

def get_transaction(transaction_id):
    """Get transaction data from the database"""
    transaction = transactions_collection.find_one({"transaction_id": transaction_id})
    if transaction:
        transaction['_id'] = str(transaction['_id'])
        # Convert datetime objects to strings
        for key in ['timestamp', 'created_at', 'updated_at']:
            if key in transaction and isinstance(transaction[key], datetime):
                transaction[key] = transaction[key].strftime('%Y-%m-%d %H:%M:%S')
    return transaction

def update_transaction_status(transaction_id, status, reference=None):
    """Update transaction status and reference"""
    update_data = {
        "status": status,
        "updated_at": datetime.now()
    }
    
    if reference:
        update_data["reference"] = reference
    
    result = transactions_collection.update_one(
        {"transaction_id": transaction_id},
        {"$set": update_data}
    )
    
    return result.modified_count > 0
