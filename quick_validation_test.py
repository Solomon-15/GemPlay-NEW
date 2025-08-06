#!/usr/bin/env python3
import requests
import json

BASE_URL = 'https://855c1c6b-3430-44a1-9946-fececb6b6343.preview.emergentagent.com/api'
ADMIN_USER = {'email': 'admin@gemplay.com', 'password': 'Admin123!'}

# Authenticate
auth_response = requests.post(f'{BASE_URL}/auth/login', json=ADMIN_USER)
token = auth_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("🔍 QUICK VALIDATION TEST FOR REGULAR BOT CREATION FIX")
print("=" * 60)

# Check active games for regular bots
active_games_response = requests.get(f'{BASE_URL}/bots/active-games', headers=headers)
if active_games_response.status_code == 200:
    games = active_games_response.json()
    print(f'✅ Found {len(games)} active regular bot games')
    if games:
        print(f'   Sample game: ID={games[0].get("id", "N/A")}, Status={games[0].get("status", "N/A")}, Bet=${games[0].get("bet_amount", "N/A")}')
else:
    print(f'❌ Failed to get active games: {active_games_response.status_code}')

# Verify bot creation with exact Russian review data
bot_data = {
    'name': 'Test Bot Fix Final',
    'min_bet_amount': 1.0,
    'max_bet_amount': 50.0,
    'win_percentage': 55.0,
    'cycle_games': 12,
    'pause_between_cycles': 5,
    'pause_on_draw': 1,
    'profit_strategy': 'balanced'
}

print(f"\n🧪 Creating bot with data: {json.dumps(bot_data, indent=2)}")

create_response = requests.post(f'{BASE_URL}/admin/bots/create-regular', headers=headers, json=bot_data)
if create_response.status_code == 200:
    result = create_response.json()
    print(f'✅ Bot creation successful: {result.get("message", "Success")}')
    print(f'   Bot ID: {result.get("created_bots", ["N/A"])[0]}')
    
    # Check if validation error is present
    response_text = str(result).lower()
    if 'ошибка валидации' in response_text or 'неверный режим создания ставок' in response_text:
        print('❌ VALIDATION ERROR STILL PRESENT!')
    else:
        print('✅ NO VALIDATION ERROR - Fix is working!')
        
    # Check bot in list
    bots_response = requests.get(f'{BASE_URL}/admin/bots', headers=headers)
    if bots_response.status_code == 200:
        bots = bots_response.json()
        for bot in bots:
            if bot.get('name') == 'Test Bot Fix Final':
                print(f'✅ Bot found in list with creation_mode: {bot.get("creation_mode", "MISSING")}')
                print(f'   Active bets: {bot.get("active_bets", 0)}, Cycle games: {bot.get("cycle_games", 0)}')
                break
else:
    print(f'❌ Bot creation failed: {create_response.status_code} - {create_response.text}')

print("\n" + "=" * 60)
print("✅ VALIDATION FIX TEST COMPLETED")