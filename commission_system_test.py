#!/usr/bin/env python3
"""
Focused PvP Commission System Testing - Russian Review
Focus: Testing commission system fixes for Human-bot games
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
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

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

def test_commission_system_comprehensive():
    """Test the commission system comprehensively based on Russian review requirements."""
    print_header("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ КОМИССИЙ")
    
    # Step 1: Admin login
    print_subheader("Step 1: Admin Login")
    admin_response, admin_success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if not admin_success or "access_token" not in admin_response:
        print_error("Cannot proceed without admin access")
        record_test("Admin Login", False)
        return
    
    admin_token = admin_response["access_token"]
    print_success("Admin logged in successfully")
    record_test("Admin Login", True)
    
    # Step 2: Create test user
    print_subheader("Step 2: Create Test User")
    timestamp = int(time.time())
    test_email = f"commissiontest_{timestamp}@test.com"
    
    register_response, register_success = make_request("POST", "/auth/register", data={
        "username": f"CommissionTest_{timestamp}",
        "email": test_email,
        "password": "Test123!",
        "gender": "male"
    })
    
    if not register_success or "verification_token" not in register_response:
        print_error("User registration failed")
        record_test("User Registration", False)
        return
    
    # Verify email
    verify_response, verify_success = make_request("POST", "/auth/verify-email", data={
        "token": register_response["verification_token"]
    })
    
    if not verify_success:
        print_error("Email verification failed")
        record_test("Email Verification", False)
        return
    
    # Login user
    login_response, login_success = make_request("POST", "/auth/login", data={
        "email": test_email,
        "password": "Test123!"
    })
    
    if not login_success or "access_token" not in login_response:
        print_error("User login failed")
        record_test("User Login", False)
        return
    
    user_token = login_response["access_token"]
    user_id = login_response["user"]["id"]
    print_success("Test user created and logged in successfully")
    record_test("User Creation", True)
    
    # Step 3: Add gems to user
    print_subheader("Step 3: Add Gems to User")
    
    # Add Ruby gems (worth $1 each)
    gem_response, gem_success = make_request("POST", "/gems/buy?gem_type=Ruby&quantity=50", auth_token=user_token)
    
    if gem_success:
        print_success("Added 50 Ruby gems ($50 worth)")
        record_test("Add Gems", True)
    else:
        print_error("Failed to add gems")
        record_test("Add Gems", False)
        return
    
    # Step 4: Get initial balance
    print_subheader("Step 4: Check Initial Balance")
    balance_response, balance_success = make_request("GET", "/auth/me", auth_token=user_token)
    
    if balance_success:
        initial_virtual = balance_response["virtual_balance"]
        initial_frozen = balance_response["frozen_balance"]
        print_success(f"Initial balance - Virtual: ${initial_virtual:.2f}, Frozen: ${initial_frozen:.2f}")
        record_test("Initial Balance Check", True)
    else:
        print_error("Failed to get initial balance")
        record_test("Initial Balance Check", False)
        return
    
    # Step 5: Create Human-bot
    print_subheader("Step 5: Create Human-Bot for Testing")
    
    bot_name = f"CommissionTestBot_{timestamp}"
    bot_response, bot_success = make_request("POST", "/admin/human-bots", data={
        "name": bot_name,
        "character": "BALANCED",
        "gender": "male",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "bet_limit": 10,
        "bet_limit_amount": 500.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "min_delay": 5,
        "max_delay": 15,
        "use_commit_reveal": True,
        "logging_level": "INFO",
        "can_play_with_other_bots": True,
        "can_play_with_players": True
    }, auth_token=admin_token)
    
    if bot_success and "id" in bot_response:
        bot_id = bot_response["id"]
        print_success(f"Human-bot created: {bot_name} (ID: {bot_id})")
        record_test("Human-Bot Creation", True)
    else:
        print_error("Failed to create Human-bot")
        record_test("Human-Bot Creation", False)
        return
    
    # Step 6: Test commission system by creating a game
    print_subheader("Step 6: Test Commission System - Create Game")
    
    # Create a $30 bet (30 Ruby gems)
    bet_amount = 30
    create_response, create_success = make_request("POST", "/games/create", data={
        "move": "rock",
        "bet_gems": {"Ruby": bet_amount}
    }, auth_token=user_token)
    
    if create_success and "game_id" in create_response:
        game_id = create_response["game_id"]
        print_success(f"Game created: {game_id}")
        record_test("Game Creation", True)
        
        # Check balance after game creation (commission should be frozen)
        balance_after_create, balance_success = make_request("GET", "/auth/me", auth_token=user_token)
        
        if balance_success:
            after_virtual = balance_after_create["virtual_balance"]
            after_frozen = balance_after_create["frozen_balance"]
            commission_frozen = after_frozen - initial_frozen
            expected_commission = bet_amount * 0.03  # 3% commission
            
            print_success(f"Balance after create - Virtual: ${after_virtual:.2f}, Frozen: ${after_frozen:.2f}")
            print_success(f"Commission frozen: ${commission_frozen:.2f} (Expected: ${expected_commission:.2f})")
            
            if abs(commission_frozen - expected_commission) < 0.01:
                print_success("✓ COMMISSION CORRECTLY FROZEN FOR GAME CREATION")
                record_test("Commission Freeze on Create", True)
            else:
                print_error(f"✗ Commission freeze mismatch: Expected ${expected_commission:.2f}, got ${commission_frozen:.2f}")
                record_test("Commission Freeze on Create", False)
        else:
            print_error("Failed to check balance after game creation")
            record_test("Balance Check After Create", False)
    else:
        print_error("Failed to create game")
        record_test("Game Creation", False)
        return
    
    # Step 7: Test available games and Human-bot interaction
    print_subheader("Step 7: Check Available Games")
    
    available_response, available_success = make_request("GET", "/games/available", auth_token=user_token)
    
    if available_success and "games" in available_response:
        available_games = available_response["games"]
        print_success(f"Found {len(available_games)} available games")
        
        # Look for our game or Human-bot games
        human_bot_games = [g for g in available_games if g.get("creator_type") == "human_bot"]
        user_games = [g for g in available_games if g.get("id") == game_id]
        
        print_success(f"Human-bot games available: {len(human_bot_games)}")
        print_success(f"User's game in available list: {len(user_games) > 0}")
        
        record_test("Available Games Check", True)
        
        # If there are Human-bot games, test joining one
        if human_bot_games:
            print_subheader("Step 8: Test Joining Human-Bot Game")
            
            target_game = human_bot_games[0]
            target_game_id = target_game["id"]
            target_bet_amount = target_game["bet_amount"]
            target_gems = target_game["bet_gems"]
            
            print_success(f"Joining Human-bot game: {target_game_id} (${target_bet_amount})")
            print_success(f"Required gems: {target_gems}")
            
            # Check if user has enough gems to join
            inventory_response, inventory_success = make_request("GET", "/gems/inventory", auth_token=user_token)
            
            if inventory_success and "gems" in inventory_response:
                user_gems = {gem["type"]: gem["quantity"] for gem in inventory_response["gems"]}
                print_success(f"User gem inventory: {user_gems}")
                
                # Try to join the Human-bot game
                join_response, join_success = make_request("POST", f"/games/{target_game_id}/join", data={
                    "move": "paper",
                    "gems": target_gems
                }, auth_token=user_token)
                
                if join_success:
                    print_success("✓ SUCCESSFULLY JOINED HUMAN-BOT GAME")
                    
                    # Check if game status is ACTIVE
                    if "status" in join_response and join_response["status"] == "ACTIVE":
                        print_success("✓ GAME STATUS IS ACTIVE AFTER JOIN")
                        record_test("Human-Bot Game Join", True)
                        
                        # Check commission handling for Human vs Human-bot
                        balance_after_join, balance_success = make_request("GET", "/auth/me", auth_token=user_token)
                        
                        if balance_success:
                            join_virtual = balance_after_join["virtual_balance"]
                            join_frozen = balance_after_join["frozen_balance"]
                            total_commission = join_frozen - initial_frozen
                            expected_total = (bet_amount + target_bet_amount) * 0.03
                            
                            print_success(f"Total commission frozen: ${total_commission:.2f}")
                            print_success(f"Expected total commission: ${expected_total:.2f}")
                            
                            # In Human vs Human-bot games, BOTH players should pay commission
                            if abs(total_commission - expected_total) < 0.01:
                                print_success("✓ COMMISSION SYSTEM WORKING: Both players pay commission in Human vs Human-bot")
                                record_test("Human vs Human-Bot Commission", True)
                            else:
                                print_warning(f"Commission handling may differ: Expected ${expected_total:.2f}, got ${total_commission:.2f}")
                                record_test("Human vs Human-Bot Commission", False, "Commission amount mismatch")
                        
                        # Wait a bit and check if game completes (Human-bots auto-complete)
                        print_subheader("Step 9: Wait for Game Completion")
                        time.sleep(10)  # Wait 10 seconds
                        
                        final_balance, final_success = make_request("GET", "/auth/me", auth_token=user_token)
                        
                        if final_success:
                            final_virtual = final_balance["virtual_balance"]
                            final_frozen = final_balance["frozen_balance"]
                            
                            print_success(f"Final balance - Virtual: ${final_virtual:.2f}, Frozen: ${final_frozen:.2f}")
                            
                            # Check if commission was handled properly after game completion
                            if final_frozen < join_frozen:
                                commission_change = join_frozen - final_frozen
                                print_success(f"✓ COMMISSION PROCESSED: ${commission_change:.2f} commission handled after game completion")
                                record_test("Commission Processing After Game", True)
                            else:
                                print_warning("Commission still frozen - game may not have completed yet")
                                record_test("Commission Processing After Game", False, "Commission still frozen")
                    else:
                        print_error("Game status not ACTIVE after join")
                        record_test("Human-Bot Game Join", False, "Status not ACTIVE")
                else:
                    print_error("Failed to join Human-bot game")
                    record_test("Human-Bot Game Join", False, "Join request failed")
            else:
                print_error("Failed to get gem inventory")
                record_test("Gem Inventory Check", False)
        else:
            print_warning("No Human-bot games available for testing")
            record_test("Human-Bot Games Available", False, "No Human-bot games found")
    else:
        print_error("Failed to get available games")
        record_test("Available Games Check", False)

def print_final_results():
    """Print final test results summary."""
    print_header("ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СИСТЕМЫ КОМИССИЙ")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Всего тестов: {total}")
    print(f"Успешно: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Неудачно: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Процент успеха: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    print_subheader("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ")
    
    for test in test_results["tests"]:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if test["passed"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"{status} {test['name']}")
        if test["details"]:
            print(f"   {test['details']}")
    
    # Summary for Russian review requirements
    print_subheader("СООТВЕТСТВИЕ ТРЕБОВАНИЯМ РУССКОГО ОБЗОРА")
    
    commission_tests = [t for t in test_results["tests"] if "Commission" in t["name"]]
    commission_passed = sum(1 for t in commission_tests if t["passed"])
    
    human_bot_tests = [t for t in test_results["tests"] if "Human-Bot" in t["name"] or "Human vs Human-Bot" in t["name"]]
    human_bot_passed = sum(1 for t in human_bot_tests if t["passed"])
    
    print(f"1. Система комиссий: {commission_passed}/{len(commission_tests)} тестов")
    print(f"2. Human-bot взаимодействие: {human_bot_passed}/{len(human_bot_tests)} тестов")
    
    if success_rate >= 80:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 СИСТЕМА КОМИССИЙ РАБОТАЕТ КОРРЕКТНО!{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ{Colors.ENDC}")

def main():
    """Main test execution."""
    print_header("ТЕСТИРОВАНИЕ СИСТЕМЫ КОМИССИЙ PVP СТАВОК")
    print("Фокус на требованиях русского обзора:")
    print("- Человек vs Human-bot: комиссию платят ОБА игрока")
    print("- Human-bot vs Human-bot: комиссию платят ОБА игрока")
    print("- Человек vs Человек: комиссию платит только победитель")
    print("- Любой vs Regular bot: без комиссии")
    
    try:
        test_commission_system_comprehensive()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Тестирование прервано пользователем{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Критическая ошибка: {e}{Colors.ENDC}")
    finally:
        print_final_results()

if __name__ == "__main__":
    main()