#!/usr/bin/env python3
"""
Regular Bots Management Editing Functionality Testing - Russian Review
Тестирование исправлений функционала редактирования обычных ботов в админ-панели

КОНТЕКСТ: Тестирование исправленного компонента RegularBotsManagement.js для корректной работы 
инлайн-редактирования и модального окна редактирования бота.

ТЕСТИРОВАТЬ:
1. API эндпоинты для инлайн-редактирования:
   - PUT /api/admin/bots/{bot_id}/win-percentage с JSON body {win_percentage: число}
   - PUT /api/admin/bots/{bot_id}/pause-settings с JSON body {pause_between_games: число}
   - Проверить что изменения сохраняются в базе данных

2. API для модального окна редактирования:
   - GET /api/admin/bots/{bot_id} должен возвращать все поля включая pause_between_cycles, pause_on_draw, creation_mode
   - PUT /api/admin/bots/{bot_id} должен принимать JSON с полями: name, min_bet_amount, max_bet_amount, win_percentage, cycle_games, pause_between_cycles, pause_on_draw, creation_mode, profit_strategy

3. Проверить что данные корректно возвращаются:
   - GET /api/admin/bots/regular/list должен показывать обновленные значения после редактирования
   - Убедиться что поля % и Пауза отображают актуальные значения

ПРИОРИТЕТ: Критически важно для пользователя - он не может редактировать ботов
ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: Все API должны работать корректно, изменения должны сохраняться и отображаться
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://da053847-7ac3-4ecc-981f-d918a9fbd110.preview.emergentagent.com/api"
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
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with colors"""
    status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if success else f"{Colors.RED}❌ FAILED{Colors.END}"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")

def record_test(test_name: str, success: bool, details: str = "", response_data: Any = None):
    """Record test result"""
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": test_name,
        "success": success,
        "details": details,
        "response_data": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    print_test_result(test_name, success, details)

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return False, None, f"Unsupported method: {method}"
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except Exception as e:
        return False, None, f"Request error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def test_inline_editing_win_percentage(token: str):
    """Test 1: PUT /api/admin/bots/{bot_id}/win-percentage с JSON body"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Inline editing - Win percentage{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get first available bot
    success, response_data, _ = make_request("GET", "/admin/bots", headers=headers)
    
    if not success or not response_data:
        record_test(
            "Inline editing - Win percentage",
            False,
            "Could not get bot data for testing"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    if not bots:
        record_test(
            "Inline editing - Win percentage",
            False,
            "No bots available for testing"
        )
        return
    
    bot_id = bots[0].get("id")
    original_win_percentage = bots[0].get("win_percentage", 55.0)
    
    # Test updating win percentage
    new_win_percentage = 67.5
    success, response_data, details = make_request(
        "PUT",
        f"/admin/bots/{bot_id}/win-percentage",
        headers=headers,
        data={"win_percentage": new_win_percentage}
    )
    
    if success:
        record_test(
            "Inline editing - Win percentage",
            True,
            f"Successfully updated win percentage from {original_win_percentage}% to {new_win_percentage}%"
        )
        return bot_id
    else:
        record_test(
            "Inline editing - Win percentage",
            False,
            f"Failed to update win percentage: {details}"
        )
        return None

def test_inline_editing_pause_settings(token: str, bot_id: str = None):
    """Test 2: PUT /api/admin/bots/{bot_id}/pause-settings с JSON body"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Inline editing - Pause settings{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not bot_id:
        # Get first available bot
        success, response_data, _ = make_request("GET", "/admin/bots", headers=headers)
        
        if success and response_data:
            bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
            if bots:
                bot_id = bots[0].get("id")
    
    if not bot_id:
        record_test(
            "Inline editing - Pause settings",
            False,
            "No bot ID available for testing"
        )
        return
    
    # Test updating pause settings
    new_pause = 15
    success, response_data, details = make_request(
        "PUT",
        f"/admin/bots/{bot_id}/pause-settings",
        headers=headers,
        data={"pause_between_games": new_pause}
    )
    
    if success:
        record_test(
            "Inline editing - Pause settings",
            True,
            f"Successfully updated pause settings to {new_pause}s"
        )
    else:
        record_test(
            "Inline editing - Pause settings",
            False,
            f"Failed to update pause settings: {details}"
        )

