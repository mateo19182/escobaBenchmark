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
        print(self.api_key)
        self.system_prompt = """You are playing the Spanish card game Escoba. Your role is to make valid moves according to these rules:
        
Card Values:
- Number cards (1-7): Face value
- Sota (Jack): 8 points
- Caballo (Knight): 9 points
- Rey (King): 10 points

Core Rules:
1. On your turn, you must play exactly one card from your hand
2. If possible, you may capture cards from the table if:
   - The sum of your played card plus chosen table cards equals EXACTLY 15
   - You can only capture cards that are currently on the table
3. Special Achievement (Escoba):
   - If you capture ALL cards from the table, this is called an "escoba"
   - An escoba is worth an extra point
4. If you cannot make a 15-sum capture, you must place your card on the table

Strategy Tips:
- Always check for possible captures that sum to 15
- Prioritize moves that achieve an escoba (capturing all table cards)
- If no capture is possible, try to avoid leaving easy captures for opponents

Your responses must be valid JSON objects with:
{
  "card": "The card you choose to play from your hand",
  "capture": ["Array of table cards to capture (empty if no capture)"]
}"""

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
        
        user_prompt = f"""Current Game State:
Your hand: {hand_list}
Table cards: {table_list}

Choose your move, responding with only a JSON object."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>"
        }
        # Use the player's model if specified, or default.
        model_name = getattr(player, "model", "google/gemini-2.0-flash-001")
        data = json.dumps({
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
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