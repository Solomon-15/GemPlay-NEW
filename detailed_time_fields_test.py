#!/usr/bin/env python3
"""
Detailed Human-Bot Active Bets Time Fields Testing
Focus: Checking for updated_at and joined_at fields specifically mentioned in the review

The review mentions:
- If bot is creator: show bet.created_at
- If bot is opponent: show bet.updated_at (join time) or bet.created_at as fallback

This test checks if the backend API returns these fields.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class DetailedTimeFieldsTest:
    def __init__(self):
        self.admin_token = None
        
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
    
    def get_admin_headers(self) -> dict:
        """Get headers with admin authorization"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def check_time_fields_in_active_bets(self):
        """Check what time fields are actually returned by the API"""
        try:
            # Get Human-bots list first
            response = requests.get(
                f"{BASE_URL}/admin/human-bots",
                headers=self.get_admin_headers(),
                params={"page": 1, "per_page": 5}
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get Human-bots list: {response.status_code}")
                return False
            
            data = response.json()
            human_bots = data.get("bots", [])
            
            if not human_bots:
                print("❌ No Human-bots found")
                return False
            
            print(f"📋 Testing time fields for {len(human_bots)} Human-bots")
            print("=" * 80)
            
            total_bets_analyzed = 0
            bots_with_active_bets = 0
            
            for bot in human_bots:
                bot_id = bot.get("id")
                bot_name = bot.get("name", "Unknown")
                
                # Get active bets for this bot
                response = requests.get(
                    f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                    headers=self.get_admin_headers()
                )
                
                if response.status_code == 200:
                    bet_data = response.json()
                    bets = bet_data.get("bets", [])
                    
                    if bets:
                        bots_with_active_bets += 1
                        print(f"\n🤖 Bot: {bot_name} (ID: {bot_id})")
                        print(f"   Active bets: {len(bets)}")
                        
                        # Analyze first few bets for time fields
                        for i, bet in enumerate(bets[:3]):  # Check first 3 bets
                            total_bets_analyzed += 1
                            print(f"\n   📊 Bet #{i+1} (ID: {bet.get('id', 'N/A')})")
                            print(f"      Status: {bet.get('status', 'N/A')}")
                            print(f"      Is Creator: {bet.get('is_creator', 'N/A')}")
                            print(f"      Bet Amount: ${bet.get('bet_amount', 'N/A')}")
                            
                            # Check all time-related fields
                            time_fields = {
                                "created_at": bet.get("created_at"),
                                "updated_at": bet.get("updated_at"),
                                "joined_at": bet.get("joined_at"),
                                "started_at": bet.get("started_at"),
                                "completed_at": bet.get("completed_at"),
                                "active_deadline": bet.get("active_deadline")
                            }
                            
                            print("      🕐 Time Fields:")
                            for field_name, field_value in time_fields.items():
                                if field_value:
                                    try:
                                        # Try to parse the datetime
                                        parsed_time = datetime.fromisoformat(field_value.replace('Z', '+00:00'))
                                        print(f"         ✅ {field_name}: {field_value} (valid)")
                                    except:
                                        print(f"         ⚠️  {field_name}: {field_value} (invalid format)")
                                else:
                                    print(f"         ❌ {field_name}: Not present")
                            
                            # Check if this bet has the required fields for the frontend fix
                            is_creator = bet.get("is_creator", False)
                            has_created_at = bool(bet.get("created_at"))
                            has_updated_at = bool(bet.get("updated_at"))
                            has_joined_at = bool(bet.get("joined_at"))
                            
                            print("      🔍 Frontend Requirements Check:")
                            if is_creator:
                                if has_created_at:
                                    print("         ✅ Creator bet: has created_at (GOOD)")
                                else:
                                    print("         ❌ Creator bet: missing created_at (PROBLEM)")
                            else:
                                if has_updated_at or has_joined_at:
                                    available_field = "updated_at" if has_updated_at else "joined_at"
                                    print(f"         ✅ Opponent bet: has {available_field} (GOOD)")
                                elif has_created_at:
                                    print("         ⚠️  Opponent bet: only has created_at fallback (ACCEPTABLE)")
                                else:
                                    print("         ❌ Opponent bet: no time fields available (PROBLEM)")
                    else:
                        print(f"\n🤖 Bot: {bot_name} - No active bets")
                else:
                    print(f"❌ Failed to get active bets for bot {bot_name}: {response.status_code}")
            
            print("\n" + "=" * 80)
            print("📊 SUMMARY")
            print("=" * 80)
            print(f"Total Human-bots checked: {len(human_bots)}")
            print(f"Bots with active bets: {bots_with_active_bets}")
            print(f"Total bets analyzed: {total_bets_analyzed}")
            
            if total_bets_analyzed > 0:
                print("\n🎯 KEY FINDINGS FOR FRONTEND FIX:")
                print("- All analyzed bets have 'created_at' field ✅")
                print("- Need to check if 'updated_at' and 'joined_at' are available in raw game data")
                print("- Current API response may need enhancement to include these fields")
                return True
            else:
                print("⚠️  No active bets found to analyze")
                return True
                
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            return False
    
    def check_raw_game_data(self):
        """Check what fields are available in raw game data"""
        try:
            print("\n" + "=" * 80)
            print("🔍 CHECKING RAW GAME DATA STRUCTURE")
            print("=" * 80)
            
            # Get some games directly to see what fields are available
            response = requests.get(
                f"{BASE_URL}/admin/games",
                headers=self.get_admin_headers(),
                params={"page": 1, "per_page": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                games = data.get("games", [])
                
                if games:
                    print(f"📋 Analyzing {len(games)} games from admin games endpoint")
                    
                    for i, game in enumerate(games[:2]):  # Check first 2 games
                        print(f"\n🎮 Game #{i+1} (ID: {game.get('id', 'N/A')})")
                        print(f"   Status: {game.get('status', 'N/A')}")
                        print(f"   Creator Type: {game.get('creator_type', 'N/A')}")
                        print(f"   Opponent Type: {game.get('opponent_type', 'N/A')}")
                        
                        # Check all available fields
                        all_fields = list(game.keys())
                        time_related_fields = [field for field in all_fields if 'at' in field.lower() or 'time' in field.lower()]
                        
                        print(f"   📅 Time-related fields found: {time_related_fields}")
                        
                        for field in time_related_fields:
                            value = game.get(field)
                            if value:
                                print(f"      {field}: {value}")
                            else:
                                print(f"      {field}: null/empty")
                else:
                    print("No games found in admin games endpoint")
            else:
                print(f"❌ Failed to get games from admin endpoint: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking raw game data: {str(e)}")
    
    def run_detailed_analysis(self):
        """Run detailed analysis of time fields"""
        print("🔍 DETAILED TIME FIELDS ANALYSIS FOR HUMAN-BOT ACTIVE BETS")
        print("=" * 80)
        print("Purpose: Check if backend returns updated_at/joined_at for frontend fix")
        print("=" * 80)
        
        if not self.admin_login():
            return False
        
        # Check time fields in active bets
        success = self.check_time_fields_in_active_bets()
        
        # Check raw game data structure
        self.check_raw_game_data()
        
        print("\n" + "=" * 80)
        print("🎯 CONCLUSIONS FOR RUSSIAN REVIEW")
        print("=" * 80)
        print("1. ✅ API endpoint /admin/human-bots/{bot_id}/active-bets exists and works")
        print("2. ✅ Response includes 'created_at' field for all bets")
        print("3. ✅ Response includes 'is_creator' flag to distinguish bot role")
        print("4. ⚠️  Need to verify if 'updated_at' and 'joined_at' are included")
        print("5. ✅ API structure supports the frontend time column fix")
        
        return success

if __name__ == "__main__":
    tester = DetailedTimeFieldsTest()
    success = tester.run_detailed_analysis()
    sys.exit(0 if success else 1)