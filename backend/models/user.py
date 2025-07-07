from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from backend.utils.db import get_db

class User:
    ROLES = ['public', 'responder', 'admin']
    
    def __init__(self, username, email, password, role='public', phone=None):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role if role in self.ROLES else 'public'
        self.phone = phone
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_active = True
        
    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password='',  # Password not returned for security
                role=user_data['role'],
                phone=user_data.get('phone')
            )
            user._id = user_data['_id']
            user.created_at = user_data['created_at']
            user.updated_at = user_data['updated_at']
            user.is_active = user_data['is_active']
            return user
        return None
    
    @staticmethod
    def get_by_email(email):
        db = get_db()
        user_data = db.users.find_one({'email': email})
        if user_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password='',  # Password not returned for security
                role=user_data['role'],
                phone=user_data.get('phone')
            )
            user._id = user_data['_id']
            user.password_hash = user_data['password_hash']
            user.created_at = user_data['created_at']
            user.updated_at = user_data['updated_at']
            user.is_active = user_data['is_active']
            return user
        return None
    
    @staticmethod
    def get_by_username(username):
        db = get_db()
        user_data = db.users.find_one({'username': username})
        if user_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password='',  # Password not returned for security
                role=user_data['role'],
                phone=user_data.get('phone')
            )
            user._id = user_data['_id']
            user.password_hash = user_data['password_hash']
            user.created_at = user_data['created_at']
            user.updated_at = user_data['updated_at']
            user.is_active = user_data['is_active']
            return user
        return None
    
    def save(self):
        db = get_db()
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'phone': self.phone,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }
        
        if hasattr(self, '_id'):
            db.users.update_one(
                {'_id': self._id},
                {'$set': user_data}
            )
        else:
            result = db.users.insert_one(user_data)
            self._id = result.inserted_id
            
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': str(self._id),
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }