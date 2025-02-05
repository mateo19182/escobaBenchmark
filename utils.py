import json
import logging

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def save_game_log(log_data, filename="game_log.json"):
    with open(filename, "w") as f:
        json.dump(log_data, f, indent=4) 