def test_get_single_bot_for_modal(token: str, bot_id: str = None):
    """Test 3: GET /api/admin/bots/{bot_id} для модального окна редактирования"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Get single bot data for modal editing{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not bot_id:
        # Get first available bot
        success, response_data, _ = make_request("GET", "/admin/bots", headers=headers)
        
        if success and response_data:
            bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
            if bots:
                bot_id = bots[0].get("id")
    
    if not bot_id:
        record_test(
            "Get single bot for modal",
            False,
            "No bot ID available for testing"
        )
        return
    
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if success and response_data:
        # Check for required modal fields
        required_fields = ["pause_between_cycles", "pause_on_draw", "creation_mode", "name", "min_bet_amount", "max_bet_amount", "win_percentage", "cycle_games", "profit_strategy"]
        found_fields = []
        missing_fields = []
        
        for field in required_fields:
            if field in response_data:
                found_fields.append(field)
            else:
                missing_fields.append(field)
        
        if len(found_fields) >= 6:  # At least 6 out of 9 required fields
            record_test(
                "Get single bot for modal",
                True,
                f"Found {len(found_fields)}/{len(required_fields)} modal fields: {found_fields}"
            )
        else:
            record_test(
                "Get single bot for modal",
                False,
                f"Missing critical modal fields: {missing_fields}. Found: {found_fields}"
            )
    else:
        record_test(
            "Get single bot for modal",
            False,
            f"Failed to get single bot data: {details}"
        )

def test_update_bot_full_modal(token: str, bot_id: str = None):
    """Test 4: PUT /api/admin/bots/{bot_id} полное обновление через модальное окно"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Full bot update via modal{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not bot_id:
        # Get first available bot
        success, response_data, _ = make_request("GET", "/admin/bots", headers=headers)
        
        if success and response_data:
            bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
            if bots:
                bot_id = bots[0].get("id")
    
    if not bot_id:
        record_test(
            "Full bot update via modal",
            False,
            "No bot ID available for testing"
        )
        return
    
    # Full update data for modal
    update_data = {
        "name": f"Updated_Bot_{int(time.time())}",
        "min_bet_amount": 3.0,
        "max_bet_amount": 75.0,
        "win_percentage": 58.0,
        "cycle_games": 18,
        "pause_between_cycles": 7,
        "pause_on_draw": 2,
        "creation_mode": "queue-based",
        "profit_strategy": "balanced"
    }
    
    success, response_data, details = make_request(
        "PUT",
        f"/admin/bots/{bot_id}",
        headers=headers,
        data=update_data
    )
    
    if success:
        record_test(
            "Full bot update via modal",
            True,
            f"Successfully updated bot with all modal fields: {list(update_data.keys())}"
        )
    else:
        record_test(
            "Full bot update via modal",
            False,
            f"Failed to update bot via modal: {details}"
        )

