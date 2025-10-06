"""
Quantum Card Encoder for Quantum Poker
Maps 5-qubit states to playing cards with positive/negative amplitudes
"""

from typing import List, Tuple, Optional
from enum import Enum

class Suit(Enum):
    """Card suits with their amplitude signs"""
    HEARTS = ("♥", 1)      # Positive amplitude
    DIAMONDS = ("♦", 1)    # Positive amplitude
    SPADES = ("♠", -1)     # Negative amplitude
    CLUBS = ("♣", -1)      # Negative amplitude

class Rank(Enum):
    """Card ranks"""
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 11)
    QUEEN = ("Q", 12)
    KING = ("K", 13)
    ACE = ("A", 14)

class QuantumCard:
    """Represents a card in quantum state"""
    def __init__(self, qubits: List[int], amplitude: int = 1):
        """
        Args:
            qubits: List of 5 qubits [q4, q3, q2, q1, q0]
            amplitude: +1 or -1 (determines suit color)
        """
        if len(qubits) != 5:
            raise ValueError("Must have exactly 5 qubits")
        if not all(q in [0, 1] for q in qubits):
            raise ValueError("Qubits must be 0 or 1")
        if amplitude not in [-1, 1]:
            raise ValueError("Amplitude must be +1 or -1")
        
        self.qubits = qubits
        self.amplitude = amplitude
        self._entangled_with = None
    
    @property
    def state_value(self) -> int:
        """Convert qubits to integer (0-31)"""
        return sum(bit << i for i, bit in enumerate(reversed(self.qubits)))
    
    def __repr__(self):
        sign = "+" if self.amplitude == 1 else "-"
        qubits_str = "".join(map(str, self.qubits))
        return f"{sign}|{qubits_str}⟩"

class CardEncoder:
    """Encodes and decodes cards to/from quantum states"""
    
    def __init__(self):
        # Create mapping: state_value -> (rank, suit)
        self.state_to_card = {}
        self.card_to_state = {}
        self._initialize_mapping()
    
    def _initialize_mapping(self):
        """
        Create sequential mapping for 52 cards:
        States 0-12: Hearts (2-A)
        States 13-25: Diamonds (2-A)
        States 26-31, 0-6 (negative): Spades (2-A)
        States 7-19 (negative): Clubs (2-A)
        
        Leaving states 20-31 (negative) undefined
        """
        ranks = list(Rank)
        state_counter = 0
        
        # Positive amplitude: Hearts (0-12) and Diamonds (13-25)
        for suit in [Suit.HEARTS, Suit.DIAMONDS]:
            for rank in ranks:
                if state_counter < 32:  # Only use states 0-31
                    self.state_to_card[(state_counter, 1)] = (rank, suit)
                    self.card_to_state[(rank, suit)] = (state_counter, 1)
                    state_counter += 1
        
        # Negative amplitude: Spades (0-12) and Clubs (13-25)
        state_counter = 0
        for suit in [Suit.SPADES, Suit.CLUBS]:
            for rank in ranks:
                if state_counter < 32:
                    self.state_to_card[(state_counter, -1)] = (rank, suit)
                    self.card_to_state[(rank, suit)] = (state_counter, -1)
                    state_counter += 1
    
    def encode_card(self, rank: Rank, suit: Suit) -> QuantumCard:
        """Convert a classical card to quantum state"""
        if (rank, suit) not in self.card_to_state:
            raise ValueError(f"Invalid card: {rank.value[0]}{suit.value[0]}")
        
        state_value, amplitude = self.card_to_state[(rank, suit)]
        qubits = self._int_to_qubits(state_value)
        return QuantumCard(qubits, amplitude)
    
    def decode_card(self, quantum_card: QuantumCard) -> Optional[Tuple[Rank, Suit]]:
        """Convert quantum state to classical card"""
        key = (quantum_card.state_value, quantum_card.amplitude)
        
        if key not in self.state_to_card:
            return None  # Undefined state
        
        return self.state_to_card[key]
    
    def _int_to_qubits(self, value: int) -> List[int]:
        """Convert integer to 5-qubit representation"""
        if not 0 <= value < 32:
            raise ValueError(f"Value must be between 0-31, got {value}")
        
        binary = format(value, '05b')
        return [int(bit) for bit in binary]
    
    def create_deck(self) -> List[QuantumCard]:
        """Create a full deck of 52 quantum cards"""
        deck = []
        for (rank, suit), (state_value, amplitude) in self.card_to_state.items():
            qubits = self._int_to_qubits(state_value)
            deck.append(QuantumCard(qubits, amplitude))
        return deck
    
    def card_to_string(self, quantum_card: QuantumCard) -> str:
        """Convert quantum card to readable string (e.g., 'A♥')"""
        card_info = self.decode_card(quantum_card)
        if card_info is None:
            return "UNDEFINED"
        
        rank, suit = card_info
        return f"{rank.value[0]}{suit.value[0]}"
    
    def string_to_card(self, card_str: str) -> QuantumCard:
        """Convert string (e.g., 'A♥') to quantum card"""
        # Parse rank
        rank_str = card_str[:-1]
        suit_symbol = card_str[-1]
        
        # Find rank
        rank = None
        for r in Rank:
            if r.value[0] == rank_str:
                rank = r
                break
        
        # Find suit
        suit = None
        for s in Suit:
            if s.value[0] == suit_symbol:
                suit = s
                break
        
        if rank is None or suit is None:
            raise ValueError(f"Invalid card string: {card_str}")
        
        return self.encode_card(rank, suit)


# Example usage and testing
if __name__ == "__main__":
    encoder = CardEncoder()
    
    print("=== Quantum Card Encoding System ===\n")
    
    # Test encoding specific cards
    print("1. Encoding specific cards:")
    ace_hearts = encoder.encode_card(Rank.ACE, Suit.HEARTS)
    print(f"Ace of Hearts: {ace_hearts}")
    print(f"Decoded: {encoder.card_to_string(ace_hearts)}\n")
    
    ace_spades = encoder.encode_card(Rank.ACE, Suit.SPADES)
    print(f"Ace of Spades: {ace_spades}")
    print(f"Decoded: {encoder.card_to_string(ace_spades)}\n")
    
    # Show amplitude difference
    print("2. Amplitude difference (positive vs negative):")
    print(f"Hearts (positive): {encoder.encode_card(Rank.KING, Suit.HEARTS)}")
    print(f"Spades (negative): {encoder.encode_card(Rank.KING, Suit.SPADES)}\n")
    
    # Create full deck
    print("3. Creating full deck (52 cards):")
    deck = encoder.create_deck()
    print(f"Deck size: {len(deck)} cards")
    print(f"First 5 cards: {[encoder.card_to_string(c) for c in deck[:5]]}")
    print(f"Last 5 cards: {[encoder.card_to_string(c) for c in deck[-5:]]}\n")
    
    # Test all suits
    print("4. Testing all suits with Queen:")
    for suit in Suit:
        card = encoder.encode_card(Rank.QUEEN, suit)
        print(f"Q{suit.value[0]}: {card} -> {encoder.card_to_string(card)}")
    
    print("\n5. State value ranges:")
    print("Hearts: states 0-12 (positive)")
    print("Diamonds: states 13-25 (positive)")
    print("Spades: states 0-12 (negative)")
    print("Clubs: states 13-25 (negative)")
    print("Undefined: states 26-31 (positive), 20-31 (negative)")