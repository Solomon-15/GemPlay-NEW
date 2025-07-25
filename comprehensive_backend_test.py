#!/usr/bin/env python3
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib

# Configuration
BASE_URL = "https://e53a4d4d-7cc3-466c-a587-0e8cb72b5c7a.preview.emergentagent.com/api"
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

def test_admin_login() -> Optional[str]:
    """Test admin login."""
    print_subheader("Testing Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin login successful")
        record_test("Admin Login", True)
        return response["access_token"]
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, f"Login failed: {response}")
        return None

def test_gem_definitions():
    """Test gem definitions API."""
    print_subheader("Testing Gem Definitions API")
    
    response, success = make_request("GET", "/gems/definitions")
    
    if success and isinstance(response, list) and len(response) > 0:
        print_success(f"Retrieved {len(response)} gem definitions")
        
        # Check if all expected gems are present
        expected_gems = ["Ruby", "Amber", "Topaz", "Emerald", "Aquamarine", "Sapphire", "Magic"]
        found_gems = [gem["name"] for gem in response]
        
        missing_gems = [gem for gem in expected_gems if gem not in found_gems]
        if not missing_gems:
            print_success("All expected gem types found")
            record_test("Gem Definitions - Complete", True)
        else:
            print_error(f"Missing gem types: {missing_gems}")
            record_test("Gem Definitions - Complete", False, f"Missing: {missing_gems}")
        
        # Check gem structure
        first_gem = response[0]
        required_fields = ["type", "name", "price", "color", "icon", "rarity"]
        missing_fields = [field for field in required_fields if field not in first_gem]
        
        if not missing_fields:
            print_success("Gem definition structure is correct")
            record_test("Gem Definitions - Structure", True)
        else:
            print_error(f"Missing fields in gem definition: {missing_fields}")
            record_test("Gem Definitions - Structure", False, f"Missing fields: {missing_fields}")
    else:
        print_error(f"Failed to get gem definitions: {response}")
        record_test("Gem Definitions", False, "API call failed")

def test_gem_inventory(token: str):
    """Test gem inventory API."""
    print_subheader("Testing Gem Inventory API")
    
    response, success = make_request("GET", "/gems/inventory", auth_token=token)
    
    if success and isinstance(response, list):
        print_success(f"Retrieved gem inventory with {len(response)} gem types")
        
        # Check inventory structure
        if response:
            first_gem = response[0]
            required_fields = ["type", "name", "price", "quantity", "frozen_quantity"]
            missing_fields = [field for field in required_fields if field not in first_gem]
            
            if not missing_fields:
                print_success("Gem inventory structure is correct")
                record_test("Gem Inventory - Structure", True)
            else:
                print_error(f"Missing fields in inventory: {missing_fields}")
                record_test("Gem Inventory - Structure", False, f"Missing fields: {missing_fields}")
        
        record_test("Gem Inventory", True)
    else:
        print_error(f"Failed to get gem inventory: {response}")
        record_test("Gem Inventory", False, "API call failed")

def test_gem_buy_sell(token: str):
    """Test gem buy and sell functionality."""
    print_subheader("Testing Gem Buy/Sell Functionality")
    
    # Test buying gems
    print("Testing gem purchase...")
    response, success = make_request(
        "POST", "/gems/buy?gem_type=Ruby&quantity=10", 
        auth_token=token
    )
    
    if success and "message" in response and "total_cost" in response:
        print_success(f"Successfully bought gems: {response['message']}")
        print_success(f"Cost: ${response['total_cost']}")
        record_test("Gem Buy", True)
        
        # Test selling gems
        print("Testing gem sale...")
        sell_response, sell_success = make_request(
            "POST", "/gems/sell?gem_type=Ruby&quantity=5", 
            auth_token=token
        )
        
        if sell_success and "message" in sell_response and "total_value" in sell_response:
            print_success(f"Successfully sold gems: {sell_response['message']}")
            print_success(f"Value: ${sell_response['total_value']}")
            record_test("Gem Sell", True)
        else:
            print_error(f"Failed to sell gems: {sell_response}")
            record_test("Gem Sell", False, "Sell API call failed")
    else:
        print_error(f"Failed to buy gems: {response}")
        record_test("Gem Buy", False, "Buy API call failed")

