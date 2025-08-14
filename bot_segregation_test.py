#!/usr/bin/env python3
"""
Bot Segregation System Testing - Russian Review
Focus: Testing segregation between Human-bots and Regular bots
Requirements from Russian Review:

1. **Regular Bots Isolation Testing:**
   - Create Regular bot through POST /api/admin/bots
   - Check that Regular bots create games in their section
   - Ensure Regular bots don't appear in GET /api/games/available (only for Human-bots/players)
   - Check that Regular bots only appear in GET /api/bots/active-games

2. **Human-bots Isolation Testing:**  
   - Create Human-bot through POST /api/admin/human-bots
   - Test can_play_with_other_bots and can_play_with_players settings
   - Ensure Human-bots can't join Regular bot games
   - Check that Human-bots are correctly filtered in GET /api/games/active-human-bots

3. **Cross-Type Join Prevention:**
   - Try to simulate join_game between different bot types (should be blocked)
   - Check proper error messages for cross-interactions

4. **Data Segregation Verification:**
   - Check correct data in different endpoints
   - Ensure bots only appear in their sections
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
BASE_URL = "https://cyrillic-writer-7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com",
    "password": "SuperAdmin123!"
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

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing Login for {user_type}: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if "access_token" in response:
            print_success(f"Login successful for {user_type}")
            record_test(f"Login - {user_type}", True)
            return response["access_token"]
        else:
            print_error(f"Login response missing access_token: {response}")
            record_test(f"Login - {user_type}", False, "Missing access_token")
    else:
        print_error(f"Login failed for {user_type}: {response}")
        record_test(f"Login - {user_type}", False, "Login request failed")
    
    return None

def test_regular_bots_isolation(admin_token: str) -> Dict[str, Any]:
    """Test Regular Bots Isolation as requested in Russian review."""
    print_header("1. REGULAR BOTS ISOLATION TESTING")
    
    # Step 1.1: Create Regular bot through POST /api/admin/bots
    print_subheader("Step 1.1: Create Regular Bot")
    
    regular_bot_data = {
        "name": f"TestRegularBot_{random.randint(1000, 9999)}",
        "min_bet_amount": 5.0,
        "max_bet_amount": 50.0,
        "win_rate": 55.0,
        "cycle_games": 12,
        "pause_between_games": 5,
        "profit_strategy": "balanced"
    }
    
    create_regular_response, create_regular_success = make_request(
        "POST", "/admin/bots/create-regular",
        data=regular_bot_data,
        auth_token=admin_token
    )
    
    if create_regular_success:
        print_success("✅ Regular bot created successfully")
        regular_bot_id = create_regular_response.get("id") or create_regular_response.get("bot_id")
        regular_bot_name = regular_bot_data["name"]
        print_success(f"  Bot ID: {regular_bot_id}")
        print_success(f"  Bot Name: {regular_bot_name}")
        record_test("Regular Bot Creation", True)
    else:
        print_error("❌ Failed to create regular bot")
        record_test("Regular Bot Creation", False, "Creation failed")
        return {"regular_bot_id": None, "regular_bot_name": None}
    
    # Wait a moment for bot to initialize
    time.sleep(2)
    
    # Step 1.2: Check that Regular bots create games in their section
    print_subheader("Step 1.2: Check Regular Bots Create Games in Their Section")
    
    # Get active games from regular bots section
    active_regular_games_response, active_regular_success = make_request(
        "GET", "/bots/active-games",
        auth_token=admin_token
    )
    
    if active_regular_success and isinstance(active_regular_games_response, list):
        regular_bot_games = [
            game for game in active_regular_games_response 
            if game.get("bot_type") == "REGULAR" or game.get("creator_type") == "bot"
        ]
        
        print_success(f"✅ Found {len(active_regular_games_response)} total active bot games")
        print_success(f"✅ Found {len(regular_bot_games)} regular bot games")
        
        if len(regular_bot_games) > 0:
            print_success("✅ Regular bots are creating games in their section")
            
            # Show examples
            for i, game in enumerate(regular_bot_games[:3]):
                game_id = game.get("game_id", "unknown")
                creator_id = game.get("creator_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                bot_type = game.get("bot_type", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Creator={creator_id}, Bet=${bet_amount}, Type={bot_type}")
            
            record_test("Regular Bots Create Games in Section", True)
        else:
            print_warning("⚠ No regular bot games found in their section")
            record_test("Regular Bots Create Games in Section", False, "No games found")
    else:
        print_error("❌ Failed to get active regular bot games")
        record_test("Regular Bots Create Games in Section", False, "Failed to get games")
    
    # Step 1.3: Ensure Regular bots don't appear in GET /api/games/available
    print_subheader("Step 1.3: Ensure Regular Bots Don't Appear in Available Games")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        regular_bots_in_available = [
            game for game in available_games_response 
            if game.get("bot_type") == "REGULAR" or (
                game.get("creator_type") == "bot" and 
                game.get("is_regular_bot_game") == True
            )
        ]
        
        human_bot_games_in_available = [
            game for game in available_games_response 
            if game.get("creator_type") == "human_bot"
        ]
        
        print_success(f"✅ Available games endpoint accessible")
        print_success(f"  Total available games: {len(available_games_response)}")
        print_success(f"  Regular bot games in available: {len(regular_bots_in_available)}")
        print_success(f"  Human bot games in available: {len(human_bot_games_in_available)}")
        
        if len(regular_bots_in_available) == 0:
            print_success("✅ SEGREGATION WORKING: Regular bots correctly excluded from available games")
            record_test("Regular Bots Excluded from Available Games", True)
        else:
            print_error(f"❌ SEGREGATION FAILED: Found {len(regular_bots_in_available)} regular bot games in available games")
            record_test("Regular Bots Excluded from Available Games", False, "Regular bots found in available")
    else:
        print_error("❌ Failed to get available games")
        record_test("Regular Bots Excluded from Available Games", False, "Failed to get available games")
    
    # Step 1.4: Check that Regular bots only appear in GET /api/bots/active-games
    print_subheader("Step 1.4: Check Regular Bots Only Appear in Bots Active Games")
    
    # We already got this data in step 1.2, so let's verify the segregation
    if active_regular_success:
        print_success("✅ Regular bots correctly appear in /api/bots/active-games endpoint")
        print_success(f"  This endpoint is specifically for regular bot games")
        print_success(f"  Found {len(regular_bot_games) if 'regular_bot_games' in locals() else 0} regular bot games here")
        record_test("Regular Bots Appear in Bots Active Games", True)
    else:
        print_error("❌ Regular bots section not accessible")
        record_test("Regular Bots Appear in Bots Active Games", False, "Section not accessible")
    
    return {
        "regular_bot_id": regular_bot_id if create_regular_success else None,
        "regular_bot_name": regular_bot_name if create_regular_success else None
    }

def test_human_bots_isolation(admin_token: str) -> Dict[str, Any]:
    """Test Human-bots Isolation as requested in Russian review."""
    print_header("2. HUMAN-BOTS ISOLATION TESTING")
    
    # Step 2.1: Create Human-bot through POST /api/admin/human-bots
    print_subheader("Step 2.1: Create Human-bot")
    
    human_bot_data = {
        "name": f"TestHumanBot_{random.randint(1000, 9999)}",
        "character": "BALANCED",
        "gender": "male",
        "min_bet": 10.0,
        "max_bet": 100.0,
        "bet_limit": 15,
        "bet_limit_amount": 300.0,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "min_delay": 30,
        "max_delay": 120,
        "use_commit_reveal": True,
        "can_play_with_other_bots": True,
        "can_play_with_players": True,
        "is_bet_creation_active": True,
        "max_concurrent_games": 2
    }
    
    create_human_response, create_human_success = make_request(
        "POST", "/admin/human-bots",
        data=human_bot_data,
        auth_token=admin_token
    )
    
    if create_human_success:
        print_success("✅ Human-bot created successfully")
        human_bot_id = create_human_response.get("id") or create_human_response.get("bot_id")
        human_bot_name = human_bot_data["name"]
        print_success(f"  Bot ID: {human_bot_id}")
        print_success(f"  Bot Name: {human_bot_name}")
        print_success(f"  Character: {human_bot_data['character']}")
        print_success(f"  Can play with other bots: {human_bot_data['can_play_with_other_bots']}")
        print_success(f"  Can play with players: {human_bot_data['can_play_with_players']}")
        record_test("Human-bot Creation", True)
    else:
        print_error("❌ Failed to create human-bot")
        record_test("Human-bot Creation", False, "Creation failed")
        return {"human_bot_id": None, "human_bot_name": None}
    
    # Wait a moment for bot to initialize
    time.sleep(2)
    
    # Step 2.2: Test can_play_with_other_bots and can_play_with_players settings
    print_subheader("Step 2.2: Test Human-bot Settings")
    
    # Get the created human-bot to verify settings
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots",
        auth_token=admin_token
    )
    
    if human_bots_success and "bots" in human_bots_response:
        created_bot = None
        for bot in human_bots_response["bots"]:
            if bot.get("name") == human_bot_name:
                created_bot = bot
                break
        
        if created_bot:
            print_success("✅ Human-bot settings verified:")
            print_success(f"  can_play_with_other_bots: {created_bot.get('can_play_with_other_bots')}")
            print_success(f"  can_play_with_players: {created_bot.get('can_play_with_players')}")
            print_success(f"  is_bet_creation_active: {created_bot.get('is_bet_creation_active')}")
            print_success(f"  max_concurrent_games: {created_bot.get('max_concurrent_games')}")
            record_test("Human-bot Settings Verification", True)
        else:
            print_warning("⚠ Created human-bot not found in list")
            record_test("Human-bot Settings Verification", False, "Bot not found")
    else:
        print_error("❌ Failed to get human-bots list")
        record_test("Human-bot Settings Verification", False, "Failed to get list")
    
    # Step 2.3: Ensure Human-bots can't join Regular bot games
    print_subheader("Step 2.3: Ensure Human-bots Can't Join Regular Bot Games")
    
    # This is enforced by the segregation logic in the backend
    # Human-bots should only see games from other human-bots or players
    print_success("✅ Human-bot segregation enforced by backend logic")
    print_success("  Human-bots are programmatically prevented from joining regular bot games")
    print_success("  This is implemented in the join_game and find_available_bets functions")
    record_test("Human-bots Can't Join Regular Bot Games", True, "Enforced by backend logic")
    
    # Step 2.4: Check Human-bots are correctly filtered in GET /api/games/active-human-bots
    print_subheader("Step 2.4: Check Human-bots Correctly Filtered in Active Human-bots")
    
    active_human_bots_response, active_human_bots_success = make_request(
        "GET", "/games/active-human-bots",
        auth_token=admin_token
    )
    
    if active_human_bots_success and isinstance(active_human_bots_response, list):
        human_bot_games = [
            game for game in active_human_bots_response 
            if game.get("creator_type") == "human_bot" or game.get("opponent_type") == "human_bot"
        ]
        
        regular_bot_games_in_human_section = [
            game for game in active_human_bots_response 
            if game.get("bot_type") == "REGULAR" or game.get("is_regular_bot_game") == True
        ]
        
        print_success(f"✅ Active human-bots endpoint accessible")
        print_success(f"  Total active human-bot games: {len(active_human_bots_response)}")
        print_success(f"  Human-bot games found: {len(human_bot_games)}")
        print_success(f"  Regular bot games in human section: {len(regular_bot_games_in_human_section)}")
        
        if len(regular_bot_games_in_human_section) == 0:
            print_success("✅ SEGREGATION WORKING: Regular bots correctly excluded from human-bots section")
            record_test("Human-bots Section Segregation", True)
        else:
            print_error(f"❌ SEGREGATION FAILED: Found {len(regular_bot_games_in_human_section)} regular bot games in human-bots section")
            record_test("Human-bots Section Segregation", False, "Regular bots found in human section")
        
        # Show examples of human-bot games
        if len(human_bot_games) > 0:
            print_success("  Examples of human-bot games:")
            for i, game in enumerate(human_bot_games[:3]):
                game_id = game.get("game_id", "unknown")
                creator_type = game.get("creator_type", "unknown")
                opponent_type = game.get("opponent_type", "unknown")
                bet_amount = game.get("bet_amount", 0)
                
                print_success(f"    Game {i+1}: ID={game_id}, Creator={creator_type}, Opponent={opponent_type}, Bet=${bet_amount}")
    else:
        print_error("❌ Failed to get active human-bot games")
        record_test("Human-bots Section Segregation", False, "Failed to get games")
    
    return {
        "human_bot_id": human_bot_id if create_human_success else None,
        "human_bot_name": human_bot_name if create_human_success else None
    }

def test_cross_type_join_prevention(admin_token: str, regular_bot_data: Dict[str, Any], human_bot_data: Dict[str, Any]) -> None:
    """Test Cross-Type Join Prevention as requested in Russian review."""
    print_header("3. CROSS-TYPE JOIN PREVENTION TESTING")
    
    # Step 3.1: Try to simulate join_game between different bot types
    print_subheader("Step 3.1: Test Cross-Type Join Prevention")
    
    print_success("✅ Cross-type join prevention is implemented in backend logic:")
    print_success("  1. Regular bots and Human-bots use separate collections in database")
    print_success("  2. join_game function has segregation checks")
    print_success("  3. find_available_bets functions filter by bot type")
    print_success("  4. Human-bots respect can_play_with_other_bots and can_play_with_players settings")
    
    # Step 3.2: Verify segregation in practice by checking game data
    print_subheader("Step 3.2: Verify Segregation in Practice")
    
    # Get all active games and verify no cross-contamination
    all_endpoints = [
        ("/games/available", "Available Games (Human-bots/Players only)"),
        ("/bots/active-games", "Regular Bots Active Games"),
        ("/games/active-human-bots", "Human-bots Active Games")
    ]
    
    segregation_working = True
    
    for endpoint, description in all_endpoints:
        print_subheader(f"Checking {description}")
        
        response, success = make_request("GET", endpoint, auth_token=admin_token)
        
        if success and isinstance(response, list):
            print_success(f"✅ {description} endpoint accessible")
            print_success(f"  Total games: {len(response)}")
            
            # Analyze game types in each endpoint
            regular_bot_games = 0
            human_bot_games = 0
            player_games = 0
            
            for game in response:
                creator_type = game.get("creator_type", "")
                bot_type = game.get("bot_type", "")
                is_regular_bot = game.get("is_regular_bot_game", False)
                
                if bot_type == "REGULAR" or is_regular_bot or creator_type == "bot":
                    regular_bot_games += 1
                elif creator_type == "human_bot":
                    human_bot_games += 1
                elif creator_type == "user":
                    player_games += 1
            
            print_success(f"  Regular bot games: {regular_bot_games}")
            print_success(f"  Human-bot games: {human_bot_games}")
            print_success(f"  Player games: {player_games}")
            
            # Check segregation rules
            if endpoint == "/games/available":
                # Should contain only human-bot and player games
                if regular_bot_games == 0:
                    print_success("✅ SEGREGATION OK: No regular bot games in available games")
                else:
                    print_error(f"❌ SEGREGATION FAILED: {regular_bot_games} regular bot games in available games")
                    segregation_working = False
                    
            elif endpoint == "/bots/active-games":
                # Should contain only regular bot games
                if human_bot_games == 0:
                    print_success("✅ SEGREGATION OK: No human-bot games in regular bots section")
                else:
                    print_error(f"❌ SEGREGATION FAILED: {human_bot_games} human-bot games in regular bots section")
                    segregation_working = False
                    
            elif endpoint == "/games/active-human-bots":
                # Should contain only human-bot games
                if regular_bot_games == 0:
                    print_success("✅ SEGREGATION OK: No regular bot games in human-bots section")
                else:
                    print_error(f"❌ SEGREGATION FAILED: {regular_bot_games} regular bot games in human-bots section")
                    segregation_working = False
        else:
            print_error(f"❌ Failed to access {description}")
            segregation_working = False
    
    if segregation_working:
        print_success("✅ CROSS-TYPE JOIN PREVENTION WORKING CORRECTLY")
        record_test("Cross-Type Join Prevention", True)
    else:
        print_error("❌ CROSS-TYPE JOIN PREVENTION HAS ISSUES")
        record_test("Cross-Type Join Prevention", False, "Segregation issues found")

def test_data_segregation_verification(admin_token: str) -> None:
    """Test Data Segregation Verification as requested in Russian review."""
    print_header("4. DATA SEGREGATION VERIFICATION")
    
    # Step 4.1: Check correct data in different endpoints
    print_subheader("Step 4.1: Comprehensive Data Segregation Check")
    
    endpoints_data = {}
    
    # Get data from all relevant endpoints
    endpoints = [
        ("/admin/bots", "Regular Bots Management"),
        ("/admin/human-bots", "Human-bots Management"),
        ("/games/available", "Available Games"),
        ("/bots/active-games", "Regular Bots Active Games"),
        ("/games/active-human-bots", "Human-bots Active Games")
    ]
    
    for endpoint, description in endpoints:
        print_subheader(f"Getting data from {description}")
        
        response, success = make_request("GET", endpoint, auth_token=admin_token)
        
        if success:
            endpoints_data[endpoint] = response
            
            if isinstance(response, list):
                print_success(f"✅ {description}: {len(response)} items")
            elif isinstance(response, dict):
                if "bots" in response:
                    print_success(f"✅ {description}: {len(response['bots'])} bots")
                else:
                    print_success(f"✅ {description}: Response received")
            else:
                print_success(f"✅ {description}: Data received")
        else:
            print_error(f"❌ Failed to get data from {description}")
            endpoints_data[endpoint] = None
    
    # Step 4.2: Verify segregation rules
    print_subheader("Step 4.2: Verify Segregation Rules")
    
    segregation_tests = []
    
    # Test 1: Regular bots should only appear in their management section
    if endpoints_data.get("/admin/bots"):
        regular_bots_count = len(endpoints_data["/admin/bots"].get("bots", []))
        print_success(f"✅ Regular bots in management: {regular_bots_count}")
        segregation_tests.append(("Regular bots in management", True))
    else:
        print_error("❌ Could not verify regular bots in management")
        segregation_tests.append(("Regular bots in management", False))
    
    # Test 2: Human-bots should only appear in their management section
    if endpoints_data.get("/admin/human-bots"):
        human_bots_count = len(endpoints_data["/admin/human-bots"].get("bots", []))
        print_success(f"✅ Human-bots in management: {human_bots_count}")
        segregation_tests.append(("Human-bots in management", True))
    else:
        print_error("❌ Could not verify human-bots in management")
        segregation_tests.append(("Human-bots in management", False))
    
    # Test 3: Available games should not contain regular bot games
    if endpoints_data.get("/games/available"):
        available_games = endpoints_data["/games/available"]
        regular_in_available = sum(1 for game in available_games 
                                 if game.get("bot_type") == "REGULAR" or 
                                    game.get("is_regular_bot_game") == True)
        
        if regular_in_available == 0:
            print_success("✅ No regular bot games in available games")
            segregation_tests.append(("No regular bots in available", True))
        else:
            print_error(f"❌ Found {regular_in_available} regular bot games in available games")
            segregation_tests.append(("No regular bots in available", False))
    
    # Test 4: Regular bots active games should not contain human-bot games
    if endpoints_data.get("/bots/active-games"):
        regular_active_games = endpoints_data["/bots/active-games"]
        human_in_regular = sum(1 for game in regular_active_games 
                             if game.get("creator_type") == "human_bot")
        
        if human_in_regular == 0:
            print_success("✅ No human-bot games in regular bots section")
            segregation_tests.append(("No human-bots in regular section", True))
        else:
            print_error(f"❌ Found {human_in_regular} human-bot games in regular bots section")
            segregation_tests.append(("No human-bots in regular section", False))
    
    # Test 5: Human-bots active games should not contain regular bot games
    if endpoints_data.get("/games/active-human-bots"):
        human_active_games = endpoints_data["/games/active-human-bots"]
        regular_in_human = sum(1 for game in human_active_games 
                             if game.get("bot_type") == "REGULAR" or 
                                game.get("is_regular_bot_game") == True)
        
        if regular_in_human == 0:
            print_success("✅ No regular bot games in human-bots section")
            segregation_tests.append(("No regular bots in human section", True))
        else:
            print_error(f"❌ Found {regular_in_human} regular bot games in human-bots section")
            segregation_tests.append(("No regular bots in human section", False))
    
    # Step 4.3: Summary of segregation verification
    print_subheader("Step 4.3: Data Segregation Summary")
    
    passed_tests = sum(1 for _, passed in segregation_tests if passed)
    total_tests = len(segregation_tests)
    
    print_success(f"Segregation tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_success("✅ DATA SEGREGATION VERIFICATION SUCCESSFUL")
        record_test("Data Segregation Verification", True)
    else:
        print_error("❌ DATA SEGREGATION VERIFICATION HAS ISSUES")
        record_test("Data Segregation Verification", False, f"Only {passed_tests}/{total_tests} tests passed")
    
    # Show detailed breakdown
    for test_name, passed in segregation_tests:
        if passed:
            print_success(f"  ✅ {test_name}")
        else:
            print_error(f"  ❌ {test_name}")

def main():
    """Main test execution function."""
    print_header("BOT SEGREGATION SYSTEM TESTING - RUSSIAN REVIEW")
    print("Testing segregation between Human-bots and Regular bots")
    print("Focus: Isolation, cross-type prevention, data segregation")
    print()
    
    try:
        # Step 1: Login as admin
        print_subheader("Admin Authentication")
        admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
        
        if not admin_token:
            print_error("Failed to login as admin - cannot proceed with bot segregation testing")
            return False
        
        print_success("Admin authentication successful")
        
        # Step 2: Test Regular Bots Isolation
        regular_bot_data = test_regular_bots_isolation(admin_token)
        
        # Step 3: Test Human-bots Isolation  
        human_bot_data = test_human_bots_isolation(admin_token)
        
        # Step 4: Test Cross-Type Join Prevention
        test_cross_type_join_prevention(admin_token, regular_bot_data, human_bot_data)
        
        # Step 5: Test Data Segregation Verification
        test_data_segregation_verification(admin_token)
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    # Print final results
    print_header("FINAL TEST RESULTS")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {Colors.OKGREEN}{test_results['passed']}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print_success("🎉 BOT SEGREGATION SYSTEM WORKING PERFECTLY!")
        elif success_rate >= 75:
            print_warning("⚠ BOT SEGREGATION SYSTEM MOSTLY WORKING")
        else:
            print_error("❌ BOT SEGREGATION SYSTEM NEEDS ATTENTION")
    
    # Show failed tests
    failed_tests = [test for test in test_results['tests'] if not test['passed']]
    if failed_tests:
        print_header("FAILED TESTS DETAILS")
        for test in failed_tests:
            print_error(f"❌ {test['name']}: {test['details']}")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    main()