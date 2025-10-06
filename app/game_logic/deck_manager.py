"""
Deck Manager for Quantum Poker
Handles deck creation, shuffling, and dealing with comprehensive features
"""

import random
import secrets
from typing import List, Optional, Dict
from app.game_logic.card_encoder import QuantumCard, CardEncoder, Rank, Suit


class DeckManager:
    """Manages the deck of cards for a poker game"""
    
    def __init__(self, use_secure_random: bool = True):
        """
        Initialize deck manager
        
        Args:
            use_secure_random: If True, use cryptographically secure random
        """
        self.encoder = CardEncoder()
        self.deck: List[QuantumCard] = []
        self.dealt_cards: List[QuantumCard] = []
        self.burn_cards: List[QuantumCard] = []
        self.use_secure_random = use_secure_random
        self._original_deck: List[QuantumCard] = []
    
    def create_deck(self) -> List[QuantumCard]:
        """Create a fresh 52-card deck"""
        self.deck = self.encoder.create_deck()
        self._original_deck = [card for card in self.deck]  # Store original for reset
        self.dealt_cards = []
        self.burn_cards = []
        return self.deck
    
    def shuffle(self, seed: Optional[int] = None):
        """
        Shuffle the deck using Fisher-Yates algorithm
        
        Args:
            seed: Optional seed for reproducible shuffles (testing only)
        """
        if not self.deck:
            raise ValueError("No deck to shuffle. Call create_deck() first.")
        
        if seed is not None:
            random.seed(seed)
        
        # Fisher-Yates shuffle with secure random
        for i in range(len(self.deck) - 1, 0, -1):
            if self.use_secure_random and seed is None:
                j = secrets.randbelow(i + 1)
            else:
                j = random.randint(0, i)
            self.deck[i], self.deck[j] = self.deck[j], self.deck[i]
    
    def deal_card(self) -> Optional[QuantumCard]:
        """
        Deal a single card from the top of the deck
        
        Returns:
            QuantumCard or None if deck is empty
        """
        if not self.deck:
            return None
        
        card = self.deck.pop(0)
        self.dealt_cards.append(card)
        return card
    
    def deal_cards(self, count: int) -> List[QuantumCard]:
        """
        Deal multiple cards
        
        Args:
            count: Number of cards to deal
        
        Returns:
            List of dealt cards
        """
        if count < 0:
            raise ValueError("Cannot deal negative number of cards")
        
        cards = []
        for _ in range(count):
            card = self.deal_card()
            if card:
                cards.append(card)
            else:
                break
        return cards
    
    def burn_card(self) -> Optional[QuantumCard]:
        """
        Burn a card (remove from play without showing)
        Used before dealing flop, turn, and river in Texas Hold'em
        
        Returns:
            The burned card or None if deck is empty
        """
        if not self.deck:
            return None
        
        card = self.deck.pop(0)
        self.burn_cards.append(card)
        return card
    
    def deal_hole_cards(self, num_players: int) -> List[List[QuantumCard]]:
        """
        Deal 2 hole cards to each player (Texas Hold'em style)
        Deals one card to each player, then repeats (standard procedure)
        
        Args:
            num_players: Number of players (2-10)
        
        Returns:
            List of lists, each containing 2 cards for one player
        """
        if num_players < 2 or num_players > 10:
            raise ValueError("Must have between 2-10 players")
        
        if len(self.deck) < num_players * 2:
            raise ValueError(f"Not enough cards in deck. Need {num_players * 2}, have {len(self.deck)}")
        
        players_hands = [[] for _ in range(num_players)]
        
        # Deal one card to each player, then repeat (standard poker dealing)
        for round_num in range(2):
            for player_idx in range(num_players):
                card = self.deal_card()
                if card:
                    players_hands[player_idx].append(card)
                else:
                    raise RuntimeError("Ran out of cards during dealing")
        
        return players_hands
    
    def deal_flop(self) -> List[QuantumCard]:
        """
        Deal the flop (3 community cards)
        Burns one card first, then deals 3 cards
        
        Returns:
            List of 3 cards
        """
        if len(self.deck) < 4:
            raise ValueError(f"Not enough cards for flop. Need 4, have {len(self.deck)}")
        
        self.burn_card()
        return self.deal_cards(3)
    
    def deal_turn(self) -> Optional[QuantumCard]:
        """
        Deal the turn (1 community card)
        Burns one card first, then deals 1 card
        
        Returns:
            The turn card or None if not enough cards
        """
        if len(self.deck) < 2:
            raise ValueError(f"Not enough cards for turn. Need 2, have {len(self.deck)}")
        
        self.burn_card()
        return self.deal_card()
    
    def deal_river(self) -> Optional[QuantumCard]:
        """
        Deal the river (1 community card)
        Burns one card first, then deals 1 card
        
        Returns:
            The river card or None if not enough cards
        """
        if len(self.deck) < 2:
            raise ValueError(f"Not enough cards for river. Need 2, have {len(self.deck)}")
        
        self.burn_card()
        return self.deal_card()
    
    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self.deck)
    
    def cards_dealt(self) -> int:
        """Get number of cards dealt"""
        return len(self.dealt_cards)
    
    def cards_burned(self) -> int:
        """Get number of cards burned"""
        return len(self.burn_cards)
    
    def reset(self):
        """Reset deck for new hand (returns all cards to deck)"""
        self.deck = [card for card in self._original_deck]
        self.dealt_cards = []
        self.burn_cards = []
    
    def get_card_strings(self, cards: List[QuantumCard]) -> List[str]:
        """
        Convert list of cards to readable strings
        
        Args:
            cards: List of QuantumCard objects
        
        Returns:
            List of card strings (e.g., ["A♥", "K♠"])
        """
        return [self.encoder.card_to_string(card) for card in cards]
    
    def get_card_string(self, card: QuantumCard) -> str:
        """
        Convert single card to readable string
        
        Args:
            card: QuantumCard object
        
        Returns:
            Card string (e.g., "A♥")
        """
        return self.encoder.card_to_string(card)
    
    def get_deck_state(self) -> Dict:
        """
        Get complete deck state information
        
        Returns:
            Dictionary with deck statistics
        """
        return {
            "cards_in_deck": self.cards_remaining(),
            "cards_dealt": self.cards_dealt(),
            "cards_burned": self.cards_burned(),
            "total_cards": 52,
            "dealt_cards_list": self.get_card_strings(self.dealt_cards),
            "burn_cards_list": self.get_card_strings(self.burn_cards)
        }
    
    def peek_top_card(self) -> Optional[str]:
        """
        Peek at the top card without dealing it (for debugging)
        
        Returns:
            String representation of top card or None
        """
        if not self.deck:
            return None
        return self.encoder.card_to_string(self.deck[0])
    
    def peek_top_cards(self, count: int) -> List[str]:
        """
        Peek at multiple top cards without dealing them (for debugging)
        
        Args:
            count: Number of cards to peek
        
        Returns:
            List of card strings
        """
        if count < 0:
            raise ValueError("Count must be non-negative")
        
        peek_count = min(count, len(self.deck))
        return self.get_card_strings(self.deck[:peek_count])
    
    def find_card(self, rank_display: str, suit_symbol: str) -> Optional[int]:
        """
        Find a specific card in the remaining deck
        
        Args:
            rank_display: Rank as string (e.g., "A", "K", "10")
            suit_symbol: Suit symbol (e.g., "♥", "♠")
        
        Returns:
            Index of card in deck or None if not found
        """
        target_card = self.encoder.encode_card(rank_display, suit_symbol)
        
        for i, card in enumerate(self.deck):
            if (card.qubits == target_card.qubits and 
                card.amplitude == target_card.amplitude):
                return i
        
        return None
    
    def validate_deck_integrity(self) -> Dict:
        """
        Validate that all 52 unique cards are accounted for
        
        Returns:
            Dictionary with validation results
        """
        all_cards = self.deck + self.dealt_cards + self.burn_cards
        
        # Convert to strings for easier comparison
        card_strings = [self.encoder.card_to_string(card) for card in all_cards]
        unique_cards = set(card_strings)
        
        is_valid = len(all_cards) == 52 and len(unique_cards) == 52
        
        return {
            "is_valid": is_valid,
            "total_cards": len(all_cards),
            "unique_cards": len(unique_cards),
            "expected": 52,
            "duplicate_cards": [card for card in card_strings if card_strings.count(card) > 1],
            "missing_cards": 52 - len(unique_cards) if len(unique_cards) < 52 else 0
        }


