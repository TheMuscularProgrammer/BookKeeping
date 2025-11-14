import requests
import jwt
from datetime import datetime, timedelta

# יצירת Token
user_id = '550e8400-e29b-41d4-a716-446655440000'
JWT_SECRET_KEY = 'my-super-secret-jwt-key-2024'

token = jwt.encode(
    {
        'user_id': user_id,
        'email': 'ori@test.com',
        'exp': datetime.utcnow() + timedelta(hours=24)
    },
    JWT_SECRET_KEY,
    algorithm='HS256'
)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

print("=== Testing Microservices ===\n")

# 1. צור חשבון
print("1. Creating account...")
response = requests.post(
    'http://localhost:5002/accounts',
    json={'type': 'checking', 'balance_cents': 100000},
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

account_id = response.json()['id']

# 2. בדוק חשבון
print("2. Getting account details...")
response = requests.get(
    f'http://localhost:5002/accounts/{account_id}',
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# 3. הפקד כסף
print("3. Depositing money...")
response = requests.post(
    f'http://localhost:5003/transactions/{account_id}/deposit',
    json={'amount': 50000},
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# 4. בדוק יתרה חדשה
print("4. Checking updated balance...")
response = requests.get(
    f'http://localhost:5002/accounts/{account_id}',
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# 5. משוך כסף
print("5. Withdrawing money...")
response = requests.post(
    f'http://localhost:5003/transactions/{account_id}/withdraw',
    json={'amount': 30000},
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# 6. בדוק היסטוריית עסקאות
print("6. Getting transaction history...")
response = requests.get(
    f'http://localhost:5003/transactions/{account_id}/history',
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

print("=== All tests completed! ===")