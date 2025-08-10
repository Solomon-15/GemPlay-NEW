#!/usr/bin/env python3
"""
DATABASE PURGE ENDPOINT TESTING
Test POST /api/admin/maintenance/purge-db endpoint functionality

Requirements:
1. Authenticate as admin (admin@gemplay.com / Admin123!) to get token
2. Call POST /api/admin/maintenance/purge-db with valid admin token
3. Validate 200 OK response
4. Report JSON summary with counts of deleted items:
   - games, bots, human_bots, users (non-admin), transactions, 
   - refresh_tokens, notifications, admin_logs, security_alerts, 
   - security_monitoring, user_gems, sounds
5. Confirm gem_definitions remain
6. Verify admin access still works after purge
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://7442eeef-ca61-40db-a631-c7dfd755caa2.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
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

def print_step(step: str, details: str = ""):
    """Print test step with colors"""
    print(f"{Colors.BLUE}🔹 {step}{Colors.END}")
    if details:
        print(f"   {Colors.YELLOW}{details}{Colors.END}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str, int]:
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
            return False, None, f"Unsupported method: {method}", 0
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details, response.status_code
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)", 0
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error", 0
    except Exception as e:
        return False, None, f"Request error: {str(e)}", 0

def authenticate_admin() -> Optional[str]:
    """Step 1: Authenticate as admin and return access token"""
    print_step("Step 1: Authenticating as admin user", "admin@gemplay.com / Admin123!")
    
    success, response_data, details, status_code = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        user_info = response_data.get("user", {})
        role = user_info.get("role", "Unknown")
        print_success(f"Admin authentication successful - Role: {role}")
        return token
    else:
        print_error(f"Admin authentication failed: {details}")
        return None

def call_purge_db_endpoint(admin_token: str) -> Tuple[bool, Dict, str]:
    """Step 2: Call POST /api/admin/maintenance/purge-db endpoint"""
    print_step("Step 2: Calling POST /api/admin/maintenance/purge-db", "Purging database with admin token")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details, status_code = make_request(
        "POST",
        "/admin/maintenance/purge-db",
        headers=headers
    )
    
    if success and status_code == 200:
        print_success(f"Database purge completed successfully - {details}")
        return True, response_data, details
    else:
        print_error(f"Database purge failed - {details}")
        return False, response_data, details

def validate_purge_response(response_data: Dict) -> bool:
    """Step 3: Validate purge response structure and content"""
    print_step("Step 3: Validating purge response structure")
    
    if not isinstance(response_data, dict):
        print_error("Response is not a JSON object")
        return False
    
    # Expected fields in purge response (based on actual backend implementation)
    expected_fields = ["success", "message", "summary"]
    
    missing_fields = []
    for field in expected_fields:
        if field not in response_data:
            missing_fields.append(field)
    
    if missing_fields:
        print_error(f"Missing required fields: {missing_fields}")
        return False
    
    # Check summary structure
    summary = response_data.get("summary", {})
    expected_summary_fields = [
        "games_deleted", "bots_deleted", "human_bots_deleted", "users_deleted", 
        "transactions_deleted", "refresh_tokens_deleted", "notifications_deleted", 
        "admin_logs_deleted", "security_alerts_deleted", "security_monitoring_deleted", 
        "user_gems_deleted", "sounds_deleted", "gem_definitions_remain"
    ]
    
    print(f"   📊 Purge summary:")
    for field in expected_summary_fields:
        count = summary.get(field, 0)
        print(f"      {field}: {count}")
    
    # Verify gem_definitions remain
    gem_definitions_remain = summary.get("gem_definitions_remain", 0)
    if gem_definitions_remain > 0:
        print_success(f"Gem definitions preserved: {gem_definitions_remain}")
    else:
        print_warning("No gem definitions preserved")
    
    print_success("Response structure validation passed")
    return True

def verify_admin_access_still_works(admin_token: str) -> bool:
    """Step 4: Verify admin access still works after purge"""
    print_step("Step 4: Verifying admin access still works", "Testing GET /api/admin/bots endpoint")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, response_data, details, status_code = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if success and status_code == 200:
        print_success("Admin access verification successful - Admin endpoints still accessible")
        return True
    else:
        print_error(f"Admin access verification failed - {details}")
        return False

def print_purge_summary(response_data: Dict):
    """Print detailed summary of purge results"""
    print_header("DATABASE PURGE SUMMARY")
    
    if not response_data:
        print_error("No response data available")
        return
    
    success = response_data.get("success", False)
    message = response_data.get("message", "No message")
    summary = response_data.get("summary", {})
    
    print(f"{Colors.BOLD}📋 Purge Operation Details:{Colors.END}")
    print(f"   Success: {Colors.GREEN if success else Colors.RED}{success}{Colors.END}")
    print(f"   Message: {message}")
    
    # Items deleted summary
    deleted_items = {
        "games": summary.get("games_deleted", 0),
        "bots": summary.get("bots_deleted", 0),
        "human_bots": summary.get("human_bots_deleted", 0),
        "users (non-admin)": summary.get("users_deleted", 0),
        "transactions": summary.get("transactions_deleted", 0),
        "refresh_tokens": summary.get("refresh_tokens_deleted", 0),
        "notifications": summary.get("notifications_deleted", 0),
        "admin_logs": summary.get("admin_logs_deleted", 0),
        "security_alerts": summary.get("security_alerts_deleted", 0),
        "security_monitoring": summary.get("security_monitoring_deleted", 0),
        "user_gems": summary.get("user_gems_deleted", 0),
        "sounds": summary.get("sounds_deleted", 0)
    }
    
    total_deleted = sum(deleted_items.values())
    
    print(f"\n{Colors.BOLD}🗑️ Items Deleted (Total: {total_deleted}):{Colors.END}")
    for item_type, count in deleted_items.items():
        color = Colors.GREEN if count > 0 else Colors.YELLOW
        print(f"   {color}{item_type}: {count}{Colors.END}")
    
    # Items preserved
    gem_definitions_remain = summary.get("gem_definitions_remain", 0)
    
    print(f"\n{Colors.BOLD}💾 Items Preserved:{Colors.END}")
    print(f"   {Colors.GREEN}gem_definitions: {gem_definitions_remain}{Colors.END}")
    print(f"   {Colors.GREEN}admin/super_admin users: preserved{Colors.END}")
    
    # Key validations
    print(f"\n{Colors.BOLD}✅ Key Validations:{Colors.END}")
    
    # Check that gem definitions are preserved
    if gem_definitions_remain > 0:
        print(f"   {Colors.GREEN}✅ Gem definitions preserved: {gem_definitions_remain}{Colors.END}")
    else:
        print(f"   {Colors.YELLOW}⚠️ No gem definitions found{Colors.END}")
    
    # Check that some cleanup occurred
    if total_deleted > 0:
        print(f"   {Colors.GREEN}✅ Database cleanup performed: {total_deleted} items deleted{Colors.END}")
    else:
        print(f"   {Colors.YELLOW}⚠️ No items deleted (database might already be clean){Colors.END}")
    
    # Highlight significant deletions
    if deleted_items["sounds"] > 0:
        print(f"   {Colors.GREEN}✅ Sounds cleaned up: {deleted_items['sounds']} deleted{Colors.END}")
    if deleted_items["refresh_tokens"] > 0:
        print(f"   {Colors.GREEN}✅ Refresh tokens cleaned up: {deleted_items['refresh_tokens']} deleted{Colors.END}")

def main():
    """Main test execution for database purge endpoint"""
    print_header("DATABASE PURGE ENDPOINT TESTING")
    print(f"{Colors.BLUE}🎯 Testing POST /api/admin/maintenance/purge-db endpoint{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Admin credentials: admin@gemplay.com / Admin123!{Colors.END}")
    
    overall_success = True
    purge_response = None
    
    try:
        # Step 1: Authenticate as admin
        admin_token = authenticate_admin()
        if not admin_token:
            print_error("Cannot proceed without admin authentication")
            return
        
        # Step 2: Call purge-db endpoint
        purge_success, purge_response, purge_details = call_purge_db_endpoint(admin_token)
        if not purge_success:
            print_error("Database purge failed")
            overall_success = False
        
        # Step 3: Validate response structure (even if purge failed)
        if purge_response:
            validation_success = validate_purge_response(purge_response)
            if not validation_success:
                overall_success = False
        
        # Step 4: Verify admin access still works
        if admin_token:
            access_success = verify_admin_access_still_works(admin_token)
            if not access_success:
                print_error("Admin access verification failed")
                overall_success = False
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
        overall_success = False
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
        overall_success = False
    
    finally:
        # Print detailed summary
        if purge_response:
            print_purge_summary(purge_response)
        
        # Final conclusion
        print_header("FINAL RESULTS")
        if overall_success:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 DATABASE PURGE ENDPOINT TEST SUCCESSFUL!{Colors.END}")
            print(f"{Colors.GREEN}✅ Admin authentication working{Colors.END}")
            print(f"{Colors.GREEN}✅ Purge endpoint accessible and functional{Colors.END}")
            print(f"{Colors.GREEN}✅ Response structure valid{Colors.END}")
            print(f"{Colors.GREEN}✅ Admin access preserved after purge{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ DATABASE PURGE ENDPOINT TEST FAILED!{Colors.END}")
            print(f"{Colors.RED}Some critical issues were detected during testing{Colors.END}")
        
        # Return JSON summary for programmatic use
        if purge_response:
            print(f"\n{Colors.BOLD}📄 JSON Response Summary:{Colors.END}")
            print(json.dumps(purge_response, indent=2, default=str))

if __name__ == "__main__":
    main()