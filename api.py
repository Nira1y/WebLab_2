from flask import Blueprint, request, jsonify, g
from models import data_base, Article, Comment
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

@api_bp.after_request
def add_token_headers(response):
    if (response.status_code in [200, 201] and 
        hasattr(g, 'new_access_token')):
        
        response.headers['X-New-Access-Token'] = g.new_access_token
        if hasattr(g, 'new_refresh_token') and g.new_refresh_token:
            response.headers['X-New-Refresh-Token'] = g.new_refresh_token

        if hasattr(g, 'new_access_token'):
            del g.new_access_token
        if hasattr(g, 'new_refresh_token'):
            del g.new_refresh_token
    
    return response

@api_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Данные должны быть в формате JSON'
        }), 400
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({
            'success': False,
            'error': 'Все поля обязательны'
        }), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            'success': False,
            'error': 'Пользователь с таким email уже существует'
        }), 400
    
    user = User(name=name, email=email)
    user.set_password(password)
    
    data_base.session.add(user)
    data_base.session.commit()

    access_token = jwt_manager.create_access_token(user.id, user.email)
    refresh_token = jwt_manager.create_refresh_token(user.id, user.email)
    
    return jsonify({
        'success': True,
        'message': 'Регистрация прошла успешно',
        'tokens': {
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        'user': user.to_dict()
    })

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
    
    g.new_access_token = new_tokens['access_token']
    g.new_refresh_token = new_tokens.get('refresh_token')
    
    return jsonify({
        'success': True,
        'message': 'Токены обновлены',
        'tokens': new_tokens
    })

@api_bp.route('/api/articles', methods=['GET'])
def get_articles():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    order = request.args.get('order', 'desc')
    
    query = Article.query
    
    if category:
        query = query.filter(Article.category == category)
    
    if search:
        query = query.filter(Article.title.ilike(f'%{search}%'))
    
    if order == 'asc':
        query = query.order_by(Article.date.asc())
    else:
        query = query.order_by(Article.date.desc())

    articles = query.paginate(
        page=page, 
        per_page=limit, 
        error_out=False
    )
    
    return jsonify({
        'success': True,
        'count': articles.total,
        'page': page,
        'pages': articles.pages,
        'articles': [article.to_dict() for article in articles.items]
    })

@api_bp.route('/api/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.get_or_404(id)
    return jsonify({
        'success': True,
        'article': article.to_dict()
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

@api_bp.route('/api/auth/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
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

@api_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': 'Успешный выход из системы'
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