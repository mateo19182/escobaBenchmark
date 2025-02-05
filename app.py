from flask import Flask, render_template, jsonify, request
from game import GameManager, Player
from llm_client import LLMClient
import logging

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
    api_key = data.get("api_key", "dummy_key")
    models = data.get("models", [])
    players = []
    for i in range(num_players):
        # Use the provided model if any; otherwise default.
        model_choice = models[i] if i < len(models) and models[i].strip() != "" else "openai/gpt-4o"
        players.append(Player(f"AI Player {i+1}", is_ai=True, api_key=api_key, model=model_choice))
    
    game_manager = GameManager(players)
    ai_client = LLMClient(api_key=api_key)
    
    final_scores = game_manager.play_game(ai_client=ai_client)
    return jsonify(game_log=game_manager.game_log, final_scores=final_scores)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True) 