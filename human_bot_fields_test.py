#!/usr/bin/env python3
"""
Human-Bot Game Fields Database Verification Test

This test specifically addresses the review request:
"Проверить поля игр Human-ботов в базе данных"

The test will:
1. Get Human-bot IDs using GET /api/admin/human-bots
2. Find games of these bots using GET /api/admin/human-bots/{bot_id}/active-bets
3. Check specific fields in each game:
   - creator_type (should be "human_bot")
   - is_bot_game (should be true)
   - bot_type (should be "HUMAN")
   - creator_id (should match bot_id)
4. Find the reason if fields are missing/incorrect
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://b06afae6-fa27-406a-847e-fa79e0465691.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
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

def login_admin() -> Optional[str]:
    """Login as admin and return access token."""
    print_subheader("Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success(f"Admin logged in successfully")
        return response["access_token"]
    else:
        print_error("Failed to login as admin")
        return None

def test_human_bot_game_fields():
    """Main test function to check Human-bot game fields in database."""
    print_header("HUMAN-BOT GAME FIELDS DATABASE VERIFICATION")
    
    # Step 1: Login as admin
    admin_token = login_admin()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Step 2: Get Human-bot IDs
    print_subheader("Step 1: Получить Human-bot IDs")
    
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=50",
        auth_token=admin_token
    )
    
    if not human_bots_success:
        print_error("Failed to get Human-bots list")
        return
    
    human_bots = human_bots_response.get("bots", [])
    if not human_bots:
        print_error("No Human-bots found in the system")
        return
    
    print_success(f"Found {len(human_bots)} Human-bots in the system")
    
    # Record several bot IDs for testing
    test_bot_ids = []
    for i, bot in enumerate(human_bots[:5]):  # Test first 5 bots
        bot_id = bot.get("id")
        bot_name = bot.get("name", "Unknown")
        if bot_id:
            test_bot_ids.append({"id": bot_id, "name": bot_name})
            print_success(f"Bot {i+1}: {bot_name} (ID: {bot_id})")
    
    if not test_bot_ids:
        print_error("No valid bot IDs found")
        return
    
    print_success(f"Selected {len(test_bot_ids)} bots for testing")
    
    # Step 3: Find games of these bots
    print_subheader("Step 2: Найти игры этих ботов")
    
    all_bot_games = []
    
    for bot_info in test_bot_ids:
        bot_id = bot_info["id"]
        bot_name = bot_info["name"]
        
        print(f"\nChecking games for bot: {bot_name} (ID: {bot_id})")
        
        # Get active bets for this bot
        active_bets_response, active_bets_success = make_request(
            "GET", f"/admin/human-bots/{bot_id}/active-bets",
            auth_token=admin_token
        )
        
        if active_bets_success:
            bets = active_bets_response.get("bets", [])
            print_success(f"Found {len(bets)} active bets for bot {bot_name}")
            
            # Convert bets to games format and add expected bot info
            for bet in bets:
                game = {
                    "game_id": bet.get("id"),
                    "bet_amount": bet.get("bet_amount"),
                    "status": bet.get("status"),
                    "created_at": bet.get("created_at"),
                    "expected_bot_id": bot_id,
                    "expected_bot_name": bot_name
                }
                all_bot_games.append(game)
        else:
            print_warning(f"Failed to get active bets for bot {bot_name}")
    
    if not all_bot_games:
        print_error("No games found for any Human-bots")
        return
    
    print_success(f"Total games found across all bots: {len(all_bot_games)}")
    
    # Get full game data from available games endpoint
    print_subheader("Getting Full Game Data from Available Games")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if not available_games_success or not isinstance(available_games_response, list):
        print_error("Failed to get available games - cannot verify game fields")
        return
    
    print_success(f"Found {len(available_games_response)} total available games")
    
    # Match bot games with available games to get full field data
    enriched_bot_games = []
    bot_game_ids = {game["game_id"] for game in all_bot_games}
    
    for available_game in available_games_response:
        game_id = available_game.get("game_id")
        if game_id in bot_game_ids:
            # Find the corresponding bot game to get expected bot info
            for bot_game in all_bot_games:
                if bot_game["game_id"] == game_id:
                    # Merge available game data with expected bot info
                    enriched_game = {**available_game}
                    enriched_game["expected_bot_id"] = bot_game["expected_bot_id"]
                    enriched_game["expected_bot_name"] = bot_game["expected_bot_name"]
                    enriched_bot_games.append(enriched_game)
                    break
    
    print_success(f"Successfully matched {len(enriched_bot_games)} bot games with available games data")
    
    if not enriched_bot_games:
        print_error("No bot games found in available games - cannot verify fields")
        return
    
    # Update all_bot_games with enriched data
    all_bot_games = enriched_bot_games
    
    # Step 4: Check fields of each game
    print_subheader("Step 3: Проверить поля каждой игры")
    
    field_check_results = {
        "total_games": len(all_bot_games),
        "correct_creator_type": 0,
        "correct_is_bot_game": 0,
        "correct_bot_type": 0,
        "correct_creator_id": 0,
        "all_fields_correct": 0,
        "issues": []
    }
    
    for i, game in enumerate(all_bot_games):
        game_id = game.get("game_id", "unknown")
        expected_bot_id = game.get("expected_bot_id")
        expected_bot_name = game.get("expected_bot_name")
        
        print(f"\n--- Game {i+1}: {game_id} (Bot: {expected_bot_name}) ---")
        
        # Check creator_type (should be "human_bot")
        creator_type = game.get("creator_type", "missing")
        if creator_type == "human_bot":
            print_success(f"✓ creator_type: {creator_type} (CORRECT)")
            field_check_results["correct_creator_type"] += 1
        else:
            print_error(f"✗ creator_type: {creator_type} (SHOULD BE 'human_bot')")
            field_check_results["issues"].append({
                "game_id": game_id,
                "bot_name": expected_bot_name,
                "field": "creator_type",
                "expected": "human_bot",
                "actual": creator_type
            })
        
        # Check is_bot_game (should be true)
        is_bot_game = game.get("is_bot_game", "missing")
        if is_bot_game == True:
            print_success(f"✓ is_bot_game: {is_bot_game} (CORRECT)")
            field_check_results["correct_is_bot_game"] += 1
        else:
            print_error(f"✗ is_bot_game: {is_bot_game} (SHOULD BE true)")
            field_check_results["issues"].append({
                "game_id": game_id,
                "bot_name": expected_bot_name,
                "field": "is_bot_game",
                "expected": True,
                "actual": is_bot_game
            })
        
        # Check bot_type (should be "HUMAN")
        bot_type = game.get("bot_type", "missing")
        if bot_type == "HUMAN":
            print_success(f"✓ bot_type: {bot_type} (CORRECT)")
            field_check_results["correct_bot_type"] += 1
        else:
            print_error(f"✗ bot_type: {bot_type} (SHOULD BE 'HUMAN')")
            field_check_results["issues"].append({
                "game_id": game_id,
                "bot_name": expected_bot_name,
                "field": "bot_type",
                "expected": "HUMAN",
                "actual": bot_type
            })
        
        # Check creator_id (should match bot_id)
        creator_id = game.get("creator_id", "missing")
        if creator_id == expected_bot_id:
            print_success(f"✓ creator_id: {creator_id} (MATCHES bot_id)")
            field_check_results["correct_creator_id"] += 1
        else:
            print_error(f"✗ creator_id: {creator_id} (SHOULD BE {expected_bot_id})")
            field_check_results["issues"].append({
                "game_id": game_id,
                "bot_name": expected_bot_name,
                "field": "creator_id",
                "expected": expected_bot_id,
                "actual": creator_id
            })
        
        # Check if all fields are correct for this game
        game_all_correct = (
            creator_type == "human_bot" and
            is_bot_game == True and
            bot_type == "HUMAN" and
            creator_id == expected_bot_id
        )
        
        if game_all_correct:
            print_success(f"✅ ALL FIELDS CORRECT for game {game_id}")
            field_check_results["all_fields_correct"] += 1
        else:
            print_error(f"❌ SOME FIELDS INCORRECT for game {game_id}")
    
    # Step 5: Analyze results and find reasons
    print_subheader("Step 4: Найти причину")
    
    total_games = field_check_results["total_games"]
    
    print_success(f"FIELD VERIFICATION RESULTS:")
    print_success(f"  Total games checked: {total_games}")
    print_success(f"  creator_type correct: {field_check_results['correct_creator_type']}/{total_games} ({field_check_results['correct_creator_type']/total_games*100:.1f}%)")
    print_success(f"  is_bot_game correct: {field_check_results['correct_is_bot_game']}/{total_games} ({field_check_results['correct_is_bot_game']/total_games*100:.1f}%)")
    print_success(f"  bot_type correct: {field_check_results['correct_bot_type']}/{total_games} ({field_check_results['correct_bot_type']/total_games*100:.1f}%)")
    print_success(f"  creator_id correct: {field_check_results['correct_creator_id']}/{total_games} ({field_check_results['correct_creator_id']/total_games*100:.1f}%)")
    print_success(f"  All fields correct: {field_check_results['all_fields_correct']}/{total_games} ({field_check_results['all_fields_correct']/total_games*100:.1f}%)")
    
    # Analyze issues
    if field_check_results["issues"]:
        print_error(f"\nFOUND {len(field_check_results['issues'])} FIELD ISSUES:")
        
        # Group issues by field type
        issues_by_field = {}
        for issue in field_check_results["issues"]:
            field = issue["field"]
            if field not in issues_by_field:
                issues_by_field[field] = []
            issues_by_field[field].append(issue)
        
        for field, issues in issues_by_field.items():
            print_error(f"\n  {field.upper()} ISSUES ({len(issues)} games):")
            for issue in issues[:3]:  # Show first 3 examples
                print_error(f"    Game {issue['game_id']} (Bot: {issue['bot_name']}): Expected '{issue['expected']}', Got '{issue['actual']}'")
            if len(issues) > 3:
                print_error(f"    ... and {len(issues) - 3} more games")
        
        # Possible reasons analysis
        print_subheader("POSSIBLE REASONS FOR INCORRECT FIELDS:")
        
        if "creator_type" in issues_by_field:
            print_warning("creator_type issues may be caused by:")
            print_warning("  - Old games created before Human-bot system implementation")
            print_warning("  - Incorrect game creation logic in Human-bot simulation")
            print_warning("  - Database migration issues")
        
        if "is_bot_game" in issues_by_field:
            print_warning("is_bot_game issues may be caused by:")
            print_warning("  - Field not being set during Human-bot game creation")
            print_warning("  - Default value being False instead of True")
            print_warning("  - Logic error in game creation endpoint")
        
        if "bot_type" in issues_by_field:
            print_warning("bot_type issues may be caused by:")
            print_warning("  - Field not being set to 'HUMAN' for Human-bot games")
            print_warning("  - Confusion between Regular bots ('REGULAR') and Human-bots ('HUMAN')")
            print_warning("  - Missing bot_type assignment in Human-bot game creation")
        
        if "creator_id" in issues_by_field:
            print_warning("creator_id issues may be caused by:")
            print_warning("  - Database corruption or inconsistency")
            print_warning("  - Incorrect bot ID assignment during game creation")
            print_warning("  - Race conditions in concurrent game creation")
    
    else:
        print_success("🎉 NO FIELD ISSUES FOUND!")
        print_success("All Human-bot games have correct field values:")
        print_success("  ✅ creator_type = 'human_bot'")
        print_success("  ✅ is_bot_game = true")
        print_success("  ✅ bot_type = 'HUMAN'")
        print_success("  ✅ creator_id matches bot_id")
    
    # Step 6: Additional verification with available games
    print_subheader("ADDITIONAL VERIFICATION: Available Games API")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        human_bot_available_games = [
            game for game in available_games_response 
            if game.get("creator_type") == "human_bot" or game.get("is_human_bot") == True
        ]
        
        print_success(f"Found {len(human_bot_available_games)} Human-bot games in Available Games")
        
        if human_bot_available_games:
            print_success("Sample Human-bot game from Available Games:")
            sample_game = human_bot_available_games[0]
            print_success(f"  Game ID: {sample_game.get('game_id')}")
            print_success(f"  creator_type: {sample_game.get('creator_type')}")
            print_success(f"  is_bot_game: {sample_game.get('is_bot_game')}")
            print_success(f"  bot_type: {sample_game.get('bot_type')}")
            print_success(f"  is_human_bot: {sample_game.get('is_human_bot')}")
    
    # Final summary
    print_subheader("FINAL SUMMARY")
    
    if field_check_results["all_fields_correct"] == total_games:
        print_success("🎉 SUCCESS: All Human-bot game fields are correctly saved!")
        print_success("✅ creator_type, is_bot_game, bot_type fields are properly set")
        print_success("✅ No database field issues found")
        print_success("✅ Human-bot game creation logic is working correctly")
    else:
        success_rate = field_check_results["all_fields_correct"] / total_games * 100
        print_error(f"❌ ISSUES FOUND: Only {field_check_results['all_fields_correct']}/{total_games} games ({success_rate:.1f}%) have all correct fields")
        print_error("❌ Human-bot game fields need to be fixed")
        print_error("❌ Check game creation logic and database consistency")
    
    print_success(f"\nTesting completed. Checked {total_games} Human-bot games across {len(test_bot_ids)} bots.")

if __name__ == "__main__":
    test_human_bot_game_fields()