def test_economy_balance(token: str):
    """Test economy balance API."""
    print_subheader("Testing Economy Balance API")
    
    response, success = make_request("GET", "/economy/balance", auth_token=token)
    
    if success and isinstance(response, dict):
        required_fields = ["virtual_balance", "frozen_balance", "total_gem_value", "available_gem_value", "total_value"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if not missing_fields:
            print_success("Economy balance structure is correct")
            print_success(f"Virtual balance: ${response['virtual_balance']}")
            print_success(f"Frozen balance: ${response['frozen_balance']}")
            print_success(f"Total gem value: ${response['total_gem_value']}")
            record_test("Economy Balance", True)
        else:
            print_error(f"Missing fields in balance response: {missing_fields}")
            record_test("Economy Balance", False, f"Missing fields: {missing_fields}")
    else:
        print_error(f"Failed to get economy balance: {response}")
        record_test("Economy Balance", False, "API call failed")

def test_add_balance_functionality(token: str):
    """Test add balance functionality."""
    print_subheader("Testing Add Balance Functionality")
    
    # Get current balance first
    balance_response, balance_success = make_request("GET", "/economy/balance", auth_token=token)
    if not balance_success:
        print_error("Cannot get current balance for add balance test")
        record_test("Add Balance", False, "Cannot get current balance")
        return
    
    current_balance = balance_response.get("virtual_balance", 0)
    daily_limit_used = balance_response.get("daily_limit_used", 0)
    daily_limit_max = balance_response.get("daily_limit_max", 1000)
    
    # Calculate how much we can add
    remaining_limit = daily_limit_max - daily_limit_used
    
    if remaining_limit <= 0:
        print_warning("Daily limit already reached - testing limit validation")
        response, success = make_request(
            "POST", "/auth/add-balance", 
            data={"amount": 10}, 
            auth_token=token,
            expected_status=400
        )
        
        if not success and "Daily limit already reached" in response.get("detail", ""):
            print_success("Daily limit validation working correctly")
            record_test("Add Balance - Daily Limit", True)
        else:
            print_error(f"Daily limit validation failed: {response}")
            record_test("Add Balance - Daily Limit", False, "Validation not working")
    else:
        # Test adding a small amount
        test_amount = min(50, remaining_limit)
        response, success = make_request(
            "POST", "/auth/add-balance", 
            data={"amount": test_amount}, 
            auth_token=token
        )
        
        if success and "new_balance" in response:
            expected_balance = current_balance + test_amount
            actual_balance = response["new_balance"]
            
            if abs(actual_balance - expected_balance) < 0.01:
                print_success(f"Successfully added ${test_amount} to balance")
                print_success(f"New balance: ${actual_balance}")
                record_test("Add Balance", True)
            else:
                print_error(f"Balance calculation error: Expected ${expected_balance}, got ${actual_balance}")
                record_test("Add Balance", False, "Balance calculation error")
        else:
            print_error(f"Failed to add balance: {response}")
            record_test("Add Balance", False, "API call failed")

def test_game_creation_and_joining(token: str):
    """Test game creation and joining functionality."""
    print_subheader("Testing Game Creation and Joining")
    
    # First ensure we have gems to bet
    buy_response, buy_success = make_request(
        "POST", "/gems/buy?gem_type=Ruby&quantity=20", 
        auth_token=token
    )
    
    if not buy_success:
        print_error("Cannot buy gems for game testing")
        record_test("Game Creation", False, "Cannot buy gems")
        return
    
    # Test creating a game
    print("Testing game creation...")
    game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5}
    }
    
    response, success = make_request(
        "POST", "/games/create", 
        data=game_data, 
        auth_token=token
    )
    
    if success and "game_id" in response:
        game_id = response["game_id"]
        print_success(f"Game created successfully: {game_id}")
        print_success(f"Bet amount: ${response.get('bet_amount', 'N/A')}")
        record_test("Game Creation", True)
        
        # Test getting available games
        print("Testing available games...")
        available_response, available_success = make_request(
            "GET", "/games/available", 
            auth_token=token
        )
        
        if available_success and isinstance(available_response, list):
            print_success(f"Retrieved {len(available_response)} available games")
            record_test("Available Games", True)
        else:
            print_error(f"Failed to get available games: {available_response}")
            record_test("Available Games", False, "API call failed")
        
        # Test my bets
        print("Testing my bets...")
        my_bets_response, my_bets_success = make_request(
            "GET", "/games/my-bets", 
            auth_token=token
        )
        
        if my_bets_success and "games" in my_bets_response:
            games = my_bets_response["games"]
            print_success(f"Retrieved {len(games)} user games")
            
            # Find our created game
            created_game = None
            for game in games:
                if game["game_id"] == game_id:
                    created_game = game
                    break
            
            if created_game:
                print_success(f"Created game found in my bets with status: {created_game['status']}")
                record_test("My Bets", True)
            else:
                print_error("Created game not found in my bets")
                record_test("My Bets", False, "Game not found")
        else:
            print_error(f"Failed to get my bets: {my_bets_response}")
            record_test("My Bets", False, "API call failed")
    else:
        print_error(f"Failed to create game: {response}")
        record_test("Game Creation", False, "API call failed")

