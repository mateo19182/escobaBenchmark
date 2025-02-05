import logging
from game import GameManager, Player
from llm_client import LLMClient
from utils import setup_logging, save_game_log
from config import OPENROUTER_API_KEY, DEFAULT_MODEL  # Import configuration
from rankings import RankingSystem  # Import the ranking system

def main():
    setup_logging()
    ranking_system = RankingSystem()  # Initialize the ranking system
    
    print("Welcome to Escoba Benchmark CLI Demo (AI Only)!")
    print("Each AI player's chosen model will be used to make moves.")
    
    while True:
        try:
            num_players = int(input("Enter number of players (2-4): "))
            if num_players in [2, 3, 4]:
                break
            else:
                print("Number of players must be 2, 3, or 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Use the API key from the config if the user leaves it blank.
    api_key = input("Enter your OpenRouter API Key (default from config): ") or OPENROUTER_API_KEY

    players = []
    for i in range(num_players):
        model_input = input(f"Enter model for player {i+1} (default from config): ").strip()
        # Use provided model or fall back to default from config.
        model_choice = model_input if model_input else DEFAULT_MODEL
        # Use the model name as the player name
        players.append(Player(model_choice, is_ai=True, api_key=api_key, model=model_choice))

    game_manager = GameManager(players)
    ai_client = LLMClient(api_key=api_key)
    
    try:
        final_scores = game_manager.play_game(ai_client=ai_client)
    except Exception as ex:
        logging.error(f"Unexpected error: {ex}")
        final_scores = game_manager.calculate_scores()
    
    print("\nGame Over!")
    print("Final Scores:")
    for name, score in final_scores.items():
        print(f"{name}: {score}")

    # Update the persistent rankings
    ranking_system.update_rankings({
        player.name: final_scores.get(player.name, 0) for player in players
    })

    # Get and display current rankings
    print("\n=== Overall Rankings ===")
    all_rankings = ranking_system.get_rankings()
    for rank, (player_name, stats) in enumerate(all_rankings, start=1):
        print(f"{rank}. {player_name}")
        print(f"   Average Score: {stats['average_score']:.2f}")
        print(f"   Wins: {stats['wins']}")
        print(f"   Games Played: {stats['games_played']}")
        print(f"   Total Score: {stats['total_score']}")
        print()

    save_game_log(game_manager.game_log, filename="game_log.json")
    print("Game log saved to game_log.json")

if __name__ == '__main__':
    main() 