# Example usage and testing
if __name__ == "__main__":
    print("=== Deck Manager Comprehensive Testing ===\n")
    
    deck_manager = DeckManager()
    
    # Test 1: Create and shuffle deck
    print("1. Creating and shuffling deck:")
    deck_manager.create_deck()
    print(f"Deck size: {deck_manager.cards_remaining()} cards")
    print(f"Top 5 cards before shuffle: {deck_manager.peek_top_cards(5)}")
    
    deck_manager.shuffle()
    print(f"Top 5 cards after shuffle: {deck_manager.peek_top_cards(5)}")
    print()
    
    # Test 2: Validate deck integrity
    print("2. Deck integrity check:")
    integrity = deck_manager.validate_deck_integrity()
    print(f"Valid: {integrity['is_valid']}")
    print(f"Total cards: {integrity['total_cards']}")
    print(f"Unique cards: {integrity['unique_cards']}")
    print()
    
    # Test 3: Deal hole cards to 4 players
    print("3. Dealing hole cards to 4 players:")
    hole_cards = deck_manager.deal_hole_cards(4)
    for i, cards in enumerate(hole_cards):
        cards_str = deck_manager.get_card_strings(cards)
        print(f"Player {i+1}: {cards_str}")
    print(f"Cards remaining: {deck_manager.cards_remaining()}")
    print(f"Cards dealt: {deck_manager.cards_dealt()}")
    print()
    
    # Test 4: Deal flop
    print("4. Dealing the flop:")
    flop = deck_manager.deal_flop()
    flop_str = deck_manager.get_card_strings(flop)
    print(f"Flop: {flop_str}")
    print(f"Cards burned: {deck_manager.cards_burned()}")
    print(f"Cards remaining: {deck_manager.cards_remaining()}")
    print()
    
    # Test 5: Deal turn
    print("5. Dealing the turn:")
    turn = deck_manager.deal_turn()
    turn_str = deck_manager.encoder.card_to_string(turn)
    print(f"Turn: {turn_str}")
    print(f"Cards burned: {deck_manager.cards_burned()}")
    print(f"Cards remaining: {deck_manager.cards_remaining()}")
    print()
    
    # Test 6: Deal river
    print("6. Dealing the river:")
    river = deck_manager.deal_river()
    river_str = deck_manager.encoder.card_to_string(river)
    print(f"River: {river_str}")
    print(f"Cards burned: {deck_manager.cards_burned()}")
    print(f"Cards remaining: {deck_manager.cards_remaining()}")
    print()
    
    # Test 7: Full community cards
    print("7. Complete board:")
    community = flop + [turn, river]
    community_str = deck_manager.get_card_strings(community)
    print(f"Community cards: {community_str}")
    print()
    
    # Test 8: Full hands for players
    print("8. Complete hands (hole + community):")
    for i, hole in enumerate(hole_cards):
        full_hand = hole + community
        full_hand_str = deck_manager.get_card_strings(full_hand)
        print(f"Player {i+1}: {full_hand_str}")
    print()
    
    # Test 9: Deck state
    print("9. Final deck state:")
    state = deck_manager.get_deck_state()
    print(f"Cards in deck: {state['cards_in_deck']}")
    print(f"Cards dealt: {state['cards_dealt']}")
    print(f"Cards burned: {state['cards_burned']}")
    print(f"Total accounted: {state['cards_in_deck'] + state['cards_dealt'] + state['cards_burned']}")
    print()
    
    # Test 10: Final integrity check
    print("10. Final integrity check:")
    integrity = deck_manager.validate_deck_integrity()
    print(f"Valid: {integrity['is_valid']}")
    print(f"Total cards: {integrity['total_cards']}")
    print(f"Unique cards: {integrity['unique_cards']}")
    
    if not integrity['is_valid']:
        print(f"Duplicates: {integrity['duplicate_cards']}")
        print(f"Missing: {integrity['missing_cards']}")
    print()
    
    # Test 11: Reset and shuffle again
    print("11. Reset and shuffle test:")
    deck_manager.reset()
    print(f"After reset - Cards in deck: {deck_manager.cards_remaining()}")
    print(f"Cards dealt: {deck_manager.cards_dealt()}")
    print(f"Cards burned: {deck_manager.cards_burned()}")
    
    deck_manager.shuffle(seed=42)  # Reproducible shuffle
    print(f"Top 5 after seeded shuffle: {deck_manager.peek_top_cards(5)}")
    
    # Second shuffle with same seed should give same result
    deck_manager.reset()
    deck_manager.shuffle(seed=42)
    print(f"Top 5 after same seed: {deck_manager.peek_top_cards(5)}")
    print()
    
    # Test 12: Find specific card
    print("12. Find specific card:")
    deck_manager.reset()
    ace_spades_idx = deck_manager.find_card("A", "♠")
    if ace_spades_idx is not None:
        print(f"Ace of Spades found at index: {ace_spades_idx}")
    else:
        print("Ace of Spades not in remaining deck")
    
    king_hearts_idx = deck_manager.find_card("K", "♥")
    if king_hearts_idx is not None:
        print(f"King of Hearts found at index: {king_hearts_idx}")
    
    print("\n=== All Tests Complete ===")