def test_commission_and_frozen_balance_system(token: str):
    """Test commission system and frozen balance functionality."""
    print_subheader("Testing Commission and Frozen Balance System")
    
    # Get initial balance
    initial_response, initial_success = make_request("GET", "/economy/balance", auth_token=token)
    if not initial_success:
        print_error("Cannot get initial balance")
        record_test("Commission System", False, "Cannot get balance")
        return
    
    initial_balance = initial_response.get("virtual_balance", 0)
    initial_frozen = initial_response.get("frozen_balance", 0)
    
    print(f"Initial balance: ${initial_balance}, frozen: ${initial_frozen}")
    
    # Create a game to test commission freezing
    game_data = {
        "move": "paper",
        "bet_gems": {"Ruby": 10}  # $10 bet, should freeze $0.60 commission (6%)
    }
    
    response, success = make_request(
        "POST", "/games/create", 
        data=game_data, 
        auth_token=token
    )
    
    if success and "game_id" in response:
        game_id = response["game_id"]
        bet_amount = response.get("bet_amount", 0)
        expected_commission = bet_amount * 0.06
        
        print_success(f"Game created with bet amount: ${bet_amount}")
        print_success(f"Expected commission frozen: ${expected_commission}")
        
        # Check balance after game creation
        after_response, after_success = make_request("GET", "/economy/balance", auth_token=token)
        if after_success:
            after_balance = after_response.get("virtual_balance", 0)
            after_frozen = after_response.get("frozen_balance", 0)
            
            print(f"After game creation - balance: ${after_balance}, frozen: ${after_frozen}")
            
            # Check if commission was frozen correctly
            frozen_increase = after_frozen - initial_frozen
            if abs(frozen_increase - expected_commission) < 0.01:
                print_success(f"Commission correctly frozen: ${frozen_increase}")
                record_test("Commission Freezing", True)
            else:
                print_error(f"Commission freezing error: Expected ${expected_commission}, got ${frozen_increase}")
                record_test("Commission Freezing", False, f"Wrong amount frozen")
            
            # Check that virtual balance didn't decrease (only frozen balance increased)
            if abs(after_balance - initial_balance) < 0.01:
                print_success("Virtual balance correctly unchanged during commission freeze")
                record_test("Balance Preservation", True)
            else:
                print_error(f"Virtual balance incorrectly changed: ${initial_balance} -> ${after_balance}")
                record_test("Balance Preservation", False, "Balance changed incorrectly")
        
        # Test canceling the game to verify commission unfreezing
        print("Testing commission unfreezing via game cancellation...")
        cancel_response, cancel_success = make_request(
            "DELETE", f"/games/{game_id}/cancel", 
            auth_token=token
        )
        
        if cancel_success and cancel_response.get("success"):
            commission_returned = cancel_response.get("commission_returned", 0)
            print_success(f"Game cancelled, commission returned: ${commission_returned}")
            
            # Check balance after cancellation
            final_response, final_success = make_request("GET", "/economy/balance", auth_token=token)
            if final_success:
                final_frozen = final_response.get("frozen_balance", 0)
                
                if abs(final_frozen - initial_frozen) < 0.01:
                    print_success("Frozen balance correctly restored after cancellation")
                    record_test("Commission Unfreezing", True)
                else:
                    print_error(f"Frozen balance not restored: Expected ${initial_frozen}, got ${final_frozen}")
                    record_test("Commission Unfreezing", False, "Balance not restored")
            
            record_test("Game Cancellation", True)
        else:
            print_error(f"Failed to cancel game: {cancel_response}")
            record_test("Game Cancellation", False, "Cancel API failed")
    else:
        print_error(f"Failed to create game for commission test: {response}")
        record_test("Commission System", False, "Game creation failed")

