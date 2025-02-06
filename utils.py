import json
import logging
from datetime import datetime
import os

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def generate_game_filename():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Generate filename with timestamp and models
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'logs/game_{timestamp}.json'

def save_game_log(game_log, metadata=None, filename=None):
    if filename is None:
        filename = generate_game_filename()
        
    # Create a complete game record with metadata
    game_record = {
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
        "game_log": game_log
    }
    
    with open(filename, 'w') as f:
        json.dump(game_record, f, indent=2)
    
    logging.info(f"Game log saved to {filename}")
    return filename 