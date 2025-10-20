from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
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
        article = article.query.get(article_id)
        if not article:
            errors.append('Сатья с указанным ID не найдена')
    
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
    data = request.get_json()
    if not data:
        return jsonify({
            'saccess': False,
            'error': 'Данные должны быть в фомате JSON'
        })
    
    errors = validate_article(data)
    if errors:
        return jsonify({
            'success': False,
            'errors':errors
        }), 404
    
    article = Article(
        title = data['title'].strip(),
        text = data['text'].strip(),
        category = data.get('category', 'Общее').strip(),
        author=current_user
    )

    data_base.session.add(article)
    data_base.session.commit()

    return jsonify({
        'success': True,
        'message': 'Статья создана',
        'article': article.to_dict()
    })


@api_bp.route('/api/articles/<int:id>', methods = ['PUT'])
@login_required
def update_article(id):
    article = Article.query.get_or_404(id)

    if article.author != current_user:
        return jsonify({
            'success': False,
            'error': 'У вас нет прав для редактирования этой статьи'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({
            'success': True,
            'error': 'Данные должны быть в формате JSON'
        }),400

    errors = validate_article(data)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        })

    article.title = data['title'].strip()
    article.text = data['text'].strip()
    article.category = data.get('category', 'Общая').strip()

    data_base.session.commit()
    return jsonify({
        'success': True,
        'message': 'Статья успешно создана',
        'article': article.to_dict()
    })
