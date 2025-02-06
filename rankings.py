import json
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)
RANKINGS_FILE = "rankings.json"

class RankingSystem:
    def __init__(self, initial_elo=1000, k_factor=32):
        self.rankings_path = Path(RANKINGS_FILE)
        self.initial_elo = initial_elo
        self.k_factor = k_factor
        self._ensure_rankings_file()
        
    def _ensure_rankings_file(self):
        if not self.rankings_path.exists():
            logger.info(f"Creating new rankings file at {self.rankings_path}")
            self._save_rankings({})
            
    def _load_rankings(self):
        try:
            with open(self.rankings_path, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content.strip():
                    logger.warning("Rankings file is empty")
                    return {}
                # Reset file pointer to beginning before json.load
                f.seek(0)
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading rankings: {e}")
            return {}
            
    def _save_rankings(self, rankings):
        with open(self.rankings_path, 'w') as f:
            logger.debug(f"Saving rankings to {self.rankings_path}")
            json.dump(rankings, f, indent=2)
            
    def update_rankings(self, game_results):
        """
        Update ELO ratings based on game results
        game_results: dict with player names as keys and their scores as values
        """
        # Skip games where all players are the same model
        unique_models = set(game_results.keys())
        if len(unique_models) == 1:
            logger.info(f"Skipping ranking update for solo game with {unique_models.pop()}")
            return

        rankings = self._load_rankings()
        
        # Convert game results to list of (player, score) and sort by score
        sorted_results = sorted(game_results.items(), key=lambda x: x[1], reverse=True)
        
        # Update ELO for all player pairs
        for i, (player_a, score_a) in enumerate(sorted_results):
            for j, (player_b, score_b) in enumerate(sorted_results):
                if i >= j or player_a == player_b:
                    continue
                
                # Initialize new players with full stats FIRST
                if player_a not in rankings:
                    rankings[player_a] = {
                        "elo": self.initial_elo,
                        "games_played": 0,
                        "total_score": 0,
                        "matchups": {}
                    }
                if player_b not in rankings:
                    rankings[player_b] = {
                        "elo": self.initial_elo,
                        "games_played": 0,
                        "total_score": 0,
                        "matchups": {}
                    }
                
                # Get current ratings
                ra = rankings[player_a]["elo"]
                rb = rankings[player_b]["elo"]
                
                # Calculate expected scores
                ea = 1 / (1 + 10 ** ((rb - ra) / 400))
                eb = 1 / (1 + 10 ** ((ra - rb) / 400))
                
                # Initialize matchups if needed (now safe to access)
                rankings[player_a]["matchups"].setdefault(player_b, {"wins": 0, "losses": 0, "draws": 0})
                rankings[player_b]["matchups"].setdefault(player_a, {"wins": 0, "losses": 0, "draws": 0})

                # Update head-to-head stats
                if score_a > score_b:
                    rankings[player_a]["matchups"][player_b]["wins"] += 1
                    rankings[player_b]["matchups"][player_a]["losses"] += 1
                elif score_a < score_b:
                    rankings[player_a]["matchups"][player_b]["losses"] += 1
                    rankings[player_b]["matchups"][player_a]["wins"] += 1
                else:
                    rankings[player_a]["matchups"][player_b]["draws"] += 1
                    rankings[player_b]["matchups"][player_a]["draws"] += 1
                
                # Determine actual scores based on game outcome
                if score_a > score_b:
                    sa, sb = 1, 0
                elif score_a < score_b:
                    sa, sb = 0, 1
                else:
                    sa = sb = 0.5
                
                # Update ratings
                new_ra = ra + self.k_factor * (sa - ea)
                new_rb = rb + self.k_factor * (sb - eb)
                
                # Update games played and scores
                rankings[player_a]["games_played"] += 1
                rankings[player_b]["games_played"] += 1
                rankings[player_a]["total_score"] += score_a
                rankings[player_b]["total_score"] += score_b
                
                # Apply updated ratings
                rankings[player_a]["elo"] = new_ra
                rankings[player_b]["elo"] = new_rb
        
        self._save_rankings(rankings)
        
    def get_rankings(self):
        """
        Return rankings sorted by ELO rating with matchup data
        """
        rankings = self._load_rankings()
        return sorted(rankings.items(), key=lambda x: x[1]["elo"], reverse=True) 