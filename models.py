from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 

data_base = SQLAlchemy()

class User(UserMixin, data_base.Model):
    __tablename__= "user"

    id = data_base.Column(data_base.Integer, primary_key = True)
    name = data_base.Column(data_base.String(100), nullable=False)
    email = data_base.Column(data_base.String(100), nullable=False)
    hashed_password = data_base.Column(data_base.String(200), nullable=False)
    date = data_base.Column(data_base.DateTime, default=datetime.utcnow)
    articles = data_base.relationship('Article', backref='author', lazy=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

class Article(data_base.Model):
    __tablename__= "article"

    id = data_base.Column(data_base.Integer, primary_key = True)
    title = data_base.Column(data_base.String(200), nullable=False)
    text = data_base.Column(data_base.Text, nullable=False)
    date = data_base.Column(data_base.DateTime, default=datetime.utcnow)
    user_id = data_base.Column(data_base.Integer, data_base.ForeignKey('user.id'), nullable=False)
    category = data_base.Column(data_base.String(50), default='Общая')
    comment = data_base.relation('Comment', backref='article', lazy='dynamic')

class Comment(data_base.Model):
    __tablename__="comment"

    id = data_base.Column(data_base.Integer, primary_key = True)
    text = data_base.Column(data_base.Text, nullable=False)
    date = data_base.Column(data_base.DateTime, default=datetime.utcnow)
    article_id = data_base.Column(data_base.Integer, data_base.ForeignKey('article.id'), nullable=False)
    author_name = data_base.Column(data_base.String(100), nullable=False)