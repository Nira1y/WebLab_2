from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import data_base, Article, Comment
from datetime import datetime
import re

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


@api_bp.route('/api/articles', methods=['POST'])
def create_article():
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для создания статьи необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
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
        author=current_user
    )

    data_base.session.add(article)
    data_base.session.commit()

    return jsonify({
        'success': True,
        'message': 'Статья создана',
        'article': article.to_dict()
    })

@api_bp.route('/api/articles/<int:id>', methods=['PUT'])
def update_article(id):
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для редактирования статьи необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
        }), 401
    
    article = data_base.session.get(Article, id) 
    if not article:
        return jsonify({
            'success': False,
            'error': 'Статья не найдена'
        }), 404

    if article.author != current_user:
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

@api_bp.route('/api/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для удаления статьи необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
        }), 401
    
    article = Article.query.get_or_404(id)
    
    if article.author != current_user:
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

@api_bp.route('/api/comment', methods=['GET'])
def get_comments():
    comments = Comment.query.all()
    return jsonify({
        'success': True,
        'count': len(comments),
        'comments': [comment.to_dict() for comment in comments]
    })

@api_bp.route('/api/comment/<int:id>', methods=['GET'])
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

@api_bp.route('/api/comment', methods=['POST'])
def create_comment():
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для создания комментария необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
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
        author_name=current_user.email,
        article_id=int(data['article_id'])
    )
        
    data_base.session.add(comment)
    data_base.session.commit()
        
    return jsonify({
        'success': True,
        'message': 'Комментарий успешно создан',
        'comment': comment.to_dict()
    }), 201

@api_bp.route('/api/comment/<int:id>', methods=['PUT'])
def update_comment(id):
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для редактирования комментария необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
        }), 401
    
    comment = Comment.query.get_or_404(id)
    
    if comment.author_name != current_user.email:
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

@api_bp.route('/api/comment/<int:id>', methods=['DELETE'])
def delete_comment(id):
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': {
                'code': 401,
                'message': '🔐 Требуется авторизация',
                'details': 'Для удаления комментария необходимо войти в систему'
            },
            'authentication': {
                'login_url': '/login',
                'register_url': '/register'
            }
        }), 401
    
    comment = Comment.query.get_or_404(id)
    
    if comment.author_name != current_user.email:
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