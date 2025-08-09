#!/usr/bin/env python3
"""
Диагностика количества старых ставок и проверка необходимости очистки базы данных
Race Condition Diagnostic Test - Russian Review

КОНТЕКСТ: Race condition все еще не исправлена. У некоторых ботов сотни активных ставок при лимите 12.

ДИАГНОСТИЧЕСКИЕ ЗАПРОСЫ:
1. Проверить старые WAITING ставки - сколько всего, самые старые по датам, есть ли старше 24 часов
2. Проверить статистику по ботам с нарушениями (Bot#1, Bot#2, Updated_Bot_1754524221)
3. Проверить общую статистику игр по статусам (WAITING, ACTIVE, COMPLETED, CANCELLED)
4. Проверить логи automation - есть ли "Cycle games limit reached", работает ли maintain_all_bots_active_bets()

ЦЕЛЬ: Понять источник избыточных ставок - старые не удаленные ставки или продолжающееся создание новых
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import pytz

# Configuration
BASE_URL = "https://9dac94ee-f135-41d4-9528-71a64685f265.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test results tracking
diagnostic_results = {
    "total_checks": 0,
    "critical_issues": 0,
    "warnings": 0,
    "checks": []
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

def print_diagnostic_result(check_name: str, status: str, details: str = "", data: Any = None):
    """Print diagnostic result with colors"""
    if status == "CRITICAL":
        status_color = f"{Colors.RED}🚨 CRITICAL{Colors.END}"
        diagnostic_results["critical_issues"] += 1
    elif status == "WARNING":
        status_color = f"{Colors.YELLOW}⚠️ WARNING{Colors.END}"
        diagnostic_results["warnings"] += 1
    elif status == "OK":
        status_color = f"{Colors.GREEN}✅ OK{Colors.END}"
    else:
        status_color = f"{Colors.BLUE}ℹ️ INFO{Colors.END}"
    
    print(f"{status_color} - {check_name}")
    if details:
        print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")
    if data and isinstance(data, dict):
        for key, value in data.items():
            print(f"   {Colors.CYAN}{key}: {value}{Colors.END}")

def record_diagnostic(check_name: str, status: str, details: str = "", data: Any = None):
    """Record diagnostic result"""
    diagnostic_results["total_checks"] += 1
    
    diagnostic_results["checks"].append({
        "name": check_name,
        "status": status,
        "details": details,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
    
    print_diagnostic_result(check_name, status, details, data)

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
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
            return False, None, f"Unsupported method: {method}"
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except Exception as e:
        return False, None, f"Request error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse datetime string with multiple format support"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def check_old_waiting_bets(token: str):
    """1. Проверить старые WAITING ставки"""
    print(f"\n{Colors.MAGENTA}🔍 Diagnostic 1: Checking old WAITING bets{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all regular bot active games
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success:
        record_diagnostic(
            "Old WAITING bets check",
            "CRITICAL",
            f"Failed to get active games: {details}"
        )
        return
    
    games = response_data if isinstance(response_data, list) else response_data.get("games", [])
    
    if not games:
        record_diagnostic(
            "Old WAITING bets check",
            "OK",
            "No active games found"
        )
        return
    
    # Analyze WAITING games
    waiting_games = [game for game in games if game.get("status") == "WAITING"]
    total_waiting = len(waiting_games)
    
    # Check ages of WAITING games
    now = datetime.utcnow()
    old_games_24h = []
    old_games_1h = []
    oldest_game = None
    oldest_age = timedelta(0)
    
    for game in waiting_games:
        created_at_str = game.get("created_at")
        if created_at_str:
            created_at = parse_datetime(created_at_str)
            if created_at:
                age = now - created_at
                
                if age > timedelta(hours=24):
                    old_games_24h.append(game)
                elif age > timedelta(hours=1):
                    old_games_1h.append(game)
                
                if age > oldest_age:
                    oldest_age = age
                    oldest_game = game
    
    # Determine status
    if len(old_games_24h) > 0:
        status = "CRITICAL"
        details = f"Found {len(old_games_24h)} WAITING games older than 24 hours! Oldest: {oldest_age}"
    elif len(old_games_1h) > 10:
        status = "WARNING"
        details = f"Found {len(old_games_1h)} WAITING games older than 1 hour"
    else:
        status = "OK"
        details = f"WAITING games age distribution looks normal"
    
    diagnostic_data = {
        "total_waiting_games": total_waiting,
        "games_older_than_24h": len(old_games_24h),
        "games_older_than_1h": len(old_games_1h),
        "oldest_game_age": str(oldest_age),
        "oldest_game_id": oldest_game.get("id") if oldest_game else None
    }
    
    record_diagnostic(
        "Old WAITING bets analysis",
        status,
        details,
        diagnostic_data
    )

def check_bot_violations(token: str):
    """2. Проверить статистику по ботам с нарушениями"""
    print(f"\n{Colors.MAGENTA}🔍 Diagnostic 2: Checking bots with violations{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get regular bots list
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_diagnostic(
            "Bot violations check",
            "CRITICAL",
            f"Failed to get bots list: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_diagnostic(
            "Bot violations check",
            "WARNING",
            "No bots found in system"
        )
        return
    
    # Check specific bots mentioned in the issue
    target_bots = ["Bot#1", "Bot#2", "Updated_Bot_1754524221"]
    violations_found = []
    
    for bot in bots:
        bot_name = bot.get("name", "")
        cycle_games = bot.get("cycle_games", 12)
        active_bets = bot.get("active_bets", 0)
        
        # Check if this is one of the target bots or has violations
        is_target_bot = bot_name in target_bots
        has_violation = active_bets > cycle_games
        
        if is_target_bot or has_violation:
            violation_data = {
                "bot_name": bot_name,
                "active_bets": active_bets,
                "cycle_games_limit": cycle_games,
                "violation_ratio": f"{active_bets}/{cycle_games}",
                "is_target_bot": is_target_bot,
                "created_at": bot.get("created_at", "unknown")
            }
            violations_found.append(violation_data)
    
    # Determine status
    critical_violations = [v for v in violations_found if v["active_bets"] > v["cycle_games_limit"] * 2]
    
    if len(critical_violations) > 0:
        status = "CRITICAL"
        details = f"Found {len(critical_violations)} bots with severe violations (>2x limit)"
    elif len(violations_found) > 0:
        status = "WARNING"
        details = f"Found {len(violations_found)} bots with cycle_games violations"
    else:
        status = "OK"
        details = "All bots are within their cycle_games limits"
    
    record_diagnostic(
        "Bot cycle_games violations",
        status,
        details,
        {"violations": violations_found}
    )

def check_game_statistics(token: str):
    """3. Проверить общую статистику игр по статусам"""
    print(f"\n{Colors.MAGENTA}🔍 Diagnostic 3: Checking overall game statistics{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get different game endpoints
    endpoints_to_check = [
        ("/bots/active-games", "Regular bots games"),
        ("/games/available", "Available games (Human-bots)"),
        ("/games/active-human-bots", "Active Human-bots games")
    ]
    
    total_stats = {
        "WAITING": 0,
        "ACTIVE": 0,
        "COMPLETED": 0,
        "CANCELLED": 0,
        "total_games": 0
    }
    
    endpoint_stats = {}
    
    for endpoint, description in endpoints_to_check:
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        if success and response_data:
            games = response_data if isinstance(response_data, list) else response_data.get("games", [])
            
            endpoint_stat = {
                "total": len(games),
                "WAITING": 0,
                "ACTIVE": 0,
                "COMPLETED": 0,
                "CANCELLED": 0
            }
            
            for game in games:
                status = game.get("status", "UNKNOWN")
                if status in endpoint_stat:
                    endpoint_stat[status] += 1
                    total_stats[status] += 1
                total_stats["total_games"] += 1
            
            endpoint_stats[description] = endpoint_stat
        else:
            endpoint_stats[description] = {"error": details}
    
    # Analyze statistics
    waiting_ratio = (total_stats["WAITING"] / total_stats["total_games"]) * 100 if total_stats["total_games"] > 0 else 0
    
    if waiting_ratio > 80:
        status = "CRITICAL"
        details = f"Too many WAITING games: {waiting_ratio:.1f}% of all games"
    elif waiting_ratio > 60:
        status = "WARNING"
        details = f"High ratio of WAITING games: {waiting_ratio:.1f}%"
    else:
        status = "OK"
        details = f"Game status distribution looks normal: {waiting_ratio:.1f}% WAITING"
    
    record_diagnostic(
        "Game statistics analysis",
        status,
        details,
        {
            "total_statistics": total_stats,
            "endpoint_breakdown": endpoint_stats
        }
    )

def check_automation_logs(token: str):
    """4. Проверить логи automation и функции maintain_all_bots_active_bets()"""
    print(f"\n{Colors.MAGENTA}🔍 Diagnostic 4: Checking automation logs and bot management{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if there are any admin logs or system logs available
    log_endpoints = [
        "/admin/logs",
        "/admin/system-logs", 
        "/admin/bot-logs",
        "/admin/automation-logs"
    ]
    
    logs_found = False
    automation_issues = []
    
    for endpoint in log_endpoints:
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        if success and response_data:
            logs_found = True
            logs = response_data if isinstance(response_data, list) else response_data.get("logs", [])
            
            # Look for automation-related messages
            for log in logs:
                log_message = str(log.get("message", "")).lower()
                log_description = str(log.get("description", "")).lower()
                
                if any(keyword in log_message or keyword in log_description for keyword in 
                       ["cycle games limit reached", "maintain_all_bots_active_bets", "race condition", "bot automation"]):
                    automation_issues.append({
                        "endpoint": endpoint,
                        "log": log,
                        "timestamp": log.get("created_at", "unknown")
                    })
    
    # Check bot activity patterns by comparing multiple snapshots
    bot_activity_snapshots = []
    
    for i in range(3):  # Take 3 snapshots 10 seconds apart
        success, response_data, details = make_request(
            "GET",
            "/admin/bots",
            headers=headers
        )
        
        if success and response_data:
            bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "bots": {bot.get("name", f"bot_{bot.get('id', 'unknown')}"): bot.get("active_bets", 0) for bot in bots}
            }
            bot_activity_snapshots.append(snapshot)
        
        if i < 2:  # Don't sleep after the last snapshot
            time.sleep(10)
    
    # Analyze snapshots for rapid bet creation
    rapid_creation_detected = False
    if len(bot_activity_snapshots) >= 2:
        for bot_name in bot_activity_snapshots[0]["bots"]:
            if bot_name in bot_activity_snapshots[-1]["bots"]:
                initial_bets = bot_activity_snapshots[0]["bots"][bot_name]
                final_bets = bot_activity_snapshots[-1]["bots"][bot_name]
                
                if final_bets > initial_bets + 5:  # More than 5 new bets in 20 seconds
                    rapid_creation_detected = True
                    automation_issues.append({
                        "type": "rapid_bet_creation",
                        "bot_name": bot_name,
                        "initial_bets": initial_bets,
                        "final_bets": final_bets,
                        "time_span": "20 seconds"
                    })
    
    # Determine status
    if rapid_creation_detected:
        status = "CRITICAL"
        details = "Rapid bet creation detected - automation may be running too frequently"
    elif len(automation_issues) > 0:
        status = "WARNING"
        details = f"Found {len(automation_issues)} automation-related log entries"
    elif not logs_found:
        status = "WARNING"
        details = "No automation logs accessible - cannot verify maintain_all_bots_active_bets() status"
    else:
        status = "OK"
        details = "No obvious automation issues detected"
    
    record_diagnostic(
        "Automation logs and bot management",
        status,
        details,
        {
            "logs_accessible": logs_found,
            "automation_issues": automation_issues,
            "bot_activity_snapshots": bot_activity_snapshots
        }
    )

def check_database_cleanup_necessity(token: str):
    """5. Дополнительная проверка - необходимость очистки базы данных"""
    print(f"\n{Colors.MAGENTA}🔍 Diagnostic 5: Checking database cleanup necessity{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get comprehensive game data
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if not success:
        record_diagnostic(
            "Database cleanup necessity",
            "WARNING",
            f"Cannot assess cleanup necessity: {details}"
        )
        return
    
    games = response_data if isinstance(response_data, list) else response_data.get("games", [])
    
    # Analyze game age distribution
    now = datetime.utcnow()
    age_buckets = {
        "< 1 hour": 0,
        "1-6 hours": 0,
        "6-24 hours": 0,
        "1-7 days": 0,
        "> 7 days": 0
    }
    
    very_old_games = []
    
    for game in games:
        created_at_str = game.get("created_at")
        if created_at_str:
            created_at = parse_datetime(created_at_str)
            if created_at:
                age = now - created_at
                
                if age < timedelta(hours=1):
                    age_buckets["< 1 hour"] += 1
                elif age < timedelta(hours=6):
                    age_buckets["1-6 hours"] += 1
                elif age < timedelta(hours=24):
                    age_buckets["6-24 hours"] += 1
                elif age < timedelta(days=7):
                    age_buckets["1-7 days"] += 1
                else:
                    age_buckets["> 7 days"] += 1
                    very_old_games.append({
                        "id": game.get("id"),
                        "age_days": age.days,
                        "status": game.get("status"),
                        "creator_type": game.get("creator_type")
                    })
    
    # Determine cleanup necessity
    old_games_count = age_buckets["1-7 days"] + age_buckets["> 7 days"]
    total_games = sum(age_buckets.values())
    old_games_ratio = (old_games_count / total_games) * 100 if total_games > 0 else 0
    
    if age_buckets["> 7 days"] > 0:
        status = "CRITICAL"
        details = f"Database cleanup REQUIRED: {age_buckets['> 7 days']} games older than 7 days"
    elif old_games_ratio > 30:
        status = "WARNING"
        details = f"Database cleanup RECOMMENDED: {old_games_ratio:.1f}% of games are old"
    else:
        status = "OK"
        details = f"Database cleanup not urgent: {old_games_ratio:.1f}% old games"
    
    record_diagnostic(
        "Database cleanup necessity",
        status,
        details,
        {
            "age_distribution": age_buckets,
            "very_old_games": very_old_games,
            "cleanup_recommended": old_games_ratio > 20
        }
    )

def print_final_diagnostic_summary():
    """Print final diagnostic summary"""
    print_header("RACE CONDITION DIAGNOSTIC SUMMARY")
    
    total = diagnostic_results["total_checks"]
    critical = diagnostic_results["critical_issues"]
    warnings = diagnostic_results["warnings"]
    
    print(f"{Colors.BOLD}📊 DIAGNOSTIC RESULTS:{Colors.END}")
    print(f"   Total Checks: {total}")
    print(f"   {Colors.RED}🚨 Critical Issues: {critical}{Colors.END}")
    print(f"   {Colors.YELLOW}⚠️ Warnings: {warnings}{Colors.END}")
    print(f"   {Colors.GREEN}✅ OK: {total - critical - warnings}{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 KEY FINDINGS:{Colors.END}")
    
    for check in diagnostic_results["checks"]:
        status_icon = "🚨" if check["status"] == "CRITICAL" else "⚠️" if check["status"] == "WARNING" else "✅"
        print(f"   {status_icon} {check['name']}: {check['details']}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED ANALYSIS:{Colors.END}")
    for check in diagnostic_results["checks"]:
        if check["data"]:
            print(f"\n{Colors.CYAN}{check['name']}:{Colors.END}")
            if isinstance(check["data"], dict):
                for key, value in check["data"].items():
                    if isinstance(value, list) and len(value) > 3:
                        print(f"   {key}: {len(value)} items (showing first 3)")
                        for item in value[:3]:
                            print(f"     - {item}")
                    else:
                        print(f"   {key}: {value}")
    
    # Final recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
    
    if critical > 0:
        print(f"{Colors.RED}🚨 URGENT ACTION REQUIRED:{Colors.END}")
        print(f"   - Race condition is still active and creating excessive bets")
        print(f"   - Database cleanup is needed to remove old WAITING games")
        print(f"   - Bot automation needs immediate fixing")
        
    if warnings > 0:
        print(f"{Colors.YELLOW}⚠️ ATTENTION NEEDED:{Colors.END}")
        print(f"   - Monitor bot activity closely")
        print(f"   - Consider implementing stricter limits")
        print(f"   - Review automation logs regularly")
    
    if critical == 0 and warnings == 0:
        print(f"{Colors.GREEN}✅ SYSTEM STATUS GOOD:{Colors.END}")
        print(f"   - No critical race condition issues detected")
        print(f"   - Bot limits are being respected")
        print(f"   - Database is in good condition")

def main():
    """Main diagnostic execution"""
    print_header("RACE CONDITION & OLD BETS DIAGNOSTIC")
    print(f"{Colors.BLUE}🎯 Diagnosing race condition issues and old bet accumulation{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Bot limits violations, old WAITING games, automation issues{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run all diagnostic checks
        check_old_waiting_bets(token)
        check_bot_violations(token)
        check_game_statistics(token)
        check_automation_logs(token)
        check_database_cleanup_necessity(token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Diagnostic interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during diagnostic: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_diagnostic_summary()

if __name__ == "__main__":
    main()