import random
from itertools import combinations
import logging

# -------------------------------
# EarlyTermination Exception
# -------------------------------
class EarlyTermination(Exception):
    """
    Raised when a player sends invalid moves 3 times.
    """
    pass

# -------------------------------
# Card Class
# -------------------------------
class Card:
    SUITS = ["Coins", "Cups", "Batons", "Swords"]
    RANKS = ["1", "2", "3", "4", "5", "6", "7", "Sota", "Caballo", "Rey"]
    CAPTURE_VALUES = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "Sota": 8,
        "Caballo": 9,
        "Rey": 10,
    }
    # Prime ranking order: best card is '7', then '6', '1', etc.
    PRIME_ORDER = ["7", "6", "1", "5", "4", "3", "2", "Sota", "Caballo", "Rey"]

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    @property
    def value(self):
        return self.CAPTURE_VALUES[self.rank]

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

# -------------------------------
# Deck Class
# -------------------------------
class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_cards(self, num):
        dealt = [self.cards.pop() for _ in range(num)] if len(self.cards) >= num else []
        return dealt

# -------------------------------
# Player Class
# -------------------------------
class Player:
    def __init__(self, name, is_ai=False, api_key=None, model="openai/gpt-4o"):
        self.name = name
        self.is_ai = is_ai
        self.hand = []
        self.captured = []  # List to store captured cards.
        self.escobas = 0
        self.api_key = api_key  # Holds API key if needed for LLM integration.
        self.model = model    # Model identifier for this player's LLM.
        self.error_count = 0  # Tracks invalid responses/moves

    def __repr__(self):
        return f"{self.name} {'(AI)' if self.is_ai else ''}"

