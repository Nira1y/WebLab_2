import requests

session = requests.Session()

login_data = {
    'email': 'yanl1n.wrk@mail.ru',
    'password': '1234'
}
login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
print(f"✅ Авторизация: {login_response.status_code}")

comments_response = session.get("http://127.0.0.1:5000/api/comment")
if comments_response.status_code == 200:
    comments = comments_response.json()
    print("💬 Доступные комментарии:")
    for comment in comments['comments']:
        print(f"  ID: {comment['id']} - '{comment['text'][:50]}...' (Статья ID: {comment['article_id']})")

update_comment_data = {
    "text": "Этот комментарий был ОТРЕДАКТИРОВАН с использованием авторизованной сессии requests"
}

comment_id = 4 
response = session.put(
    f"http://127.0.0.1:5000/api/comment/{comment_id}",
    json=update_comment_data
)

print(f"\n📊 Результат редактирования комментария ID {comment_id}:")
print(f"Статус: {response.status_code}")
try:
    print(f"Ответ: {response.json()}")
except:
    print(f"Текст ответа: {response.text[:200]}")