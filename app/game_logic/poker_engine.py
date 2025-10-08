"""
Poker Engine for Quantum Poker
Manages Texas Hold'em game flow with quantum gate integration
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from app.game_logic.card_encoder import QuantumCard, CardEncoder
from app.game_logic.deck_manager import DeckManager
from app.game_logic.betting import BettingManager, BettingRound, BettingAction
from app.game_logic.hand_evaluator import HandEvaluator
from app.game_logic.quantum_gates import QuantumGates


class GamePhase(Enum):
    """Phases of the game"""
    WAITING = "waiting"
    DEALING = "dealing"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    COMPLETE = "complete"


@dataclass
class PlayerGameState:
    """Tracks player state during a game"""
    player_id: str
    name: str
    position: int
    chips: int
    hole_cards: List[QuantumCard] = field(default_factory=list)
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    gates_used_this_round: int = 0
    gates_used_this_game: int = 0
    cards_collapsed: bool = False
    is_active: bool = True  # Not folded
    
    def can_apply_gate(self) -> bool:
        """Check if player can apply a quantum gate"""
        return (self.gates_used_this_round < 2 and 
                self.gates_used_this_game < 4 and 
                not self.cards_collapsed and
                self.is_active)
    
    def apply_gate(self):
        """Record that a gate was applied"""
        self.gates_used_this_round += 1
        self.gates_used_this_game += 1
    
    def reset_round_gates(self):
        """Reset gate count for new betting round"""
        self.gates_used_this_round = 0
    
    def collapse_cards(self):
        """Mark cards as collapsed"""
        self.cards_collapsed = True


class PokerEngine:
    """Main poker game engine"""
    
    def __init__(
        self, 
        player_ids: List[str],
        player_names: List[str],
        starting_chips: int = 1000,
        small_blind: int = 10,
        big_blind: int = 20
    ):
        if len(player_ids) != len(player_names):
            raise ValueError("Player IDs and names must match")
        if len(player_ids) < 2 or len(player_ids) > 4:
            raise ValueError("Must have 2-4 players")
        
        # Game components
        self.deck_manager = DeckManager()
        self.betting_manager = BettingManager(small_blind, big_blind)
        self.hand_evaluator = HandEvaluator()
        self.quantum_gates = QuantumGates()
        self.encoder = CardEncoder()
        
        # Initialize players
        self.players: Dict[str, PlayerGameState] = {}
        for i, (pid, name) in enumerate(zip(player_ids, player_names)):
            self.players[pid] = PlayerGameState(
                player_id=pid,
                name=name,
                position=i,
                chips=starting_chips
            )
            self.betting_manager.add_player(pid, starting_chips)
        
        # Game state
        self.phase = GamePhase.WAITING
        self.community_cards: List[QuantumCard] = []
        self.dealer_position = 0
        self.current_player_index = 0
        self.hand_number = 0
        self.winners: List[Tuple[str, int, str]] = []
        
    def get_player_order(self) -> List[str]:
        """Get players in order starting from dealer+1"""
        player_list = list(self.players.keys())
        rotated = player_list[self.dealer_position+1:] + player_list[:self.dealer_position+1]
        return rotated
    
    def get_active_players(self) -> List[str]:
        """Get players who haven't folded"""
        return [pid for pid, p in self.players.items() if p.is_active]
    
    def start_new_hand(self):
        """Start a new hand"""
        self.hand_number += 1
        self.phase = GamePhase.DEALING
        self.community_cards = []
        self.winners = []
        
        # Reset player states
        for player in self.players.values():
            player.hole_cards = []
            player.is_dealer = False
            player.is_small_blind = False
            player.is_big_blind = False
            player.gates_used_this_round = 0
            player.gates_used_this_game = 0
            player.cards_collapsed = False
            player.is_active = True
        
        # Rotate dealer button
        player_ids = list(self.players.keys())
        dealer_id = player_ids[self.dealer_position]
        self.players[dealer_id].is_dealer = True
        
        # Assign blinds
        num_players = len(player_ids)
        sb_position = (self.dealer_position + 1) % num_players
        bb_position = (self.dealer_position + 2) % num_players
        
        sb_id = player_ids[sb_position]
        bb_id = player_ids[bb_position]
        
        self.players[sb_id].is_small_blind = True
        self.players[bb_id].is_big_blind = True
        
        # Create and shuffle deck
        self.deck_manager.create_deck()
        self.deck_manager.shuffle()
        
        # Deal hole cards
        player_order = self.get_player_order()
        hole_cards = self.deck_manager.deal_hole_cards(len(player_order))
        
        for i, pid in enumerate(player_order):
            self.players[pid].hole_cards = hole_cards[i]
        
        # Post blinds
        blind_result = self.betting_manager.post_blinds(sb_id, bb_id)
        
        # Update player chips after blinds
        for pid in [sb_id, bb_id]:
            self.players[pid].chips = self.betting_manager.players[pid].chips
        
        # Move to preflop
        self.phase = GamePhase.PREFLOP
        
        # Set first player to act (after big blind in preflop)
        if num_players == 2:
            # Heads up: dealer is small blind
            self.current_player_index = self.dealer_position
        else:
            self.current_player_index = (bb_position + 1) % num_players
        
        return {
            "hand_number": self.hand_number,
            "dealer": dealer_id,
            "small_blind": sb_id,
            "big_blind": bb_id,
            "blinds_posted": blind_result,
            "phase": self.phase.value
        }

    def is_game_over(self) -> bool:
        """Return True if only one player has chips left."""
        players_with_chips = [p for p in self.players.values() if p.chips > 0]
        return len(players_with_chips) <= 1

    def start_next_hand_if_possible(self) -> Optional[Dict]:
        """If the game is not over, rotate dealer and start the next hand.
        Returns next hand info dict if started, else None.
        """
        # Remove busted players from being active in next hand
        for pid, p in list(self.players.items()):
            if p.chips <= 0:
                p.is_active = False
        if self.is_game_over():
            return None
        self.advance_dealer()
        return self.start_new_hand()
    
    def deal_flop(self):
        """Deal the flop (3 community cards)"""
        if self.phase != GamePhase.PREFLOP:
            raise ValueError("Can only deal flop after preflop")
        
        # Check if only one player remains (auto-win)
        remaining_player = self.betting_manager.get_remaining_active_player()
        if remaining_player:
            self.phase = GamePhase.COMPLETE
            return {
                "phase": self.phase.value,
                "auto_win": True,
                "winner": remaining_player,
                "message": f"Player {self.players[remaining_player].name} wins automatically"
            }
        
        self.community_cards.extend(self.deck_manager.deal_flop())
        self.phase = GamePhase.FLOP
        self.betting_manager.start_new_betting_round(BettingRound.FLOP)
        
        # Reset round gates for all players
        for player in self.players.values():
            player.reset_round_gates()
        
        # First player to act is first active player after dealer
        player_ids = list(self.players.keys())
        for i in range(1, len(player_ids) + 1):
            idx = (self.dealer_position + i) % len(player_ids)
            pid = player_ids[idx]
            if self.players[pid].is_active:
                self.current_player_index = idx
                break
        
        return {
            "phase": self.phase.value,
            "flop": self.deck_manager.get_card_strings(self.community_cards[-3:]),
            "community_cards": self.deck_manager.get_card_strings(self.community_cards)
        }
    
    def deal_turn(self):
        """Deal the turn (1 community card)"""
        if self.phase != GamePhase.FLOP:
            raise ValueError("Can only deal turn after flop")
        
        # Check if only one player remains (auto-win)
        remaining_player = self.betting_manager.get_remaining_active_player()
        if remaining_player:
            self.phase = GamePhase.COMPLETE
            return {
                "phase": self.phase.value,
                "auto_win": True,
                "winner": remaining_player,
                "message": f"Player {self.players[remaining_player].name} wins automatically"
            }
        
        turn_card = self.deck_manager.deal_turn()
        if turn_card:
            self.community_cards.append(turn_card)
        
        self.phase = GamePhase.TURN
        self.betting_manager.start_new_betting_round(BettingRound.TURN)
        
        # Reset round gates
        for player in self.players.values():
            player.reset_round_gates()
        
        # Set first active player after dealer
        player_ids = list(self.players.keys())
        for i in range(1, len(player_ids) + 1):
            idx = (self.dealer_position + i) % len(player_ids)
            pid = player_ids[idx]
            if self.players[pid].is_active:
                self.current_player_index = idx
                break
        
        return {
            "phase": self.phase.value,
            "turn": self.encoder.card_to_string(turn_card),
            "community_cards": self.deck_manager.get_card_strings(self.community_cards)
        }
    
    def deal_river(self):
        """Deal the river (1 community card)"""
        if self.phase != GamePhase.TURN:
            raise ValueError("Can only deal river after turn")
        
        # Check if only one player remains (auto-win)
        remaining_player = self.betting_manager.get_remaining_active_player()
        if remaining_player:
            self.phase = GamePhase.COMPLETE
            return {
                "phase": self.phase.value,
                "auto_win": True,
                "winner": remaining_player,
                "message": f"Player {self.players[remaining_player].name} wins automatically"
            }
        
        river_card = self.deck_manager.deal_river()
        if river_card:
            self.community_cards.append(river_card)
        
        self.phase = GamePhase.RIVER
        self.betting_manager.start_new_betting_round(BettingRound.RIVER)
        
        # Reset round gates
        for player in self.players.values():
            player.reset_round_gates()
        
        # Set first active player after dealer
        player_ids = list(self.players.keys())
        for i in range(1, len(player_ids) + 1):
            idx = (self.dealer_position + i) % len(player_ids)
            pid = player_ids[idx]
            if self.players[pid].is_active:
                self.current_player_index = idx
                break
        
        return {
            "phase": self.phase.value,
            "river": self.encoder.card_to_string(river_card),
            "community_cards": self.deck_manager.get_card_strings(self.community_cards)
        }
    
    def player_action(self, player_id: str, action: str, amount: int = 0) -> Dict:
        """
        Handle player betting action
        
        Args:
            player_id: Player making action
            action: "fold", "check", "call", "raise"
            amount: Amount for raise (total amount to raise TO)
        """
        # Validate player exists
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found")
        
        player = self.players[player_id]
        
        if not player.is_active:
            raise ValueError(f"Player {player_id} has folded")
        
        # Validate it's player's turn
        player_ids = list(self.players.keys())
        current_player_id = player_ids[self.current_player_index]
        if current_player_id != player_id:
            raise ValueError(f"Not {player_id}'s turn. Current player: {current_player_id}")
        
        # Execute action
        result = None
        action = action.lower()
        
        try:
            if action == "fold":
                result = self.betting_manager.fold(player_id)
                player.is_active = False
            
            elif action == "check":
                result = self.betting_manager.check(player_id)
            
            elif action == "call":
                result = self.betting_manager.call(player_id)
                player.chips = self.betting_manager.players[player_id].chips
            
            elif action == "raise":
                result = self.betting_manager.bet_raise(player_id, amount)
                player.chips = self.betting_manager.players[player_id].chips
            
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            raise ValueError(f"Action failed: {str(e)}")
        
        # Move to next player
        self._advance_to_next_player()
        
        # Check if betting round is complete
        if self.betting_manager.is_betting_round_complete():
            result["betting_round_complete"] = True
            
            # Check if only one player remains (auto-win)
            remaining_player = self.betting_manager.get_remaining_active_player()
            if remaining_player:
                result["auto_win"] = True
                result["winner"] = remaining_player
                result["next_phase"] = GamePhase.COMPLETE.value
            else:
                result["next_phase"] = self._get_next_phase()
        else:
            result["betting_round_complete"] = False
            result["next_player"] = player_ids[self.current_player_index]
        
        return result
    
    def apply_quantum_gate(
        self, 
        player_id: str, 
        gate_type: str, 
        card_indices: List[int],
        preview_only: bool = False
    ) -> Dict:
        """
        Apply quantum gate to player's cards
        
        Args:
            player_id: Player applying gate
            gate_type: "X", "Z", or "CNOT"
            card_indices: [0] for X/Z, [0, 1] for CNOT
            preview_only: If True, only preview the result
        """
        player = self.players[player_id]
        
        if not preview_only and not player.can_apply_gate():
            raise ValueError(f"Player {player_id} cannot apply gate")
        
        # Get cards to apply gate to
        cards = [player.hole_cards[i] for i in card_indices]
        
        if preview_only:
            preview = self.quantum_gates.preview_gate(gate_type, cards)
            return {
                "preview": True,
                "gate_info": preview
            }
        
        # Apply gate
        result = self.quantum_gates.apply_gate(gate_type, cards)
        player.apply_gate()
        
        return {
            "preview": False,
            "gate_applied": True,
            "gate_info": result,
            "gates_remaining_this_round": 2 - player.gates_used_this_round,
            "gates_remaining_this_game": 4 - player.gates_used_this_game
        }
    
    def collapse_player_cards(self, player_id: str) -> Dict:
        """Manually collapse player's cards"""
        player = self.players[player_id]
        
        if player.cards_collapsed:
            raise ValueError(f"Player {player_id} cards already collapsed")
        
        collapse_result = self.quantum_gates.collapse_cards(player.hole_cards)
        player.collapse_cards()
        
        return {
            "player_id": player_id,
            "collapsed": True,
            "cards": self.deck_manager.get_card_strings(player.hole_cards),
            "collapse_info": collapse_result
        }
    
    def auto_collapse_all_cards(self):
        """Auto-collapse all player cards at showdown"""
        results = {}
        
        for pid, player in self.players.items():
            if player.is_active and not player.cards_collapsed:
                collapse_result = self.quantum_gates.collapse_cards(player.hole_cards)
                player.collapse_cards()
                results[pid] = {
                    "cards": self.deck_manager.get_card_strings(player.hole_cards),
                    "collapse_info": collapse_result
                }
        
        return results
    
    def handle_auto_win(self, winner_id: str) -> Dict:
        """Handle automatic win when only one player remains"""
        self.phase = GamePhase.COMPLETE
        
        # Get total pot amount
        total_pot = self.betting_manager.get_total_pot()
        
        # Winner gets all chips
        self.players[winner_id].chips += total_pot
        
        # Store winner info
        self.winners = [(winner_id, 0, "Auto-win (all others folded)")]
        
        return {
            "phase": self.phase.value,
            "auto_win": True,
            "winner": winner_id,
            "winner_name": self.players[winner_id].name,
            "winnings": total_pot,
            "message": f"{self.players[winner_id].name} wins automatically - all other players folded"
        }
    
    def showdown(self) -> Dict:
        """Evaluate hands and determine winner(s)"""
        self.phase = GamePhase.SHOWDOWN
        
        # Auto-collapse any remaining cards
        collapse_results = self.auto_collapse_all_cards()
        
        # Get active players with their full hands
        players_hands = []
        for pid, player in self.players.items():
            if player.is_active:
                full_hand = player.hole_cards + self.community_cards
                players_hands.append((pid, full_hand))
        
        # Find winners
        winners = self.hand_evaluator.find_winners(players_hands)
        
        # Prepare winner info for pot distribution
        winner_ranks = [(pid, rank.value) for pid, rank, _, _ in winners]
        
        # Create side pots if needed
        self.betting_manager.create_side_pots()
        
        # Distribute pot
        winnings = self.betting_manager.distribute_pot(winner_ranks)
        
        # Update player chips
        for pid, amount in winnings.items():
            self.players[pid].chips += amount
        
        # Store winners
        self.winners = [(pid, rank.value, desc) for pid, rank, _, desc in winners]
        
        self.phase = GamePhase.COMPLETE
        
        return {
            "phase": self.phase.value,
            "winners": [
                {
                    "player_id": pid,
                    "hand_rank": rank,
                    "description": desc,
                    "winnings": winnings.get(pid, 0)
                }
                for pid, rank, desc in self.winners
            ],
            "pots": [
                {
                    "amount": pot.amount,
                    "eligible_players": pot.eligible_players,
                    "is_main_pot": pot.is_main_pot
                }
                for pot in self.betting_manager.pots
            ],
            "collapse_results": collapse_results
        }
    
    def _advance_to_next_player(self):
        """Move to next active player"""
        player_ids = list(self.players.keys())
        num_players = len(player_ids)
        
        for _ in range(num_players):
            self.current_player_index = (self.current_player_index + 1) % num_players
            next_pid = player_ids[self.current_player_index]
            
            # Check if player is active and can act
            if (self.players[next_pid].is_active and 
                not self.betting_manager.players[next_pid].is_all_in):
                break
    
    def _get_next_phase(self) -> str:
        """Get the next game phase"""
        phase_order = [
            GamePhase.PREFLOP,
            GamePhase.FLOP,
            GamePhase.TURN,
            GamePhase.RIVER,
            GamePhase.SHOWDOWN
        ]
        
        try:
            current_idx = phase_order.index(self.phase)
            if current_idx < len(phase_order) - 1:
                return phase_order[current_idx + 1].value
        except ValueError:
            pass
        
        return GamePhase.SHOWDOWN.value
    
    def get_game_state(self) -> Dict:
        """Get complete game state"""
        return {
            "hand_number": self.hand_number,
            "phase": self.phase.value,
            "dealer_position": self.dealer_position,
            "current_player": list(self.players.keys())[self.current_player_index],
            "pot": self.betting_manager.get_total_pot(),
            "current_bet": self.betting_manager.current_bet,
            "community_cards": self.deck_manager.get_card_strings(self.community_cards),
            "players": {
                pid: {
                    "name": p.name,
                    "position": p.position,
                    "chips": p.chips,
                    "hole_cards": self.deck_manager.get_card_strings(p.hole_cards) if p.is_active else [],
                    "is_dealer": p.is_dealer,
                    "is_small_blind": p.is_small_blind,
                    "is_big_blind": p.is_big_blind,
                    "is_active": p.is_active,
                    "gates_used_this_round": p.gates_used_this_round,
                    "gates_used_this_game": p.gates_used_this_game,
                    "cards_collapsed": p.cards_collapsed,
                    "can_apply_gate": p.can_apply_gate()
                }
                for pid, p in self.players.items()
            },
            "betting_state": self.betting_manager.get_all_states()
        }
    
    def advance_dealer(self):
        """Move dealer button to next player (for next hand)"""
        self.dealer_position = (self.dealer_position + 1) % len(self.players)


