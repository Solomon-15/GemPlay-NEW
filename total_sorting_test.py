#!/usr/bin/env python3
"""
TOTAL Column Sorting Test for User Management
Focus: Testing TOTAL column sorting after frontend fix in UserManagement.js
Russian Review Requirements: Verify TOTAL sorting works correctly with proper numeric ordering
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class TotalSortingTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()

    def authenticate_admin(self) -> bool:
        """Authenticate as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed to authenticate: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Authentication error: {str(e)}")
            return False

    def get_admin_headers(self) -> Dict[str, str]:
        """Get headers with admin authorization"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

    def test_total_sorting_asc(self) -> bool:
        """Test TOTAL column sorting in ascending order"""
        try:
            # Test ascending sort
            params = {
                "sort_by": "total",
                "sort_order": "asc",
                "page": 1,
                "per_page": 20
            }
            
            response = requests.get(f"{BASE_URL}/admin/users", 
                                  headers=self.get_admin_headers(), 
                                  params=params)
            
            if response.status_code != 200:
                self.log_result("TOTAL Sorting ASC", False, 
                              f"API request failed: {response.status_code}")
                return False
            
            data = response.json()
            users = data.get("users", [])
            
            if not users:
                self.log_result("TOTAL Sorting ASC", False, "No users returned")
                return False
            
            # Check if users are sorted by total_balance in ascending order
            total_balances = []
            for user in users:
                total_balance = user.get("total_balance")
                if total_balance is None:
                    self.log_result("TOTAL Sorting ASC", False, 
                                  f"User {user.get('username')} missing total_balance")
                    return False
                
                # Verify total_balance is numeric
                if not isinstance(total_balance, (int, float)):
                    self.log_result("TOTAL Sorting ASC", False, 
                                  f"total_balance is not numeric: {type(total_balance)} - {total_balance}")
                    return False
                
                total_balances.append(float(total_balance))
            
            # Check if sorted in ascending order
            is_sorted_asc = all(total_balances[i] <= total_balances[i+1] 
                               for i in range(len(total_balances)-1))
            
            if not is_sorted_asc:
                self.log_result("TOTAL Sorting ASC", False, 
                              f"Users not sorted in ascending order: {total_balances[:5]}")
                return False
            
            self.log_result("TOTAL Sorting ASC", True, 
                          f"Successfully sorted {len(users)} users by TOTAL in ascending order",
                          {"first_5_totals": total_balances[:5], 
                           "last_5_totals": total_balances[-5:]})
            return True
            
        except Exception as e:
            self.log_result("TOTAL Sorting ASC", False, f"Error: {str(e)}")
            return False

    def test_total_sorting_desc(self) -> bool:
        """Test TOTAL column sorting in descending order"""
        try:
            # Test descending sort
            params = {
                "sort_by": "total",
                "sort_order": "desc",
                "page": 1,
                "per_page": 20
            }
            
            response = requests.get(f"{BASE_URL}/admin/users", 
                                  headers=self.get_admin_headers(), 
                                  params=params)
            
            if response.status_code != 200:
                self.log_result("TOTAL Sorting DESC", False, 
                              f"API request failed: {response.status_code}")
                return False
            
            data = response.json()
            users = data.get("users", [])
            
            if not users:
                self.log_result("TOTAL Sorting DESC", False, "No users returned")
                return False
            
            # Check if users are sorted by total_balance in descending order
            total_balances = []
            for user in users:
                total_balance = user.get("total_balance")
                if total_balance is None:
                    self.log_result("TOTAL Sorting DESC", False, 
                                  f"User {user.get('username')} missing total_balance")
                    return False
                
                # Verify total_balance is numeric
                if not isinstance(total_balance, (int, float)):
                    self.log_result("TOTAL Sorting DESC", False, 
                                  f"total_balance is not numeric: {type(total_balance)} - {total_balance}")
                    return False
                
                total_balances.append(float(total_balance))
            
            # Check if sorted in descending order
            is_sorted_desc = all(total_balances[i] >= total_balances[i+1] 
                                for i in range(len(total_balances)-1))
            
            if not is_sorted_desc:
                self.log_result("TOTAL Sorting DESC", False, 
                              f"Users not sorted in descending order: {total_balances[:5]}")
                return False
            
            self.log_result("TOTAL Sorting DESC", True, 
                          f"Successfully sorted {len(users)} users by TOTAL in descending order",
                          {"first_5_totals": total_balances[:5], 
                           "last_5_totals": total_balances[-5:]})
            return True
            
        except Exception as e:
            self.log_result("TOTAL Sorting DESC", False, f"Error: {str(e)}")
            return False

    def test_total_balance_calculation(self) -> bool:
        """Test that total_balance is calculated correctly (virtual_balance + frozen_balance + total_gems_value)"""
        try:
            params = {
                "sort_by": "total",
                "sort_order": "desc",
                "page": 1,
                "per_page": 10
            }
            
            response = requests.get(f"{BASE_URL}/admin/users", 
                                  headers=self.get_admin_headers(), 
                                  params=params)
            
            if response.status_code != 200:
                self.log_result("TOTAL Balance Calculation", False, 
                              f"API request failed: {response.status_code}")
                return False
            
            data = response.json()
            users = data.get("users", [])
            
            if not users:
                self.log_result("TOTAL Balance Calculation", False, "No users returned")
                return False
            
            calculation_errors = []
            for user in users:
                virtual_balance = float(user.get("virtual_balance", 0))
                frozen_balance = float(user.get("frozen_balance", 0))
                # Use total_gems_value instead of gems_value
                gems_value = float(user.get("total_gems_value", 0))
                total_balance = float(user.get("total_balance", 0))
                
                expected_total = virtual_balance + frozen_balance + gems_value
                
                # Allow small floating point differences
                if abs(total_balance - expected_total) > 0.01:
                    calculation_errors.append({
                        "username": user.get("username"),
                        "virtual_balance": virtual_balance,
                        "frozen_balance": frozen_balance,
                        "total_gems_value": gems_value,
                        "total_balance": total_balance,
                        "expected_total": expected_total,
                        "difference": total_balance - expected_total
                    })
            
            if calculation_errors:
                self.log_result("TOTAL Balance Calculation", False, 
                              f"Found {len(calculation_errors)} calculation errors",
                              {"errors": calculation_errors[:3]})  # Show first 3 errors
                return False
            
            self.log_result("TOTAL Balance Calculation", True, 
                          f"All {len(users)} users have correct total_balance calculation")
            return True
            
        except Exception as e:
            self.log_result("TOTAL Balance Calculation", False, f"Error: {str(e)}")
            return False

    def test_user_deduplication(self) -> bool:
        """Test that there are no duplicate users in the results"""
        try:
            params = {
                "sort_by": "total",
                "sort_order": "desc",
                "page": 1,
                "per_page": 50  # Get more users to check for duplicates
            }
            
            response = requests.get(f"{BASE_URL}/admin/users", 
                                  headers=self.get_admin_headers(), 
                                  params=params)
            
            if response.status_code != 200:
                self.log_result("User Deduplication", False, 
                              f"API request failed: {response.status_code}")
                return False
            
            data = response.json()
            users = data.get("users", [])
            
            if not users:
                self.log_result("User Deduplication", False, "No users returned")
                return False
            
            # Check for duplicate usernames
            usernames = [user.get("username") for user in users]
            unique_usernames = set(usernames)
            
            if len(usernames) != len(unique_usernames):
                duplicates = []
                seen = set()
                for username in usernames:
                    if username in seen:
                        duplicates.append(username)
                    seen.add(username)
                
                self.log_result("User Deduplication", False, 
                              f"Found duplicate usernames: {duplicates}")
                return False
            
            # Check for duplicate user IDs
            user_ids = [user.get("id") for user in users]
            unique_user_ids = set(user_ids)
            
            if len(user_ids) != len(unique_user_ids):
                self.log_result("User Deduplication", False, 
                              "Found duplicate user IDs")
                return False
            
            self.log_result("User Deduplication", True, 
                          f"No duplicates found in {len(users)} users")
            return True
            
        except Exception as e:
            self.log_result("User Deduplication", False, f"Error: {str(e)}")
            return False

    def test_pagination_with_sorting(self) -> bool:
        """Test that pagination works correctly with TOTAL sorting"""
        try:
            # Get first page
            params1 = {
                "sort_by": "total",
                "sort_order": "desc",
                "page": 1,
                "per_page": 5
            }
            
            response1 = requests.get(f"{BASE_URL}/admin/users", 
                                   headers=self.get_admin_headers(), 
                                   params=params1)
            
            if response1.status_code != 200:
                self.log_result("Pagination with Sorting", False, 
                              f"First page request failed: {response1.status_code}")
                return False
            
            data1 = response1.json()
            users1 = data1.get("users", [])
            # Check for different pagination field names
            pagination1 = data1.get("pagination", {})
            if not pagination1:
                # Try alternative pagination structure
                pagination1 = {
                    "current_page": data1.get("page"),
                    "total_pages": data1.get("pages"),
                    "per_page": data1.get("limit"),
                    "total_items": data1.get("total")
                }
            
            # Get second page
            params2 = {
                "sort_by": "total",
                "sort_order": "desc",
                "page": 2,
                "per_page": 5
            }
            
            response2 = requests.get(f"{BASE_URL}/admin/users", 
                                   headers=self.get_admin_headers(), 
                                   params=params2)
            
            if response2.status_code != 200:
                self.log_result("Pagination with Sorting", False, 
                              f"Second page request failed: {response2.status_code}")
                return False
            
            data2 = response2.json()
            users2 = data2.get("users", [])
            
            if not users1 or not users2:
                self.log_result("Pagination with Sorting", False, 
                              "Not enough users for pagination test")
                return False
            
            # Check that first page has higher total_balance than second page
            last_total_page1 = float(users1[-1].get("total_balance", 0))
            first_total_page2 = float(users2[0].get("total_balance", 0))
            
            if last_total_page1 < first_total_page2:
                self.log_result("Pagination with Sorting", False, 
                              f"Pagination order incorrect: page1_last={last_total_page1}, page2_first={first_total_page2}")
                return False
            
            # Check pagination metadata
            current_page = pagination1.get("current_page") or pagination1.get("page")
            if current_page != 1:
                self.log_result("Pagination with Sorting", False, 
                              f"Incorrect current_page: {current_page}")
                return False
            
            self.log_result("Pagination with Sorting", True, 
                          f"Pagination works correctly with sorting",
                          {"page1_last_total": last_total_page1,
                           "page2_first_total": first_total_page2,
                           "pagination": pagination1})
            return True
            
        except Exception as e:
            self.log_result("Pagination with Sorting", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all TOTAL sorting tests"""
        print("🚀 STARTING TOTAL COLUMN SORTING TESTS")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed.")
            return
        
        # Run tests
        tests = [
            self.test_total_sorting_asc,
            self.test_total_sorting_desc,
            self.test_total_balance_calculation,
            self.test_user_deduplication,
            self.test_pagination_with_sorting
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # Summary
        print("=" * 60)
        print(f"📊 TOTAL SORTING TEST SUMMARY")
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TOTAL SORTING TESTS PASSED!")
            print("✅ TOTAL column sorting is working correctly")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("❌ TOTAL column sorting needs attention")
        
        return passed == total

def main():
    """Main test execution"""
    tester = TotalSortingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSION: TOTAL column sorting is FULLY FUNCTIONAL")
        sys.exit(0)
    else:
        print("\n🚨 CONCLUSION: TOTAL column sorting has ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()