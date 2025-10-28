import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_jwt_flow():
    
    print("1. Получение JWT токенов:")
    login_data = {
        'email': 'developer@test.com',
        'password': '123456'
    }
    
    response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        tokens = data['tokens']
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        
        print("Токены получены успешно")
        print(f"Access Token: {access_token[:50]}...")
        print(f"Refresh Token: {refresh_token[:50]}...")
        
        print("\n2. Доступ к защищенному эндпоинту С токеном:")
        headers = {'Authorization': f'Bearer {access_token}'}
        me_response = requests.get(f'{BASE_URL}/api/auth/me', headers=headers)
        print(f"Статус: {me_response.status_code}")
        print(f"Ответ: {me_response.json()}")
        
        print("\n3. Доступ к защищенному эндпоинту БЕЗ токена:")
        me_response_no_token = requests.get(f'{BASE_URL}/api/auth/me')
        print(f"Статус: {me_response_no_token.status_code}")
        print(f"Ответ: {me_response_no_token.json()}")
    
        print("\n4. Создание статьи через JWT:")
        article_data = {
            'title': 'Тестовая статья через JWT',
            'text': 'Это тестовая статья, созданная через JWT авторизацию',
            'category': 'Технологии'
        }
        
        article_response = requests.post(
            f'{BASE_URL}/api/protected/articles', 
            json=article_data, 
            headers=headers
        )
        print(f"Статус: {article_response.status_code}")
        if article_response.status_code == 200:
            print("Статья создана успешно")
            print(f"Ответ: {article_response.json()}")
        else:
            print(f"Ошибка: {article_response.json()}")
        
        print("\n5. Обновление токенов:")
        refresh_data = {'refresh_token': refresh_token}
        refresh_response = requests.post(f'{BASE_URL}/api/auth/refresh', json=refresh_data)
        print(f"Статус: {refresh_response.status_code}")
        
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()['tokens']
            print("Токены обновлены успешно")
            
            new_headers = {'Authorization': f'Bearer {new_tokens["access_token"]}'}
            me_response_new = requests.get(f'{BASE_URL}/api/auth/me', headers=new_headers)
            print(f"\n6. Тест с новым токеном:")
            print(f"Статус: {me_response_new.status_code}")
            if me_response_new.status_code == 200:
                print("Новый токен работает корректно")
        
        print("\n7. Тест публичных эндпоинтов (без токена):")
        articles_response = requests.get(f'{BASE_URL}/api/articles')
        print(f"GET /api/articles - Статус: {articles_response.status_code}")
        
    else:
        print(f" Ошибка логина: {response.json()}")

if __name__ == '__main__':
    test_jwt_flow()