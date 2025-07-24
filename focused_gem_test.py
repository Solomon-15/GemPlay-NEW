#!/usr/bin/env python3
"""
Focused test for Gem Display Changes from Dollars to Gems
Testing the specific changes in bot bet range display from dollars to gems.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://b668b82c-dc8f-4fe0-a08d-9342c0894445.preview.emergentagent.com/api"
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if "access_token" in response:
            print_success(f"{user_type.title()} logged in successfully")
            record_test(f"{user_type.title()} Login", True)
            return response["access_token"]
        else:
            print_error(f"{user_type.title()} login response missing access_token: {response}")
            record_test(f"{user_type.title()} Login", False, "Missing access_token")
    else:
        record_test(f"{user_type.title()} Login", False, "Request failed")
    
    return None

def test_gem_display_changes() -> None:
    """Test the specific gem display changes from dollars to gems."""
    print_header("GEM DISPLAY CHANGES TESTING")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with test")
        record_test("Gem Display - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test Human-Bot creation with integer values (gems)
    print_subheader("Step 2: Test Human-Bot Creation with Integer Gem Values")
    
    test_bot_data = {
        "name": f"GemDisplayTest_{int(time.time())}",
        "character": "BALANCED",
        "min_bet": 5,  # 5 gems (was $5)
        "max_bet": 50,  # 50 gems (was $50)
        "bet_limit": 12,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "min_delay": 30,
        "max_delay": 90,
        "use_commit_reveal": True,
        "logging_level": "INFO",
        "can_play_with_other_bots": True,
        "can_play_with_players": True
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/human-bots",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    test_bot_id = None
    if create_success:
        test_bot_id = create_response.get("id")
        min_bet_response = create_response.get("min_bet")
        max_bet_response = create_response.get("max_bet")
        
        print_success(f"✓ Human-Bot created with integer gem values")
        print_success(f"  Bot ID: {test_bot_id}")
        print_success(f"  Min bet: {min_bet_response} (should be 5.0 for 5 gems)")
        print_success(f"  Max bet: {max_bet_response} (should be 50.0 for 50 gems)")
        
        # Verify the values are correct for gem display
        if min_bet_response == 5.0 and max_bet_response == 50.0:
            print_success("✓ Backend correctly handles integer gem values")
            record_test("Gem Display - Human-Bot Integer Values", True)
        else:
            print_error(f"✗ Backend values incorrect: min={min_bet_response}, max={max_bet_response}")
            record_test("Gem Display - Human-Bot Integer Values", False, f"Values: min={min_bet_response}, max={max_bet_response}")
    else:
        print_error(f"Failed to create Human-Bot: {create_response}")
        record_test("Gem Display - Human-Bot Integer Values", False, "Creation failed")
    
    # Step 3: Test Regular Bot creation with correct endpoint
    print_subheader("Step 3: Test Regular Bot Creation with Integer Gem Values")
    
    regular_bot_data = {
        "name": f"GemRegularTest_{int(time.time())}",
        "bot_type": "REGULAR",
        "min_bet_amount": 3,  # 3 gems (was $3)
        "max_bet_amount": 30,  # 30 gems (was $30)
        "win_rate": 55.0,
        "cycle_games": 15,
        "individual_limit": 15,
        "creation_mode": "queue-based",
        "priority_order": 50,
        "pause_between_games": 5,
        "profit_strategy": "balanced",
        "can_accept_bets": False,
        "can_play_with_bots": False,
        "avatar_gender": "male",
        "simple_mode": False
    }
    
    regular_create_response, regular_create_success = make_request(
        "POST", "/admin/bots/create-regular",
        data=regular_bot_data,
        auth_token=admin_token
    )
    
    regular_bot_id = None
    if regular_create_success:
        regular_bot_id = regular_create_response.get("id")
        regular_min_bet = regular_create_response.get("min_bet_amount")
        regular_max_bet = regular_create_response.get("max_bet_amount")
        
        print_success(f"✓ Regular Bot created with integer gem values")
        print_success(f"  Bot ID: {regular_bot_id}")
        print_success(f"  Min bet amount: {regular_min_bet} (should be 3.0 for 3 gems)")
        print_success(f"  Max bet amount: {regular_max_bet} (should be 30.0 for 30 gems)")
        
        # Verify the values are correct for gem display
        if regular_min_bet == 3.0 and regular_max_bet == 30.0:
            print_success("✓ Backend correctly handles integer gem values for Regular Bots")
            record_test("Gem Display - Regular Bot Integer Values", True)
        else:
            print_error(f"✗ Regular Bot values incorrect: min={regular_min_bet}, max={regular_max_bet}")
            record_test("Gem Display - Regular Bot Integer Values", False, f"Values: min={regular_min_bet}, max={regular_max_bet}")
    else:
        print_error(f"Failed to create Regular Bot: {regular_create_response}")
        record_test("Gem Display - Regular Bot Integer Values", False, "Creation failed")
    
    # Step 4: Test that existing bots display correctly with gem values
    print_subheader("Step 4: Test Existing Bots Display with Gem Values")
    
    # Get Human-Bot list
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if human_bots_success:
        human_bots = human_bots_response.get("bots", [])
        print_success(f"✓ Retrieved {len(human_bots)} Human-Bots")
        
        # Check that values can be displayed as gems (integers)
        gem_compatible_count = 0
        for bot in human_bots[:5]:
            bot_name = bot.get("name", "unknown")
            min_bet = bot.get("min_bet")
            max_bet = bot.get("max_bet")
            
            # Check if values can be displayed as gems (whole numbers)
            min_bet_gems = int(min_bet) if isinstance(min_bet, (int, float)) else 0
            max_bet_gems = int(max_bet) if isinstance(max_bet, (int, float)) else 0
            
            print_success(f"  {bot_name}: {min_bet_gems}-{max_bet_gems} gems (was ${min_bet}-${max_bet})")
            
            if min_bet_gems > 0 and max_bet_gems > 0 and min_bet_gems <= max_bet_gems:
                gem_compatible_count += 1
        
        if gem_compatible_count >= 4:  # At least 4 out of 5 should be compatible
            print_success("✓ Existing Human-Bots are compatible with gem display")
            record_test("Gem Display - Human-Bot Compatibility", True)
        else:
            print_warning("⚠ Some Human-Bots may have gem display issues")
            record_test("Gem Display - Human-Bot Compatibility", False, f"Only {gem_compatible_count}/5 compatible")
    else:
        print_error("Failed to retrieve Human-Bots")
        record_test("Gem Display - Human-Bot Compatibility", False, "Retrieval failed")
    
    # Get Regular Bot list
    regular_bots_response, regular_bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    
    if regular_bots_success:
        regular_bots = regular_bots_response.get("bots", [])
        print_success(f"✓ Retrieved {len(regular_bots)} Regular Bots")
        
        # Check that values can be displayed as gems (integers)
        gem_compatible_count = 0
        for bot in regular_bots[:5]:
            bot_name = bot.get("name", "unknown")
            min_bet = bot.get("min_bet_amount")
            max_bet = bot.get("max_bet_amount")
            
            # Check if values can be displayed as gems (whole numbers)
            min_bet_gems = int(min_bet) if isinstance(min_bet, (int, float)) else 0
            max_bet_gems = int(max_bet) if isinstance(max_bet, (int, float)) else 0
            
            print_success(f"  {bot_name}: {min_bet_gems}-{max_bet_gems} gems (was ${min_bet}-${max_bet})")
            
            if min_bet_gems > 0 and max_bet_gems > 0 and min_bet_gems <= max_bet_gems:
                gem_compatible_count += 1
        
        if gem_compatible_count >= 4:  # At least 4 out of 5 should be compatible
            print_success("✓ Existing Regular Bots are compatible with gem display")
            record_test("Gem Display - Regular Bot Compatibility", True)
        else:
            print_warning("⚠ Some Regular Bots may have gem display issues")
            record_test("Gem Display - Regular Bot Compatibility", False, f"Only {gem_compatible_count}/5 compatible")
    else:
        print_error("Failed to retrieve Regular Bots")
        record_test("Gem Display - Regular Bot Compatibility", False, "Retrieval failed")
    
    # Step 5: Test that game creation logic still works with gem values
    print_subheader("Step 5: Test Game Creation Logic with Gem Values")
    
    # Get available games and check bet amounts
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        bot_games = [game for game in available_games_response if game.get("creator_type") in ["bot", "human_bot"]]
        
        if bot_games:
            print_success(f"✓ Found {len(bot_games)} bot games")
            
            # Check that bet amounts are reasonable for gem display
            reasonable_bets = 0
            for i, game in enumerate(bot_games[:10]):
                bet_amount = game.get("bet_amount", 0)
                creator_type = game.get("creator_type", "unknown")
                
                # Check if bet amount is a reasonable gem value (whole number or close to it)
                is_gem_compatible = isinstance(bet_amount, (int, float)) and bet_amount == int(bet_amount)
                
                print_success(f"  Game {i+1}: ${bet_amount} ({int(bet_amount)} gems) - {creator_type}")
                
                if is_gem_compatible and 1 <= bet_amount <= 10000:
                    reasonable_bets += 1
                    print_success(f"    ✓ Compatible with gem display")
                else:
                    print_warning(f"    ⚠ May have gem display issues")
            
            if reasonable_bets >= 8:  # At least 8 out of 10 should be reasonable
                print_success("✓ Most bot games are compatible with gem display")
                record_test("Gem Display - Game Compatibility", True)
            else:
                print_warning("⚠ Some bot games may have gem display issues")
                record_test("Gem Display - Game Compatibility", False, f"Only {reasonable_bets}/10 compatible")
        else:
            print_warning("No bot games found for testing")
            record_test("Gem Display - Game Compatibility", False, "No games found")
    else:
        print_error("Failed to retrieve available games")
        record_test("Gem Display - Game Compatibility", False, "Games retrieval failed")
    
    # Step 6: Cleanup
    print_subheader("Step 6: Cleanup Test Bots")
    
    # Delete test Human-Bot
    if test_bot_id:
        delete_response, delete_success = make_request(
            "DELETE", f"/admin/human-bots/{test_bot_id}",
            auth_token=admin_token
        )
        if delete_success:
            print_success("✓ Test Human-Bot deleted")
        else:
            print_warning("⚠ Failed to delete test Human-Bot")
    
    # Delete test Regular Bot
    if regular_bot_id:
        delete_response, delete_success = make_request(
            "DELETE", f"/admin/bots/{regular_bot_id}/delete",
            auth_token=admin_token
        )
        if delete_success:
            print_success("✓ Test Regular Bot deleted")
        else:
            print_warning("⚠ Failed to delete test Regular Bot")
    
    print_success("✓ Gem display testing completed")

def print_test_summary() -> None:
    """Print a summary of all test results."""
    print_header("GEM DISPLAY CHANGES TEST SUMMARY")
    
    print_success(f"Total tests run: {test_results['total']}")
    print_success(f"Tests passed: {test_results['passed']}")
    
    if test_results['failed'] > 0:
        print_error(f"Tests failed: {test_results['failed']}")
    else:
        print_success(f"Tests failed: {test_results['failed']}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print_success(f"Success rate: {success_rate:.1f}%")
    
    # Print failed tests details
    if test_results['failed'] > 0:
        print_subheader("Failed Tests Details")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"❌ {test['name']}")
                if test['details']:
                    print_error(f"   Details: {test['details']}")
    
    # Overall assessment
    print_subheader("Overall Assessment")
    
    if test_results['failed'] == 0:
        print_success("🎉 ALL TESTS PASSED!")
        print_success("✅ Gem display changes are working correctly")
        print_success("✅ Backend APIs handle integer values properly")
        print_success("✅ Bot creation and management work with gem values")
        print_success("✅ Existing bots are compatible with the changes")
        print_success("✅ Game creation logic is not broken")
    elif test_results['failed'] <= test_results['total'] * 0.2:  # Less than 20% failed
        print_success("✅ MOSTLY SUCCESSFUL!")
        print_success("✅ Gem display changes are mostly working correctly")
        print_warning("⚠ Minor issues detected - see failed tests above")
    else:
        print_error("❌ SIGNIFICANT ISSUES DETECTED!")
        print_error("❌ Gem display changes have problems")
        print_error("❌ Review failed tests and fix issues")

def main():
    """Main test execution function."""
    print_header("GEM DISPLAY CHANGES TESTING")
    print("Testing changes in bot bet range display from dollars to gems")
    print("CONVERSION LOGIC: $1 = 1 gem (formatAsGems() removes $ and formats as integer)")
    print()
    
    try:
        # Run focused test
        test_gem_display_changes()
        
        # Print summary
        print_test_summary()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()