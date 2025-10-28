from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import data_base, Article, Comment
from datetime import datetime
import re
from models import User
from werkzeug.security import check_password_hash
from jwt_util import jwt_manager

api_bp = Blueprint('api', __name__)

def validate_article(data):
    errors = []

    if not data.get('title') or not data['title'].strip():
        errors.append('Заголовок не может быть пустым')
    
    if not data.get('text') or not data['text'].strip():
        errors.append('Текст статьи не может быть пустым')
    
    return errors

def validate_comment(data):
    errors = []

    if not data.get('text') or not data['text'].strip():
        errors.append('Комментарий не может быть пустым')
    
    if not data.get('article_id'):
        errors.append('ID статьи не может быть пустым')
    else:
        article_id = data['article_id']
        article = data_base.session.get(Article, article_id) 
        if not article:
            errors.append('Статья с указанным ID не найдена')  
    
    return errors


@api_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Данные должны быть в формате JSON'
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'success': False,
            'error': 'Email и пароль обязательны'
        }), 400
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.hashed_password, password):
        return jsonify({
            'success': False,
            'error': 'Неверный email или пароль'
        }), 401
    
    access_token = jwt_manager.create_access_token(user.id, user.email)
    refresh_token = jwt_manager.create_refresh_token(user.id, user.email)
    
    return jsonify({
        'success': True,
        'message': 'Успешная авторизация',
        'tokens': {
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        'user': user.to_dict()
    })

@api_bp.route('/api/auth/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Данные должны быть в формате JSON'
        }), 400
    
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({
            'success': False,
            'error': 'Refresh token обязателен'
        }), 400
    
    new_tokens = jwt_manager.refresh_tokens(refresh_token)
    if not new_tokens:
        return jsonify({
            'success': False,
            'error': 'Невалидный refresh token'
        }), 401
    
    return jsonify({
        'success': True,
        'message': 'Токены обновлены',
        'tokens': new_tokens
    })

@api_bp.route('/api/articles', methods=['GET'])
def get_articles():
    articles = Article.query.all()
    return jsonify({
        'success': True,
        'count': len(articles),
        'articles': [article.to_dict() for article in articles]
    })

@api_bp.route('/api/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.get_or_404(id)
    return jsonify({
        'success': True,
        'article': article.to_dict()
    })

@api_bp.route('/api/articles/category/<string:category>', methods=['GET'])
def get_by_category(category):
    articles = Article.query.filter_by(category=category).all()
    return jsonify({
        'success': True,
        'category': category,
        'count': len(articles),
        'articles': [article.to_dict() for article in articles]
    })  

@api_bp.route('/api/articles/sort/date', methods=['GET'])
def sort_by_date():
    order = request.args.get('order', 'desc').lower()

    if order == 'asc':
        articles = Article.query.order_by(Article.date.asc()).all()
    else:
        articles = Article.query.order_by(Article.date.desc()).all()
    
    return jsonify({
        'success': True,
        'order': order,
        'count': len(articles),
        'articles': [article.to_dict() for article in articles]
    })

@api_bp.route('/api/comments', methods=['GET'])
def get_comments():
    comments = Comment.query.all()
    return jsonify({
        'success': True,
        'count': len(comments),
        'comments': [comment.to_dict() for comment in comments]
    })

@api_bp.route('/api/comments/<int:id>', methods=['GET'])
def get_comment(id):
    comment = Comment.query.get(id)
    if not comment:
        return jsonify({
            'success': False,
            'error': {
                'code': 404,
                'message': 'Комментарий не найден',
                'details': f'Комментарий с ID {id} не существует'
            }
        }), 404
    return jsonify({
        'success': True,
        'comment': comment.to_dict()
    })


@api_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    return jsonify({
        'success': True,
        'user': request.current_user.to_dict()
    })

@api_bp.route('/api/protected/articles', methods=['POST'])
def create_article_jwt():
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False, 
            'error': 'Данные должны быть в формате JSON' 
        }), 400  
    
    errors = validate_article(data)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400
    
    article = Article(
        title=data['title'].strip(),
        text=data['text'].strip(),
        category=data.get('category', 'Общее').strip(),
        author=request.current_user
    )

    data_base.session.add(article)
    data_base.session.commit()

    return jsonify({
        'success': True,
        'message': 'Статья создана',
        'article': article.to_dict()
    })

@api_bp.route('/api/protected/articles/<int:id>', methods=['PUT'])
def update_article_jwt(id):
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    article = data_base.session.get(Article, id) 
    if not article:
        return jsonify({
            'success': False,
            'error': 'Статья не найдена'
        }), 404

    if article.author != request.current_user:
        return jsonify({
            'success': False,
            'error': 'У вас нет прав для редактирования этой статьи'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,  
            'error': 'Данные должны быть в формате JSON'
        }), 400

    errors = validate_article(data)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400  

    article.title = data.get('title', article.title).strip()
    article.text = data.get('text', article.text).strip()
    article.category = data.get('category', article.category).strip()

    data_base.session.commit()
    return jsonify({
        'success': True,
        'message': 'Статья успешно обновлена',
        'article': article.to_dict()
    })

@api_bp.route('/api/protected/articles/<int:id>', methods=['DELETE'])
def delete_article_jwt(id):
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    article = Article.query.get_or_404(id)
    
    if article.author != request.current_user:
        return jsonify({
            'success': False,
            'error': 'У вас нет прав для удаления этой статьи'
        }), 403
    
    Comment.query.filter_by(article_id=id).delete()
        
    data_base.session.delete(article)
    data_base.session.commit()
        
    return jsonify({
        'success': True,
        'message': 'Статья успешно удалена'
    })

@api_bp.route('/api/protected/comments', methods=['POST'])
def create_comment_jwt():
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Данные должны быть в формате JSON'
        }), 400
    
    errors = validate_comment(data)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400
    
    comment = Comment(
        text=data['text'].strip(),
        author_name=request.current_user.email,
        article_id=int(data['article_id'])
    )
        
    data_base.session.add(comment)
    data_base.session.commit()
        
    return jsonify({
        'success': True,
        'message': 'Комментарий успешно создан',
        'comment': comment.to_dict()
    }), 201

@api_bp.route('/api/protected/comments/<int:id>', methods=['PUT'])
def update_comment_jwt(id):
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    comment = Comment.query.get_or_404(id)
    
    if comment.author_name != request.current_user.email:
        return jsonify({
            'success': False,
            'error': 'У вас нет прав для редактирования этого комментария'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Данные должны быть в формате JSON'
        }), 400
    
    errors = []
    if not data.get('text') or not data['text'].strip():
        errors.append('Текст комментария не может быть пустым')
    
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400
    
    comment.text = data['text'].strip()
    data_base.session.commit()
        
    return jsonify({
        'success': True,
        'message': 'Комментарий успешно обновлен',
        'comment': comment.to_dict()
    })

@api_bp.route('/api/protected/comments/<int:id>', methods=['DELETE'])
def delete_comment_jwt(id):
    if not hasattr(request, 'current_user') or not request.current_user:
        return jsonify({
            'success': False,
            'error': 'Требуется авторизация'
        }), 401
    
    comment = Comment.query.get_or_404(id)
    
    if comment.author_name != request.current_user.email:
        return jsonify({
            'success': False,
            'error': 'У вас нет прав для удаления этого комментария'
        }), 403
    
    data_base.session.delete(comment)
    data_base.session.commit()
        
    return jsonify({
        'success': True,
        'message': 'Комментарий успешно удален'
    })