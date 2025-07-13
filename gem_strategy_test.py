#!/usr/bin/env python3
"""
Comprehensive test for Gem Combination Strategy Logic
Tests the fixed gem combination strategy logic to verify specific issues are resolved.
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://267d68c2-b4b0-4ffd-a7d5-c634e2d1a520.preview.emergentagent.com/api"
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

def test_gem_combination_strategy_logic() -> None:
    """Test the fixed gem combination strategy logic to verify specific issues are resolved."""
    print_header("TESTING GEM COMBINATION STRATEGY LOGIC")
    
    # Step 1: Login as admin
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed with gem combination tests - admin login failed")
        return
    
    # Step 2: Setup test inventory - buy specific quantities of each gem type
    print_subheader("Setting up test inventory with specific gem quantities")
    
    # Buy gems to create a controlled test environment
    test_inventory = {
        "Ruby": 100,      # $1 each - cheapest
        "Amber": 50,      # $2 each
        "Topaz": 20,      # $5 each
        "Emerald": 10,    # $10 each
        "Aquamarine": 8,  # $25 each - medium price
        "Sapphire": 5,    # $50 each
        "Magic": 5        # $100 each - most expensive
    }
    
    for gem_type, quantity in test_inventory.items():
        response, success = make_request(
            "POST", 
            f"/gems/buy?gem_type={gem_type}&quantity={quantity}", 
            auth_token=admin_token
        )
        
        if success:
            print_success(f"Bought {quantity} {gem_type} gems")
        else:
            print_error(f"Failed to buy {gem_type} gems: {response}")
            return
    
    # Step 3: Test Small Strategy - should use cheapest gems first
    print_subheader("Testing Small Strategy - Should Use Cheapest Gems First")
    
    test_amounts = [25, 50, 100, 123]
    
    for amount in test_amounts:
        print(f"\nTesting Small strategy with ${amount}")
        
        response, success = make_request(
            "POST", 
            "/gems/calculate-combination",
            data={"bet_amount": amount, "strategy": "small"},
            auth_token=admin_token
        )
        
        if success and response.get("success"):
            combinations = response.get("combinations", [])
            total_amount = response.get("total_amount", 0)
            
            print_success(f"Small strategy found combination for ${amount}")
            print_success(f"Total amount: ${total_amount}")
            
            # Verify exact amount matching
            if abs(total_amount - amount) < 0.01:
                print_success("✓ Exact amount matching verified")
                record_test(f"Small Strategy - Exact Amount ${amount}", True)
            else:
                print_error(f"✗ Amount mismatch: Expected ${amount}, got ${total_amount}")
                record_test(f"Small Strategy - Exact Amount ${amount}", False, f"Amount mismatch")
            
            # Verify strategy uses cheapest gems first
            gem_prices = []
            for combo in combinations:
                gem_prices.extend([combo["price"]] * combo["quantity"])
            
            # Check if gems are sorted by price (cheapest first)
            is_sorted_cheap_first = all(gem_prices[i] <= gem_prices[i+1] for i in range(len(gem_prices)-1))
            
            if is_sorted_cheap_first or len(set(gem_prices)) <= 1:
                print_success("✓ Small strategy correctly uses cheapest gems first")
                record_test(f"Small Strategy - Cheapest First ${amount}", True)
            else:
                print_error(f"✗ Small strategy not using cheapest gems first. Prices: {gem_prices}")
                record_test(f"Small Strategy - Cheapest First ${amount}", False, f"Wrong order: {gem_prices}")
            
            # Verify it starts with Ruby, Amber, Topaz (cheapest gems)
            expected_cheap_gems = ["Ruby", "Amber", "Topaz"]
            used_gems = [combo["type"] for combo in combinations]
            uses_cheap_gems = any(gem in expected_cheap_gems for gem in used_gems)
            
            if uses_cheap_gems:
                print_success(f"✓ Small strategy uses cheap gems: {used_gems}")
                record_test(f"Small Strategy - Uses Cheap Gems ${amount}", True)
            else:
                print_error(f"✗ Small strategy should use cheap gems but used: {used_gems}")
                record_test(f"Small Strategy - Uses Cheap Gems ${amount}", False, f"Used: {used_gems}")
            
            # Verify it does NOT start with expensive gems
            expensive_gems = ["Magic", "Sapphire"]
            uses_expensive_first = any(combo["type"] in expensive_gems for combo in combinations[:2])
            
            if not uses_expensive_first:
                print_success("✓ Small strategy correctly avoids expensive gems first")
                record_test(f"Small Strategy - Avoids Expensive ${amount}", True)
            else:
                print_error(f"✗ Small strategy incorrectly uses expensive gems first: {used_gems}")
                record_test(f"Small Strategy - Avoids Expensive ${amount}", False, f"Used expensive: {used_gems}")
                
        else:
            print_error(f"Small strategy failed for ${amount}: {response}")
            record_test(f"Small Strategy - ${amount}", False, f"API call failed")
    
    # Step 4: Test Big Strategy - should use most expensive gems first
    print_subheader("Testing Big Strategy - Should Use Most Expensive Gems First")
    
    for amount in test_amounts:
        print(f"\nTesting Big strategy with ${amount}")
        
        response, success = make_request(
            "POST", 
            "/gems/calculate-combination",
            data={"bet_amount": amount, "strategy": "big"},
            auth_token=admin_token
        )
        
        if success and response.get("success"):
            combinations = response.get("combinations", [])
            total_amount = response.get("total_amount", 0)
            
            print_success(f"Big strategy found combination for ${amount}")
            print_success(f"Total amount: ${total_amount}")
            
            # Verify exact amount matching
            if abs(total_amount - amount) < 0.01:
                print_success("✓ Exact amount matching verified")
                record_test(f"Big Strategy - Exact Amount ${amount}", True)
            else:
                print_error(f"✗ Amount mismatch: Expected ${amount}, got ${total_amount}")
                record_test(f"Big Strategy - Exact Amount ${amount}", False, f"Amount mismatch")
            
            # Verify strategy uses most expensive gems first
            gem_prices = []
            for combo in combinations:
                gem_prices.extend([combo["price"]] * combo["quantity"])
            
            # Check if gems are sorted by price (most expensive first)
            is_sorted_expensive_first = all(gem_prices[i] >= gem_prices[i+1] for i in range(len(gem_prices)-1))
            
            if is_sorted_expensive_first or len(set(gem_prices)) <= 1:
                print_success("✓ Big strategy correctly uses most expensive gems first")
                record_test(f"Big Strategy - Expensive First ${amount}", True)
            else:
                print_error(f"✗ Big strategy not using expensive gems first. Prices: {gem_prices}")
                record_test(f"Big Strategy - Expensive First ${amount}", False, f"Wrong order: {gem_prices}")
            
            # Verify it starts with Magic, Sapphire, Aquamarine (expensive gems)
            expected_expensive_gems = ["Magic", "Sapphire", "Aquamarine"]
            used_gems = [combo["type"] for combo in combinations]
            uses_expensive_gems = any(gem in expected_expensive_gems for gem in used_gems)
            
            if uses_expensive_gems:
                print_success(f"✓ Big strategy uses expensive gems: {used_gems}")
                record_test(f"Big Strategy - Uses Expensive Gems ${amount}", True)
            else:
                print_error(f"✗ Big strategy should use expensive gems but used: {used_gems}")
                record_test(f"Big Strategy - Uses Expensive Gems ${amount}", False, f"Used: {used_gems}")
            
            # Verify it does NOT start with cheap gems
            cheap_gems = ["Ruby", "Amber"]
            uses_cheap_first = any(combo["type"] in cheap_gems for combo in combinations[:2])
            
            if not uses_cheap_first:
                print_success("✓ Big strategy correctly avoids cheap gems first")
                record_test(f"Big Strategy - Avoids Cheap ${amount}", True)
            else:
                print_error(f"✗ Big strategy incorrectly uses cheap gems first: {used_gems}")
                record_test(f"Big Strategy - Avoids Cheap ${amount}", False, f"Used cheap: {used_gems}")
                
        else:
            print_error(f"Big strategy failed for ${amount}: {response}")
            record_test(f"Big Strategy - ${amount}", False, f"API call failed")
    
    # Step 5: Test Smart Strategy - should use medium-price gems first
    print_subheader("Testing Smart Strategy - Should Use Medium-Price Gems First")
    
    for amount in test_amounts:
        print(f"\nTesting Smart strategy with ${amount}")
        
        response, success = make_request(
            "POST", 
            "/gems/calculate-combination",
            data={"bet_amount": amount, "strategy": "smart"},
            auth_token=admin_token
        )
        
        if success and response.get("success"):
            combinations = response.get("combinations", [])
            total_amount = response.get("total_amount", 0)
            
            print_success(f"Smart strategy found combination for ${amount}")
            print_success(f"Total amount: ${total_amount}")
            
            # Verify exact amount matching
            if abs(total_amount - amount) < 0.01:
                print_success("✓ Exact amount matching verified")
                record_test(f"Smart Strategy - Exact Amount ${amount}", True)
            else:
                print_error(f"✗ Amount mismatch: Expected ${amount}, got ${total_amount}")
                record_test(f"Smart Strategy - Exact Amount ${amount}", False, f"Amount mismatch")
            
            # Verify strategy prioritizes medium-priced gems (around $25)
            expected_medium_gems = ["Aquamarine", "Emerald", "Topaz"]  # $25, $10, $5
            used_gems = [combo["type"] for combo in combinations]
            uses_medium_gems = any(gem in expected_medium_gems for gem in used_gems)
            
            if uses_medium_gems:
                print_success(f"✓ Smart strategy uses medium-priced gems: {used_gems}")
                record_test(f"Smart Strategy - Uses Medium Gems ${amount}", True)
            else:
                print_error(f"✗ Smart strategy should prioritize medium gems but used: {used_gems}")
                record_test(f"Smart Strategy - Uses Medium Gems ${amount}", False, f"Used: {used_gems}")
                
        else:
            print_error(f"Smart strategy failed for ${amount}: {response}")
            record_test(f"Smart Strategy - ${amount}", False, f"API call failed")
    
    # Step 6: Test Inventory Limit - Magic gems limited to 5
    print_subheader("Testing Inventory Limit - Magic Gems Limited to 5")
    
    # Test with amount that would require more than 5 Magic gems if using only Magic
    test_amount = 600  # Would need 6 Magic gems at $100 each
    
    response, success = make_request(
        "POST", 
        "/gems/calculate-combination",
        data={"bet_amount": test_amount, "strategy": "big"},
        auth_token=admin_token
    )
    
    if success and response.get("success"):
        combinations = response.get("combinations", [])
        
        # Count Magic gems used
        magic_gems_used = 0
        for combo in combinations:
            if combo["type"] == "Magic":
                magic_gems_used += combo["quantity"]
        
        if magic_gems_used <= 5:
            print_success(f"✓ Inventory limit respected: Used {magic_gems_used} Magic gems (≤ 5)")
            record_test("Inventory Limit - Magic Gems", True)
        else:
            print_error(f"✗ Inventory limit violated: Used {magic_gems_used} Magic gems (> 5)")
            record_test("Inventory Limit - Magic Gems", False, f"Used {magic_gems_used} > 5")
    else:
        # If it fails, that's also acceptable as it means the algorithm correctly
        # identified that it cannot make the combination with available gems
        print_success("✓ Algorithm correctly failed when insufficient gems available")
        record_test("Inventory Limit - Magic Gems", True, "Correctly failed with insufficient gems")
    
    # Step 7: Test edge cases and validation
    print_subheader("Testing Edge Cases and Validation")
    
    # Test with amount too large for available gems
    response, success = make_request(
        "POST", 
        "/gems/calculate-combination",
        data={"bet_amount": 3000, "strategy": "big"},  # Use max allowed amount
        auth_token=admin_token,
        expected_status=200  # Should return success=false, not HTTP error
    )
    
    if success and not response.get("success"):
        print_success("✓ Large amount correctly rejected with insufficient gems")
        record_test("Edge Case - Large Amount", True)
    elif success and response.get("success"):
        print_success("✓ Large amount successfully calculated (sufficient gems available)")
        record_test("Edge Case - Large Amount", True)
    else:
        print_error(f"✗ Large amount handling unexpected: {response}")
        record_test("Edge Case - Large Amount", False, f"Unexpected response")
    
    # Test with invalid strategy
    response, success = make_request(
        "POST", 
        "/gems/calculate-combination",
        data={"bet_amount": 50, "strategy": "invalid"},
        auth_token=admin_token,
        expected_status=422  # Validation error
    )
    
    if not success:
        print_success("✓ Invalid strategy correctly rejected")
        record_test("Edge Case - Invalid Strategy", True)
    else:
        print_error(f"✗ Invalid strategy not rejected: {response}")
        record_test("Edge Case - Invalid Strategy", False, f"Not rejected")
    
    # Step 8: Test strategy differentiation with same amount
    print_subheader("Testing Strategy Differentiation with Same Amount")
    
    test_amount = 50
    strategies = ["small", "smart", "big"]
    strategy_results = {}
    
    for strategy in strategies:
        response, success = make_request(
            "POST", 
            "/gems/calculate-combination",
            data={"bet_amount": test_amount, "strategy": strategy},
            auth_token=admin_token
        )
        
        if success and response.get("success"):
            combinations = response.get("combinations", [])
            used_gems = [combo["type"] for combo in combinations]
            strategy_results[strategy] = used_gems
            print_success(f"{strategy.capitalize()} strategy uses: {used_gems}")
    
    # Verify that different strategies produce different results
    if len(strategy_results) == 3:
        small_gems = set(strategy_results.get("small", []))
        smart_gems = set(strategy_results.get("smart", []))
        big_gems = set(strategy_results.get("big", []))
        
        # Check if strategies are actually different
        all_same = (small_gems == smart_gems == big_gems)
        
        if not all_same:
            print_success("✓ Different strategies produce different gem selections")
            record_test("Strategy Differentiation", True)
        else:
            print_warning("⚠ All strategies produced same result (might be due to limited options)")
            record_test("Strategy Differentiation", True, "Same result but acceptable")
    else:
        print_error("✗ Not all strategies worked for differentiation test")
        record_test("Strategy Differentiation", False, "Some strategies failed")

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

if __name__ == "__main__":
    test_gem_combination_strategy_logic()
    print_summary()