# Example usage and testing
if __name__ == "__main__":
    print("=== Poker Engine Testing ===\n")
    
    # Initialize game with 4 players
    player_ids = ["p1", "p2", "p3", "p4"]
    player_names = ["Alice", "Bob", "Charlie", "Diana"]
    
    engine = PokerEngine(player_ids, player_names, starting_chips=1000)
    
    print("1. Starting new hand:")
    hand_result = engine.start_new_hand()
    print(f"Hand #{hand_result['hand_number']}")
    print(f"Dealer: {hand_result['dealer']}")
    print(f"Small Blind: {hand_result['small_blind']}")
    print(f"Big Blind: {hand_result['big_blind']}")
    print(f"Phase: {hand_result['phase']}\n")
    
    # Show player cards
    print("2. Hole cards:")
    for pid in player_ids:
        player = engine.players[pid]
        cards_str = engine.deck_manager.get_card_strings(player.hole_cards)
        print(f"{player.name}: {cards_str}")
    print()
    
    # Preflop betting
    print("3. Preflop betting:")
    state = engine.get_game_state()
    print(f"Current player: {state['current_player']}")
    print(f"Pot: ${state['pot']}\n")
    
    # Deal flop
    print("4. Dealing flop:")
    flop_result = engine.deal_flop()
    print(f"Flop: {flop_result['flop']}")
    print(f"Phase: {flop_result['phase']}\n")
    
    # Test quantum gate preview
    print("5. Quantum gate preview (Player 1, X gate on card 0):")
    preview = engine.apply_quantum_gate("p1", "X", [0], preview_only=True)
    print(f"Preview: {preview['gate_info']}\n")
    
    # Apply quantum gate
    print("6. Applying quantum gate:")
    gate_result = engine.apply_quantum_gate("p1", "X", [0], preview_only=False)
    print(f"Gate applied: {gate_result['gate_applied']}")
    print(f"Gates remaining this round: {gate_result['gates_remaining_this_round']}")
    print(f"Gates remaining this game: {gate_result['gates_remaining_this_game']}\n")
    
    # Show updated card
    print("7. Player 1's cards after gate:")
    cards_str = engine.deck_manager.get_card_strings(engine.players["p1"].hole_cards)
    print(f"Alice: {cards_str}\n")
    
    print("Game engine initialized successfully!")
    print(f"Total chips in play: {sum(p.chips for p in engine.players.values())}")
    print(f"Pot: ${engine.betting_manager.get_total_pot()}")