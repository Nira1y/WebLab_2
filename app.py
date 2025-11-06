from api import api_bp
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date
import re
from models import data_base, User, Article, Comment
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import unquote
from jwt_util import jwt_manager
from middleware import jwt_middleware
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

data_base.init_app(app)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"]
    }
})

app.before_request(jwt_middleware)

app.register_blueprint(api_bp)

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

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)