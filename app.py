from flask import Flask, render_template, jsonify, request
from game import GameManager, Player
from llm_client import LLMClient
from rankings import RankingSystem
import logging
from config import OPENROUTER_API_KEY, DEFAULT_MODEL  # Import configuration

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
ranking_system = RankingSystem()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rankings")
def rankings():
    rankings_data = ranking_system.get_rankings()
    return render_template("rankings.html", rankings=rankings_data)

@app.route("/simulate", methods=["POST"])
def simulate():
    # Read parameters from the POST JSON payload.
    data = request.get_json()
    logger.debug(f"Received simulation request with data: {data}")
    try:
        num_players = int(data.get("num_players", 3))
    except ValueError:
        num_players = 3
    logger.debug(f"Number of players: {num_players}")
    
    # Use the API key from the configuration as default if not supplied.
    api_key = data.get("api_key", OPENROUTER_API_KEY)
    models = data.get("models", [])
    logger.debug(f"Using models: {models}")
    
    players = []
    for i in range(num_players):
        # Use provided model if available; otherwise default.
        model_choice = models[i] if i < len(models) and models[i].strip() != "" else DEFAULT_MODEL
        # Use the model name as the player name to be consistent with CLI
        players.append(Player(model_choice, is_ai=True, api_key=api_key, model=model_choice))
    logger.debug(f"Created players: {players}")
    
    game_manager = GameManager(players)
    ai_client = LLMClient(api_key=api_key)
    
    logger.debug("Starting game simulation...")
    final_scores = game_manager.play_game(ai_client=ai_client)
    logger.debug(f"Game completed. Final scores: {final_scores}")
    
    # Update rankings with the game results
    ranking_system.update_rankings(final_scores)
    logger.debug("Rankings updated successfully")
    
    return jsonify(game_log=game_manager.game_log, final_scores=final_scores)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True) 