# -------------------------------
# GameManager Class
# -------------------------------
class GameManager:
    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.deck.shuffle()
        self.table = []
        self.game_log = []  # A list to store the move history for JSON logging.

        # For this demo, assume the last player in the players list is the dealer.
        self.dealer_index = len(players) - 1
        # Track the last capturing player to pick up remaining table cards.
        self.last_capture_player = None
        self.early_termination = False
        self.early_loser = None

    def initial_deal(self):
        # Each player gets 3 cards; the table gets 4 cards.
        # logging.debug("Starting initial deal")
        for player in self.players:
            player.hand = self.deck.deal_cards(3)
            logging.debug(f"{player.name} hand: {player.hand}")
        self.table = self.deck.deal_cards(4)
        logging.debug(f"Initial table: {self.table}")

        # Check for immediate capture in the opening deal.
        table_sum = sum(card.value for card in self.table)
        dealer = self.players[self.dealer_index]
        if table_sum == 15:
            logging.debug("Immediate capture: Table sums to 15, dealer collects and scores an escoba")
            dealer.captured.extend(self.table)
            dealer.escobas += 1
            self.game_log.append({
                "event": "immediate_capture",
                "player": dealer.name,
                "cards": [str(card) for card in self.table]
            })
            self.table.clear()
        elif table_sum == 30:
            logging.debug("Immediate capture: Table sums to 30, dealer collects and scores two escobas")
            dealer.captured.extend(self.table)
            dealer.escobas += 2
            self.game_log.append({
                "event": "immediate_capture",
                "player": dealer.name,
                "cards": [str(card) for card in self.table]
            })
            self.table.clear()

    def find_valid_captures(self, played_card, table_cards):
        needed = 15 - played_card.value
        valid_sets = []
        for i in range(1, len(table_cards) + 1):
            for combo in combinations(table_cards, i):
                if sum(card.value for card in combo) == needed:
                    valid_sets.append(list(combo))
        return valid_sets

    def play_turn(self, player, ai_client=None):
        """
        Processes a single turn for a player using the LLM to decide the move.
        Now properly removes the played card from the player's hand.
        """
        logging.debug(f"{player.name}'s turn with hand: {player.hand}")
        logging.debug(f"Current table: {self.table}")
        move_log = {
            "player": player.name,
            "hand": [str(card) for card in player.hand],
            "table_before": [str(card) for card in self.table]
        }

        # Always use LLM-based decision.
        card_str, capture_cards_strs, move_error = ai_client.get_move(player, self.table)

        # Map the returned card string to an actual Card object from the player's hand.
        selected_card = None
        for card in player.hand:
            if str(card) == card_str:
                selected_card = card
                break
        if not selected_card:
            selected_card = player.hand[0]  # Fallback if not found.

        # IMPORTANT FIX: Remove the played card from the player's hand
        player.hand.remove(selected_card)

        # Map each capture card string to actual Card objects from the table.
        capture_cards = []
        for cap_str in capture_cards_strs:
            for card in self.table:
                if str(card) == cap_str:
                    capture_cards.append(card)
                    break

        logging.debug(f"AI {player.name} decided to play {selected_card} with capture {capture_cards}")
        move_log["played_card"] = str(selected_card)

        if capture_cards:
            total = selected_card.value + sum(card.value for card in capture_cards)
            if total == 15:
                for captured in capture_cards:
                    if captured in self.table:
                        self.table.remove(captured)
                # Add played card and captured cards to player's pile
                player.captured.append(selected_card)
                player.captured.extend(capture_cards)
                self.last_capture_player = player
                move_log["action"] = f"Captured {', '.join(str(c) for c in capture_cards)}"
                if not self.table:
                    player.escobas += 1
                    move_log["escoba"] = True
                    logging.debug(f"{player.name} made an escoba!")
                else:
                    move_log["escoba"] = False
            else:
                # If the provided capture is invalid, treat move as a non-capture move:
                self.table.append(selected_card)
                move_log["action"] = "Played card to table (invalid capture provided, treated as no capture)"
                move_log["escoba"] = False
        else:
            # No capture; add the played card to the table.
            self.table.append(selected_card)
            move_log["action"] = "Played card to table (no capture)"
            move_log["escoba"] = False

        move_log["table_after"] = [str(card) for card in self.table]
        logging.debug(f"After move, table: {self.table}")
        self.game_log.append(move_log)

        # Check for early termination: if a player reaches 3 errors.
        if move_error:
            player.error_count += 1
            logging.error(f"{player.name} encountered an LLM response error. Error count: {player.error_count}")
            if player.error_count >= 3:
                logging.error(f"{player.name} reached 3 errors. Terminating game early.")
                self.early_loser = player.name
                raise EarlyTermination(player.name)

    def deal_new_hands(self):
        """
        When players' hands are empty yet cards remain in the deck, deal new hands.
        """
        for player in self.players:
            if self.deck.cards:
                new_cards = self.deck.deal_cards(3)
                player.hand = new_cards
                logging.debug(f"{player.name} new hand: {player.hand}")

    def finalize_round(self):
        """
        When the round ends, award any remaining table cards to the last capturing player.
        """
        if self.table and self.last_capture_player:
            logging.debug(f"{self.last_capture_player.name} collects remaining table cards: {self.table}")
            self.last_capture_player.captured.extend(self.table)
            self.game_log.append({
                "event": "finalize_round",
                "player": self.last_capture_player.name,
                "collected": [str(card) for card in self.table]
            })
            self.table.clear()

    def calculate_scores(self):
        """
        Computes points for each player.
        For this demo we give:
         - 1 point for most captured cards (Cartas)
         - 1 point for most Coins (Oros)
         - 1 point for capturing the 7 of Coins (Siete de Oros)
         - 1 point per escoba achieved
        (The prime calculation is omitted for now.)
        """
        scores = {}
        # Cartas: score bonus for most captured
        captured_counts = {player.name: len(player.captured) for player in self.players}
        max_captured = max(captured_counts.values())
        cartas_winners = [name for name, count in captured_counts.items() if count == max_captured and count > 0]

        # Coins (Oros)
        coins_counts = {}
        for player in self.players:
            coins_counts[player.name] = len([card for card in player.captured if card.suit == "Coins"])
        max_coins = max(coins_counts.values())
        oros_winners = [name for name, count in coins_counts.items() if count == max_coins and count > 0]

        # Siete de Oros
        siete_de_oros_winner = None
        for player in self.players:
            for card in player.captured:
                if card.suit == "Coins" and card.rank == "7":
                    siete_de_oros_winner = player.name
                    break
            if siete_de_oros_winner:
                break

        # Tally points.
        for player in self.players:
            score = 0
            if player.name in cartas_winners:
                score += 1
            if player.name in oros_winners:
                score += 1
            if player.name == siete_de_oros_winner:
                score += 1
            score += player.escobas
            scores[player.name] = score
        return scores

    def play_game(self, ai_client=None):
        """
        Main game loop executing rounds until the deck is exhausted.
        """
        self.initial_deal()

        # Play rounds until players have no cards.
        try:
            while any(player.hand for player in self.players):
                # Play in order starting with dealer's right.
                starting_index = (self.dealer_index + 1) % len(self.players)
                num_players = len(self.players)
                for i in range(num_players):
                    idx = (starting_index + i) % num_players
                    player = self.players[idx]
                    if player.hand:
                        self.play_turn(player, ai_client=ai_client)
                if self.deck.cards:
                    self.deal_new_hands()
        except EarlyTermination as et:
            logging.error(f"Game terminated early due to invalid moves by {et}.")
            self.game_log.append({"event": "early_termination", "player": str(et)})

        # End-of-round: assign any leftover table cards.
        self.finalize_round()
        final_scores = self.calculate_scores()
        # If early termination, set the offender's score to 0.
        if self.early_loser:
            final_scores[self.early_loser] = 0
        self.game_log.append({"event": "final_scores", "scores": final_scores})
        logging.debug(f"Final scores: {final_scores}")
        return final_scores 