from flask import Flask, render_template
from datetime import datetime, date

app = Flask(__name__)

articles = [
    {'id': 1, 'title': 'Первая новость', 'date': date.today()},
    {'id': 2, 'title': 'Вторая новость', 'date': date(2024, 1, 14)},
    {'id': 3, 'title': 'Третья новость', 'date': date.today()},
    {'id': 4, 'title': 'Четвертая новость', 'date': date(2024, 1, 13)},
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

@app.route("/feedback")
def feedback():
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