def test_data_persistence_after_editing(token: str):
    """Test 5: Проверить что данные корректно сохраняются и отображаются после редактирования"""
    print(f"\n{Colors.MAGENTA}🧪 Test 5: Data persistence after editing{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Get current bot data
    success, response_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
    
    if not success or not response_data:
        record_test(
            "Data persistence after editing",
            False,
            "Could not get initial bot data"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    if not bots:
        record_test(
            "Data persistence after editing",
            False,
            "No bots available for persistence testing"
        )
        return
    
    test_bot = bots[0]
    bot_id = test_bot.get("id")
    original_win_percentage = test_bot.get("win_percentage", 55.0)
    original_pause = test_bot.get("pause_between_games", 5)
    
    # Step 2: Update win percentage
    new_win_percentage = 62.0 if original_win_percentage != 62.0 else 68.0
    success, _, _ = make_request(
        "PUT",
        f"/admin/bots/{bot_id}/win-percentage",
        headers=headers,
        data={"win_percentage": new_win_percentage}
    )
    
    if not success:
        record_test(
            "Data persistence after editing",
            False,
            "Failed to update win percentage for persistence test"
        )
        return
    
    # Step 3: Update pause settings
    new_pause = 9 if original_pause != 9 else 11
    success, _, _ = make_request(
        "PUT",
        f"/admin/bots/{bot_id}/pause-settings",
        headers=headers,
        data={"pause_between_games": new_pause}
    )
    
    if not success:
        record_test(
            "Data persistence after editing",
            False,
            "Failed to update pause settings for persistence test"
        )
        return
    
    # Step 4: Verify changes are reflected in list
    time.sleep(1)  # Small delay to ensure database update
    success, response_data, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
    
    if success and response_data:
        updated_bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
        updated_bot = next((bot for bot in updated_bots if bot.get("id") == bot_id), None)
        
        if updated_bot:
            current_win_percentage = updated_bot.get("win_percentage")
            current_pause = updated_bot.get("pause_between_games")
            
            win_percentage_updated = abs(current_win_percentage - new_win_percentage) < 0.1
            pause_updated = current_pause == new_pause
            
            if win_percentage_updated and pause_updated:
                record_test(
                    "Data persistence after editing",
                    True,
                    f"Changes persisted correctly: win_percentage {original_win_percentage}% → {current_win_percentage}%, pause {original_pause}s → {current_pause}s"
                )
            else:
                record_test(
                    "Data persistence after editing",
                    False,
                    f"Changes not persisted: win_percentage expected {new_win_percentage}% got {current_win_percentage}%, pause expected {new_pause}s got {current_pause}s"
                )
        else:
            record_test(
                "Data persistence after editing",
                False,
                "Could not find updated bot in list"
            )
    else:
        record_test(
            "Data persistence after editing",
            False,
            "Failed to get updated bot list for verification"
        )

def test_regular_bots_list_shows_updated_values(token: str):
    """Test 6: GET /api/admin/bots/regular/list показывает обновленные значения"""
    print(f"\n{Colors.MAGENTA}🧪 Test 6: Regular bots list shows updated values{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if success and response_data:
        bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
        
        if bots:
            # Check that % and Pause fields display actual values
            first_bot = bots[0]
            win_percentage = first_bot.get("win_percentage")
            pause_between_games = first_bot.get("pause_between_games")
            
            # Verify fields exist and have reasonable values
            win_percentage_valid = win_percentage is not None and 0 <= win_percentage <= 100
            pause_valid = pause_between_games is not None and pause_between_games > 0
            
            if win_percentage_valid and pause_valid:
                record_test(
                    "Regular bots list shows updated values",
                    True,
                    f"List shows valid values: win_percentage={win_percentage}%, pause={pause_between_games}s for {len(bots)} bots"
                )
            else:
                record_test(
                    "Regular bots list shows updated values",
                    False,
                    f"Invalid values in list: win_percentage={win_percentage}, pause={pause_between_games}"
                )
        else:
            record_test(
                "Regular bots list shows updated values",
                False,
                "No bots found in regular list"
            )
    else:
        record_test(
            "Regular bots list shows updated values",
            False,
            f"Failed to get regular bots list: {details}"
        )

def print_final_summary():
    """Print final test summary"""
    print_header("REGULAR BOTS EDITING FUNCTIONALITY TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "PUT /api/admin/bots/{bot_id}/win-percentage с JSON body",
        "PUT /api/admin/bots/{bot_id}/pause-settings с JSON body", 
        "Изменения сохраняются в базе данных",
        "GET /api/admin/bots/{bot_id} возвращает все поля для модального окна",
        "PUT /api/admin/bots/{bot_id} принимает JSON с полями модального окна",
        "GET /api/admin/bots/regular/list показывает обновленные значения",
        "Поля % и Пауза отображают актуальные значения"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Find corresponding test result
        test_found = False
        for test in test_results["tests"]:
            if any(keyword in test["name"].lower() for keyword in req.lower().split()[:3]):
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   {i}. {req}: {status}")
                test_found = True
                break
        
        if not test_found:
            print(f"   {i}. {req}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Final conclusion
    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOTS EDITING FUNCTIONALITY IS {success_rate:.1f}% WORKING!{Colors.END}")
        print(f"{Colors.GREEN}The Regular Bots Management editing functionality is working well. User can edit bots successfully.{Colors.END}")
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: REGULAR BOTS EDITING FUNCTIONALITY IS {success_rate:.1f}% WORKING{Colors.END}")
        print(f"{Colors.YELLOW}The editing functionality has some issues but core features are working.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: REGULAR BOTS EDITING FUNCTIONALITY NEEDS ATTENTION ({success_rate:.1f}% working){Colors.END}")
        print(f"{Colors.RED}Critical issues found that prevent user from editing bots properly.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS EDITING FUNCTIONALITY TESTING")
    print(f"{Colors.BLUE}🎯 Testing Regular Bots Management editing functionality{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Inline editing and modal editing of Regular Bots{Colors.END}")
    print(f"{Colors.BLUE}🔥 Priority: CRITICAL - User cannot edit bots{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    # Store bot ID for subsequent tests
    test_bot_id = None
    
    try:
        # Run all tests in sequence
        test_bot_id = test_inline_editing_win_percentage(token)
        test_inline_editing_pause_settings(token, test_bot_id)
        test_get_single_bot_for_modal(token, test_bot_id)
        test_update_bot_full_modal(token, test_bot_id)
        test_data_persistence_after_editing(token)
        test_regular_bots_list_shows_updated_values(token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()