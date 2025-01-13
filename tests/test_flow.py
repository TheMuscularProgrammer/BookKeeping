import pytest
import requests
import uuid
from datetime import datetime

class TestBankingFlow:
    @pytest.fixture
    def test_data(self):
        return {
            "user": {
                "first_name": "Test",
                "last_name": "User",
                "email": f"test{uuid.uuid4()}@example.com",
                "password": "test1234"
            }
        }
    
    def test_banking_operations(self, test_data, base_url):
        """
        Test the main banking operations flow:
        1. Login
        2. Create account
        3. Deposit
        4. Withdrawal
        """
        # Step 1: Create a user first
        response = requests.post(
            f"{base_url}/users/",
            json=test_data["user"]
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Step 2: Login
        response = requests.post(
            f"{base_url}/auth/login",
            json={
                "email": test_data["user"]["email"],
                "password": test_data["user"]["password"]
            }
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Create account
        response = requests.post(
            f"{base_url}/accounts/",
            headers=headers,
            json={"owner_id": user_id}
        )
        assert response.status_code == 201
        account_id = response.json()["id"]
        
        # Step 4: Deposit
        deposit_amount = 1000
        response = requests.post(
            f"{base_url}/transactions/{account_id}/deposit",
            headers=headers,
            json={"amount": deposit_amount}
        )
        assert response.status_code == 200
        
        # Step 5: Withdrawal
        withdraw_amount = 500
        response = requests.post(
            f"{base_url}/transactions/{account_id}/withdraw",
            headers=headers,
            json={"amount": withdraw_amount}
        )
        assert response.status_code == 200
        
        # Step 6: Verify transactions
        response = requests.get(
            f"{base_url}/transactions/{account_id}/transactions",
            headers=headers
        )
        assert response.status_code == 200
        transactions = response.json()["transactions"]
        
        # Verify we have both transactions
        assert len(transactions) == 2, "Should have exactly 2 transactions"
        
        # Verify final balance (can be added if you have an endpoint to check balance)
        # Expected balance should be deposit_amount - withdraw_amount = 500