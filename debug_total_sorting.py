#!/usr/bin/env python3
"""
Debug TOTAL Column Sorting - Investigate API Response Structure
"""

import requests
import json

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

def authenticate_admin():
    """Authenticate as admin"""
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def debug_api_response():
    """Debug the API response structure"""
    token = authenticate_admin()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test TOTAL sorting DESC
    params = {
        "sort_by": "total",
        "sort_order": "desc",
        "page": 1,
        "per_page": 3
    }
    
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers, params=params)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n📋 FULL API RESPONSE STRUCTURE:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check specific user structure
        users = data.get("users", [])
        if users:
            print(f"\n👤 FIRST USER DETAILED STRUCTURE:")
            print(json.dumps(users[0], indent=2, ensure_ascii=False))
            
            # Check balance calculation manually
            user = users[0]
            virtual_balance = user.get("virtual_balance", 0)
            frozen_balance = user.get("frozen_balance", 0)
            gems_value = user.get("gems_value", 0)
            total_balance = user.get("total_balance", 0)
            
            print(f"\n🧮 BALANCE CALCULATION CHECK:")
            print(f"Virtual Balance: {virtual_balance}")
            print(f"Frozen Balance: {frozen_balance}")
            print(f"Gems Value: {gems_value}")
            print(f"Total Balance (API): {total_balance}")
            print(f"Expected Total: {virtual_balance + frozen_balance + gems_value}")
            print(f"Difference: {total_balance - (virtual_balance + frozen_balance + gems_value)}")
    else:
        print(f"❌ API Error: {response.text}")

if __name__ == "__main__":
    debug_api_response()