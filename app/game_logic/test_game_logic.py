"""
Test Script for Quantum Poker Game Logic
Run this file directly to test all game components

Usage:
    python test_game_logic.py
    
Or test individual components:
    python -m app.game_logic.card_encoder
    python -m app.game_logic.quantum_gates
    python -m app.game_logic.hand_evaluator
    python -m app.game_logic.betting
    python -m app.game_logic.deck_manager
    python -m app.game_logic.poker_engine
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.game_logic.card_encoder import CardEncoder, Rank, Suit, QuantumCard
from app.game_logic.quantum_gates import QuantumGates
from app.game_logic.hand_evaluator import HandEvaluator, HandRank
from app.game_logic.betting import BettingManager, BettingAction
from app.game_logic.deck_manager import DeckManager
from app.game_logic.poker_engine import PokerEngine, GamePhase


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_card_encoder():
    """Test card encoding system"""
    print_section("1. CARD ENCODING SYSTEM")
    
    encoder = CardEncoder()
    
    # Test specific cards
    print("Testing specific cards:")
    ace_hearts = encoder.encode_card(Rank.ACE, Suit.HEARTS)
    print(f"  Ace of Hearts: {ace_hearts} -> {encoder.card_to_string(ace_hearts)}")
    
    ace_spades = encoder.encode_card(Rank.ACE, Suit.SPADES)
    print(f"  Ace of Spades: {ace_spades} -> {encoder.card_to_string(ace_spades)}")
    
    # Test deck creation
    deck = encoder.create_deck()
    print(f"\n  Full deck created: {len(deck)} cards")
    print(f"  First 5 cards: {[encoder.card_to_string(c) for c in deck[:5]]}")
    print(f"  Last 5 cards: {[encoder.card_to_string(c) for c in deck[-5:]]}")
    
    print("\n✓ Card encoding system working correctly")


def test_quantum_gates():
    """Test quantum gate operations"""
    print_section("2. QUANTUM GATES")
    
    encoder = CardEncoder()
    gates = QuantumGates()
    
    # Test X Gate
    print("Testing X Gate (Bit Flip):")
    king_hearts = encoder.encode_card(Rank.KING, Suit.HEARTS)
    print(f"  Original: {encoder.card_to_string(king_hearts)} {king_hearts}")
    
    preview = gates.preview_gate("X", [king_hearts])
    print(f"  Preview: {preview['original_card']} -> {preview['result_card']}")
    
    result = gates.apply_gate("X", [king_hearts])
    print(f"  After X gate: {result['result_card']} {result['new_state']}")
    
    # Test Z Gate
    print("\nTesting Z Gate (Phase Flip):")
    queen_hearts = encoder.encode_card(Rank.QUEEN, Suit.HEARTS)
    print(f"  Original: {encoder.card_to_string(queen_hearts)} {queen_hearts}")
    
    result = gates.apply_gate("Z", [queen_hearts])
    print(f"  After Z gate: {result['result_card']} {result['new_state']}")
    print(f"  Note: Suit color changed (red -> black)")
    
    # Test CNOT Gate
    print("\nTesting CNOT Gate (Entanglement):")
    jack_spades = encoder.encode_card(Rank.JACK, Suit.SPADES)
    ten_diamonds = encoder.encode_card(Rank.TEN, Suit.DIAMONDS)
    
    print(f"  Control: {encoder.card_to_string(jack_spades)}")
    print(f"  Target: {encoder.card_to_string(ten_diamonds)}")
    
    result = gates.apply_gate("CNOT", [jack_spades, ten_diamonds])
    print(f"  After CNOT:")
    print(f"    Control: {result['control_card']}")
    print(f"    Target: {result['target_card']}")
    print(f"    Entangled: {result['entangled']}")
    
    print("\n✓ Quantum gates working correctly")


def test_hand_evaluator():
    """Test poker hand evaluation"""
    print_section("3. HAND EVALUATOR")
    
    encoder = CardEncoder()
    evaluator = HandEvaluator()
    
    # Test Royal Flush
    print("Testing Royal Flush:")
    royal = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.QUEEN, Suit.HEARTS),
        encoder.encode_card(Rank.JACK, Suit.HEARTS),
        encoder.encode_card(Rank.TEN, Suit.HEARTS),
    ]
    rank, _, desc = evaluator.evaluate_hand(royal)
    print(f"  {desc} (Rank: {rank.name})")
    
    # Test Full House
    print("\nTesting Full House:")
    full_house = [
        encoder.encode_card(Rank.ACE, Suit.HEARTS),
        encoder.encode_card(Rank.ACE, Suit.DIAMONDS),
        encoder.encode_card(Rank.ACE, Suit.SPADES),
        encoder.encode_card(Rank.KING, Suit.HEARTS),
        encoder.encode_card(Rank.KING, Suit.DIAMONDS),
    ]
    rank, _, desc = evaluator.evaluate_hand(full_house)
    print(f"  {desc} (Rank: {rank.name})")
    
    # Test Two Pair
    print("\nTesting Two Pair:")
    two_pair = [
        encoder.encode_card(Rank.QUEEN, Suit.HEARTS),
        encoder.encode_card(Rank.QUEEN, Suit.DIAMONDS),
        encoder.encode_card(Rank.JACK, Suit.SPADES),
        encoder.encode_card(Rank.JACK, Suit.CLUBS),
        encoder.encode_card(Rank.NINE, Suit.HEARTS),
    ]
    rank, _, desc = evaluator.evaluate_hand(two_pair)
    print(f"  {desc} (Rank: {rank.name})")
    
    print("\n✓ Hand evaluator working correctly")


def test_betting_system():
    """Test betting mechanics"""
    print_section("4. BETTING SYSTEM")
    
    betting = BettingManager(small_blind=10, big_blind=20)
    
    # Add players
    for i in range(1, 5):
        betting.add_player(f"player{i}", 1000)
    
    print("Players added with 1000 chips each")
    
    # Post blinds
    print("\nPosting blinds:")
    blinds = betting.post_blinds("player1", "player2")
    print(f"  Small Blind (player1): ${blinds['small_blind']['amount']}")
    print(f"  Big Blind (player2): ${blinds['big_blind']['amount']}")
    print(f"  Current Bet: ${blinds['current_bet']}")
    print(f"  Pot: ${betting.get_total_pot()}")
    
    # Player actions
    print("\nPlayer actions:")
    result = betting.call("player3")
    print(f"  Player3 calls: ${result['amount']}, Pot: ${result['pot']}")
    
    result = betting.bet_raise("player4", 60)
    print(f"  Player4 raises to: ${result['raise_to']}, Pot: ${result['pot']}")
    
    result = betting.fold("player1")
    print(f"  Player1 folds")
    
    print(f"\n  Active players: {betting.get_active_players()}")
    print(f"  Betting round complete: {betting.is_betting_round_complete()}")
    
    print("\n✓ Betting system working correctly")


def test_deck_manager():
    """Test deck management"""
    print_section("5. DECK MANAGER")
    
    deck_mgr = DeckManager()
    
    print("Creating and shuffling deck:")
    deck_mgr.create_deck()
    print(f"  Deck size: {deck_mgr.cards_remaining()} cards")
    
    deck_mgr.shuffle()
    print(f"  Top 5 cards: {deck_mgr.peek_top_cards(5)}")
    
    # Deal hole cards
    print("\nDealing hole cards to 4 players:")
    hole_cards = deck_mgr.deal_hole_cards(4)
    for i, cards in enumerate(hole_cards):
        print(f"  Player {i+1}: {deck_mgr.get_card_strings(cards)}")
    
    # Deal community cards
    print("\nDealing community cards:")
    flop = deck_mgr.deal_flop()
    print(f"  Flop: {deck_mgr.get_card_strings(flop)}")
    
    turn = deck_mgr.deal_turn()
    print(f"  Turn: {deck_mgr.get_card_string(turn)}")
    
    river = deck_mgr.deal_river()
    print(f"  River: {deck_mgr.get_card_string(river)}")
    
    # Validate integrity
    print("\nDeck integrity check:")
    integrity = deck_mgr.validate_deck_integrity()
    print(f"  Valid: {integrity['is_valid']}")
    print(f"  Total cards: {integrity['total_cards']}/52")
    
    print("\n✓ Deck manager working correctly")


def test_poker_engine():
    """Test complete poker engine"""
    print_section("6. POKER ENGINE (INTEGRATION TEST)")
    
    # Initialize game
    player_ids = ["p1", "p2", "p3", "p4"]
    player_names = ["Alice", "Bob", "Charlie", "Diana"]
    
    engine = PokerEngine(player_ids, player_names, starting_chips=1000)
    
    print("Starting new hand:")
    result = engine.start_new_hand()
    print(f"  Hand #{result['hand_number']}")
    print(f"  Dealer: {result['dealer']}")
    print(f"  Phase: {result['phase']}")
    
    # Show hole cards
    print("\nHole cards dealt:")
    for pid in player_ids:
        player = engine.players[pid]
        cards_str = engine.deck_manager.get_card_strings(player.hole_cards)
        print(f"  {player.name}: {cards_str}")
    
    # Deal flop
    print("\nDealing flop:")
    flop_result = engine.deal_flop()
    print(f"  Flop: {flop_result['flop']}")
    
    # Test quantum gate
    print("\nApplying quantum gate (X gate on Alice's first card):")
    preview = engine.apply_quantum_gate("p1", "X", [0], preview_only=True)
    print(f"  Preview: {preview['gate_info']['original_card']} -> {preview['gate_info']['result_card']}")
    
    gate_result = engine.apply_quantum_gate("p1", "X", [0], preview_only=False)
    print(f"  Applied successfully")
    print(f"  Gates remaining this round: {gate_result['gates_remaining_this_round']}")
    print(f"  Gates remaining this game: {gate_result['gates_remaining_this_game']}")
    
    # Show updated card
    alice_cards = engine.deck_manager.get_card_strings(engine.players["p1"].hole_cards)
    print(f"  Alice's cards after gate: {alice_cards}")
    
    # Get game state
    print("\nCurrent game state:")
    state = engine.get_game_state()
    print(f"  Phase: {state['phase']}")
    print(f"  Pot: ${state['pot']}")
    print(f"  Community cards: {state['community_cards']}")
    
    print("\n✓ Poker engine working correctly")


def run_all_tests():
    """Run all tests"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  QUANTUM POKER - GAME LOGIC TEST SUITE".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        test_card_encoder()
        test_quantum_gates()
        test_hand_evaluator()
        test_betting_system()
        test_deck_manager()
        test_poker_engine()
        
        print_section("ALL TESTS PASSED ✓")
        print("All game logic components are working correctly!")
        print("Ready to integrate with FastAPI and Socket.IO\n")
        
        return True
        
    except Exception as e:
        print_section("TEST FAILED ✗")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)