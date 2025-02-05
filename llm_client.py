import requests
import json
import logging
import random
import re
from itertools import combinations

class LLMClient:
    """
    LLM client that integrates with OpenRouter API to decide moves.
    Now returns a triple: (card, capture_set, error_flag)
    where error_flag is True if an exception occurred.
    """
    def __init__(self, api_key):
        self.api_key = api_key

    def find_valid_captures(self, played_card, table_cards):
        needed = 15 - played_card.value
        valid_sets = []
        # Check every non-empty subset of table_cards.
        for i in range(1, len(table_cards) + 1):
            for combo in combinations(table_cards, i):
                if sum(card.value for card in combo) == needed:
                    valid_sets.append(list(combo))
        return valid_sets

    def get_move(self, player, table_cards):
        """
        Constructs a prompt for the LLM and returns a tuple:
           (card, capture_set, error_flag)
        where card is a string representing the chosen card,
        capture_set is a list of table card strings to capture, and
        error_flag is True if an error occurred.
        """
        hand_list = [str(card) for card in player.hand]
        table_list = [str(card) for card in table_cards]
        
        prompt = f"""You are an AI playing the card game Escoba. The card values are defined as:
1 = 1, 2 = 2, 3 = 3, 4 = 4, 5 = 5, 6 = 6, 7 = 7, Sota = 8, Caballo = 9, Rey = 10.
Rules:
- On your turn, choose one card from your hand to play.
- You may capture a set of table cards if the sum of their values plus the played card's value equals exactly 15.
- If a capture move can take all the table cards (an escoba), prefer that move.
- If no valid capture exists, simply play a card from your hand to add it to the table.

Your task: Return a move as a JSON object with two keys:
   "card": The chosen card from your hand to play (e.g., "7 of Coins").
   "capture": A list of table cards to capture (or an empty list if no capture).

Ensure that:
- The chosen card is one from your hand.
- The capture, if any, is a valid subset of the table cards such that the sum of the played card's value and the capture set equals 15.

Data provided:
Your hand: {hand_list}
Table cards: {table_list}

Respond ONLY with a valid JSON object.
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>"
        }
        # Use the player's model if specified, or default.
        model_name = getattr(player, "model", "openai/gpt-4o")
        data = json.dumps({
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=data
            )
            # logging.debug(f"OpenRouter API response: {response.text}")
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            # Extract JSON from a markdown code block if present.
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = content.strip()
            move = json.loads(json_str)
            return move["card"], move["capture"], False
        except Exception as e:
            logging.error(f"Error parsing API response: {e}")
            # Fallback: randomly select a card with no capture, and flag an error.
            chosen_card = random.choice(player.hand)
            return str(chosen_card), [], True 