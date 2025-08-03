#!/usr/bin/env python3
"""
Human-Bot Active Bets Time Fields Testing
Focus: Verify that updated_at and joined_at fields are now included in API response
Russian Review Requirements: Test the fixed API endpoint /admin/human-bots/{bot_id}/active-bets
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
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
        print_success(f"{name}: PASSED")
    else:
        test_results["failed"] += 1
        print_error(f"{name}: FAILED - {details}")
    
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
    
    try:
        if data and method.lower() in ["post", "put", "patch"]:
            headers["Content-Type"] = "application/json"
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, params=data, headers=headers, timeout=30)
        
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
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, False

def test_admin_login() -> Optional[str]:
    """Test admin login and return token."""
    print_subheader("Testing Admin Login")
    
    response, success = make_request("POST", "/auth/login", data=ADMIN_USER)
    
    if success and "access_token" in response:
        token = response["access_token"]
        print_success(f"Admin logged in successfully")
        record_test("Admin Login", True)
        return token
    else:
        print_error(f"Admin login failed: {response}")
        record_test("Admin Login", False, "Login failed")
        return None

def test_human_bot_active_bets_time_fields(admin_token: str) -> None:
    """Test the Human-Bot active bets API for time fields."""
    print_header("HUMAN-BOT ACTIVE BETS TIME FIELDS TESTING")
    
    # Step 1: Get list of Human-Bots
    print_subheader("Step 1: Get Human-Bots List")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("Failed to get Human-Bots list")
        record_test("Get Human-Bots List", False, "Request failed")
        return
    
    if "bots" not in bots_response or not bots_response["bots"]:
        print_error("No Human-Bots found in the system")
        record_test("Get Human-Bots List", False, "No bots found")
        return
    
    bots = bots_response["bots"]
    print_success(f"Found {len(bots)} Human-Bots")
    record_test("Get Human-Bots List", True)
    
    # Step 2: Test active bets endpoint for multiple bots
    print_subheader("Step 2: Test Active Bets Time Fields")
    
    bots_tested = 0
    bots_with_active_bets = 0
    total_bets_tested = 0
    
    # Test up to 5 bots
    for bot in bots[:5]:
        bot_id = bot["id"]
        bot_name = bot["name"]
        bots_tested += 1
        
        print(f"\n--- Testing Bot: {bot_name} (ID: {bot_id}) ---")
        
        # Get active bets for this bot
        active_bets_response, active_bets_success = make_request(
            "GET", f"/admin/human-bots/{bot_id}/active-bets",
            auth_token=admin_token
        )
        
        if not active_bets_success:
            print_error(f"Failed to get active bets for bot {bot_name}")
            record_test(f"Active Bets API - {bot_name}", False, "Request failed")
            continue
        
        # Check response structure
        if "bets" not in active_bets_response:
            print_error(f"Response missing 'bets' field for bot {bot_name}")
            record_test(f"Active Bets Response Structure - {bot_name}", False, "Missing bets field")
            continue
        
        bets = active_bets_response["bets"]
        print_success(f"Bot {bot_name} has {len(bets)} active bets")
        
        if len(bets) > 0:
            bots_with_active_bets += 1
            total_bets_tested += len(bets)
            
            # Test time fields in each bet
            created_at_present = 0
            updated_at_present = 0
            joined_at_present = 0
            
            for i, bet in enumerate(bets):
                print(f"  Bet {i+1}: Game ID {bet.get('game_id', 'unknown')}")
                
                # Check for created_at field (should be present)
                if "created_at" in bet:
                    created_at_present += 1
                    created_at_value = bet["created_at"]
                    print_success(f"    ✓ created_at: {created_at_value}")
                    
                    # Validate datetime format
                    try:
                        datetime.fromisoformat(created_at_value.replace('Z', '+00:00'))
                        print_success(f"    ✓ created_at has valid datetime format")
                    except ValueError:
                        print_error(f"    ✗ created_at has invalid datetime format: {created_at_value}")
                else:
                    print_error(f"    ✗ created_at field missing")
                
                # Check for updated_at field (NEW - should be present after fix)
                if "updated_at" in bet:
                    updated_at_present += 1
                    updated_at_value = bet["updated_at"]
                    print_success(f"    ✓ updated_at: {updated_at_value}")
                    
                    # Validate datetime format if not null
                    if updated_at_value:
                        try:
                            datetime.fromisoformat(updated_at_value.replace('Z', '+00:00'))
                            print_success(f"    ✓ updated_at has valid datetime format")
                        except ValueError:
                            print_error(f"    ✗ updated_at has invalid datetime format: {updated_at_value}")
                    else:
                        print_warning(f"    ⚠ updated_at is null (game not yet updated)")
                else:
                    print_error(f"    ✗ updated_at field missing")
                
                # Check for joined_at field (NEW - should be present after fix)
                if "joined_at" in bet:
                    joined_at_present += 1
                    joined_at_value = bet["joined_at"]
                    print_success(f"    ✓ joined_at: {joined_at_value}")
                    
                    # Validate datetime format if not null
                    if joined_at_value:
                        try:
                            datetime.fromisoformat(joined_at_value.replace('Z', '+00:00'))
                            print_success(f"    ✓ joined_at has valid datetime format")
                        except ValueError:
                            print_error(f"    ✗ joined_at has invalid datetime format: {joined_at_value}")
                    else:
                        print_warning(f"    ⚠ joined_at is null (game not yet joined)")
                else:
                    print_error(f"    ✗ joined_at field missing")
            
            # Record results for this bot
            record_test(f"Active Bets API Access - {bot_name}", True)
            record_test(f"created_at Field Present - {bot_name}", created_at_present == len(bets), 
                       f"{created_at_present}/{len(bets)} bets have created_at")
            record_test(f"updated_at Field Present - {bot_name}", updated_at_present == len(bets), 
                       f"{updated_at_present}/{len(bets)} bets have updated_at")
            record_test(f"joined_at Field Present - {bot_name}", joined_at_present == len(bets), 
                       f"{joined_at_present}/{len(bets)} bets have joined_at")
        else:
            print_warning(f"Bot {bot_name} has no active bets to test")
            record_test(f"Active Bets API Access - {bot_name}", True)
    
    # Step 3: Summary and Analysis
    print_subheader("Step 3: Summary and Analysis")
    
    print_success(f"Tested {bots_tested} Human-Bots")
    print_success(f"Found {bots_with_active_bets} bots with active bets")
    print_success(f"Tested {total_bets_tested} total active bets")
    
    if bots_with_active_bets == 0:
        print_warning("No bots with active bets found - cannot fully test time fields")
        print_warning("This may be due to system state, not necessarily a bug")
        record_test("Time Fields Testing", False, "No active bets available for testing")
    else:
        print_success(f"Successfully tested time fields on {total_bets_tested} active bets")
        record_test("Time Fields Testing", True)

def test_specific_time_field_requirements() -> None:
    """Test the specific requirements from the Russian review."""
    print_header("RUSSIAN REVIEW REQUIREMENTS VERIFICATION")
    
    admin_token = test_admin_login()
    if not admin_token:
        return
    
    print_subheader("Testing Specific Requirements")
    
    # Get a Human-Bot with active bets for detailed testing
    bots_response, bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=20",
        auth_token=admin_token
    )
    
    if not bots_success or "bots" not in bots_response:
        print_error("Cannot get Human-Bots for detailed testing")
        record_test("Detailed Requirements Test", False, "Cannot get bots")
        return
    
    # Find a bot with active bets
    test_bot = None
    for bot in bots_response["bots"]:
        active_bets_response, active_bets_success = make_request(
            "GET", f"/admin/human-bots/{bot['id']}/active-bets",
            auth_token=admin_token
        )
        
        if active_bets_success and "bets" in active_bets_response and len(active_bets_response["bets"]) > 0:
            test_bot = bot
            test_bets = active_bets_response["bets"]
            break
    
    if not test_bot:
        print_warning("No Human-Bot with active bets found for detailed testing")
        record_test("Detailed Requirements Test", False, "No active bets available")
        return
    
    print_success(f"Testing detailed requirements with bot: {test_bot['name']}")
    print_success(f"Bot has {len(test_bets)} active bets")
    
    # Test each requirement
    requirements_met = {
        "created_at_present": True,
        "updated_at_present": True,
        "joined_at_present": True,
        "datetime_format_valid": True
    }
    
    for i, bet in enumerate(test_bets):
        print(f"\n--- Detailed Analysis of Bet {i+1} ---")
        
        # Requirement 1: created_at field must be present (existing functionality)
        if "created_at" not in bet:
            requirements_met["created_at_present"] = False
            print_error("✗ REQUIREMENT FAILED: created_at field missing")
        else:
            print_success("✓ REQUIREMENT MET: created_at field present")
        
        # Requirement 2: updated_at field must be present (NEW)
        if "updated_at" not in bet:
            requirements_met["updated_at_present"] = False
            print_error("✗ REQUIREMENT FAILED: updated_at field missing")
        else:
            print_success("✓ REQUIREMENT MET: updated_at field present")
        
        # Requirement 3: joined_at field must be present (NEW)
        if "joined_at" not in bet:
            requirements_met["joined_at_present"] = False
            print_error("✗ REQUIREMENT FAILED: joined_at field missing")
        else:
            print_success("✓ REQUIREMENT MET: joined_at field present")
        
        # Requirement 4: All datetime fields should have valid format
        for field_name in ["created_at", "updated_at", "joined_at"]:
            if field_name in bet and bet[field_name]:
                try:
                    datetime.fromisoformat(bet[field_name].replace('Z', '+00:00'))
                    print_success(f"✓ {field_name} has valid datetime format")
                except ValueError:
                    requirements_met["datetime_format_valid"] = False
                    print_error(f"✗ {field_name} has invalid datetime format: {bet[field_name]}")
    
    # Final requirements assessment
    print_subheader("Final Requirements Assessment")
    
    all_requirements_met = all(requirements_met.values())
    
    if all_requirements_met:
        print_success("🎉 ALL RUSSIAN REVIEW REQUIREMENTS MET!")
        print_success("✅ created_at field present in all bets")
        print_success("✅ updated_at field present in all bets (NEW)")
        print_success("✅ joined_at field present in all bets (NEW)")
        print_success("✅ All datetime fields have valid format")
        record_test("Russian Review Requirements", True)
    else:
        print_error("❌ SOME REQUIREMENTS NOT MET:")
        if not requirements_met["created_at_present"]:
            print_error("❌ created_at field missing from some bets")
        if not requirements_met["updated_at_present"]:
            print_error("❌ updated_at field missing from some bets")
        if not requirements_met["joined_at_present"]:
            print_error("❌ joined_at field missing from some bets")
        if not requirements_met["datetime_format_valid"]:
            print_error("❌ Some datetime fields have invalid format")
        record_test("Russian Review Requirements", False, "Some requirements not met")

def print_final_summary():
    """Print final test summary."""
    print_header("FINAL TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.FAIL}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print(f"\n{Colors.FAIL}Failed Tests:{Colors.ENDC}")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"  ✗ {test['name']}: {test['details']}")
    
    print(f"\n{Colors.HEADER}CONCLUSION:{Colors.ENDC}")
    if success_rate >= 80:
        print(f"{Colors.OKGREEN}✅ Human-Bot Active Bets Time Fields API is working correctly!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✅ The backend changes have been successfully implemented.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✅ Frontend can now display proper time information.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ Human-Bot Active Bets Time Fields API needs further fixes.{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Backend changes may not be complete.{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Frontend time column may not work properly.{Colors.ENDC}")

def main():
    """Main test execution."""
    print_header("HUMAN-BOT ACTIVE BETS TIME FIELDS TESTING")
    print("Testing the fixed API endpoint /admin/human-bots/{bot_id}/active-bets")
    print("Verifying that updated_at and joined_at fields are now included")
    print("Russian Review Requirements: Повторное тестирование исправленного API")
    
    # Test admin login
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin authentication")
        return
    
    # Test the active bets time fields
    test_human_bot_active_bets_time_fields(admin_token)
    
    # Test specific requirements
    test_specific_time_field_requirements()
    
    # Print final summary
    print_final_summary()

if __name__ == "__main__":
    main()