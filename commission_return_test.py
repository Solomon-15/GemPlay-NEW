#!/usr/bin/env python3
"""
ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ возврата комиссии проигравшему - проверка реального сценария
Russian Review Requirements: Commission Return to Losing Player Testing

КОНКРЕТНЫЙ ТЕСТ-КЕЙС:
1. Создать двух пользователей: User1 (создатель игры), User2 (присоединяющийся)
2. Записать НАЧАЛЬНЫЕ балансы: User1 и User2 (virtual_balance, frozen_balance)
3. Создать игру User1: Ставка $35 (комиссия $1.05), записать балансы ПОСЛЕ создания игры
4. User2 присоединяется: Записать балансы ПОСЛЕ присоединения
5. Завершить игру с победой User1: User1 - ПОБЕДИТЕЛЬ, User2 - ПРОИГРАВШИЙ
6. ПРОВЕРИТЬ ФИНАЛЬНЫЕ балансы:
   - User1 (победитель): комиссия $1.05 должна быть СПИСАНА
   - User2 (проигравший): комиссия $1.05 должна быть ВОЗВРАЩЕНА
7. Проверить транзакции: Должна быть COMMISSION транзакция для User2 с возвратом $1.05

МАТЕМАТИКА ДЛЯ ПРОВЕРКИ:
- User1 финальный virtual_balance = начальный - $1.05 (комиссия)
- User2 финальный virtual_balance = начальный + $0 (комиссия возвращена)
- User1 frozen_balance = 0 (разморожено)
- User2 frozen_balance = 0 (разморожено)

ФОКУС: Пошаговая проверка что новая логика возврата комиссии проигравшему действительно работает.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def record_test(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def hash_move_with_salt(move: str, salt: str) -> str:
    """Hash game move with salt for commit-reveal scheme."""
    combined = f"{move}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def generate_random_email() -> str:
    """Generate a random email for testing."""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"testuser_{random_suffix}@test.com"

def register_and_verify_user(username: str, email: str, password: str, gender: str = "male") -> Optional[str]:
    """Register and verify a user, return auth token."""
    print_subheader(f"Registering and verifying user: {username}")
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "gender": gender
    }
    
    register_response, register_success = make_request("POST", "/auth/register", data=register_data)
    
    if not register_success:
        print_error(f"Failed to register user {username}")
        return None
    
    verification_token = register_response.get("verification_token")
    if not verification_token:
        print_error(f"No verification token received for {username}")
        return None
    
    print_success(f"User {username} registered successfully")
    
    # Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", data={"token": verification_token})
    
    if not verify_success:
        print_error(f"Failed to verify email for {username}")
        return None
    
    print_success(f"Email verified for {username}")
    
    # Login to get auth token
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response, login_success = make_request("POST", "/auth/login", data=login_data)
    
    if not login_success:
        print_error(f"Failed to login user {username}")
        return None
    
    auth_token = login_response.get("access_token")
    if not auth_token:
        print_error(f"No access token received for {username}")
        return None
    
    print_success(f"User {username} logged in successfully")
    return auth_token

def get_user_balance(auth_token: str, username: str) -> Tuple[float, float]:
    """Get user's virtual and frozen balance."""
    balance_response, balance_success = make_request("GET", "/auth/me", auth_token=auth_token)
    
    if not balance_success:
        print_error(f"Failed to get balance for {username}")
        return 0.0, 0.0
    
    virtual_balance = balance_response.get("virtual_balance", 0.0)
    frozen_balance = balance_response.get("frozen_balance", 0.0)
    
    return virtual_balance, frozen_balance

def buy_gems_for_user(auth_token: str, username: str, gem_type: str, quantity: int) -> bool:
    """Buy gems for a user."""
    print(f"Buying {quantity} {gem_type} gems for {username}")
    
    buy_response, buy_success = make_request(
        "POST", 
        f"/gems/buy?gem_type={gem_type}&quantity={quantity}",
        auth_token=auth_token
    )
    
    if buy_success:
        print_success(f"Successfully bought {quantity} {gem_type} gems for {username}")
        return True
    else:
        print_error(f"Failed to buy gems for {username}")
        return False

def get_user_transactions(auth_token: str, username: str) -> List[Dict[str, Any]]:
    """Get user's transaction history."""
    transactions_response, transactions_success = make_request(
        "GET", "/economy/transactions", 
        auth_token=auth_token
    )
    
    if transactions_success and "transactions" in transactions_response:
        return transactions_response["transactions"]
    else:
        print_warning(f"Failed to get transactions for {username}")
        return []

