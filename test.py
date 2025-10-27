import requests

session = requests.Session()

login_data = {
    'email': 'yanl1n.wrk@mail.ru',
    'password': '1234'
}
login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
print(f"Авторизация: {login_response.status_code}")

articles_response = session.get("http://127.0.0.1:5000/api/articles")
if articles_response.status_code == 200:
    articles = articles_response.json()
    print("Доступные статьи:")
    for article in articles['articles']:
        print(f"  ID: {article['id']} - '{article['title']}'")

comment_data = {
    "text": "мяу",
}

response = session.put(
    "http://127.0.0.1:5000/api/comment/1",  json = comment_data
)

print("\nРезультат создания комментария:")
print(f"Статус: {response.status_code}")
print(f"Ответ: {response.json()}")