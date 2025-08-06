#!/usr/bin/env python3
import requests
import json

BASE_URL = 'https://6abba581-4136-46bf-9b8f-5cb9aece096f.preview.emergentagent.com/api'

# Login first
login_data = {'email': 'admin@gemplay.com', 'password': 'Admin123!'}
login_response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
token = login_response.json()['access_token']

# Get available games
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{BASE_URL}/games/available', headers=headers)
games = response.json()

# Filter for regular bot games
regular_bot_games = [g for g in games if g.get('is_regular_bot') == True]
human_bot_games = [g for g in games if g.get('is_human_bot') == True]

print('Total available games:', len(games))
print('Regular bot games:', len(regular_bot_games))
print('Human bot games:', len(human_bot_games))

if regular_bot_games:
    print('\nFirst 3 regular bot games:')
    for i, game in enumerate(regular_bot_games[:3]):
        print(f'{i+1}. {game["creator_username"]} - ${game["bet_amount"]}')
else:
    print('\nNo regular bot games found in available games')