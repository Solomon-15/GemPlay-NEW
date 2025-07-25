#!/usr/bin/env python3
"""
Test Rock-Paper-Scissors logic to verify current implementation
"""

class GameMove:
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

def determine_rps_winner(creator_move, opponent_move, creator_id="creator", opponent_id="opponent"):
    """Determine winner using rock-paper-scissors logic."""
    winner_id = None
    result_status = "draw"
    
    if creator_move == opponent_move:
        result_status = "draw"
    elif (
        (creator_move == GameMove.ROCK and opponent_move == GameMove.SCISSORS) or
        (creator_move == GameMove.SCISSORS and opponent_move == GameMove.PAPER) or
        (creator_move == GameMove.PAPER and opponent_move == GameMove.ROCK)
    ):
        winner_id = creator_id
        result_status = "creator_wins"
    else:
        winner_id = opponent_id
        result_status = "opponent_wins"
    
    return winner_id, result_status

def test_rps_logic():
    print("Testing Rock-Paper-Scissors logic...")
    print("Expected rules: Rock beats Scissors, Scissors beats Paper, Paper beats Rock")
    print()
    
    # Test cases
    tests = [
        # Format: (creator_move, opponent_move, expected_winner, description)
        (GameMove.ROCK, GameMove.SCISSORS, "creator", "Rock vs Scissors -> Rock wins"),
        (GameMove.SCISSORS, GameMove.ROCK, "opponent", "Scissors vs Rock -> Rock wins"),
        (GameMove.SCISSORS, GameMove.PAPER, "creator", "Scissors vs Paper -> Scissors wins"),  
        (GameMove.PAPER, GameMove.SCISSORS, "opponent", "Paper vs Scissors -> Scissors wins"),
        (GameMove.PAPER, GameMove.ROCK, "creator", "Paper vs Rock -> Paper wins"),
        (GameMove.ROCK, GameMove.PAPER, "opponent", "Rock vs Paper -> Paper wins"),
        (GameMove.ROCK, GameMove.ROCK, "draw", "Rock vs Rock -> Draw"),
        (GameMove.PAPER, GameMove.PAPER, "draw", "Paper vs Paper -> Draw"),
        (GameMove.SCISSORS, GameMove.SCISSORS, "draw", "Scissors vs Scissors -> Draw"),
    ]
    
    all_correct = True
    
    for creator_move, opponent_move, expected, description in tests:
        winner, status = determine_rps_winner(creator_move, opponent_move)
        
        if expected == "draw":
            actual = "draw" if winner is None else "not_draw"
        elif expected == "creator":
            actual = "creator" if winner == "creator" else "opponent" 
        else:  # expected == "opponent"
            actual = "opponent" if winner == "opponent" else "creator"
        
        correct = (actual == expected)
        status_icon = "✅" if correct else "❌"
        
        print(f"{status_icon} {description}")
        print(f"   Actual: {actual}, Expected: {expected}")
        
        if not correct:
            all_correct = False
        print()
    
    if all_correct:
        print("🎉 All tests passed! Logic is correct.")
    else:
        print("⚠️ Some tests failed! Logic needs to be fixed.")
        
    return all_correct

if __name__ == "__main__":
    test_rps_logic()