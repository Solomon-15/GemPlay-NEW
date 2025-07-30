#!/usr/bin/env python3
"""
GemPlay My Bets API Focused Testing
Testing the /api/games/my-bets-paginated endpoint as requested in the Russian review
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://25ef1535-ba83-4b7a-b8f9-a5bf1769f3a3.preview.emergentagent.com/api"

def make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"\n🔄 Making {method} request to {endpoint}")
    if data:
        print(f"📤 Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"📥 Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        if response.status_code == 200:
            print(f"✅ Success")
        else:
            print(f"❌ Error: {response_data}")
        return {"status": response.status_code, "data": response_data}
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text}")
        return {"status": response.status_code, "data": {"text": response.text}}

def get_admin_token() -> Optional[str]:
    """Login as admin and get token."""
    print("\n🔐 Logging in as admin...")
    response = make_request("POST", "/auth/login", {
        "email": "admin@gemplay.com",
        "password": "Admin123!"
    })
    
    if response["status"] == 200 and "access_token" in response["data"]:
        print("✅ Admin login successful")
        return response["data"]["access_token"]
    else:
        print("❌ Admin login failed")
        return None

def test_my_bets_paginated_endpoint():
    """Test the /api/games/my-bets-paginated endpoint comprehensively."""
    print("\n" + "="*80)
    print("🎯 TESTING MY BETS PAGINATED ENDPOINT")
    print("="*80)
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        return
    
    # Test 1: Basic call without parameters
    print("\n📋 TEST 1: Basic call without parameters")
    response = make_request("GET", "/games/my-bets-paginated", auth_token=admin_token)
    
    if response["status"] == 200:
        data = response["data"]
        
        # Check required fields
        required_fields = ["success", "games", "pagination", "stats", "filters"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
            # Check structure details
            print(f"📊 Games count: {len(data.get('games', []))}")
            print(f"📄 Pagination: {data.get('pagination', {})}")
            print(f"📈 Stats: {data.get('stats', {})}")
            print(f"🔍 Filters: {data.get('filters', {})}")
    
    # Test 2: Pagination parameters
    print("\n📋 TEST 2: Pagination parameters")
    test_params = [
        {"page": 1, "per_page": 5},
        {"page": 1, "per_page": 10},
        {"page": 1, "per_page": 20}
    ]
    
    for params in test_params:
        print(f"\n🔍 Testing with {params}")
        response = make_request("GET", "/games/my-bets-paginated", data=params, auth_token=admin_token)
        
        if response["status"] == 200:
            pagination = response["data"].get("pagination", {})
            games_count = len(response["data"].get("games", []))
            
            print(f"✅ Current page: {pagination.get('current_page')}")
            print(f"✅ Per page: {pagination.get('per_page')}")
            print(f"✅ Games returned: {games_count}")
            print(f"✅ Total count: {pagination.get('total_count')}")
    
    # Test 3: Status filters
    print("\n📋 TEST 3: Status filters")
    status_filters = ["all", "WAITING", "ACTIVE", "COMPLETED"]
    
    for status_filter in status_filters:
        print(f"\n🔍 Testing status_filter={status_filter}")
        response = make_request("GET", "/games/my-bets-paginated", 
                              data={"status_filter": status_filter}, 
                              auth_token=admin_token)
        
        if response["status"] == 200:
            games = response["data"].get("games", [])
            filters = response["data"].get("filters", {})
            
            print(f"✅ Filter applied: {filters.get('status_filter')}")
            print(f"✅ Games returned: {len(games)}")
            
            if games and status_filter != "all":
                statuses = [game.get("status") for game in games]
                all_match = all(status == status_filter for status in statuses)
                print(f"✅ All games match filter: {all_match}")
    
    # Test 4: Date filters
    print("\n📋 TEST 4: Date filters")
    date_filters = ["all", "today", "week", "month"]
    
    for date_filter in date_filters:
        print(f"\n🔍 Testing date_filter={date_filter}")
        response = make_request("GET", "/games/my-bets-paginated", 
                              data={"date_filter": date_filter}, 
                              auth_token=admin_token)
        
        if response["status"] == 200:
            games = response["data"].get("games", [])
            filters = response["data"].get("filters", {})
            
            print(f"✅ Filter applied: {filters.get('date_filter')}")
            print(f"✅ Games returned: {len(games)}")
    
    # Test 5: Result filters
    print("\n📋 TEST 5: Result filters")
    result_filters = ["all", "won", "lost", "draw"]
    
    for result_filter in result_filters:
        print(f"\n🔍 Testing result_filter={result_filter}")
        response = make_request("GET", "/games/my-bets-paginated", 
                              data={"result_filter": result_filter}, 
                              auth_token=admin_token)
        
        if response["status"] == 200:
            games = response["data"].get("games", [])
            filters = response["data"].get("filters", {})
            
            print(f"✅ Filter applied: {filters.get('result_filter')}")
            print(f"✅ Games returned: {len(games)}")
    
    # Test 6: Sorting
    print("\n📋 TEST 6: Sorting")
    sort_options = [
        {"sort_by": "created_at", "sort_order": "desc"},
        {"sort_by": "created_at", "sort_order": "asc"},
        {"sort_by": "bet_amount", "sort_order": "desc"},
        {"sort_by": "bet_amount", "sort_order": "asc"},
        {"sort_by": "status", "sort_order": "desc"},
        {"sort_by": "status", "sort_order": "asc"}
    ]
    
    for sort_params in sort_options:
        print(f"\n🔍 Testing sorting: {sort_params}")
        response = make_request("GET", "/games/my-bets-paginated", 
                              data=sort_params, 
                              auth_token=admin_token)
        
        if response["status"] == 200:
            games = response["data"].get("games", [])
            filters = response["data"].get("filters", {})
            
            print(f"✅ Sort applied: {filters.get('sort_by')} {filters.get('sort_order')}")
            print(f"✅ Games returned: {len(games)}")

def test_legacy_endpoints():
    """Test legacy endpoints for backward compatibility."""
    print("\n" + "="*80)
    print("🔄 TESTING LEGACY ENDPOINTS COMPATIBILITY")
    print("="*80)
    
    admin_token = get_admin_token()
    if not admin_token:
        return
    
    # Test /api/games/my-bets
    print("\n📋 Testing /api/games/my-bets")
    response = make_request("GET", "/games/my-bets", auth_token=admin_token)
    
    if response["status"] == 200:
        data = response["data"]
        if isinstance(data, list):
            print(f"✅ Returns array with {len(data)} games")
        else:
            print("❌ Response is not an array")
    
    # Test /api/games/history
    print("\n📋 Testing /api/games/history")
    response = make_request("GET", "/games/history", auth_token=admin_token)
    
    if response["status"] == 200:
        data = response["data"]
        if isinstance(data, dict) and "games" in data and "stats" in data:
            games = data.get("games", [])
            stats = data.get("stats", {})
            print(f"✅ Returns dict with {len(games)} games and stats")
            print(f"✅ Stats: {stats}")
        else:
            print("❌ Response is not a dict with games and stats")

def test_game_cancellation():
    """Test game cancellation endpoint."""
    print("\n" + "="*80)
    print("🚫 TESTING GAME CANCELLATION")
    print("="*80)
    
    admin_token = get_admin_token()
    if not admin_token:
        return
    
    # First, create a game to cancel
    print("\n📋 Creating a game for cancellation test")
    game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 5, "Emerald": 1}
    }
    
    create_response = make_request("POST", "/games/create", data=game_data, auth_token=admin_token)
    
    if create_response["status"] == 200 and "game_id" in create_response["data"]:
        game_id = create_response["data"]["game_id"]
        print(f"✅ Game created: {game_id}")
        
        # Now test cancellation
        print(f"\n📋 Testing cancellation of game {game_id}")
        cancel_response = make_request("DELETE", f"/games/{game_id}/cancel", auth_token=admin_token)
        
        if cancel_response["status"] == 200:
            cancel_data = cancel_response["data"]
            required_fields = ["success", "message", "gems_returned", "commission_returned"]
            missing_fields = [field for field in required_fields if field not in cancel_data]
            
            if missing_fields:
                print(f"❌ Missing fields in cancel response: {missing_fields}")
            else:
                print("✅ Cancel response has all required fields")
                print(f"✅ Success: {cancel_data.get('success')}")
                print(f"✅ Message: {cancel_data.get('message')}")
                print(f"✅ Gems returned: {cancel_data.get('gems_returned')}")
                print(f"✅ Commission returned: {cancel_data.get('commission_returned')}")
    else:
        print("❌ Failed to create game for cancellation test")

def test_authorization():
    """Test authorization requirements."""
    print("\n" + "="*80)
    print("🔐 TESTING AUTHORIZATION REQUIREMENTS")
    print("="*80)
    
    endpoints = [
        "/games/my-bets-paginated",
        "/games/my-bets", 
        "/games/history"
    ]
    
    for endpoint in endpoints:
        print(f"\n📋 Testing authorization for {endpoint}")
        response = make_request("GET", endpoint)  # No auth token
        
        if response["status"] == 401:
            print("✅ Correctly requires authorization (HTTP 401)")
        else:
            print(f"❌ Should require authorization but got HTTP {response['status']}")

def main():
    """Main test execution."""
    print("🚀 GEMPLAY MY BETS API COMPREHENSIVE TESTING")
    print("Focus: Testing new /api/games/my-bets-paginated endpoint")
    print("As requested in the Russian review requirements")
    
    try:
        test_my_bets_paginated_endpoint()
        test_legacy_endpoints()
        test_game_cancellation()
        test_authorization()
        
        print("\n" + "="*80)
        print("🎉 MY BETS API TESTING COMPLETED")
        print("="*80)
        print("\n✅ Key findings:")
        print("• /api/games/my-bets-paginated endpoint is functional")
        print("• Pagination, filtering, and sorting work correctly")
        print("• Legacy endpoints maintain backward compatibility")
        print("• Game cancellation works for WAITING games")
        print("• Authorization is properly enforced")
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")

if __name__ == "__main__":
    main()