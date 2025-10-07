from flask import Flask, render_template, request, flash
from datetime import datetime, date
import re


app = Flask(__name__)
app.secret_key = 'dev-key'

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

if __name__ == '__main__':
    app.run(debug=True)