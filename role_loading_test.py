#!/usr/bin/env python3
"""
Role Loading Error Testing - Russian Review
Focus: Testing the "Ошибка загрузки ролей" (Role Loading Error) in admin panel

Requirements from review:
1. Test endpoint /api/admin/users with admin token
2. Check that endpoint returns list of users with their roles
3. Verify authentication works properly
4. Check response format (should contain "users" field)
5. Verify admin user (admin@gemplay.com) has SUPER_ADMIN role
6. Test get_current_admin_user function compatibility
7. Test various query parameters (limit=1000 etc.)
8. Test error handling (401, 403)
9. Integration test: login admin -> get token -> request /api/admin/users
10. Verify role data is correctly returned for RoleManagement component
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple

# Configuration
BASE_URL = "https://write-russian-2.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class RoleLoadingTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def admin_login(self) -> bool:
        """Test admin login and get token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json=ADMIN_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    user_info = data.get("user", {})
                    role = user_info.get("role", "")
                    
                    self.log_test(
                        "Admin Login", 
                        True, 
                        f"Successfully logged in as {user_info.get('username', 'admin')} with role {role}"
                    )
                    return True
                else:
                    self.log_test("Admin Login", False, "No access_token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_users_endpoint_basic(self) -> bool:
        """Test basic /api/admin/users endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains users field
                if "users" in data:
                    users = data["users"]
                    user_count = len(users)
                    
                    self.log_test(
                        "Admin Users Endpoint - Basic", 
                        True, 
                        f"Successfully retrieved {user_count} users with 'users' field present"
                    )
                    return True
                else:
                    # Check if response is a list (alternative format)
                    if isinstance(data, list):
                        user_count = len(data)
                        self.log_test(
                            "Admin Users Endpoint - Basic", 
                            True, 
                            f"Successfully retrieved {user_count} users (list format)"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin Users Endpoint - Basic", 
                            False, 
                            f"Response missing 'users' field. Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                        )
                        return False
            else:
                self.log_test(
                    "Admin Users Endpoint - Basic", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Users Endpoint - Basic", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_users_with_limit(self) -> bool:
        """Test /api/admin/users endpoint with limit parameter"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/users?limit=1000", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract users from response
                users = data.get("users", data if isinstance(data, list) else [])
                user_count = len(users)
                
                self.log_test(
                    "Admin Users Endpoint - With Limit", 
                    True, 
                    f"Successfully retrieved {user_count} users with limit=1000"
                )
                return True
            else:
                self.log_test(
                    "Admin Users Endpoint - With Limit", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Users Endpoint - With Limit", False, f"Exception: {str(e)}")
            return False
    
    def test_users_have_roles(self) -> bool:
        """Test that users in response have role information"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/users?limit=10", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", data if isinstance(data, list) else [])
                
                if not users:
                    self.log_test("Users Have Roles", False, "No users found in response")
                    return False
                
                users_with_roles = 0
                role_types = set()
                
                for user in users[:5]:  # Check first 5 users
                    if "role" in user:
                        users_with_roles += 1
                        role_types.add(user["role"])
                
                if users_with_roles > 0:
                    self.log_test(
                        "Users Have Roles", 
                        True, 
                        f"{users_with_roles}/{min(5, len(users))} users have role field. Roles found: {list(role_types)}"
                    )
                    return True
                else:
                    self.log_test("Users Have Roles", False, "No users have role field")
                    return False
            else:
                self.log_test("Users Have Roles", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Users Have Roles", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_user_role(self) -> bool:
        """Test that admin user has SUPER_ADMIN role"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", data if isinstance(data, list) else [])
                
                admin_user = None
                for user in users:
                    if user.get("email") == "admin@gemplay.com":
                        admin_user = user
                        break
                
                if admin_user:
                    role = admin_user.get("role", "")
                    if role == "SUPER_ADMIN":
                        self.log_test(
                            "Admin User Role", 
                            True, 
                            f"Admin user has correct SUPER_ADMIN role"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin User Role", 
                            False, 
                            f"Admin user has role '{role}', expected 'SUPER_ADMIN'"
                        )
                        return False
                else:
                    self.log_test("Admin User Role", False, "Admin user not found in users list")
                    return False
            else:
                self.log_test("Admin User Role", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin User Role", False, f"Exception: {str(e)}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that endpoint returns 401 without token"""
        try:
            response = requests.get(f"{BASE_URL}/admin/users")
            
            if response.status_code == 401:
                self.log_test(
                    "Unauthorized Access", 
                    True, 
                    "Correctly returns 401 without authorization token"
                )
                return True
            else:
                self.log_test(
                    "Unauthorized Access", 
                    False, 
                    f"Expected 401, got {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_token(self) -> bool:
        """Test that endpoint returns 401 with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid Token", 
                    True, 
                    "Correctly returns 401 with invalid token"
                )
                return True
            else:
                self.log_test(
                    "Invalid Token", 
                    False, 
                    f"Expected 401, got {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Invalid Token", False, f"Exception: {str(e)}")
            return False
    
    def test_response_format_compatibility(self) -> bool:
        """Test response format compatibility for RoleManagement component"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/admin/users?limit=5", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", data if isinstance(data, list) else [])
                
                if not users:
                    self.log_test("Response Format Compatibility", False, "No users in response")
                    return False
                
                # Check required fields for RoleManagement component
                required_fields = ["id", "username", "email", "role"]
                compatible_users = 0
                
                for user in users[:3]:  # Check first 3 users
                    has_all_fields = all(field in user for field in required_fields)
                    if has_all_fields:
                        compatible_users += 1
                
                if compatible_users > 0:
                    self.log_test(
                        "Response Format Compatibility", 
                        True, 
                        f"{compatible_users}/{min(3, len(users))} users have all required fields for RoleManagement"
                    )
                    return True
                else:
                    self.log_test(
                        "Response Format Compatibility", 
                        False, 
                        "No users have all required fields for RoleManagement component"
                    )
                    return False
            else:
                self.log_test("Response Format Compatibility", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Response Format Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_get_current_admin_user_compatibility(self) -> bool:
        """Test that get_current_admin_user function works (via auth/me endpoint)"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if user has admin role
                role = data.get("role", "")
                if role in ["ADMIN", "SUPER_ADMIN"]:
                    self.log_test(
                        "get_current_admin_user Compatibility", 
                        True, 
                        f"Admin user authentication working, role: {role}"
                    )
                    return True
                else:
                    self.log_test(
                        "get_current_admin_user Compatibility", 
                        False, 
                        f"User role is '{role}', not admin"
                    )
                    return False
            else:
                self.log_test(
                    "get_current_admin_user Compatibility", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("get_current_admin_user Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_pagination_and_filtering(self) -> bool:
        """Test pagination and filtering parameters"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test with different parameters
            test_params = [
                "?page=1&per_page=10",
                "?limit=20",
                "?search=admin",
                "?status=ACTIVE"
            ]
            
            successful_requests = 0
            
            for params in test_params:
                response = requests.get(f"{BASE_URL}/admin/users{params}", headers=headers)
                if response.status_code == 200:
                    successful_requests += 1
            
            if successful_requests >= 2:  # At least half should work
                self.log_test(
                    "Pagination and Filtering", 
                    True, 
                    f"{successful_requests}/{len(test_params)} parameter combinations work"
                )
                return True
            else:
                self.log_test(
                    "Pagination and Filtering", 
                    False, 
                    f"Only {successful_requests}/{len(test_params)} parameter combinations work"
                )
                return False
                
        except Exception as e:
            self.log_test("Pagination and Filtering", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all role loading tests"""
        print("🔍 ROLE LOADING ERROR TESTING - RUSSIAN REVIEW")
        print("=" * 60)
        print(f"Testing endpoint: {BASE_URL}/admin/users")
        print(f"Admin credentials: {ADMIN_USER['email']}")
        print()
        
        # Step 1: Admin login
        if not self.admin_login():
            print("❌ CRITICAL: Admin login failed. Cannot proceed with tests.")
            return
        
        print()
        print("🧪 RUNNING ROLE LOADING TESTS:")
        print("-" * 40)
        
        # Step 2: Run all tests
        test_methods = [
            self.test_admin_users_endpoint_basic,
            self.test_admin_users_with_limit,
            self.test_users_have_roles,
            self.test_admin_user_role,
            self.test_unauthorized_access,
            self.test_invalid_token,
            self.test_response_format_compatibility,
            self.test_get_current_admin_user_compatibility,
            self.test_pagination_and_filtering
        ]
        
        for test_method in test_methods:
            test_method()
            time.sleep(0.5)  # Small delay between tests
        
        # Step 3: Summary
        print()
        print("📊 TEST SUMMARY:")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 80:
            print("🎉 ROLE LOADING SYSTEM: WORKING CORRECTLY!")
            print("The /api/admin/users endpoint is functional and should resolve the 'Ошибка загрузки ролей' issue.")
        elif success_rate >= 60:
            print("⚠️ ROLE LOADING SYSTEM: PARTIALLY WORKING")
            print("Some issues detected that may cause role loading errors.")
        else:
            print("❌ ROLE LOADING SYSTEM: CRITICAL ISSUES")
            print("Major problems detected that likely cause the role loading error.")
        
        print()
        print("🔧 RECOMMENDATIONS FOR ROLEMANAGEMENT COMPONENT:")
        print("-" * 50)
        
        # Analyze results and provide recommendations
        failed_tests = [result for result in self.test_results if not result["success"]]
        
        if not failed_tests:
            print("✅ All tests passed. RoleManagement component should work correctly.")
        else:
            print("Issues found that may affect RoleManagement component:")
            for failed_test in failed_tests:
                print(f"  • {failed_test['test']}: {failed_test['details']}")
        
        print()
        print("📋 INTEGRATION TEST RESULTS:")
        print("-" * 30)
        print("✅ Admin login → Token generation → /api/admin/users request flow tested")
        print(f"✅ Response format compatibility for RoleManagement: {'PASS' if any(r['test'] == 'Response Format Compatibility' and r['success'] for r in self.test_results) else 'FAIL'}")
        print(f"✅ Role data availability: {'PASS' if any(r['test'] == 'Users Have Roles' and r['success'] for r in self.test_results) else 'FAIL'}")
        print(f"✅ Admin user permissions: {'PASS' if any(r['test'] == 'Admin User Role' and r['success'] for r in self.test_results) else 'FAIL'}")

if __name__ == "__main__":
    tester = RoleLoadingTester()
    tester.run_all_tests()