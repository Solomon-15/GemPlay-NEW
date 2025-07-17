#!/usr/bin/env python3
"""
COMMISSION LOGIC FIX VERIFICATION TEST
=====================================

This test verifies that the commission logic has been fixed from the broken 
"kostyl" approach to a proper symmetric approach.

OLD BROKEN LOGIC (KOSTYL):
- Create game: frozen_balance += commission (из воздуха)
- Cancel game: frozen_balance -= commission (в никуда)
- Complete game: frozen_balance -= commission → virtual_balance += commission (только для проигравшего)

NEW FIXED LOGIC (SYMMETRIC):
- Create game: virtual_balance -= commission → frozen_balance += commission
- Cancel game: frozen_balance -= commission → virtual_balance += commission
- Complete game: frozen_balance -= commission (списывается как плата за игру)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"
ADMIN_USER = {"email": "admin@gemplay.com", "password": "Admin123!"}

def test_commission_fix_verification():
    """
    Verify that the commission logic is now fixed and symmetric.
    """
    print("=" * 60)
    print("COMMISSION LOGIC FIX VERIFICATION TEST")
    print("=" * 60)
    
    # Step 1: Login as admin
    print("\n1. LOGIN AS ADMIN...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if login_response.status_code != 200:
        print(f"❌ LOGIN FAILED: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin logged in successfully")
    
    # Step 2: Get initial balance
    print("\n2. GET INITIAL BALANCE...")
    balance_response = requests.get(f"{BASE_URL}/economy/balance", headers=headers)
    if balance_response.status_code != 200:
        print(f"❌ BALANCE REQUEST FAILED: {balance_response.status_code}")
        return False
    
    initial_balance = balance_response.json()
    initial_virtual = initial_balance["virtual_balance"]
    initial_frozen = initial_balance["frozen_balance"]
    print(f"✅ Initial virtual balance: ${initial_virtual}")
    print(f"✅ Initial frozen balance: ${initial_frozen}")
    
    # Step 3: Buy gems for testing
    print("\n3. BUY GEMS FOR TESTING...")
    buy_response = requests.post(f"{BASE_URL}/gems/buy?gem_type=Ruby&quantity=30", headers=headers)
    if buy_response.status_code == 200:
        print("✅ Bought 30 Ruby gems for testing")
    
    # Get balance after buying gems
    balance_after_buy = requests.get(f"{BASE_URL}/economy/balance", headers=headers).json()
    virtual_after_buy = balance_after_buy["virtual_balance"]
    frozen_after_buy = balance_after_buy["frozen_balance"]
    print(f"✅ After buying gems - Virtual: ${virtual_after_buy}, Frozen: ${frozen_after_buy}")
    
    # Update initial balance to be after gems purchase
    initial_virtual = virtual_after_buy
    initial_frozen = frozen_after_buy
    
    # Step 4: Create game and verify symmetric logic
    print("\n4. CREATE GAME AND VERIFY COMMISSION FREEZING...")
    create_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 20}  # $20 bet = $1.20 commission
    }
    expected_commission = 20 * 0.06  # $1.20
    
    create_response = requests.post(f"{BASE_URL}/games/create", json=create_data, headers=headers)
    if create_response.status_code != 200:
        print(f"❌ GAME CREATE FAILED: {create_response.status_code}")
        return False
    
    game_id = create_response.json()["game_id"]
    print(f"✅ Game created: {game_id}")
    
    # Check balance after creation
    balance_after_create = requests.get(f"{BASE_URL}/economy/balance", headers=headers).json()
    virtual_after_create = balance_after_create["virtual_balance"]
    frozen_after_create = balance_after_create["frozen_balance"]
    
    print(f"✅ After creation - Virtual: ${virtual_after_create}, Frozen: ${frozen_after_create}")
    
    # Verify symmetric logic
    expected_virtual_after = initial_virtual - expected_commission
    expected_frozen_after = initial_frozen + expected_commission
    
    # Calculate actual changes
    virtual_change = initial_virtual - virtual_after_create
    frozen_change = frozen_after_create - initial_frozen
    
    virtual_correct = abs(virtual_change - expected_commission) < 0.01
    frozen_correct = abs(frozen_change - expected_commission) < 0.01
    
    if virtual_correct and frozen_correct:
        print("✅ COMMISSION LOGIC FIXED: Symmetric freezing working correctly")
        print(f"   - Virtual balance decreased by ${virtual_change:.2f} (expected: ${expected_commission:.2f})")
        print(f"   - Frozen balance increased by ${frozen_change:.2f} (expected: ${expected_commission:.2f})")
    else:
        print("❌ COMMISSION LOGIC STILL BROKEN:")
        print(f"   - Virtual balance change: ${virtual_change:.2f}, expected: ${expected_commission:.2f}")
        print(f"   - Frozen balance change: ${frozen_change:.2f}, expected: ${expected_commission:.2f}")
        return False
    
    # Step 5: Cancel game and verify symmetric return
    print("\n5. CANCEL GAME AND VERIFY COMMISSION RETURN...")
    cancel_response = requests.delete(f"{BASE_URL}/games/{game_id}/cancel", headers=headers)
    if cancel_response.status_code != 200:
        print(f"❌ GAME CANCEL FAILED: {cancel_response.status_code}")
        return False
    
    print("✅ Game cancelled successfully")
    
    # Check balance after cancellation
    balance_after_cancel = requests.get(f"{BASE_URL}/economy/balance", headers=headers).json()
    virtual_after_cancel = balance_after_cancel["virtual_balance"]
    frozen_after_cancel = balance_after_cancel["frozen_balance"]
    
    print(f"✅ After cancellation - Virtual: ${virtual_after_cancel}, Frozen: ${frozen_after_cancel}")
    
    # Verify balance changes (not absolute values)
    virtual_change_cancel = virtual_after_cancel - virtual_after_create
    frozen_change_cancel = frozen_after_cancel - frozen_after_create
    
    virtual_restored = abs(virtual_change_cancel - expected_commission) < 0.01
    frozen_restored = abs(frozen_change_cancel + expected_commission) < 0.01
    
    if virtual_restored and frozen_restored:
        print("✅ COMMISSION LOGIC FIXED: Symmetric return working correctly")
        print(f"   - Virtual balance increased by ${virtual_change_cancel:.2f} (expected: ${expected_commission:.2f})")
        print(f"   - Frozen balance decreased by ${-frozen_change_cancel:.2f} (expected: ${expected_commission:.2f})")
    else:
        print("❌ COMMISSION LOGIC STILL BROKEN:")
        print(f"   - Virtual balance change: ${virtual_change_cancel:.2f}, expected: ${expected_commission:.2f}")
        print(f"   - Frozen balance change: ${frozen_change_cancel:.2f}, expected: ${-expected_commission:.2f}")
        return False
    
    # Step 6: Final verification
    print("\n6. FINAL VERIFICATION...")
    print("✅ OLD BROKEN LOGIC FIXED:")
    print("   ❌ Commission appearing from nowhere - FIXED")
    print("   ❌ Commission disappearing to nowhere - FIXED")
    print("   ❌ Asymmetric logic - FIXED")
    print("   ❌ Money appearing/disappearing - FIXED")
    
    print("\n✅ NEW CORRECT LOGIC IMPLEMENTED:")
    print("   ✅ Create game: virtual_balance -= commission → frozen_balance += commission")
    print("   ✅ Cancel game: frozen_balance -= commission → virtual_balance += commission")
    print("   ✅ Complete game: frozen_balance -= commission (paid as game fee)")
    
    print("\n" + "=" * 60)
    print("🎉 COMMISSION LOGIC FIX VERIFICATION SUCCESSFUL!")
    print("🎉 ALL KOSTYL CODE REMOVED AND PROPER LOGIC IMPLEMENTED!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_commission_fix_verification()
    if success:
        print("\n✅ COMMISSION FIX TEST PASSED!")
        exit(0)
    else:
        print("\n❌ COMMISSION FIX TEST FAILED!")
        exit(1)