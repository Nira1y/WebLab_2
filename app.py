from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date
import re
from models import data_base, User, Article, Comment


app = Flask(__name__)
app.secret_key = 'dev-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

data_base.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    data_base.create_all()


articles = [
    {'id': 1, 'title': 'Первая новость', 'date': date.today()},
    {'id': 2, 'title': 'Вторая новость', 'date': date(2025, 1, 14)},
    {'id': 3, 'title': 'Третья новость', 'date': date.today()},
    {'id': 4, 'title': 'Четвертая новость', 'date': date(2025, 1, 13)},
    {'id': 5, 'title': 'Пятая новость', 'date': date.today()}
]

@app.route("/index")
@app.route("/")
def index():
    return render_template('index.html', articles=articles, current_date = date.today())

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
        

@app.route('/news/<int:id>')
def news_article(id):
    article = next((a for a in articles if a['id'] == id), None)
    if article:
        return render_template('article.html', article=article, current_date=date.today())
    else:
        return "Статья не найдена", 404

@app.route("/articles_list")
def articles_list():
    return render_template('articles_list.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/create_article", methods=['GET', 'POST'])
@login_required
def create_article():
    users = User.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        category = request.form.get('category')
        author_id = request.form.get('author_id')

        if title and text and author_id:
            author = User.query.get(author_id)
            article = Article(
                title=title,
                text=text,
                category=category,
                author_id=current_user.id,
                author=author
            )

            data_base.session.add(article)
            data_base.session.commit()
            flash('Статья создана!')
            return redirect(url_for('articles_list'))
        else:
            flash('Заполните обязательные поля', 'error')

    return render_template('create_article.html')

@app.route("/edit_article")
def edit_article():
    return render_template('edit_article.html')

@app.route("/logout")
def logout():
    return render_template('logout.html')

@app.route("/articles_list")
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)