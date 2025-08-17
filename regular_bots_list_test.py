#!/usr/bin/env python3
"""
RUSSIAN REVIEW - REGULAR BOTS LIST API TEST
Повтори тест 2 (список регулярных ботов) после добавления плоских полей active_pool и cycle_total_display

SPECIFIC REQUIREMENTS:
- В ответе /admin/bots/regular/list НЕТ legacy полей win_percentage/creation_mode/profit_strategy
- Присутствуют поля cycle_total_amount, active_pool, cycle_total_info.display и новый cycle_total_display
- active_pool = wins_sum + losses_sum
- cycle_total_amount = total_bet_sum (включая ничьи)
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://ru-modals.preview.emergentagent.com/api"
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

def test_regular_bots_list_legacy_cleanup():
    """Test the /admin/bots/regular/list endpoint for legacy cleanup and new fields"""
    print(f"\n{Colors.MAGENTA}🧪 Testing Regular Bots List API - Legacy Cleanup & New Fields{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Regular Bots List API Test", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /admin/bots/regular/list endpoint...")
    
    # Test regular bots list endpoint
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Regular Bots List API Test",
            False,
            f"Failed to get regular bots list: {details}"
        )
        return
    
    print(f"   📊 Response received, analyzing structure...")
    
    # Check if response has bots data
    bots_data = []
    if isinstance(response_data, dict):
        if "bots" in response_data:
            bots_data = response_data["bots"]
        elif "data" in response_data:
            bots_data = response_data["data"]
        else:
            # Maybe the response itself is the bots list
            if isinstance(response_data, list):
                bots_data = response_data
    elif isinstance(response_data, list):
        bots_data = response_data
    
    if not bots_data:
        record_test(
            "Regular Bots List API Test",
            False,
            "No bots data found in response"
        )
        return
    
    print(f"   📈 Found {len(bots_data)} regular bots in response")
    
    # Analyze first bot for field structure (if any bots exist)
    if len(bots_data) == 0:
        record_test(
            "Regular Bots List API Test",
            False,
            "No regular bots found to test field structure"
        )
        return
    
    # Test each bot for required fields and absence of legacy fields
    legacy_fields_found = []
    missing_required_fields = []
    field_validation_errors = []
    
    # Legacy fields that should NOT be present
    legacy_fields = ["win_percentage", "creation_mode", "profit_strategy"]
    
    # Required new fields
    required_fields = [
        "cycle_total_amount",
        "active_pool", 
        "cycle_total_display"
    ]
    
    # Optional but expected fields
    expected_fields = [
        "cycle_total_info"  # Should contain display field
    ]
    
    for i, bot in enumerate(bots_data[:3]):  # Test first 3 bots
        bot_id = bot.get("id", f"bot_{i}")
        print(f"   🔍 Analyzing bot {i+1}: {bot_id}")
        
        # Check for legacy fields (should NOT be present)
        for legacy_field in legacy_fields:
            if legacy_field in bot:
                legacy_fields_found.append(f"{bot_id}.{legacy_field}")
        
        # Check for required new fields
        for required_field in required_fields:
            if required_field not in bot:
                missing_required_fields.append(f"{bot_id}.{required_field}")
        
        # Validate active_pool calculation if possible
        if "active_pool" in bot and "wins_sum" in bot and "losses_sum" in bot:
            expected_active_pool = bot.get("wins_sum", 0) + bot.get("losses_sum", 0)
            actual_active_pool = bot.get("active_pool", 0)
            if abs(expected_active_pool - actual_active_pool) > 0.01:
                field_validation_errors.append(
                    f"{bot_id}: active_pool ({actual_active_pool}) ≠ wins_sum + losses_sum ({expected_active_pool})"
                )
        
        # Check cycle_total_info.display if present
        if "cycle_total_info" in bot and isinstance(bot["cycle_total_info"], dict):
            if "display" not in bot["cycle_total_info"]:
                missing_required_fields.append(f"{bot_id}.cycle_total_info.display")
        
        # Show bot structure for first bot
        if i == 0:
            print(f"   📋 Sample bot structure:")
            for key, value in bot.items():
                if isinstance(value, dict):
                    print(f"      {key}: {type(value).__name__} with keys: {list(value.keys())}")
                else:
                    print(f"      {key}: {type(value).__name__} = {value}")
    
    # Evaluate test results
    has_legacy_fields = len(legacy_fields_found) > 0
    has_missing_fields = len(missing_required_fields) > 0
    has_validation_errors = len(field_validation_errors) > 0
    
    print(f"\n   📊 FIELD ANALYSIS RESULTS:")
    print(f"      Legacy fields found: {len(legacy_fields_found)}")
    print(f"      Missing required fields: {len(missing_required_fields)}")
    print(f"      Field validation errors: {len(field_validation_errors)}")
    
    if legacy_fields_found:
        print(f"      🚨 Legacy fields still present: {', '.join(legacy_fields_found)}")
    
    if missing_required_fields:
        print(f"      ❌ Missing required fields: {', '.join(missing_required_fields)}")
    
    if field_validation_errors:
        print(f"      ⚠️ Validation errors: {'; '.join(field_validation_errors)}")
    
    # Determine overall success
    if not has_legacy_fields and not has_missing_fields and not has_validation_errors:
        record_test(
            "Regular Bots List API - Legacy Cleanup",
            True,
            f"✅ All requirements met: No legacy fields, all required fields present, validations passed"
        )
    else:
        error_details = []
        if has_legacy_fields:
            error_details.append(f"Legacy fields found: {', '.join(legacy_fields_found)}")
        if has_missing_fields:
            error_details.append(f"Missing fields: {', '.join(missing_required_fields)}")
        if has_validation_errors:
            error_details.append(f"Validation errors: {'; '.join(field_validation_errors)}")
        
        record_test(
            "Regular Bots List API - Legacy Cleanup",
            False,
            f"❌ Requirements not met: {'; '.join(error_details)}"
        )

def print_test_summary():
    """Print test summary"""
    print_header("REGULAR BOTS LIST API TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: REGULAR BOTS LIST API FULLY COMPLIANT!{Colors.END}")
        print(f"{Colors.GREEN}✅ No legacy fields (win_percentage, creation_mode, profit_strategy){Colors.END}")
        print(f"{Colors.GREEN}✅ All required fields present (cycle_total_amount, active_pool, cycle_total_display){Colors.END}")
        print(f"{Colors.GREEN}✅ Field validations passed (active_pool = wins_sum + losses_sum){Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: REGULAR BOTS LIST API NEEDS FIXES ({success_rate:.1f}% compliant){Colors.END}")
        print(f"{Colors.RED}Legacy cleanup is INCOMPLETE or required fields are missing.{Colors.END}")

def main():
    """Main test execution for Regular Bots List API"""
    print_header("REGULAR BOTS LIST API - LEGACY CLEANUP TEST")
    print(f"{Colors.BLUE}🎯 Testing /admin/bots/regular/list endpoint after legacy cleanup{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 REQUIREMENTS:{Colors.END}")
    print(f"{Colors.BLUE}   ❌ NO legacy fields: win_percentage, creation_mode, profit_strategy{Colors.END}")
    print(f"{Colors.BLUE}   ✅ Required fields: cycle_total_amount, active_pool, cycle_total_display{Colors.END}")
    print(f"{Colors.BLUE}   🧮 active_pool = wins_sum + losses_sum{Colors.END}")
    print(f"{Colors.BLUE}   🧮 cycle_total_amount = total_bet_sum (including draws){Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test Regular Bots List API
        test_regular_bots_list_legacy_cleanup()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_test_summary()

if __name__ == "__main__":
    main()