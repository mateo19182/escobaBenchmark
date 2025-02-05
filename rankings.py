import json
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)
RANKINGS_FILE = "rankings.json"

class RankingSystem:
    def __init__(self):
        self.rankings_path = Path(RANKINGS_FILE)
        self._ensure_rankings_file()
        
    def _ensure_rankings_file(self):
        if not self.rankings_path.exists():
            logger.info(f"Creating new rankings file at {self.rankings_path}")
            self._save_rankings({})
            
    def _load_rankings(self):
        with open(self.rankings_path, 'r') as f:
            return json.load(f)
            
    def _save_rankings(self, rankings):
        with open(self.rankings_path, 'w') as f:
            logger.debug(f"Saving rankings to {self.rankings_path}")
            json.dump(rankings, f, indent=2)
            
    def update_rankings(self, game_results):
        """
        Update rankings based on game results
        game_results: dict with player names as keys and their scores as values
        """
        rankings = self._load_rankings()
        
        for player, score in game_results.items():
            player_name = player.strip()  # Ensure consistent model names by stripping whitespace
            
            if player_name not in rankings:
                logger.info(f"Adding new model to rankings: {player_name}")
                rankings[player_name] = {
                    "games_played": 0,
                    "total_score": 0,
                    "wins": 0,
                    "average_score": 0
                }
            else:
                logger.info(f"Updating existing model in rankings: {player_name}")
            
            rankings[player_name]["games_played"] += 1
            rankings[player_name]["total_score"] += score
            
            # Check if this player won (had the highest score)
            if score == max(game_results.values()):
                rankings[player_name]["wins"] += 1
                logger.info(f"Model {player_name} won this game")
                
            # Update average
            rankings[player_name]["average_score"] = (
                rankings[player_name]["total_score"] / rankings[player_name]["games_played"]
            )
            
            logger.debug(f"Updated stats for {player_name}: {rankings[player_name]}")
        
        self._save_rankings(rankings)
        
    def get_rankings(self):
        """
        Return rankings sorted by average score
        """
        rankings = self._load_rankings()
        sorted_rankings = sorted(
            rankings.items(),
            key=lambda x: (x[1]["average_score"], x[1]["wins"]),
            reverse=True
        )
        return sorted_rankings 