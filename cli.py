import logging
from game import GameManager, Player
from llm_client import LLMClient
from utils import setup_logging, save_game_log
from config import OPENROUTER_API_KEY, DEFAULT_MODEL, DEFAULT_MODELS  # Updated import
from rankings import RankingSystem  # Import the ranking system

def main():
    setup_logging()
    ranking_system = RankingSystem()  # Initialize the ranking system
    
    print("Welcome to Escoba Bench CLI")
    
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
        print(f"\nFor player {i+1}:")
        print("Enter model number or name (default: 1):")
        for idx, model in enumerate(DEFAULT_MODELS, 1):
            print(f"{idx}. {model}")
        
        model_input = input("> ").strip()
        
        # Handle numeric input or direct model name
        try:
            idx = int(model_input)
            if 1 <= idx <= len(DEFAULT_MODELS):
                model_choice = DEFAULT_MODELS[idx-1]
            else:
                model_choice = DEFAULT_MODELS[0]
        except ValueError:
            model_choice = model_input if model_input in DEFAULT_MODELS else DEFAULT_MODELS[0]
        
        players.append(Player(model_choice, api_key=api_key, model=model_choice))

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
        print(f"   ELO: {stats['elo']:.0f} | Games: {stats['games_played']}")
        
        # Display top 3 matchups
        if 'matchups' in stats:
            print("   Key Matchups:")
            opponents = sorted(
                stats['matchups'].items(),
                key=lambda x: (x[1]['wins'], -x[1]['losses']),
                reverse=True
            )[:3]  # Show top 3 opponents
            
            for opponent, matchup in opponents:
                total = matchup['wins'] + matchup['losses'] + matchup['draws']
                win_rate = (matchup['wins'] / total * 100) if total > 0 else 0
                print(f"    vs {opponent}: {matchup['wins']}W/{matchup['losses']}L/{matchup['draws']}D ({win_rate:.1f}%)")
                
        print()

    # Save detailed game log
    log_file = save_game_log(
        game_manager.game_log,
        metadata=game_manager.metadata,
    )
    print(f"\nDetailed game log saved to: {log_file}")

if __name__ == '__main__':
    main() 