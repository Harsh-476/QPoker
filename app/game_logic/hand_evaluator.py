"""
Hand Evaluator for Quantum Poker
Evaluates poker hands using standard Texas Hold'em rankings
"""

from typing import List, Tuple, Optional
from collections import Counter
from enum import IntEnum
from app.game_logic.card_encoder import QuantumCard, CardEncoder, Rank, Suit


class HandRank(IntEnum):
    """Poker hand rankings (lower is better)"""
    ROYAL_FLUSH = 1
    STRAIGHT_FLUSH = 2
    FOUR_OF_A_KIND = 3
    FULL_HOUSE = 4
    FLUSH = 5
    STRAIGHT = 6
    THREE_OF_A_KIND = 7
    TWO_PAIR = 8
    PAIR = 9
    HIGH_CARD = 10


class HandEvaluator:
    """Evaluates poker hands"""
    
    def __init__(self):
        self.encoder = CardEncoder()
    
    def evaluate_hand(self, cards: List[QuantumCard]) -> Tuple[HandRank, List[int], str]:
        """
        Evaluate a poker hand (5-7 cards)
        
        Args:
            cards: List of QuantumCard objects (should be 5-7 cards)
        
        Returns:
            Tuple of (hand_rank, tiebreaker_values, description)
        """
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate")
        
        # Decode all cards
        decoded_cards = []
        for card in cards:
            card_info = self.encoder.decode_card(card)
            if card_info is None:
                raise ValueError(f"Cannot evaluate undefined card: {card}")
            decoded_cards.append(card_info)
        
        # Find best 5-card combination
        if len(cards) == 5:
            return self._evaluate_5_cards(decoded_cards)
        else:
            return self._find_best_hand(decoded_cards)
    
    def _find_best_hand(self, cards: List[Tuple]) -> Tuple[HandRank, List[int], str]:
        """Find best 5-card hand from 6 or 7 cards"""
        from itertools import combinations
        
        best_rank = HandRank.HIGH_CARD
        best_tiebreakers = []
        best_description = ""
        
        # Try all 5-card combinations
        for combo in combinations(cards, 5):
            rank, tiebreakers, desc = self._evaluate_5_cards(list(combo))
            
            # Lower rank is better
            if rank < best_rank or (rank == best_rank and tiebreakers > best_tiebreakers):
                best_rank = rank
                best_tiebreakers = tiebreakers
                best_description = desc
        
        return best_rank, best_tiebreakers, best_description
    
    def _evaluate_5_cards(self, cards: List[Tuple]) -> Tuple[HandRank, List[int], str]:
        """Evaluate exactly 5 cards"""
        ranks = [card[0] for card in cards]
        suits = [card[1] for card in cards]
        
        # Get rank values
        rank_values = sorted([r.value[1] for r in ranks], reverse=True)
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight, straight_high = self._is_straight(rank_values)
        
        # Count rank occurrences
        rank_counts = Counter(rank_values)
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Royal Flush
        if is_flush and is_straight and max(rank_values) == 14:
            return (HandRank.ROYAL_FLUSH, [14], "Royal Flush")
        
        # Straight Flush
        if is_flush and is_straight:
            return (HandRank.STRAIGHT_FLUSH, [straight_high], f"Straight Flush, {self._value_to_rank_name(straight_high)} high")
        
        # Four of a Kind
        if counts == [4, 1]:
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return (HandRank.FOUR_OF_A_KIND, [quad, kicker], f"Four of a Kind, {self._value_to_rank_name(quad)}s")
        
        # Full House
        if counts == [3, 2]:
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return (HandRank.FULL_HOUSE, [trips, pair], f"Full House, {self._value_to_rank_name(trips)}s over {self._value_to_rank_name(pair)}s")
        
        # Flush
        if is_flush:
            return (HandRank.FLUSH, rank_values, f"Flush, {self._value_to_rank_name(max(rank_values))} high")
        
        # Straight
        if is_straight:
            return (HandRank.STRAIGHT, [straight_high], f"Straight, {self._value_to_rank_name(straight_high)} high")
        
        # Three of a Kind
        if counts == [3, 1, 1]:
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return (HandRank.THREE_OF_A_KIND, [trips] + kickers, f"Three of a Kind, {self._value_to_rank_name(trips)}s")
        
        # Two Pair
        if counts == [2, 2, 1]:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return (HandRank.TWO_PAIR, pairs + [kicker], f"Two Pair, {self._value_to_rank_name(pairs[0])}s and {self._value_to_rank_name(pairs[1])}s")
        
        # One Pair
        if counts == [2, 1, 1, 1]:
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return (HandRank.PAIR, [pair] + kickers, f"Pair of {self._value_to_rank_name(pair)}s")
        
        # High Card
        return (HandRank.HIGH_CARD, rank_values, f"High Card, {self._value_to_rank_name(max(rank_values))}")
    
    def _is_straight(self, rank_values: List[int]) -> Tuple[bool, int]:
        """
        Check if values form a straight
        
        Returns:
            Tuple of (is_straight, high_card_value)
        """
        sorted_values = sorted(set(rank_values), reverse=True)
        
        if len(sorted_values) < 5:
            return False, 0
        
        # Check for regular straight (consecutive values)
        for i in range(len(sorted_values) - 4):
            if sorted_values[i] - sorted_values[i+4] == 4:
                return True, sorted_values[i]
        
        # Check for A-2-3-4-5 (wheel/bicycle)
        if sorted_values == [14, 5, 4, 3, 2]:
            return True, 5  # In wheel, 5 is the high card
        
        return False, 0
    
    def _value_to_rank_name(self, value: int) -> str:
        """Convert rank value to name"""
        value_to_name = {
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
            8: "8", 9: "9", 10: "10", 11: "Jack", 12: "Queen",
            13: "King", 14: "Ace"
        }
        return value_to_name.get(value, str(value))
    
    def compare_hands(
        self, 
        hand1: List[QuantumCard], 
        hand2: List[QuantumCard]
    ) -> int:
        """
        Compare two hands
        
        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, tie1, _ = self.evaluate_hand(hand1)
        rank2, tie2, _ = self.evaluate_hand(hand2)
        
        # Lower rank is better
        if rank1 < rank2:
            return 1
        elif rank1 > rank2:
            return -1
        
        # Same rank, compare tiebreakers
        if tie1 > tie2:
            return 1
        elif tie1 < tie2:
            return -1
        
        return 0  # Exact tie
    
    def find_winners(
        self, 
        players_hands: List[Tuple[str, List[QuantumCard]]]
    ) -> List[Tuple[str, HandRank, List[int], str]]:
        """
        Find winner(s) from multiple players
        
        Args:
            players_hands: List of (player_id, cards) tuples
        
        Returns:
            List of (player_id, rank, tiebreakers, description) for winners
        """
        evaluated = []
        
        for player_id, cards in players_hands:
            rank, tiebreakers, description = self.evaluate_hand(cards)
            evaluated.append((player_id, rank, tiebreakers, description))
        
        # Sort by rank (lower is better), then tiebreakers (higher is better)
        evaluated.sort(key=lambda x: (x[1], [-v for v in x[2]]))
        
        # Find all players with the best hand
        best_rank = evaluated[0][1]
        best_tiebreakers = evaluated[0][2]
        
        winners = [
            player for player in evaluated 
            if player[1] == best_rank and player[2] == best_tiebreakers
        ]
        
        return winners


# Example usage and testing
if __name__ == "__main__":
    encoder = CardEncoder()
    evaluator = HandEvaluator()
    
    print("=== Hand Evaluator Testing ===\n")
    
    # Test 1: Royal Flush
    print("1. Royal Flush Test:")
    royal_flush = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.QUEEN, Suit.HEARTS),
        encoder.encode_card(Rank.JACK, Suit.HEARTS),
        encoder.encode_card(Rank.TEN, Suit.HEARTS),
    ]
    rank, tie, desc = evaluator.evaluate_hand(royal_flush)
    print(f"{desc} (Rank: {rank.name})\n")
    
    # Test 2: Four of a Kind
    print("2. Four of a Kind Test:")
    quads = [
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.DIAMONDS),
        encoder.encode_card(Rank.KING, Suit.SPADES),
        encoder.encode_card(Rank.KING, Suit.CLUBS),
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
    ]
    rank, tie, desc = evaluator.evaluate_hand(quads)
    print(f"{desc} (Rank: {rank.name})\n")
    
    # Test 3: Full House
    print("3. Full House Test:")
    full_house = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.ACE, Suit.DIAMONDS),
        encoder.encode_card(Rank.ACE, Suit.SPADES),
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.DIAMONDS),
    ]
    rank, tie, desc = evaluator.evaluate_hand(full_house)
    print(f"{desc} (Rank: {rank.name})\n")
    
    # Test 4: Straight
    print("4. Straight Test:")
    straight = [
        encoder.encode_card(Rank.NINE, Suit.HEARTS),
        encoder.encode_card(Rank.EIGHT, Suit.DIAMONDS),
        encoder.encode_card(Rank.SEVEN, Suit.SPADES),
        encoder.encode_card(Rank.SIX, Suit.CLUBS),
        encoder.encode_card(Rank.FIVE, Suit.HEARTS),
    ]
    rank, tie, desc = evaluator.evaluate_hand(straight)
    print(f"{desc} (Rank: {rank.name})\n")
    
    # Test 5: Two Pair
    print("5. Two Pair Test:")
    two_pair = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.ACE, Suit.DIAMONDS),
        encoder.encode_card(Rank.KING, Suit.SPADES),
        encoder.encode_card(Rank.KING, Suit.CLUBS),
        encoder.encode_card(Rank.QUEEN, Suit.HEARTS),
    ]
    rank, tie, desc = evaluator.evaluate_hand(two_pair)
    print(f"{desc} (Rank: {rank.name})\n")
    
    # Test 6: Compare hands
    print("6. Hand Comparison:")
    hand1 = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.ACE, Suit.DIAMONDS),
        encoder.encode_card(Rank.KING, Suit.SPADES),
        encoder.encode_card(Rank.QUEEN, Suit.CLUBS),
        encoder.encode_card(Rank.JACK, Suit.HEARTS),
    ]
    hand2 = [
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.DIAMONDS),
        encoder.encode_card(Rank.QUEEN, Suit.SPADES),
        encoder.encode_card(Rank.JACK, Suit.CLUBS),
        encoder.encode_card(Rank.TEN, Suit.HEARTS),
    ]
    
    result = evaluator.compare_hands(hand1, hand2)
    rank1, _, desc1 = evaluator.evaluate_hand(hand1)
    rank2, _, desc2 = evaluator.evaluate_hand(hand2)
    
    print(f"Hand 1: {desc1}")
    print(f"Hand 2: {desc2}")
    print(f"Winner: {'Hand 1' if result == 1 else 'Hand 2' if result == -1 else 'Tie'}\n")
    
    # Test 7: Find winners among multiple players
    print("7. Multiple Players Test:")
    players = [
        ("Player1", [
            encoder.encode_card(Rank.ACE, Suit.HEARTS),
            encoder.encode_card(Rank.ACE, Suit.DIAMONDS),
            encoder.encode_card(Rank.KING, Suit.SPADES),
            encoder.encode_card(Rank.QUEEN, Suit.CLUBS),
            encoder.encode_card(Rank.JACK, Suit.HEARTS),
        ]),
        ("Player2", [
            encoder.encode_card(Rank.KING, Suit.HEARTS),
            encoder.encode_card(Rank.KING, Suit.DIAMONDS),
            encoder.encode_card(Rank.KING, Suit.SPADES),
            encoder.encode_card(Rank.QUEEN, Suit.CLUBS),
            encoder.encode_card(Rank.JACK, Suit.HEARTS),
        ]),
        ("Player3", [
            encoder.encode_card(Rank.QUEEN, Suit.HEARTS),
            encoder.encode_card(Rank.QUEEN, Suit.DIAMONDS),
            encoder.encode_card(Rank.JACK, Suit.SPADES),
            encoder.encode_card(Rank.TEN, Suit.CLUBS),
            encoder.encode_card(Rank.NINE, Suit.HEARTS),
        ]),
    ]
    
    winners = evaluator.find_winners(players)
    print(f"Winners: {len(winners)} player(s)")
    for player_id, rank, tie, desc in winners:
        print(f"  {player_id}: {desc}")