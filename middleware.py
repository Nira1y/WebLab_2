from flask import request, jsonify, g
from jwt_util import jwt_manager
from models import User
import jwt
import datetime

def jwt_middleware():
    if request.method == 'OPTIONS':
        return
    protected_endpoints = {
        'api.get_current_user',       
        'api.create_article_jwt',    
        'api.update_article_jwt',      
        'api.delete_article_jwt',      
        'api.create_comment_jwt',     
        'api.update_comment_jwt',      
        'api.delete_comment_jwt'       
    }
    
    if not request.endpoint or request.endpoint not in protected_endpoints:
        return
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'success': False,
            'error': 'Токен отсутствует. Используйте: Bearer <token>'
        }), 401
    
    token = auth_header.split(' ')[1]
    payload = jwt_manager.verify_token(token)
    
    if not payload:
        refresh_token = request.headers.get('X-Refresh-Token')
        if refresh_token:
            try:
                refresh_payload = jwt.decode(refresh_token, jwt_manager.secret_key, algorithms=['HS256'])
                
                if refresh_payload.get('type') == 'refresh':
                    user = User.query.get(refresh_payload['user_id'])
                    if user:
                        new_access_token = jwt_manager.create_access_token(user.id, user.email)
                        
                        refresh_exp = refresh_payload['exp']
                        now = datetime.datetime.utcnow()
                        time_until_expiry = datetime.datetime.fromtimestamp(refresh_exp) - now
                        
                        new_refresh_token = None
                        if time_until_expiry < datetime.timedelta(days=7):
                            new_refresh_token = jwt_manager.create_refresh_token(user.id, user.email)
                        
                        g.new_access_token = new_access_token
                        if new_refresh_token:
                            g.new_refresh_token = new_refresh_token
                        
                        request.current_user = user
                        return
                        
            except jwt.ExpiredSignatureError:
                return jsonify({
                    'success': False,
                    'error': 'Refresh token истек. Требуется повторная авторизация'
                }), 401
            except jwt.InvalidTokenError:
                pass
        
        return jsonify({
            'success': False,
            'error': 'Неверный или просроченный токен'
        }), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({
            'success': False,
            'error': 'Пользователь не найден'
        }), 401
    
    request.current_user = user