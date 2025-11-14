"""
Simple Transfer Workflow Test
==============================

Prerequisites:
1. Run this SQL command first to create a test user:

docker exec -it bookkeeping-db psql -U postgres -d mydatabase -c "
INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'Test',
    'User',
    'test@example.com',
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqXjM1oXMa',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;
"

The password for this user is: password123

2. Then run: python test_simple.py
"""

import requests
import jwt
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = 'http://localhost'
ACCOUNT_SERVICE_PORT = 5002
TRANSACTION_SERVICE_PORT = 5003

# Pre-created test user
USER_ID = '550e8400-e29b-41d4-a716-446655440000'
JWT_SECRET_KEY = 'my-super-secret-jwt-key-2024'

# Generate token
token = jwt.encode(
    {
        'user_id': USER_ID,
        'email': 'test@example.com',
        'exp': datetime.utcnow() + timedelta(hours=24)
    },
    JWT_SECRET_KEY,
    algorithm='HS256'
)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_success(msg):
    print(f"✅ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def print_waiting(msg):
    print(f"⏳ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def main():
    print("\n" + "="*70)
    print("  🧪 בדיקת מערכת ההעברות הבנקאית")
    print("="*70)
    
    try:
        # יצירת חשבון 1
        print_section("1. יצירת חשבון 1 - $5,000")
        response1 = requests.post(
            f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts',
            json={'type': 'checking', 'balance_cents': 500000},
            headers=headers
        )
        
        if response1.status_code != 201:
            print_error(f"שגיאה: {response1.json()}")
            return
        
        account1 = response1.json()['id']
        print_success(f"חשבון 1 נוצר: {account1}")
        
        # יצירת חשבון 2
        print_section("2. יצירת חשבון 2 - $1,000")
        response2 = requests.post(
            f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts',
            json={'type': 'savings', 'balance_cents': 100000},
            headers=headers
        )
        
        if response2.status_code != 201:
            print_error(f"שגיאה: {response2.json()}")
            return
        
        account2 = response2.json()['id']
        print_success(f"חשבון 2 נוצר: {account2}")
        
        # בדיקת יתרות התחלתיות
        print_section("3. יתרות התחלתיות")
        acc1_data = requests.get(f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts/{account1}', headers=headers).json()
        acc2_data = requests.get(f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts/{account2}', headers=headers).json()
        print_info(f"חשבון 1: ${acc1_data['balance_cents']/100:.2f}")
        print_info(f"חשבון 2: ${acc2_data['balance_cents']/100:.2f}")
        
        # העברה קטנה - $100 (אוטומטי)
        print_section("4. העברה קטנה - $100 (אישור אוטומטי)")
        transfer1 = requests.post(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transactions/{account1}/transfer',
            json={'amount': 10000, 'to_account_id': account2},
            headers=headers
        ).json()
        
        print_success(f"העברה נוצרה: {transfer1['transfer_request_id']}")
        print_info(f"State: {transfer1['state']}")
        print_info(f"Requires Approval: {transfer1['requires_approval']}")
        
        if transfer1['requires_approval']:
            print_error("שגיאה! לא אמור לדרוש אישור")
        
        print_waiting("ממתין 5 שניות לעיבוד...")
        time.sleep(5)
        
        status1 = requests.get(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transfers/{transfer1["transfer_request_id"]}/status',
            headers=headers
        ).json()
        print_success(f"סטטוס: {status1['state']}")
        
        # העברה גדולה - $300 (דורש אישור)
        print_section("5. העברה גדולה - $300 (דורש אישור)")
        transfer2 = requests.post(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transactions/{account1}/transfer',
            json={'amount': 30000, 'to_account_id': account2},
            headers=headers
        ).json()
        
        print_success(f"העברה נוצרה: {transfer2['transfer_request_id']}")
        print_info(f"State: {transfer2['state']}")
        print_info(f"Requires Approval: {transfer2['requires_approval']}")
        
        if not transfer2['requires_approval']:
            print_error("שגיאה! אמור לדרוש אישור")
        
        print_waiting("ממתין 2 שניות...")
        time.sleep(2)
        
        # אישור
        print_info("מאשר את ההעברה...")
        approve_resp = requests.post(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transfers/{transfer2["transfer_request_id"]}/approve',
            headers=headers
        )
        
        if approve_resp.status_code == 200:
            print_success("אושר!")
        
        print_waiting("ממתין 5 שניות לעיבוד...")
        time.sleep(5)
        
        status2 = requests.get(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transfers/{transfer2["transfer_request_id"]}/status',
            headers=headers
        ).json()
        print_success(f"סטטוס: {status2['state']}")
        
        # העברה שתדחה - $250
        print_section("6. העברה לדחייה - $250")
        transfer3 = requests.post(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transactions/{account1}/transfer',
            json={'amount': 25000, 'to_account_id': account2},
            headers=headers
        ).json()
        
        print_success(f"העברה נוצרה: {transfer3['transfer_request_id']}")
        
        print_waiting("ממתין 2 שניות...")
        time.sleep(2)
        
        # דחייה
        print_info("דוחה את ההעברה...")
        decline_resp = requests.post(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transfers/{transfer3["transfer_request_id"]}/decline',
            json={'reason': 'פעילות חשודה'},
            headers=headers
        )
        
        if decline_resp.status_code == 200:
            print_success("נדחה!")
        
        status3 = requests.get(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transfers/{transfer3["transfer_request_id"]}/status',
            headers=headers
        ).json()
        print_success(f"סטטוס: {status3['state']}")
        
        # יתרות סופיות
        print_section("7. יתרות סופיות")
        acc1_final = requests.get(f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts/{account1}', headers=headers).json()
        acc2_final = requests.get(f'{BASE_URL}:{ACCOUNT_SERVICE_PORT}/accounts/{account2}', headers=headers).json()
        
        balance1 = acc1_final['balance_cents'] / 100
        balance2 = acc2_final['balance_cents'] / 100
        
        print_info(f"חשבון 1: ${balance1:,.2f}")
        print_info(f"חשבון 2: ${balance2:,.2f}")
        
        expected1 = 5000 - 100 - 300  # $4,600
        expected2 = 1000 + 100 + 300  # $1,400
        
        print("\n📊 השוואה:")
        print(f"   חשבון 1 - צפוי: ${expected1:,.2f}, בפועל: ${balance1:,.2f}")
        print(f"   חשבון 2 - צפוי: ${expected2:,.2f}, בפועל: ${balance2:,.2f}")
        
        if abs(balance1 - expected1) < 0.01 and abs(balance2 - expected2) < 0.01:
            print_success("\n✅ כל הבדיקות עברו בהצלחה!")
            print("\n🎉 המערכת עובדת מצוין! 🎉")
        else:
            print_error("\n❌ יש אי-התאמה ביתרות")
        
        # היסטוריה
        print_section("8. היסטוריית עסקאות חשבון 1")
        history = requests.get(
            f'{BASE_URL}:{TRANSACTION_SERVICE_PORT}/transactions/{account1}/history',
            headers=headers
        ).json()
        
        print_info(f"נמצאו {len(history['transactions'])} עסקאות:")
        for i, tx in enumerate(history['transactions'][:5], 1):  # 5 הראשונות
            print(f"   {i}. {tx['type'].upper()}: ${tx['amount']/100:.2f}")
        
    except Exception as e:
        print_error(f"\n💥 שגיאה: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print(__doc__)
    
    input("\n▶️  לחץ Enter אחרי שהרצת את הפקודה SQL למעלה...")
    
    main()