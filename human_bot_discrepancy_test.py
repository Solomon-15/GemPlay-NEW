#!/usr/bin/env python3
"""
DETAILED INVESTIGATION: Human-Bot Bet Count Discrepancy
GOAL: Find where exactly the bets are lost between 121 (admin panel) and 45 (lobby)
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotDiscrepancyInvestigator:
    def __init__(self):
        self.admin_token = None
        self.investigation_results = {}
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin to access admin endpoints"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                print("✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return False
    
    def get_admin_headers(self) -> Dict[str, str]:
        """Get headers with admin authorization"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def investigate_admin_panel_source(self) -> Dict[str, Any]:
        """1. Check admin panel data source - GET /api/admin/human-bots/stats"""
        print("\n🔍 STEP 1: INVESTIGATING ADMIN PANEL DATA SOURCE")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/stats",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                total_bets = data.get("total_bets", 0)
                
                print(f"✅ Admin Panel Stats API Response:")
                print(f"   - total_bots: {data.get('total_bots', 'N/A')}")
                print(f"   - active_bots: {data.get('active_bots', 'N/A')}")
                print(f"   - total_bets: {total_bets} ⭐ (THIS IS THE 121 VALUE)")
                print(f"   - total_games_24h: {data.get('total_games_24h', 'N/A')}")
                print(f"   - total_revenue_24h: ${data.get('total_revenue_24h', 'N/A')}")
                
                self.investigation_results["admin_panel"] = {
                    "status": "success",
                    "total_bets": total_bets,
                    "raw_data": data
                }
                
                return data
            else:
                print(f"❌ Admin stats API failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.investigation_results["admin_panel"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                return {}
                
        except Exception as e:
            print(f"❌ Admin stats API error: {e}")
            self.investigation_results["admin_panel"] = {
                "status": "error",
                "error": str(e)
            }
            return {}
    
    def investigate_lobby_source(self) -> Dict[str, Any]:
        """2. Check lobby data source - GET /api/games/available"""
        print("\n🔍 STEP 2: INVESTIGATING LOBBY DATA SOURCE")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{BASE_URL}/games/available",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                games = response.json()  # API returns list directly
                
                # Count Human-bot games
                human_bot_games = []
                regular_games = []
                
                for game in games:
                    is_human_bot = game.get("is_human_bot", False)
                    
                    if is_human_bot:
                        human_bot_games.append(game)
                    else:
                        regular_games.append(game)
                
                print(f"✅ Lobby Available Games API Response:")
                print(f"   - Total available games: {len(games)}")
                print(f"   - Human-bot games: {len(human_bot_games)} ⭐ (THIS IS THE 45 VALUE)")
                print(f"   - Regular games: {len(regular_games)}")
                
                # Show sample Human-bot games
                print(f"\n📋 Sample Human-bot games (first 5):")
                for i, game in enumerate(human_bot_games[:5]):
                    creator = game.get("creator", {})
                    print(f"   {i+1}. Game ID: {game.get('game_id', 'N/A')[:8]}...")
                    print(f"      Creator: {creator.get('username', 'N/A')} (ID: {creator.get('id', 'N/A')[:8]}...)")
                    print(f"      Is Human Bot: {game.get('is_human_bot', 'N/A')}")
                    print(f"      Bet Amount: ${game.get('bet_amount', 'N/A')}")
                    print(f"      Time Remaining: {game.get('time_remaining_hours', 'N/A'):.1f}h")
                
                self.investigation_results["lobby"] = {
                    "status": "success",
                    "total_games": len(games),
                    "human_bot_games": len(human_bot_games),
                    "regular_games": len(regular_games),
                    "human_bot_game_ids": [g.get("game_id") for g in human_bot_games],
                    "raw_data": {"games": games}
                }
                
                return {"games": games}
            else:
                print(f"❌ Lobby available games API failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.investigation_results["lobby"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                return {}
                
        except Exception as e:
            print(f"❌ Lobby available games API error: {e}")
            self.investigation_results["lobby"] = {
                "status": "error",
                "error": str(e)
            }
            return {}
    
    def investigate_database_direct_count(self) -> Dict[str, Any]:
        """3. Compare games directly from database using Human-bot list API"""
        print("\n🔍 STEP 3: INVESTIGATING DATABASE DIRECT COUNT")
        print("=" * 60)
        
        try:
            # Get all Human-bots first
            response = requests.get(
                f"{BASE_URL}/admin/human-bots",
                headers=self.get_admin_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get Human-bots list: {response.status_code}")
                return {}
            
            bots_data = response.json()
            human_bots = bots_data.get("bots", [])
            
            print(f"✅ Found {len(human_bots)} Human-bots in system")
            
            # Get active bets for each Human-bot
            total_active_bets = 0
            bot_bet_details = []
            
            for bot in human_bots:
                bot_id = bot.get("id")
                bot_name = bot.get("name", "Unknown")
                is_active = bot.get("is_active", False)
                
                # Get active bets for this bot
                try:
                    active_bets_response = requests.get(
                        f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                        headers=self.get_admin_headers()
                    )
                    
                    if active_bets_response.status_code == 200:
                        active_bets_data = active_bets_response.json()
                        active_bets = active_bets_data.get("active_bets", [])
                        active_count = len(active_bets)
                        total_active_bets += active_count
                        
                        bot_bet_details.append({
                            "bot_id": bot_id,
                            "bot_name": bot_name,
                            "is_active": is_active,
                            "active_bets_count": active_count,
                            "bet_limit": bot.get("bet_limit", "N/A"),
                            "active_bets_from_list": bot.get("active_bets_count", "N/A")
                        })
                        
                        print(f"   📊 {bot_name}: {active_count} active bets (limit: {bot.get('bet_limit', 'N/A')}, active: {is_active})")
                    else:
                        print(f"   ❌ Failed to get active bets for {bot_name}: {active_bets_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error getting active bets for {bot_name}: {e}")
            
            print(f"\n📊 DIRECT DATABASE COUNT SUMMARY:")
            print(f"   - Total Human-bots: {len(human_bots)}")
            print(f"   - Total active bets (via active-bets API): {total_active_bets}")
            print(f"   - Active bots: {sum(1 for bot in human_bots if bot.get('is_active', False))}")
            
            self.investigation_results["database_direct"] = {
                "status": "success",
                "total_human_bots": len(human_bots),
                "total_active_bets": total_active_bets,
                "bot_details": bot_bet_details
            }
            
            return {
                "total_human_bots": len(human_bots),
                "total_active_bets": total_active_bets,
                "bot_details": bot_bet_details
            }
            
        except Exception as e:
            print(f"❌ Database direct count error: {e}")
            self.investigation_results["database_direct"] = {
                "status": "error",
                "error": str(e)
            }
            return {}
    
    def find_lost_games(self) -> None:
        """4. Find the lost games - identify discrepancies"""
        print("\n🔍 STEP 4: FINDING LOST GAMES")
        print("=" * 60)
        
        admin_total = self.investigation_results.get("admin_panel", {}).get("total_bets", 0)
        lobby_total = self.investigation_results.get("lobby", {}).get("human_bot_games", 0)
        database_total = self.investigation_results.get("database_direct", {}).get("total_active_bets", 0)
        
        print(f"📊 COMPARISON SUMMARY:")
        print(f"   - Admin Panel total_bets: {admin_total}")
        print(f"   - Lobby Human-bot games: {lobby_total}")
        print(f"   - Database direct count: {database_total}")
        
        discrepancy_admin_lobby = admin_total - lobby_total
        discrepancy_admin_db = admin_total - database_total
        discrepancy_lobby_db = lobby_total - database_total
        
        print(f"\n🔍 DISCREPANCIES:")
        print(f"   - Admin vs Lobby: {discrepancy_admin_lobby} games missing from lobby")
        print(f"   - Admin vs Database: {discrepancy_admin_db} games difference")
        print(f"   - Lobby vs Database: {discrepancy_lobby_db} games difference")
        
        if discrepancy_admin_lobby > 0:
            print(f"\n⚠️  CRITICAL FINDING: {discrepancy_admin_lobby} games are missing from the lobby!")
            print(f"   This explains why users see fewer available bets than the admin panel reports.")
        
        # Analyze possible causes
        print(f"\n🔍 POSSIBLE CAUSES ANALYSIS:")
        
        # Check if lobby games have different statuses
        lobby_games = self.investigation_results.get("lobby", {}).get("raw_data", {}).get("games", [])
        if lobby_games:
            statuses = {}
            for game in lobby_games:
                status = game.get("status", "unknown")
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"   - Lobby game statuses: {statuses}")
            if "WAITING" not in statuses or statuses.get("WAITING", 0) != lobby_total:
                print(f"   ⚠️  Issue: Not all lobby games have WAITING status!")
        
        # Check bot activity
        bot_details = self.investigation_results.get("database_direct", {}).get("bot_details", [])
        active_bots = sum(1 for bot in bot_details if bot.get("is_active", False))
        inactive_bots = len(bot_details) - active_bots
        
        print(f"   - Active Human-bots: {active_bots}")
        print(f"   - Inactive Human-bots: {inactive_bots}")
        
        if inactive_bots > 0:
            print(f"   ⚠️  Possible cause: Inactive bots may have games counted in admin but not shown in lobby")
    
    def check_filtering_logic(self) -> None:
        """5. Check filtering logic - how lobby determines Human-bot games"""
        print("\n🔍 STEP 5: CHECKING FILTERING LOGIC")
        print("=" * 60)
        
        print("🔍 Analyzing how lobby identifies Human-bot games:")
        
        lobby_games = self.investigation_results.get("lobby", {}).get("raw_data", {}).get("games", [])
        
        if not lobby_games:
            print("❌ No lobby games data available for analysis")
            return
        
        # Analyze game properties
        human_bot_identifiers = {
            "creator_type_human_bot": 0,
            "is_bot_game_true": 0,
            "bot_type_human": 0,
            "both_flags": 0
        }
        
        for game in lobby_games:
            creator_type = game.get("creator_type")
            is_bot_game = game.get("is_bot_game", False)
            bot_type = game.get("bot_type")
            
            if creator_type == "human_bot":
                human_bot_identifiers["creator_type_human_bot"] += 1
            
            if is_bot_game:
                human_bot_identifiers["is_bot_game_true"] += 1
            
            if bot_type == "HUMAN":
                human_bot_identifiers["bot_type_human"] += 1
            
            if creator_type == "human_bot" and is_bot_game and bot_type == "HUMAN":
                human_bot_identifiers["both_flags"] += 1
        
        print(f"📊 Human-bot identification analysis:")
        print(f"   - Games with creator_type='human_bot': {human_bot_identifiers['creator_type_human_bot']}")
        print(f"   - Games with is_bot_game=true: {human_bot_identifiers['is_bot_game_true']}")
        print(f"   - Games with bot_type='HUMAN': {human_bot_identifiers['bot_type_human']}")
        print(f"   - Games with all three flags: {human_bot_identifiers['both_flags']}")
        
        # Check for inconsistencies
        lobby_human_bot_count = self.investigation_results.get("lobby", {}).get("human_bot_games", 0)
        
        if human_bot_identifiers["creator_type_human_bot"] != lobby_human_bot_count:
            print(f"⚠️  Inconsistency: creator_type count ({human_bot_identifiers['creator_type_human_bot']}) != lobby count ({lobby_human_bot_count})")
        
        if human_bot_identifiers["is_bot_game_true"] != lobby_human_bot_count:
            print(f"⚠️  Inconsistency: is_bot_game count ({human_bot_identifiers['is_bot_game_true']}) != lobby count ({lobby_human_bot_count})")
        
        if human_bot_identifiers["bot_type_human"] != lobby_human_bot_count:
            print(f"⚠️  Inconsistency: bot_type count ({human_bot_identifiers['bot_type_human']}) != lobby count ({lobby_human_bot_count})")
    
    def generate_final_report(self) -> None:
        """Generate final investigation report"""
        print("\n" + "=" * 80)
        print("🎯 FINAL INVESTIGATION REPORT")
        print("=" * 80)
        
        admin_total = self.investigation_results.get("admin_panel", {}).get("total_bets", 0)
        lobby_total = self.investigation_results.get("lobby", {}).get("human_bot_games", 0)
        database_total = self.investigation_results.get("database_direct", {}).get("total_active_bets", 0)
        
        print(f"📊 DATA SOURCES SUMMARY:")
        print(f"   1. Admin Panel (/api/admin/human-bots/stats): {admin_total} total_bets")
        print(f"   2. Lobby (/api/games/available): {lobby_total} Human-bot games")
        print(f"   3. Database Direct Count: {database_total} active bets")
        
        discrepancy = admin_total - lobby_total
        
        if discrepancy > 0:
            print(f"\n🚨 CRITICAL DISCREPANCY FOUND:")
            print(f"   - {discrepancy} games are missing from the lobby display")
            print(f"   - Users see {lobby_total} available Human-bot bets instead of {admin_total}")
            
            print(f"\n🔍 ROOT CAUSE ANALYSIS:")
            
            # Determine most likely cause
            if database_total == lobby_total:
                print(f"   ✅ Database direct count matches lobby count ({database_total})")
                print(f"   🎯 LIKELY CAUSE: Admin panel total_bets includes non-WAITING games")
                print(f"      - Admin stats may count ALL Human-bot games (including ACTIVE, COMPLETED)")
                print(f"      - Lobby only shows WAITING games (available for joining)")
                
            elif database_total == admin_total:
                print(f"   ✅ Database direct count matches admin count ({database_total})")
                print(f"   🎯 LIKELY CAUSE: Lobby filtering logic excludes some valid games")
                print(f"      - Check game status filtering in lobby")
                print(f"      - Check Human-bot identification logic")
                
            else:
                print(f"   ⚠️  All three counts are different - complex issue")
                print(f"   🎯 LIKELY CAUSE: Multiple issues in data counting/filtering")
        
        else:
            print(f"\n✅ NO DISCREPANCY FOUND:")
            print(f"   All data sources show consistent counts")
        
        print(f"\n📋 RECOMMENDATIONS:")
        if discrepancy > 0:
            print(f"   1. Verify admin stats query - ensure it only counts WAITING games")
            print(f"   2. Check lobby filtering logic for Human-bot identification")
            print(f"   3. Investigate game status transitions and cleanup")
            print(f"   4. Add logging to track game lifecycle and status changes")
        else:
            print(f"   1. Monitor counts regularly to ensure consistency")
            print(f"   2. Add automated alerts for significant discrepancies")
        
        print(f"\n🎯 INVESTIGATION COMPLETE")
        print("=" * 80)
    
    def run_full_investigation(self) -> bool:
        """Run the complete investigation"""
        print("🚀 STARTING HUMAN-BOT BET COUNT DISCREPANCY INVESTIGATION")
        print("=" * 80)
        print("GOAL: Find where exactly the bets are lost between admin panel and lobby")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            return False
        
        # Run all investigation steps
        self.investigate_admin_panel_source()
        self.investigate_lobby_source()
        self.investigate_database_direct_count()
        self.find_lost_games()
        self.check_filtering_logic()
        self.generate_final_report()
        
        return True

def main():
    """Main function to run the investigation"""
    investigator = HumanBotDiscrepancyInvestigator()
    
    try:
        success = investigator.run_full_investigation()
        if success:
            print("\n✅ Investigation completed successfully")
            return 0
        else:
            print("\n❌ Investigation failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Investigation failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())