#!/usr/bin/env python3
import requests
import json

BASE_URL = 'https://rusdetails-1.preview.emergentagent.com/api'

# Login first
login_data = {'email': 'admin@gemplay.com', 'password': 'Admin123!'}
login_response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
token = login_response.json()['access_token']

# Get admin games
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{BASE_URL}/admin/games', headers=headers)
games = response.json()['games']

# Filter for regular bot games
regular_bot_games = []
for game in games:
    if game.get('bot_type') == 'REGULAR' and game.get('creator_type') == 'bot':
        regular_bot_games.append(game)

print('Total games:', len(games))
print('Regular bot games:', len(regular_bot_games))

if regular_bot_games:
    print('\nFirst 5 regular bot games:')
    for i, game in enumerate(regular_bot_games[:5]):
        print(f'{i+1}. Game {game["id"]}:')
        print(f'   Creator: {game["creator_id"]}')
        print(f'   Status: {game["status"]}')
        print(f'   Bet: ${game["bet_amount"]}')
        print(f'   Created: {game["created_at"]}')
        print()
else:
    print('No regular bot games found')