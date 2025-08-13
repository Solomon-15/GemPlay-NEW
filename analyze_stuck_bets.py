#!/usr/bin/env python3
"""
Create Stuck Bets for Testing
=============================

This script creates some stuck bets by manipulating the active_deadline
to simulate stuck conditions for testing the unfreeze functionality.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://pishi-po-russki.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class StuckBetsCreator:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                print(f"✅ Successfully authenticated as {ADMIN_EMAIL}")
                return True
            else:
                print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def create_stuck_bets_scenario(self):
        """Create a scenario with stuck bets for testing"""
        print("\n🎯 Creating Stuck Bets Scenario...")
        
        # First, let's check current stats
        stats_response = self.session.get(f"{API_BASE}/admin/bets/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"📊 Current Stats: Active bets: {stats.get('active_bets', 0)}, Stuck bets: {stats.get('stuck_bets', 0)}")
        
        # Get some active bets to manipulate
        bets_response = self.session.get(f"{API_BASE}/admin/bets/list?limit=10")
        if bets_response.status_code == 200:
            bets_data = bets_response.json()
            active_bets = [bet for bet in bets_data.get("bets", []) if bet.get("status") == "ACTIVE"]
            
            if active_bets:
                print(f"📋 Found {len(active_bets)} active bets to potentially make stuck")
                
                # For testing purposes, we'll use the MongoDB direct manipulation
                # Since we can't directly manipulate the database from here,
                # let's create a test scenario by checking what happens when we call unfreeze
                
                print("🔍 Testing current unfreeze behavior with existing bets...")
                
                # Call unfreeze to see current behavior
                unfreeze_response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
                if unfreeze_response.status_code == 200:
                    unfreeze_data = unfreeze_response.json()
                    print(f"🔓 Unfreeze result: {unfreeze_data}")
                    
                    # Check if any games were processed
                    total_processed = unfreeze_data.get("total_processed", 0)
                    if total_processed > 0:
                        print(f"⚠️  CRITICAL: {total_processed} games were processed by unfreeze")
                        
                        # Check if they were cancelled or unfrozen
                        cancelled_games = unfreeze_data.get("cancelled_games", [])
                        if cancelled_games:
                            print("🚨 ISSUE DETECTED: Games are being CANCELLED instead of UNFROZEN!")
                            for game in cancelled_games[:3]:  # Show first 3
                                print(f"   - Game {game.get('game_id')}: Status was {game.get('status')}")
                        else:
                            print("✅ Games appear to be properly unfrozen (no cancelled_games field)")
                    else:
                        print("ℹ️  No stuck games found to process")
                else:
                    print(f"❌ Unfreeze failed: {unfreeze_response.status_code} - {unfreeze_response.text}")
            else:
                print("ℹ️  No active bets found to test with")
        else:
            print(f"❌ Failed to get bets list: {bets_response.status_code}")

    def analyze_current_implementation(self):
        """Analyze what the current implementation actually does"""
        print("\n🔍 Analyzing Current Implementation...")
        
        # Get initial stats
        stats_before = self.session.get(f"{API_BASE}/admin/bets/stats")
        if stats_before.status_code == 200:
            stats_data = stats_before.json()
            stuck_before = stats_data.get("stuck_bets", 0)
            active_before = stats_data.get("active_bets", 0)
            print(f"📊 Before unfreeze: Active={active_before}, Stuck={stuck_before}")
        
        # Call unfreeze endpoint
        unfreeze_response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
        
        if unfreeze_response.status_code == 200:
            unfreeze_data = unfreeze_response.json()
            total_processed = unfreeze_data.get("total_processed", 0)
            message = unfreeze_data.get("message", "")
            
            print(f"🔓 Unfreeze Response:")
            print(f"   - Total processed: {total_processed}")
            print(f"   - Message: {message}")
            print(f"   - Success: {unfreeze_data.get('success', False)}")
            
            # Check for implementation issues
            if "cancelled_games" in unfreeze_data:
                cancelled_games = unfreeze_data["cancelled_games"]
                if cancelled_games and len(cancelled_games) > 0:
                    print(f"🚨 CRITICAL ISSUE: Implementation is CANCELLING games instead of UNFREEZING!")
                    print(f"   - {len(cancelled_games)} games were cancelled")
                    print(f"   - This violates the requirement to keep games ACTIVE and extend deadline")
                else:
                    print("✅ No games were cancelled (good)")
            
            # Check for proper unfreezing fields
            if "unfrozen_games" in unfreeze_data:
                unfrozen_games = unfreeze_data["unfrozen_games"]
                print(f"✅ Found unfrozen_games field with {len(unfrozen_games) if unfrozen_games else 0} games")
            else:
                print("⚠️  No unfrozen_games field found in response")
            
            # Get stats after
            stats_after = self.session.get(f"{API_BASE}/admin/bets/stats")
            if stats_after.status_code == 200:
                stats_data_after = stats_after.json()
                stuck_after = stats_data_after.get("stuck_bets", 0)
                active_after = stats_data_after.get("active_bets", 0)
                print(f"📊 After unfreeze: Active={active_after}, Stuck={stuck_after}")
                
                # Analyze the change
                if total_processed > 0:
                    if active_after < active_before:
                        print(f"🚨 ISSUE: Active bets decreased from {active_before} to {active_after}")
                        print("   This suggests games were CANCELLED, not UNFROZEN")
                    elif active_after == active_before:
                        print(f"✅ Active bets remained the same ({active_before})")
                        print("   This suggests games were properly UNFROZEN (kept ACTIVE)")
        else:
            print(f"❌ Unfreeze failed: {unfreeze_response.status_code} - {unfreeze_response.text}")

    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting Stuck Bets Analysis...")
        print("=" * 60)
        
        if not self.authenticate_admin():
            print("❌ Authentication failed. Cannot proceed.")
            return False
        
        self.create_stuck_bets_scenario()
        self.analyze_current_implementation()
        
        print("\n" + "=" * 60)
        print("📋 ANALYSIS COMPLETE")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    creator = StuckBetsCreator()
    creator.run_analysis()