def test_asynchronous_commit_reveal_system(token: str):
    """Test the asynchronous commit-reveal system for PvP games."""
    print_subheader("Testing Asynchronous Commit-Reveal System")
    
    # Create two test users for PvP testing
    timestamp = int(time.time())
    test_user1 = {
        "username": f"pvptest1_{timestamp}",
        "email": f"pvptest1_{timestamp}@test.com",
        "password": "Test123!",
        "gender": "male"
    }
    
    test_user2 = {
        "username": f"pvptest2_{timestamp}",
        "email": f"pvptest2_{timestamp}@test.com",
        "password": "Test123!",
        "gender": "female"
    }
    
    # Register users
    print("Registering test users...")
    user1_response, user1_success = make_request("POST", "/auth/register", data=test_user1)
    user2_response, user2_success = make_request("POST", "/auth/register", data=test_user2)
    
    if not user1_success or not user2_success:
        print_error("Failed to register test users for PvP")
        record_test("Commit-Reveal System", False, "User registration failed")
        return
    
    # Verify emails
    if "verification_token" in user1_response:
        verify_response, _ = make_request("POST", "/auth/verify-email", data={"token": user1_response["verification_token"]})
    if "verification_token" in user2_response:
        verify_response, _ = make_request("POST", "/auth/verify-email", data={"token": user2_response["verification_token"]})
    
    # Login users
    user1_login_response, user1_login_success = make_request("POST", "/auth/login", data={"email": test_user1["email"], "password": test_user1["password"]})
    user2_login_response, user2_login_success = make_request("POST", "/auth/login", data={"email": test_user2["email"], "password": test_user2["password"]})
    
    if not user1_login_success or not user2_login_success:
        print_error("Failed to login test users for PvP")
        record_test("Commit-Reveal System", False, "User login failed")
        return
    
    user1_token = user1_login_response["access_token"]
    user2_token = user2_login_response["access_token"]
    
    # Give users gems for betting
    for user_token in [user1_token, user2_token]:
        buy_response, buy_success = make_request(
            "POST", "/gems/buy?gem_type=Ruby&quantity=20", 
            auth_token=user_token
        )
        if not buy_success:
            print_error("Failed to buy gems for PvP users")
            record_test("Commit-Reveal System", False, "Gem purchase failed")
            return
    
    # Test commit phase - User 1 creates game
    print("Testing commit phase...")
    start_time = time.time()
    
    game_data = {
        "move": "rock",  # This will be hashed and hidden
        "bet_gems": {"Ruby": 5}
    }
    
    create_response, create_success = make_request(
        "POST", "/games/create", 
        data=game_data, 
        auth_token=user1_token
    )
    
    create_time = time.time() - start_time
    
    if create_success and "game_id" in create_response:
        game_id = create_response["game_id"]
        print_success(f"Commit phase completed in {create_time:.3f} seconds")
        print_success(f"Game created with hidden move: {game_id}")
        record_test("Commit Phase", True)
        
        # Test reveal phase - User 2 joins and triggers immediate completion
        print("Testing asynchronous reveal phase...")
        join_start_time = time.time()
        
        join_data = {
            "move": "scissors",  # Rock beats scissors, so user1 should win
            "gems": {"Ruby": 5}  # User2's gem selection
        }
        
        join_response, join_success = make_request(
            "POST", f"/games/{game_id}/join", 
            data=join_data, 
            auth_token=user2_token
        )
        
        join_time = time.time() - join_start_time
        total_time = time.time() - start_time
        
        if join_success:
            print_success(f"Join completed in {join_time:.3f} seconds")
            print_success(f"Total game flow time: {total_time:.3f} seconds")
            
            # Verify asynchronous completion
            if total_time < 1.0:  # Should complete in under 1 second
                print_success("Game completed asynchronously (no polling required)")
                record_test("Asynchronous Completion", True)
            else:
                print_warning(f"Game took {total_time:.3f}s - might not be fully asynchronous")
                record_test("Asynchronous Completion", False, f"Took {total_time:.3f}s")
            
            # Verify response contains all required fields
            required_fields = ["success", "status", "result", "creator_move", "opponent_move"]
            missing_fields = [field for field in required_fields if field not in join_response]
            
            if not missing_fields:
                print_success("Join response contains all required fields")
                print_success(f"Game result: {join_response['result']}")
                print_success(f"Creator move: {join_response['creator_move']}")
                print_success(f"Opponent move: {join_response['opponent_move']}")
                record_test("Response Completeness", True)
                
                # Verify game logic (rock beats scissors)
                if join_response["result"] == "creator_wins":
                    print_success("Game logic correct: rock beats scissors")
                    record_test("Game Logic", True)
                else:
                    print_error(f"Game logic error: Expected creator_wins, got {join_response['result']}")
                    record_test("Game Logic", False, f"Wrong result: {join_response['result']}")
                
                # Verify status is COMPLETED
                if join_response.get("status") == "COMPLETED":
                    print_success("Game status correctly set to COMPLETED")
                    record_test("Game Status", True)
                else:
                    print_error(f"Game status incorrect: {join_response.get('status')}")
                    record_test("Game Status", False, f"Status: {join_response.get('status')}")
            else:
                print_error(f"Join response missing fields: {missing_fields}")
                record_test("Response Completeness", False, f"Missing: {missing_fields}")
            
            record_test("Commit-Reveal System", True)
        else:
            print_error(f"Failed to join game: {join_response}")
            record_test("Commit-Reveal System", False, "Join failed")
    else:
        print_error(f"Failed to create game for commit-reveal test: {create_response}")
        record_test("Commit-Reveal System", False, "Create failed")

