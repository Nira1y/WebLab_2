import jwt
import datetime
from flask import current_app, request, jsonify
from functools import wraps
from models import User

class JWTManager: 
    def __init__(self):
        self.secret_key = 'your-secret-key-change-in-production'
        self.access_token_expires = datetime.timedelta(hours=1)
        self.refresh_token_expires = datetime.timedelta(days=30)
    
    def create_access_token(self, user_id, email):
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.datetime.utcnow() + self.access_token_expires,
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def create_refresh_token(self, user_id, email):
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.datetime.utcnow() + self.refresh_token_expires, 
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_tokens(self, refresh_token):
        payload = self.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None
        
        user = User.query.get(payload['user_id']) 
        if not user:
            return None

        return {
            'access_token': self.create_access_token(user.id, user.email),
            'refresh_token': self.create_refresh_token(user.id, user.email),
        }

jwt_manager = JWTManager()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')  
        if auth_header and auth_header.startswith('Bearer '):  
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Токен отсутствует'
            }), 401
        
        payload = jwt_manager.verify_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Невалидный или просроченный токен'
            }), 401
        
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден'
            }), 401
        
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated