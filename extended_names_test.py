#!/usr/bin/env python3
"""
Extended Human-Bot Names Integration Testing
Test multiple bot creations to verify name patterns
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class ExtendedHumanBotNamesTest:
    def __init__(self):
        self.admin_token = None
        self.created_bot_ids = []
        
    def admin_login(self) -> bool:
        """Login as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                print("✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}")
            return False

    def create_multiple_bots(self, count: int = 5) -> List[str]:
        """Create multiple Human-bots to test name patterns"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            created_names = []
            
            for i in range(count):
                bulk_request = {
                    "count": 1,
                    "character": "BALANCED",
                    "min_bet_range": [10.0, 20.0],
                    "max_bet_range": [50.0, 100.0],
                    "bet_limit_range": [12, 12],
                    "win_percentage": 40.0,
                    "loss_percentage": 40.0,
                    "draw_percentage": 20.0,
                    "delay_range": [30, 120],
                    "use_commit_reveal": True,
                    "logging_level": "INFO"
                }
                
                response = requests.post(f"{BASE_URL}/admin/human-bots/bulk-create", headers=headers, json=bulk_request)
                
                if response.status_code == 200:
                    data = response.json()
                    created_bots = data.get("created_bots", [])
                    
                    if created_bots:
                        bot = created_bots[0]
                        bot_id = bot.get("id")
                        bot_name = bot.get("name")
                        
                        if bot_id:
                            self.created_bot_ids.append(bot_id)
                        if bot_name:
                            created_names.append(bot_name)
                            print(f"✅ Created bot #{i+1}: {bot_name}")
                        
                        # Small delay between creations
                        time.sleep(0.5)
                else:
                    print(f"❌ Failed to create bot #{i+1}: {response.status_code}")
            
            return created_names
            
        except Exception as e:
            print(f"❌ Error creating bots: {str(e)}")
            return []

    def analyze_name_patterns(self, names: List[str]):
        """Analyze the patterns in created bot names"""
        print(f"\n📊 ANALYZING {len(names)} CREATED BOT NAMES:")
        print("=" * 50)
        
        old_patterns = ["Silnyy", "Umnyy", "Krasivyy", "Bystryy", "Smellyy"]
        names_with_old_patterns = []
        
        for name in names:
            has_old_pattern = any(pattern in name for pattern in old_patterns)
            if has_old_pattern:
                matching_patterns = [pattern for pattern in old_patterns if pattern in name]
                names_with_old_patterns.append((name, matching_patterns))
                print(f"⚠️  {name} - Contains old pattern: {matching_patterns}")
            else:
                print(f"✅ {name} - Clean name (no old patterns)")
        
        print(f"\n📈 SUMMARY:")
        print(f"Total names created: {len(names)}")
        print(f"Names with old patterns: {len(names_with_old_patterns)}")
        print(f"Clean names: {len(names) - len(names_with_old_patterns)}")
        
        if names_with_old_patterns:
            print(f"\n⚠️  PROBLEMATIC NAMES:")
            for name, patterns in names_with_old_patterns:
                print(f"   - {name} (contains: {', '.join(patterns)})")

    def cleanup_created_bots(self):
        """Clean up created test bots"""
        if not self.created_bot_ids:
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            deleted_count = 0
            
            for bot_id in self.created_bot_ids:
                try:
                    response = requests.delete(f"{BASE_URL}/admin/human-bots/{bot_id}", headers=headers)
                    if response.status_code == 200:
                        deleted_count += 1
                except Exception as e:
                    print(f"Warning: Failed to delete bot {bot_id}: {str(e)}")
            
            print(f"🧹 Cleaned up {deleted_count}/{len(self.created_bot_ids)} test bots")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")

    def run_test(self):
        """Run the extended test"""
        print("🚀 EXTENDED HUMAN-BOT NAMES PATTERN TESTING")
        print("=" * 60)
        
        try:
            # Login
            if not self.admin_login():
                return False
            
            # Create multiple bots
            created_names = self.create_multiple_bots(5)
            
            if not created_names:
                print("❌ No bots were created. Cannot analyze patterns.")
                return False
            
            # Analyze patterns
            self.analyze_name_patterns(created_names)
            
            # Cleanup
            self.cleanup_created_bots()
            
            return True
            
        except Exception as e:
            print(f"❌ Test error: {str(e)}")
            return False

def main():
    test = ExtendedHumanBotNamesTest()
    try:
        test.run_test()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        test.cleanup_created_bots()
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        test.cleanup_created_bots()

if __name__ == "__main__":
    main()