def test_core_backend_functionality():
    """Test all core backend functionality as requested in the review."""
    print_header("COMPREHENSIVE BACKEND API TESTING")
    
    # 1. Authentication System
    print_subheader("1. AUTHENTICATION SYSTEM")
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Critical: Admin authentication failed - cannot proceed")
        return
    
    # Test invalid login
    print("Testing invalid login...")
    invalid_response, invalid_success = make_request(
        "POST", "/auth/login", 
        data={"email": "invalid@test.com", "password": "wrongpassword"}, 
        expected_status=401
    )
    if not invalid_success and "Incorrect email or password" in invalid_response.get("detail", ""):
        print_success("Invalid login correctly rejected")
        record_test("Invalid Login", True)
    else:
        print_error(f"Invalid login validation failed: {invalid_response}")
        record_test("Invalid Login", False, "Validation failed")
    
    # 2. Gem System - Definitions, Inventory, Buy/Sell
    print_subheader("2. GEM SYSTEM")
    test_gem_definitions()
    test_gem_inventory(admin_token)
    test_gem_buy_sell(admin_token)
    
    # 3. Balance & Economy System
    print_subheader("3. BALANCE & ECONOMY SYSTEM")
    test_economy_balance(admin_token)
    test_add_balance_functionality(admin_token)
    
    # 4. Game Creation & Joining System
    print_subheader("4. GAME CREATION & JOINING SYSTEM")
    test_game_creation_and_joining(admin_token)
    
    # 5. Commission System & Frozen Balance
    print_subheader("5. COMMISSION SYSTEM & FROZEN BALANCE")
    test_commission_and_frozen_balance_system(admin_token)
    
    # 6. Asynchronous Commit-Reveal System
    print_subheader("6. ASYNCHRONOUS COMMIT-REVEAL SYSTEM")
    test_asynchronous_commit_reveal_system(admin_token)

def print_summary() -> None:
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results["failed"] > 0:
        print("\nFailed tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"{Colors.FAIL}✗ {test['name']}: {test['details']}{Colors.ENDC}")
    
    success_rate = (test_results["passed"] / test_results["total"]) * 100 if test_results["total"] > 0 else 0
    print(f"\nSuccess rate: {Colors.BOLD}{success_rate:.2f}%{Colors.ENDC}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed!{Colors.ENDC}")

def main():
    """Main test function."""
    test_core_backend_functionality()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()