# auth_handlers.py
from flask import request, jsonify
from jwt_util import jwt_manager
from models import User

def jwt_middleware():
    """Middleware для проверки JWT токена по именам эндпоинтов"""
    
    # Все защищенные эндпоинты
    protected_endpoints = {
        'api.get_current_user',        # GET /api/auth/me
        'api.create_article_jwt',      # POST /api/protected/articles
        'api.update_article_jwt',      # PUT /api/protected/articles/1
        'api.delete_article_jwt',      # DELETE /api/protected/articles/1
        'api.create_comment_jwt',      # POST /api/protected/comments
        'api.update_comment_jwt',      # PUT /api/protected/comments/1
        'api.delete_comment_jwt'       # DELETE /api/protected/comments/1
    }
    
    # Если эндпоинт не защищенный - выходим
    if not request.endpoint or request.endpoint not in protected_endpoints:
        return
    
    # Проверяем JWT токен
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'success': False,
            'error': 'Токен отсутствует. Используйте: Bearer <token>'
        }), 401
    
    token = auth_header.split(' ')[1]
    payload = jwt_manager.verify_token(token)
    
    if not payload:
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