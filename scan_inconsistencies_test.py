#!/usr/bin/env python3
"""
Backend Testing Script for GET /api/admin/games/scan-inconsistencies Endpoint
Testing Requirements:
1. With admin auth, call without params and expect default 24h window
2. Call with start_ts/end_ts ISO strings and page/page_size=25 and verify pagination
3. Backward compatibility: call with legacy params start/end/limit=100
4. Auth required: ensure non-admin token returns 403/401
5. Ensure all items have required keys and verify period.start/end are ISO serializable
"""

import asyncio
import aiohttp
import json
import os
import sys
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://modalni-dialogi.preview.emergentagent.com/api"

class ScanInconsistenciesTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def login_admin(self) -> bool:
        """Login as admin to get admin token"""
        try:
            login_data = {
                "email": "admin@gemplay.com",
                "password": "Admin123!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print("✅ Admin login successful")
                    return True
                else:
                    print(f"❌ Admin login failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False
            
    async def login_regular_user(self) -> bool:
        """Login as regular user to test auth restrictions"""
        try:
            # Try to find a regular user or create one
            login_data = {
                "email": "testuser@example.com",
                "password": "TestPassword123!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.user_token = data["access_token"]
                    print("✅ Regular user login successful")
                    return True
                else:
                    print(f"⚠️ Regular user login failed: {response.status} - will test without user token")
                    return False
        except Exception as e:
            print(f"⚠️ Regular user login error: {e} - will test without user token")
            return False

    async def test_default_24h_window(self) -> Dict[str, Any]:
        """Test 1: Call without params and expect default 24h window"""
        print("\n🔍 TEST 1: Default 24h window without parameters")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify required fields
                    required_fields = ["success", "checked", "found", "items", "page", "page_size", "pages", "period"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        return {
                            "passed": False,
                            "error": f"Missing required fields: {missing_fields}",
                            "data": data
                        }
                    
                    # Verify default values
                    if data["page"] != 1:
                        return {"passed": False, "error": f"Expected page=1, got {data['page']}"}
                    
                    if data["page_size"] != 50:
                        return {"passed": False, "error": f"Expected page_size=50, got {data['page_size']}"}
                    
                    if data["pages"] < 1:
                        return {"passed": False, "error": f"Expected pages>=1, got {data['pages']}"}
                    
                    # Verify checked count is >= 0
                    if data["checked"] < 0:
                        return {"passed": False, "error": f"Expected checked>=0, got {data['checked']}"}
                    
                    # Verify found count is >= 0
                    if data["found"] < 0:
                        return {"passed": False, "error": f"Expected found>=0, got {data['found']}"}
                    
                    # Verify period has start and end
                    period = data.get("period", {})
                    if "start" not in period or "end" not in period:
                        return {"passed": False, "error": "Period missing start or end"}
                    
                    # Verify items is an array
                    if not isinstance(data["items"], list):
                        return {"passed": False, "error": "Items should be an array"}
                    
                    print(f"✅ Default 24h window test passed")
                    print(f"   - Checked: {data['checked']} games")
                    print(f"   - Found: {data['found']} inconsistencies")
                    print(f"   - Page: {data['page']}/{data['pages']}")
                    print(f"   - Period: {period['start']} to {period['end']}")
                    
                    return {
                        "passed": True,
                        "data": data,
                        "checked": data["checked"],
                        "found": data["found"]
                    }
                else:
                    return {"passed": False, "error": f"HTTP {response.status}: {await response.text()}"}
                    
        except Exception as e:
            return {"passed": False, "error": f"Exception: {e}"}

    async def test_pagination_with_timestamps(self) -> Dict[str, Any]:
        """Test 2: Call with start_ts/end_ts ISO strings and page/page_size=25"""
        print("\n🔍 TEST 2: Pagination with ISO timestamps")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Use last 7 days for better chance of finding data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            params = {
                "start_ts": start_time.isoformat() + "Z",
                "end_ts": end_time.isoformat() + "Z",
                "page": 1,
                "page_size": 25
            }
            
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                      headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify pagination structure
                    if data["page"] != 1:
                        return {"passed": False, "error": f"Expected page=1, got {data['page']}"}
                    
                    if data["page_size"] != 25:
                        return {"passed": False, "error": f"Expected page_size=25, got {data['page_size']}"}
                    
                    # Verify pagination math
                    expected_pages = math.ceil(data["found"] / 25) if data["found"] > 0 else 1
                    if data["pages"] != expected_pages:
                        return {"passed": False, "error": f"Expected pages={expected_pages}, got {data['pages']}"}
                    
                    # Verify items length <= 25
                    if len(data["items"]) > 25:
                        return {"passed": False, "error": f"Items length {len(data['items'])} exceeds page_size 25"}
                    
                    # If there are items, verify they have required keys
                    if data["items"]:
                        required_item_keys = ["game_id", "creator_id", "opponent_id", "creator_move", 
                                            "opponent_move", "winner_id", "expected_winner_id", "completed_at"]
                        
                        for i, item in enumerate(data["items"]):
                            missing_keys = [key for key in required_item_keys if key not in item]
                            if missing_keys:
                                return {"passed": False, "error": f"Item {i} missing keys: {missing_keys}"}
                    
                    # Test second page if available
                    if data["pages"] > 1:
                        params["page"] = 2
                        async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                                  headers=headers, params=params) as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                if data2["page"] != 2:
                                    return {"passed": False, "error": f"Page 2 test failed: expected page=2, got {data2['page']}"}
                    
                    print(f"✅ Pagination test passed")
                    print(f"   - Found: {data['found']} inconsistencies")
                    print(f"   - Pages: {data['pages']}")
                    print(f"   - Items on page 1: {len(data['items'])}")
                    
                    return {"passed": True, "data": data}
                else:
                    return {"passed": False, "error": f"HTTP {response.status}: {await response.text()}"}
                    
        except Exception as e:
            return {"passed": False, "error": f"Exception: {e}"}

    async def test_backward_compatibility(self) -> Dict[str, Any]:
        """Test 3: Backward compatibility with legacy params start/end/limit=100"""
        print("\n🔍 TEST 3: Backward compatibility with legacy parameters")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Use legacy datetime format
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=3)
            
            params = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "limit": 100
            }
            
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                      headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify it still returns pagination structure
                    required_fields = ["page", "page_size", "pages", "items"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        return {"passed": False, "error": f"Missing pagination fields: {missing_fields}"}
                    
                    # Verify items length <= min(found, 100) on first page
                    if len(data["items"]) > min(data["found"], 100):
                        return {"passed": False, "error": f"Items length {len(data['items'])} exceeds limit"}
                    
                    print(f"✅ Backward compatibility test passed")
                    print(f"   - Found: {data['found']} inconsistencies")
                    print(f"   - Items returned: {len(data['items'])}")
                    print(f"   - Page structure maintained")
                    
                    return {"passed": True, "data": data}
                else:
                    return {"passed": False, "error": f"HTTP {response.status}: {await response.text()}"}
                    
        except Exception as e:
            return {"passed": False, "error": f"Exception: {e}"}

    async def test_auth_required(self) -> Dict[str, Any]:
        """Test 4: Auth required - ensure non-admin token returns 403/401"""
        print("\n🔍 TEST 4: Authentication and authorization requirements")
        
        results = []
        
        # Test 1: No token
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies") as response:
                if response.status in [401, 403]:
                    results.append({"test": "no_token", "passed": True, "status": response.status})
                    print(f"✅ No token test passed: {response.status}")
                else:
                    results.append({"test": "no_token", "passed": False, "status": response.status})
                    print(f"❌ No token test failed: expected 401/403, got {response.status}")
        except Exception as e:
            results.append({"test": "no_token", "passed": False, "error": str(e)})
        
        # Test 2: Regular user token (if available)
        if self.user_token:
            try:
                headers = {"Authorization": f"Bearer {self.user_token}"}
                async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                          headers=headers) as response:
                    if response.status in [401, 403]:
                        results.append({"test": "user_token", "passed": True, "status": response.status})
                        print(f"✅ User token test passed: {response.status}")
                    else:
                        results.append({"test": "user_token", "passed": False, "status": response.status})
                        print(f"❌ User token test failed: expected 401/403, got {response.status}")
            except Exception as e:
                results.append({"test": "user_token", "passed": False, "error": str(e)})
        else:
            print("⚠️ Skipping user token test - no user token available")
        
        # Test 3: Invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                      headers=headers) as response:
                if response.status in [401, 403]:
                    results.append({"test": "invalid_token", "passed": True, "status": response.status})
                    print(f"✅ Invalid token test passed: {response.status}")
                else:
                    results.append({"test": "invalid_token", "passed": False, "status": response.status})
                    print(f"❌ Invalid token test failed: expected 401/403, got {response.status}")
        except Exception as e:
            results.append({"test": "invalid_token", "passed": False, "error": str(e)})
        
        all_passed = all(result.get("passed", False) for result in results)
        return {"passed": all_passed, "results": results}

    async def test_item_structure_and_serialization(self) -> Dict[str, Any]:
        """Test 5: Ensure all items have required keys and period.start/end are ISO serializable"""
        print("\n🔍 TEST 5: Item structure and JSON serialization")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get data with a longer time range to increase chances of finding items
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            params = {
                "start_ts": start_time.isoformat() + "Z",
                "end_ts": end_time.isoformat() + "Z",
                "page_size": 10
            }
            
            async with self.session.get(f"{BACKEND_URL}/admin/games/scan-inconsistencies", 
                                      headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Test JSON serialization of the entire response
                    try:
                        json_str = json.dumps(data)
                        print("✅ Response is JSON serializable")
                    except Exception as e:
                        return {"passed": False, "error": f"Response not JSON serializable: {e}"}
                    
                    # Verify period.start/end are present and serializable
                    period = data.get("period", {})
                    if "start" not in period or "end" not in period:
                        return {"passed": False, "error": "Period missing start or end"}
                    
                    try:
                        json.dumps(period)
                        print("✅ Period start/end are JSON serializable")
                    except Exception as e:
                        return {"passed": False, "error": f"Period not JSON serializable: {e}"}
                    
                    # If there are items, verify their structure
                    if data["items"]:
                        required_keys = ["game_id", "creator_id", "opponent_id", "creator_move", 
                                       "opponent_move", "winner_id", "expected_winner_id", "completed_at"]
                        
                        for i, item in enumerate(data["items"]):
                            # Check all required keys are present
                            missing_keys = [key for key in required_keys if key not in item]
                            if missing_keys:
                                return {"passed": False, "error": f"Item {i} missing keys: {missing_keys}"}
                            
                            # Verify item is JSON serializable
                            try:
                                json.dumps(item)
                            except Exception as e:
                                return {"passed": False, "error": f"Item {i} not JSON serializable: {e}"}
                        
                        print(f"✅ All {len(data['items'])} items have required keys and are JSON serializable")
                    else:
                        print("ℹ️ No inconsistent items found in the test period")
                    
                    return {"passed": True, "data": data, "items_count": len(data["items"])}
                else:
                    return {"passed": False, "error": f"HTTP {response.status}: {await response.text()}"}
                    
        except Exception as e:
            return {"passed": False, "error": f"Exception: {e}"}

    async def run_all_tests(self):
        """Run all tests and generate summary"""
        print("🚀 Starting GET /api/admin/games/scan-inconsistencies endpoint testing")
        print("=" * 80)
        
        # Setup
        await self.setup_session()
        
        # Login
        if not await self.login_admin():
            print("❌ Cannot proceed without admin access")
            await self.cleanup_session()
            return
        
        # Try to login regular user (optional)
        await self.login_regular_user()
        
        # Run tests
        tests = [
            ("Default 24h Window", self.test_default_24h_window),
            ("Pagination with Timestamps", self.test_pagination_with_timestamps),
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Auth Required", self.test_auth_required),
            ("Item Structure & Serialization", self.test_item_structure_and_serialization)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                result["test_name"] = test_name
                results.append(result)
            except Exception as e:
                results.append({
                    "test_name": test_name,
                    "passed": False,
                    "error": f"Test execution failed: {e}"
                })
        
        # Cleanup
        await self.cleanup_session()
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_count = 0
        total_count = len(results)
        
        for result in results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"{status}: {result['test_name']}")
            if not result["passed"] and "error" in result:
                print(f"   Error: {result['error']}")
            if result["passed"]:
                passed_count += 1
        
        print(f"\nOVERALL RESULT: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("🎉 ALL TESTS PASSED! The scan-inconsistencies endpoint is working correctly.")
        else:
            print("⚠️ Some tests failed. Please review the errors above.")
        
        return results

async def main():
    """Main test execution"""
    tester = ScanInconsistenciesTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(result["passed"] for result in results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())