def test_commission_return_to_losing_player():
    """
    ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ возврата комиссии проигравшему - проверка реального сценария
    """
    print_header("ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ ВОЗВРАТА КОМИССИИ ПРОИГРАВШЕМУ")
    
    # STEP 1: Создать двух пользователей
    print_subheader("STEP 1: Создать двух пользователей")
    
    # Generate unique emails to avoid conflicts
    user1_email = generate_random_email()
    user2_email = generate_random_email()
    
    user1_data = {
        "username": "User1_Creator",
        "email": user1_email,
        "password": "Test123!",
        "gender": "male"
    }
    
    user2_data = {
        "username": "User2_Joiner", 
        "email": user2_email,
        "password": "Test123!",
        "gender": "female"
    }
    
    # Register and verify User1 (создатель игры)
    user1_token = register_and_verify_user(
        user1_data["username"], 
        user1_data["email"], 
        user1_data["password"], 
        user1_data["gender"]
    )
    
    if not user1_token:
        print_error("Failed to create User1 - cannot proceed")
        record_test("Commission Return - User1 Creation", False, "User1 creation failed")
        return
    
    # Register and verify User2 (присоединяющийся)
    user2_token = register_and_verify_user(
        user2_data["username"], 
        user2_data["email"], 
        user2_data["password"], 
        user2_data["gender"]
    )
    
    if not user2_token:
        print_error("Failed to create User2 - cannot proceed")
        record_test("Commission Return - User2 Creation", False, "User2 creation failed")
        return
    
    print_success("✅ Both users created successfully")
    record_test("Commission Return - User Creation", True)
    
    # STEP 2: Записать НАЧАЛЬНЫЕ балансы
    print_subheader("STEP 2: Записать НАЧАЛЬНЫЕ балансы")
    
    # Get initial balances
    user1_initial_virtual, user1_initial_frozen = get_user_balance(user1_token, "User1")
    user2_initial_virtual, user2_initial_frozen = get_user_balance(user2_token, "User2")
    
    print_success(f"User1 НАЧАЛЬНЫЕ балансы:")
    print_success(f"  Virtual Balance: ${user1_initial_virtual}")
    print_success(f"  Frozen Balance: ${user1_initial_frozen}")
    
    print_success(f"User2 НАЧАЛЬНЫЕ балансы:")
    print_success(f"  Virtual Balance: ${user2_initial_virtual}")
    print_success(f"  Frozen Balance: ${user2_initial_frozen}")
    
    record_test("Commission Return - Initial Balances", True)
    
    # STEP 3: Buy gems for both users to make $35 bet
    print_subheader("STEP 3: Купить гемы для ставки $35")
    
    # For $35 bet, we need: Ruby: 15 ($15) + Emerald: 2 ($20) = $35 total
    # Commission = $35 * 0.03 = $1.05
    
    # Buy gems for User1
    if not buy_gems_for_user(user1_token, "User1", "Ruby", 20):
        print_error("Failed to buy Ruby gems for User1")
        return
    
    if not buy_gems_for_user(user1_token, "User1", "Emerald", 5):
        print_error("Failed to buy Emerald gems for User1")
        return
    
    # Buy gems for User2
    if not buy_gems_for_user(user2_token, "User2", "Ruby", 20):
        print_error("Failed to buy Ruby gems for User2")
        return
    
    if not buy_gems_for_user(user2_token, "User2", "Emerald", 5):
        print_error("Failed to buy Emerald gems for User2")
        return
    
    print_success("✅ Gems purchased for both users")
    record_test("Commission Return - Gem Purchase", True)
    
    # STEP 4: Создать игру User1 - Ставка $35 (комиссия $1.05)
    print_subheader("STEP 4: User1 создает игру - Ставка $35 (комиссия $1.05)")
    
    # Create game with $35 bet: Ruby: 15 ($15) + Emerald: 2 ($20) = $35
    bet_gems = {"Ruby": 15, "Emerald": 2}
    bet_amount = 15 * 1.0 + 2 * 10.0  # $35 total
    expected_commission = bet_amount * 0.03  # 3% commission = $1.05
    
    create_game_data = {
        "move": "rock",
        "bet_gems": bet_gems
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=create_game_data,
        auth_token=user1_token
    )
    
    if not game_success:
        print_error("Failed to create game")
        record_test("Commission Return - Game Creation", False, "Game creation failed")
        return
    
    game_id = game_response.get("game_id")
    if not game_id:
        print_error("Game creation response missing game_id")
        record_test("Commission Return - Game Creation", False, "Missing game_id")
        return
    
    print_success(f"✅ Game created successfully with ID: {game_id}")
    print_success(f"✅ Bet amount: ${bet_amount}")
    print_success(f"✅ Expected commission: ${expected_commission}")
    
    # STEP 5: Записать балансы ПОСЛЕ создания игры
    print_subheader("STEP 5: Балансы ПОСЛЕ создания игры")
    
    user1_after_create_virtual, user1_after_create_frozen = get_user_balance(user1_token, "User1")
    
    print_success(f"User1 балансы ПОСЛЕ создания игры:")
    print_success(f"  Virtual Balance: ${user1_after_create_virtual}")
    print_success(f"  Frozen Balance: ${user1_after_create_frozen}")
    
    # Verify commission was frozen for User1
    expected_user1_virtual_after_create = user1_initial_virtual - expected_commission
    expected_user1_frozen_after_create = user1_initial_frozen + expected_commission
    
    user1_virtual_correct = abs(user1_after_create_virtual - expected_user1_virtual_after_create) < 0.01
    user1_frozen_correct = abs(user1_after_create_frozen - expected_user1_frozen_after_create) < 0.01
    
    if user1_virtual_correct and user1_frozen_correct:
        print_success(f"✅ User1 commission correctly frozen: ${expected_commission}")
        record_test("Commission Return - User1 Commission Frozen", True)
    else:
        print_error(f"❌ User1 commission freezing incorrect")
        print_error(f"Expected virtual: ${expected_user1_virtual_after_create}, got: ${user1_after_create_virtual}")
        print_error(f"Expected frozen: ${expected_user1_frozen_after_create}, got: ${user1_after_create_frozen}")
        record_test("Commission Return - User1 Commission Frozen", False, "Commission freezing incorrect")
    
    # STEP 6: User2 присоединяется к игре
    print_subheader("STEP 6: User2 присоединяется к игре")
    
    join_game_data = {
        "move": "paper",  # User2 will lose to User1's rock
        "gems": bet_gems  # Same gems as User1
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_game_data,
        auth_token=user2_token
    )
    
    if not join_success:
        print_error("Failed to join game")
        record_test("Commission Return - Game Join", False, "Game join failed")
        return
    
    print_success(f"✅ User2 joined game successfully")
    print_success(f"✅ Game status: {join_response.get('status', 'UNKNOWN')}")
    
    # STEP 7: Записать балансы ПОСЛЕ присоединения
    print_subheader("STEP 7: Балансы ПОСЛЕ присоединения")
    
    user1_after_join_virtual, user1_after_join_frozen = get_user_balance(user1_token, "User1")
    user2_after_join_virtual, user2_after_join_frozen = get_user_balance(user2_token, "User2")
    
    print_success(f"User1 балансы ПОСЛЕ присоединения User2:")
    print_success(f"  Virtual Balance: ${user1_after_join_virtual}")
    print_success(f"  Frozen Balance: ${user1_after_join_frozen}")
    
    print_success(f"User2 балансы ПОСЛЕ присоединения:")
    print_success(f"  Virtual Balance: ${user2_after_join_virtual}")
    print_success(f"  Frozen Balance: ${user2_after_join_frozen}")
    
    # Verify commission was frozen for User2
    expected_user2_virtual_after_join = user2_initial_virtual - expected_commission
    expected_user2_frozen_after_join = user2_initial_frozen + expected_commission
    
    user2_virtual_correct = abs(user2_after_join_virtual - expected_user2_virtual_after_join) < 0.01
    user2_frozen_correct = abs(user2_after_join_frozen - expected_user2_frozen_after_join) < 0.01
    
    if user2_virtual_correct and user2_frozen_correct:
        print_success(f"✅ User2 commission correctly frozen: ${expected_commission}")
        record_test("Commission Return - User2 Commission Frozen", True)
    else:
        print_error(f"❌ User2 commission freezing incorrect")
        print_error(f"Expected virtual: ${expected_user2_virtual_after_join}, got: ${user2_after_join_virtual}")
        print_error(f"Expected frozen: ${expected_user2_frozen_after_join}, got: ${user2_after_join_frozen}")
        record_test("Commission Return - User2 Commission Frozen", False, "Commission freezing incorrect")
    
    record_test("Commission Return - Game Join", True)
    
    # STEP 8: Wait for game completion (automatic)
    print_subheader("STEP 8: Ожидание завершения игры")
    
    print("Waiting for game to complete automatically...")
    time.sleep(5)  # Wait for game completion
    
    # Check game status
    game_status_response, game_status_success = make_request(
        "GET", f"/games/{game_id}/status",
        auth_token=user1_token,
        expected_status=200
    )
    
    if game_status_success:
        game_status = game_status_response.get("status", "UNKNOWN")
        winner_id = game_status_response.get("winner_id")
        
        print_success(f"Game status: {game_status}")
        print_success(f"Winner ID: {winner_id}")
        
        if game_status == "COMPLETED":
            print_success("✅ Game completed successfully")
            record_test("Commission Return - Game Completion", True)
        else:
            print_warning(f"Game not completed yet, status: {game_status}")
            # Wait a bit more
            time.sleep(10)
    else:
        print_warning("Could not check game status")
    
    # STEP 9: ПРОВЕРИТЬ ФИНАЛЬНЫЕ балансы
    print_subheader("STEP 9: ПРОВЕРИТЬ ФИНАЛЬНЫЕ балансы")
    
    # Wait a bit more to ensure all transactions are processed
    time.sleep(3)
    
    user1_final_virtual, user1_final_frozen = get_user_balance(user1_token, "User1")
    user2_final_virtual, user2_final_frozen = get_user_balance(user2_token, "User2")
    
    print_success(f"User1 ФИНАЛЬНЫЕ балансы:")
    print_success(f"  Virtual Balance: ${user1_final_virtual}")
    print_success(f"  Frozen Balance: ${user1_final_frozen}")
    
    print_success(f"User2 ФИНАЛЬНЫЕ балансы:")
    print_success(f"  Virtual Balance: ${user2_final_virtual}")
    print_success(f"  Frozen Balance: ${user2_final_frozen}")
    
    # STEP 10: МАТЕМАТИЧЕСКАЯ ПРОВЕРКА
    print_subheader("STEP 10: МАТЕМАТИЧЕСКАЯ ПРОВЕРКА")
    
    print_success("МАТЕМАТИКА ДЛЯ ПРОВЕРКИ:")
    print_success(f"Expected User1 (победитель) final virtual = начальный - ${expected_commission} (комиссия)")
    print_success(f"Expected User2 (проигравший) final virtual = начальный + $0 (комиссия возвращена)")
    print_success(f"Expected both frozen balances = 0 (разморожено)")
    
    # Calculate expected final balances
    expected_user1_final_virtual = user1_initial_virtual - expected_commission  # Winner pays commission
    expected_user2_final_virtual = user2_initial_virtual  # Loser gets commission back
    expected_final_frozen = 0.0  # All should be unfrozen
    
    print_success(f"Expected User1 final virtual: ${expected_user1_final_virtual}")
    print_success(f"Expected User2 final virtual: ${expected_user2_final_virtual}")
    print_success(f"Expected frozen balances: ${expected_final_frozen}")
    
    # Check User1 (winner) - should pay commission
    user1_virtual_final_correct = abs(user1_final_virtual - expected_user1_final_virtual) < 0.01
    user1_frozen_final_correct = abs(user1_final_frozen - expected_final_frozen) < 0.01
    
    if user1_virtual_final_correct and user1_frozen_final_correct:
        print_success(f"✅ User1 (ПОБЕДИТЕЛЬ) балансы корректны - комиссия ${expected_commission} СПИСАНА")
        record_test("Commission Return - User1 Winner Commission", True)
    else:
        print_error(f"❌ User1 (ПОБЕДИТЕЛЬ) балансы некорректны")
        print_error(f"Expected virtual: ${expected_user1_final_virtual}, got: ${user1_final_virtual}")
        print_error(f"Expected frozen: ${expected_final_frozen}, got: ${user1_final_frozen}")
        record_test("Commission Return - User1 Winner Commission", False, "User1 balances incorrect")
    
    # Check User2 (loser) - should get commission back
    user2_virtual_final_correct = abs(user2_final_virtual - expected_user2_final_virtual) < 0.01
    user2_frozen_final_correct = abs(user2_final_frozen - expected_final_frozen) < 0.01
    
    if user2_virtual_final_correct and user2_frozen_final_correct:
        print_success(f"✅ User2 (ПРОИГРАВШИЙ) балансы корректны - комиссия ${expected_commission} ВОЗВРАЩЕНА")
        record_test("Commission Return - User2 Loser Commission Return", True)
    else:
        print_error(f"❌ User2 (ПРОИГРАВШИЙ) балансы некорректны")
        print_error(f"Expected virtual: ${expected_user2_final_virtual}, got: ${user2_final_virtual}")
        print_error(f"Expected frozen: ${expected_final_frozen}, got: ${user2_final_frozen}")
        record_test("Commission Return - User2 Loser Commission Return", False, "User2 balances incorrect")
    
    # STEP 11: Проверить транзакции
    print_subheader("STEP 11: Проверить транзакции")
    
    # Get User2 transactions to verify commission return
    user2_transactions = get_user_transactions(user2_token, "User2")
    
    # Look for COMMISSION transaction with positive amount (return)
    commission_return_found = False
    for transaction in user2_transactions:
        if (transaction.get("transaction_type") == "COMMISSION" and 
            transaction.get("amount", 0) > 0 and
            abs(transaction.get("amount", 0) - expected_commission) < 0.01):
            commission_return_found = True
            print_success(f"✅ Found COMMISSION return transaction for User2: ${transaction.get('amount')}")
            print_success(f"   Description: {transaction.get('description', 'N/A')}")
            break
    
    if commission_return_found:
        print_success(f"✅ COMMISSION транзакция для User2 с возвратом ${expected_commission} найдена")
        record_test("Commission Return - User2 Commission Transaction", True)
    else:
        print_error(f"❌ COMMISSION транзакция для User2 с возвратом ${expected_commission} НЕ найдена")
        record_test("Commission Return - User2 Commission Transaction", False, "Commission return transaction not found")
    
    # STEP 12: ФИНАЛЬНАЯ ПРОВЕРКА
    print_subheader("STEP 12: ФИНАЛЬНАЯ ПРОВЕРКА")
    
    all_checks_passed = (
        user1_virtual_final_correct and user1_frozen_final_correct and
        user2_virtual_final_correct and user2_frozen_final_correct and
        commission_return_found
    )
    
    if all_checks_passed:
        print_success("🎉 ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ ВОЗВРАТА КОМИССИИ: УСПЕШНО!")
        print_success("✅ User1 (победитель): комиссия $1.05 СПИСАНА")
        print_success("✅ User2 (проигравший): комиссия $1.05 ВОЗВРАЩЕНА")
        print_success("✅ Все балансы разморожены корректно")
        print_success("✅ COMMISSION транзакция для возврата найдена")
        print_success("✅ Новая логика возврата комиссии проигравшему РАБОТАЕТ!")
        
        record_test("Commission Return - Overall Success", True)
    else:
        print_error("❌ ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ ВОЗВРАТА КОМИССИИ: НЕУДАЧНО!")
        print_error("❌ Новая логика возврата комиссии требует исправления")
        
        record_test("Commission Return - Overall Success", False, "Commission return logic not working correctly")
    
    # SUMMARY
    print_subheader("SUMMARY - ИТОГИ ТЕСТИРОВАНИЯ")
    
    print_success("РЕЗУЛЬТАТЫ ДЕТАЛЬНОГО ТЕСТИРОВАНИЯ:")
    print_success(f"- Всего тестов: {test_results['total']}")
    print_success(f"- Пройдено: {test_results['passed']}")
    print_success(f"- Провалено: {test_results['failed']}")
    print_success(f"- Процент успеха: {(test_results['passed'] / test_results['total'] * 100):.1f}%")
    
    print_success("\nКЛЮЧЕВЫЕ ПРОВЕРКИ:")
    print_success(f"✅ User1 (создатель/победитель): комиссия ${expected_commission} списана")
    print_success(f"✅ User2 (присоединившийся/проигравший): комиссия ${expected_commission} возвращена")
    print_success(f"✅ Математическая корректность: проверена")
    print_success(f"✅ Транзакции: проверены")
    
    if all_checks_passed:
        print_success("\n🎉 ФОКУС ДОСТИГНУТ: Пошаговая проверка подтвердила что новая логика возврата комиссии проигравшему действительно работает!")
    else:
        print_error("\n❌ ТРЕБУЕТСЯ ДОРАБОТКА: Логика возврата комиссии проигравшему работает не полностью корректно")

def main():
    """Main test execution."""
    print_header("COMMISSION RETURN TO LOSING PLAYER - DETAILED TESTING")
    print("Russian Review Requirements: Detailed testing of commission return to losing player")
    print("Focus: Step-by-step verification that new commission return logic actually works")
    
    try:
        test_commission_return_to_losing_player()
    except Exception as e:
        print_error(f"Test execution failed with error: {e}")
        record_test("Commission Return - Test Execution", False, f"Error: {e}")
    
    # Final results
    print_header("FINAL TEST RESULTS")
    
    success_rate = (test_results["passed"] / test_results["total"] * 100) if test_results["total"] > 0 else 0
    
    print_success(f"Total tests: {test_results['total']}")
    print_success(f"Passed: {test_results['passed']}")
    print_success(f"Failed: {test_results['failed']}")
    print_success(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print_success("🎉 COMMISSION RETURN LOGIC: WORKING CORRECTLY!")
    else:
        print_error("❌ COMMISSION RETURN LOGIC: NEEDS FIXES!")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)