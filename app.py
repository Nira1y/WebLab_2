from api import api_bp
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date
import re
from models import data_base, User, Article, Comment
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import unquote
from jwt_util import jwt_manager

app = Flask(__name__)
app.secret_key = 'dev-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

data_base.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page' 
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
app.register_blueprint(api_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        data_base.create_all() 
        
        test_user = User.query.filter_by(email='developer@test.com').first()
        
        if not test_user:
            test_user = User(
                name='Разработчик', 
                email='developer@test.com',
                hashed_password=generate_password_hash('123456')
            )
            data_base.session.add(test_user)
            data_base.session.commit()
            
            articles_data = [
                {
                    'title': 'Первая новость',
                    'text': 'Текст первой новости',
                    'category': 'Общее'
                },
                {
                    'title': 'Вторая новость',
                    'text': 'Текст второй новости', 
                    'category': 'Наука и технологии'
                },
                {
                    'title': 'Третья новость', 
                    'text': 'Текст третьей новости',
                    'category': 'Культура'
                }
            ]
                
            for article_data in articles_data:
                if not Article.query.filter_by(title=article_data['title']).first():
                    article = Article(
                        title=article_data['title'],
                        text=article_data['text'],
                        category=article_data['category'],
                        author=test_user  
                    )
                    data_base.session.add(article)
                
            data_base.session.commit()

@app.before_request
def before_request():
    if not current_user.is_authenticated:
        jwt_token = request.cookies.get('jwt_token')
        if jwt_token:
            payload = jwt_manager.verify_token(jwt_token)
            if payload:
                user = User.query.get(payload['user_id'])
                if user:
                    login_user(user)

@app.route("/index")
@app.route("/")
def index():
    articles = Article.query.order_by(Article.date.desc()).limit(6).all()
    return render_template('index.html', articles=articles, current_date=date.today())

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        errors = []
        
        if not name:
            errors.append('Имя обязательно для заполнения')
        
        if not email:
            errors.append('Email обязателен для заполнения')
        elif not re.match(r'^[a-zA-Z0-9.]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Введите корректный email адрес')
        
        if not message:
            errors.append('Сообщение обязательно для заполнения')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            flash('Сообщение успешно отправлено!', 'success')
            return render_template('feedback.html', 
                                 name=name, 
                                 email=email, 
                                 message=message,
                                 submitted=True)
    
    return render_template('feedback.html')
        
@app.route('/news/<int:id>', methods=['GET', 'POST'])
def news_article(id):
    article = Article.query.get_or_404(id)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Для добавления комментариев необходимо войти в систему', 'error')
            return redirect(url_for('login_page', next=request.url))
        
        comment_text = request.form.get('comment_text')
        
        if comment_text:
            comment = Comment(
                text=comment_text,
                author_name=current_user.email, 
                article_id=id
            ) 
            
            data_base.session.add(comment)
            data_base.session.commit()
            flash('Комментарий успешно добавлен!', 'success')
            return redirect(url_for('news_article', id=id))
        else:
            flash('Заполните текст комментария', 'error')
            return redirect(url_for('news_article', id=id))

    comments = Comment.query.filter_by(article_id=id).order_by(Comment.date.desc()).all()
    return render_template('article.html', article=article, current_date=date.today(), comments=comments)

@app.route("/articles")
@app.route("/articles/<category>")
def articles_list(category=None):
    if category is None:
        category = request.args.get('category', '').strip()
    
    if category:
        category = unquote(category)
    
    categories = data_base.session.query(Article.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    if category and category not in categories:
        flash(f'Категория "{category}" не найдена', 'error')
        articles = []
    elif category:
        articles = Article.query.filter_by(category=category).order_by(Article.date.desc()).all()
    else:
        articles = Article.query.order_by(Article.date.desc()).all()
    
    return render_template('articles_list.html', 
                         articles=articles, 
                         current_category=category,
                         categories=categories)

@app.route("/create_article", methods=['GET', 'POST'])
@login_required
def create_article():
    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        category = request.form.get('category', 'general')

        if title and text:
            article = Article(
                title=title,
                text=text,
                category=category,
                author=current_user,
            )

            data_base.session.add(article)
            data_base.session.commit()
            flash('Статья создана!', 'success')
            return redirect(url_for('articles_list'))
        
        else:
            flash('Заполните обязательные поля', 'error')

    return render_template('create_article.html')

@app.route("/edit_article/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)

    if article.author != current_user:
        flash('У вас нет прав для редактирования этой статьи', 'error')
        return redirect(url_for('news_article', id=id))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.text = request.form.get('text')
        article.category = request.form.get('category', 'general')

        data_base.session.commit()
        flash('Статья обновлена', 'success')
        return redirect(url_for("news_article", id=id))

    return render_template('edit_article.html', article=article)

@app.route('/delete-article/<int:id>')
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)

    if article.author != current_user:
        flash('У вас нет прав для удаления статьи', 'error')
        return redirect(url_for('news_article', id=id))
    
    Comment.query.filter_by(article_id=id).delete()
    data_base.session.delete(article)
    data_base.session.commit()
    flash('Статья успешно удалена', 'success')
    return redirect(url_for('articles_list'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            access_token = jwt_manager.create_access_token(user.id, user.email)
            refresh_token = jwt_manager.create_refresh_token(user.id, user.email)
            
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            
            response = redirect(next_page or url_for('index'))
            response.set_cookie('jwt_token', access_token, max_age=3600, httponly=True)
            response.set_cookie('refresh_token', refresh_token, max_age=2592000, httponly=True)
            
            return response
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        errors = []

        if not name or not email or not password:
            errors.append('Все поля обязательны для заполнения')
        
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        
        if User.query.filter_by(email=email).first():
            errors.append('Пользователь с таким email уже существует')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            user = User(
                name=name,
                email=email
            )
            user.set_password(password)
            data_base.session.add(user)
            data_base.session.commit()
            
            login_user(user)
            access_token = jwt_manager.create_access_token(user.id, user.email)
            refresh_token = jwt_manager.create_refresh_token(user.id, user.email)
            
            flash("Вы зарегистрированы", 'success')
            
            response = redirect(url_for('index'))
            response.set_cookie('jwt_token', access_token, max_age=3600, httponly=True)
            response.set_cookie('refresh_token', refresh_token, max_age=2592000, httponly=True)
            
            return response
        
    return render_template('register.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли", 'success')
    
    response = redirect(url_for('index'))
    response.set_cookie('jwt_token', '', expires=0)
    response.set_cookie('refresh_token', '', expires=0)
    
    return response


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)