from flask import Flask, render_template, jsonify, request
from game import GameManager, Player
from llm_client import LLMClient
import logging
from config import OPENROUTER_API_KEY, DEFAULT_MODEL  # Import configuration

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    # Read parameters from the POST JSON payload.
    data = request.get_json()
    try:
        num_players = int(data.get("num_players", 3))
    except ValueError:
        num_players = 3
    # Use the API key from the configuration as default if not supplied.
    api_key = data.get("api_key", OPENROUTER_API_KEY)
    models = data.get("models", [])
    players = []
    for i in range(num_players):
        # Use provided model if available; otherwise default.
        model_choice = models[i] if i < len(models) and models[i].strip() != "" else DEFAULT_MODEL
        players.append(Player(f"AI Player {i+1}", is_ai=True, api_key=api_key, model=model_choice))
    
    game_manager = GameManager(players)
    ai_client = LLMClient(api_key=api_key)
    
    final_scores = game_manager.play_game(ai_client=ai_client)
    return jsonify(game_log=game_manager.game_log, final_scores=final_scores)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True) 