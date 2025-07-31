#!/usr/bin/env python3
import requests
import json

BASE_URL = 'https://acffc923-2545-42ed-a41d-4e93fa17c383.preview.emergentagent.com/api'
game_id = '57339c4b-18a9-4ee5-bd21-00a0260871fb'
user1_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZjc1NTY1My1kYmI0LTQwZTItYTUxYy0wMjgzMGU1NjczMDUiLCJleHAiOjE3NTM5ODkwOTB9.OjqiP9U6XjiEdaIEbaAwxVZNwZSiVwzPkjsdPpqQIQg'
user2_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5MGIzNjE2Yy1jZTU4LTQ5N2YtOGRkMi0wM2VmY2QwZjVkMzgiLCJleHAiOjE3NTM5ODkwOTB9.cfer4_SMbvQm3fTKrPMGBcN_iSLKJWcZdxLvvSlAjeg'

headers1 = {'Authorization': f'Bearer {user1_token}'}
headers2 = {'Authorization': f'Bearer {user2_token}'}

print('=== CHECKING GAME STATUS AFTER TIMEOUT ===')

# Check User1 balance
response = requests.get(f'{BASE_URL}/auth/me', headers=headers1)
if response.status_code == 200:
    data = response.json()
    print(f'User1 Final Balance: Virtual=${data["virtual_balance"]}, Frozen=${data["frozen_balance"]}')
else:
    print(f'Failed to get User1 balance: {response.status_code}')

# Check User2 balance  
response = requests.get(f'{BASE_URL}/auth/me', headers=headers2)
if response.status_code == 200:
    data = response.json()
    print(f'User2 Final Balance: Virtual=${data["virtual_balance"]}, Frozen=${data["frozen_balance"]}')
else:
    print(f'Failed to get User2 balance: {response.status_code}')

# Try to get game details from admin endpoint
admin_response = requests.post(f'{BASE_URL}/auth/login', json={'email': 'admin@gemplay.com', 'password': 'Admin123!'})
if admin_response.status_code == 200:
    admin_token = admin_response.json()['access_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    
    # Check admin games list
    games_response = requests.get(f'{BASE_URL}/admin/bets/list', headers=admin_headers)
    if games_response.status_code == 200:
        games = games_response.json().get('games', [])
        for game in games:
            if game.get('id') == game_id:
                print(f'Game Status: {game.get("status")}')
                print(f'Winner ID: {game.get("winner_id")}')
                print(f'Creator ID: {game.get("creator_id")}')
                print(f'Opponent ID: {game.get("opponent_id")}')
                break
        else:
            print('Game not found in admin list')
    else:
        print(f'Failed to get admin games: {games_response.status_code}')
else:
    print('Failed to login as admin')