import logging
from game import GameManager, Player
from llm_client import LLMClient
from utils import setup_logging, save_game_log

def main():
    setup_logging()
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

    # Get the OpenRouter API key.
    api_key = input("Enter your OpenRouter API Key: ")

    players = []
    for i in range(num_players):
        model_input = input(f"Enter model for AI Player {i+1} (default: openai/gpt-4o): ").strip()
        model_choice = model_input if model_input else "openai/gpt-4o"
        players.append(Player(f"AI Player {i+1}", is_ai=True, api_key=api_key, model=model_choice))

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

    # Build a ranking system (highest score first).
    ranking = sorted(players, key=lambda p: final_scores.get(p.name, 0), reverse=True)
    print("\n=== Rankings ===")
    for rank, player in enumerate(ranking, start=1):
        print(f"{rank}. {player.name} (Model: {player.model}) - Score: {final_scores.get(player.name, 0)}")

    save_game_log(game_manager.game_log, filename="game_log.json")
    print("Game log saved to game_log.json")

if __name__ == '__main__':
    main() 