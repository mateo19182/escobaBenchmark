from flask import Flask, render_template, jsonify, request
from game import GameManager, Player
from llm_client import LLMClient
from rankings import RankingSystem
import logging
from config import OPENROUTER_API_KEY, DEFAULT_MODEL, DEFAULT_MODELS  # Updated import
from utils import save_game_log

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
ranking_system = RankingSystem()

@app.route("/")
def index():
    return render_template("index.html", 
                         default_models=DEFAULT_MODELS,
                         default_api_key=OPENROUTER_API_KEY)

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
        players.append(Player(model_choice, api_key=api_key, model=model_choice))
    logger.debug(f"Created players: {players}")
    
    game_manager = GameManager(players)
    ai_client = LLMClient(api_key=api_key)
    
    logger.debug("Starting game...")
    final_scores = game_manager.play_game(ai_client=ai_client)
    logger.debug(f"Game completed. Final scores: {final_scores}")
    
    # Update rankings with the game results
    ranking_system.update_rankings(final_scores)
    logger.debug("Rankings updated successfully")
    
    # Save detailed game log
    log_file = save_game_log(
        game_manager.game_log,
        metadata=game_manager.metadata
    )
    logger.info(f"Game log saved to {log_file}")
    
    return jsonify(
        game_log=game_manager.game_log,
        final_scores=final_scores,
        log_file=log_file
    )

@app.route("/models")
def models():
    logger.debug(f"Returning models: {DEFAULT_MODELS}")
    return jsonify(DEFAULT_MODELS)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True) 