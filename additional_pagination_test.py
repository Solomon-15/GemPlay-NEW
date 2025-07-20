#!/usr/bin/env python3
"""
Additional Pagination Edge Cases Testing
Tests specific edge cases and metadata format validation
"""
import requests
import json

BASE_URL = "https://c420eb5d-1c25-48f9-b245-20bde3be2c13.preview.emergentagent.com/api"
ADMIN_USER = {"email": "admin@gemplay.com", "password": "Admin123!"}

def login_admin():
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_detailed_pagination_metadata():
    """Test detailed pagination metadata format."""
    print("=== DETAILED PAGINATION METADATA TESTING ===")
    
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test regular bots endpoint
    response = requests.get(f"{BASE_URL}/admin/bots/regular/list?page=1&limit=5", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Regular Bots Pagination Metadata:")
        print(f"   - total_count: {data.get('total_count')} (type: {type(data.get('total_count')).__name__})")
        print(f"   - current_page: {data.get('current_page')} (type: {type(data.get('current_page')).__name__})")
        print(f"   - total_pages: {data.get('total_pages')} (type: {type(data.get('total_pages')).__name__})")
        print(f"   - items_per_page: {data.get('items_per_page')} (type: {type(data.get('items_per_page')).__name__})")
        print(f"   - has_next: {data.get('has_next')} (type: {type(data.get('has_next')).__name__})")
        print(f"   - has_prev: {data.get('has_prev')} (type: {type(data.get('has_prev')).__name__})")
        print(f"   - actual items returned: {len(data.get('bots', []))}")
        
        # Verify metadata consistency
        expected_total_pages = (data['total_count'] + data['items_per_page'] - 1) // data['items_per_page']
        if data['total_pages'] == expected_total_pages:
            print("   ✅ total_pages calculation is correct")
        else:
            print(f"   ❌ total_pages calculation error: expected {expected_total_pages}, got {data['total_pages']}")
    
    # Test profit entries endpoint
    response = requests.get(f"{BASE_URL}/admin/profit/entries?page=2&limit=8", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Profit Entries Pagination Metadata:")
        print(f"   - total_count: {data.get('total_count')} (type: {type(data.get('total_count')).__name__})")
        print(f"   - page: {data.get('page')} (type: {type(data.get('page')).__name__})")
        print(f"   - limit: {data.get('limit')} (type: {type(data.get('limit')).__name__})")
        print(f"   - total_pages: {data.get('total_pages')} (type: {type(data.get('total_pages')).__name__})")
        print(f"   - actual items returned: {len(data.get('entries', []))}")
        
        # Verify metadata consistency
        expected_total_pages = (data['total_count'] + data['limit'] - 1) // data['limit']
        if data['total_pages'] == expected_total_pages:
            print("   ✅ total_pages calculation is correct")
        else:
            print(f"   ❌ total_pages calculation error: expected {expected_total_pages}, got {data['total_pages']}")

def test_empty_results_pagination():
    """Test pagination with empty results."""
    print("\n=== EMPTY RESULTS PAGINATION TESTING ===")
    
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with very high page number to get empty results
    response = requests.get(f"{BASE_URL}/admin/bots/regular/list?page=999&limit=10", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Empty Results Test (Regular Bots):")
        print(f"   - total_count: {data.get('total_count')}")
        print(f"   - current_page: {data.get('current_page')}")
        print(f"   - total_pages: {data.get('total_pages')}")
        print(f"   - has_next: {data.get('has_next')}")
        print(f"   - has_prev: {data.get('has_prev')}")
        print(f"   - items returned: {len(data.get('bots', []))}")
        
        if len(data.get('bots', [])) == 0 and data.get('has_next') == False:
            print("   ✅ Empty results handled correctly")
        else:
            print("   ❌ Empty results not handled correctly")

def test_single_page_results():
    """Test pagination with results that fit in a single page."""
    print("\n=== SINGLE PAGE RESULTS TESTING ===")
    
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with large limit to get all results in one page
    response = requests.get(f"{BASE_URL}/admin/bots/regular/list?page=1&limit=100", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Single Page Results Test:")
        print(f"   - total_count: {data.get('total_count')}")
        print(f"   - current_page: {data.get('current_page')}")
        print(f"   - total_pages: {data.get('total_pages')}")
        print(f"   - has_next: {data.get('has_next')}")
        print(f"   - has_prev: {data.get('has_prev')}")
        print(f"   - items returned: {len(data.get('bots', []))}")
        
        if data.get('total_pages') == 1 and data.get('has_next') == False and data.get('has_prev') == False:
            print("   ✅ Single page pagination handled correctly")
        else:
            print("   ❌ Single page pagination not handled correctly")

def test_profit_entries_filtering():
    """Test profit entries pagination with filtering."""
    print("\n=== PROFIT ENTRIES FILTERING WITH PAGINATION ===")
    
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different entry types with pagination
    entry_types = ["BET_COMMISSION", "GIFT_COMMISSION", "ADMIN_ADJUSTMENT"]
    
    for entry_type in entry_types:
        response = requests.get(
            f"{BASE_URL}/admin/profit/entries?page=1&limit=5&entry_type={entry_type}", 
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filter: {entry_type}")
            print(f"   - total_count: {data.get('total_count')}")
            print(f"   - entries returned: {len(data.get('entries', []))}")
            print(f"   - page: {data.get('page')}")
            print(f"   - limit: {data.get('limit')}")
        else:
            print(f"❌ Filter: {entry_type} - HTTP {response.status_code}")

if __name__ == "__main__":
    test_detailed_pagination_metadata()
    test_empty_results_pagination()
    test_single_page_results()
    test_profit_entries_filtering()
    print("\n=== ADDITIONAL TESTING COMPLETED ===")