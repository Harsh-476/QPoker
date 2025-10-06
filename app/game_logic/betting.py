"""
Betting System for Quantum Poker
Handles all betting logic including raises, calls, folds, all-ins, pots, and side pots
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field


class BettingAction(Enum):
    """Types of betting actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class BettingRound(Enum):
    """Betting rounds in Texas Hold'em"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class PlayerBettingState:
    """Tracks a player's betting state"""
    player_id: str
    chips: int
    bet_this_round: int = 0
    total_bet_in_pot: int = 0
    is_all_in: bool = False
    has_folded: bool = False
    has_acted: bool = False
    
    def can_bet(self) -> bool:
        """Check if player can make a bet"""
        return not self.has_folded and not self.is_all_in and self.chips > 0
    
    def reset_round(self):
        """Reset betting state for new round"""
        self.bet_this_round = 0
        self.has_acted = False


@dataclass
class Pot:
    """Represents a pot (main or side pot)"""
    amount: int = 0
    eligible_players: List[str] = field(default_factory=list)
    is_main_pot: bool = True
    
    def add_chips(self, amount: int):
        """Add chips to the pot"""
        self.amount += amount
    
    def __repr__(self):
        pot_type = "Main" if self.is_main_pot else "Side"
        return f"{pot_type} Pot: ${self.amount} ({len(self.eligible_players)} players)"


class BettingManager:
    """Manages all betting logic for a poker game"""
    
    def __init__(self, small_blind: int = 10, big_blind: int = 20):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.current_bet = 0
        self.minimum_raise = big_blind
        self.pots: List[Pot] = [Pot(is_main_pot=True)]
        self.players: Dict[str, PlayerBettingState] = {}
        self.current_round = BettingRound.PREFLOP
        
    def add_player(self, player_id: str, starting_chips: int):
        """Add a player to the betting system"""
        self.players[player_id] = PlayerBettingState(
            player_id=player_id,
            chips=starting_chips
        )
    
    def remove_player(self, player_id: str):
        """Remove a player from the betting system"""
        if player_id in self.players:
            del self.players[player_id]
    
    def post_blinds(self, small_blind_player: str, big_blind_player: str) -> Dict:
        """
        Post small and big blinds at start of hand
        
        Returns:
            Dictionary with blind posting results
        """
        results = {
            "small_blind": {},
            "big_blind": {},
            "current_bet": 0
        }
        
        # Post small blind
        sb_player = self.players[small_blind_player]
        sb_amount = min(self.small_blind, sb_player.chips)
        sb_player.chips -= sb_amount
        sb_player.bet_this_round = sb_amount
        sb_player.total_bet_in_pot = sb_amount
        self.pots[0].add_chips(sb_amount)
        
        if sb_amount == sb_player.chips + sb_amount:  # Was all-in
            sb_player.is_all_in = True
        
        results["small_blind"] = {
            "player_id": small_blind_player,
            "amount": sb_amount,
            "is_all_in": sb_player.is_all_in,
            "remaining_chips": sb_player.chips
        }
        
        # Post big blind
        bb_player = self.players[big_blind_player]
        bb_amount = min(self.big_blind, bb_player.chips)
        bb_player.chips -= bb_amount
        bb_player.bet_this_round = bb_amount
        bb_player.total_bet_in_pot = bb_amount
        self.pots[0].add_chips(bb_amount)
        
        if bb_amount == bb_player.chips + bb_amount:  # Was all-in
            bb_player.is_all_in = True
        
        results["big_blind"] = {
            "player_id": big_blind_player,
            "amount": bb_amount,
            "is_all_in": bb_player.is_all_in,
            "remaining_chips": bb_player.chips
        }
        
        # Set current bet to big blind
        self.current_bet = bb_amount
        self.minimum_raise = self.big_blind
        results["current_bet"] = self.current_bet
        
        return results
    
    def can_check(self, player_id: str) -> bool:
        """Check if player can check (no bet to call)"""
        player = self.players[player_id]
        return player.bet_this_round == self.current_bet and player.can_bet()
    
    def can_call(self, player_id: str) -> bool:
        """Check if player can call"""
        player = self.players[player_id]
        return (player.bet_this_round < self.current_bet and 
                player.can_bet() and 
                player.chips > 0)
    
    def can_raise(self, player_id: str) -> bool:
        """Check if player can raise"""
        player = self.players[player_id]
        call_amount = self.current_bet - player.bet_this_round
        return player.can_bet() and player.chips > call_amount
    
    def get_call_amount(self, player_id: str) -> int:
        """Get amount needed to call"""
        player = self.players[player_id]
        return self.current_bet - player.bet_this_round
    
    def get_min_raise_amount(self, player_id: str) -> int:
        """Get minimum raise amount"""
        call_amount = self.get_call_amount(player_id)
        return call_amount + self.minimum_raise
    
    def fold(self, player_id: str) -> Dict:
        """Player folds"""
        player = self.players[player_id]
        
        if player.has_folded:
            raise ValueError(f"Player {player_id} has already folded")
        
        player.has_folded = True
        player.has_acted = True
        
        return {
            "action": BettingAction.FOLD.value,
            "player_id": player_id,
            "success": True
        }
    
    def check(self, player_id: str) -> Dict:
        """Player checks"""
        if not self.can_check(player_id):
            raise ValueError(f"Player {player_id} cannot check")
        
        player = self.players[player_id]
        player.has_acted = True
        
        return {
            "action": BettingAction.CHECK.value,
            "player_id": player_id,
            "success": True
        }
    
    def call(self, player_id: str) -> Dict:
        """Player calls the current bet"""
        if not self.can_call(player_id):
            raise ValueError(f"Player {player_id} cannot call")
        
        player = self.players[player_id]
        call_amount = self.get_call_amount(player_id)
        
        # Handle all-in call
        if call_amount >= player.chips:
            return self.all_in(player_id)
        
        # Normal call
        player.chips -= call_amount
        player.bet_this_round += call_amount
        player.total_bet_in_pot += call_amount
        player.has_acted = True
        self.pots[0].add_chips(call_amount)
        
        return {
            "action": BettingAction.CALL.value,
            "player_id": player_id,
            "amount": call_amount,
            "remaining_chips": player.chips,
            "pot": self.get_total_pot(),
            "success": True
        }
    
    def bet_raise(self, player_id: str, raise_to_amount: int) -> Dict:
        """
        Player raises (or makes initial bet)
        
        Args:
            player_id: Player making the raise
            raise_to_amount: Total amount to raise TO (not raise BY)
        """
        player = self.players[player_id]
        
        if not player.can_bet():
            raise ValueError(f"Player {player_id} cannot bet/raise")
        
        # Calculate actual raise amount needed
        call_amount = self.get_call_amount(player_id)
        min_raise = self.get_min_raise_amount(player_id)
        
        # Validate raise amount
        if raise_to_amount < min_raise and raise_to_amount != player.chips + player.bet_this_round:
            raise ValueError(
                f"Raise must be at least ${min_raise}. "
                f"Got ${raise_to_amount}"
            )
        
        # Calculate chips needed
        chips_needed = raise_to_amount - player.bet_this_round
        
        # Handle all-in raise
        if chips_needed >= player.chips:
            return self.all_in(player_id)
        
        # Update player state
        player.chips -= chips_needed
        player.bet_this_round = raise_to_amount
        player.total_bet_in_pot += chips_needed
        player.has_acted = True
        self.pots[0].add_chips(chips_needed)
        
        # Update current bet and minimum raise
        old_bet = self.current_bet
        self.current_bet = raise_to_amount
        self.minimum_raise = raise_to_amount - old_bet
        
        # Reset other players' acted status (they need to respond to raise)
        for other_player in self.players.values():
            if other_player.player_id != player_id and not other_player.has_folded:
                other_player.has_acted = False
        
        return {
            "action": BettingAction.RAISE.value,
            "player_id": player_id,
            "raise_to": raise_to_amount,
            "chips_committed": chips_needed,
            "remaining_chips": player.chips,
            "current_bet": self.current_bet,
            "pot": self.get_total_pot(),
            "success": True
        }
    
    def all_in(self, player_id: str) -> Dict:
        """Player goes all-in"""
        player = self.players[player_id]
        
        if not player.can_bet():
            raise ValueError(f"Player {player_id} cannot go all-in")
        
        all_in_amount = player.chips
        new_total_bet = player.bet_this_round + all_in_amount
        
        player.chips = 0
        player.bet_this_round = new_total_bet
        player.total_bet_in_pot += all_in_amount
        player.is_all_in = True
        player.has_acted = True
        self.pots[0].add_chips(all_in_amount)
        
        # If all-in is greater than current bet, it's a raise
        is_raise = new_total_bet > self.current_bet
        
        if is_raise:
            old_bet = self.current_bet
            self.current_bet = new_total_bet
            self.minimum_raise = new_total_bet - old_bet
            
            # Reset other players' acted status
            for other_player in self.players.values():
                if other_player.player_id != player_id and not other_player.has_folded:
                    other_player.has_acted = False
        
        return {
            "action": BettingAction.ALL_IN.value,
            "player_id": player_id,
            "amount": all_in_amount,
            "total_bet": new_total_bet,
            "is_raise": is_raise,
            "pot": self.get_total_pot(),
            "success": True
        }
    
    def is_betting_round_complete(self) -> bool:
        """Check if current betting round is complete"""
        active_players = [p for p in self.players.values() 
                         if not p.has_folded and not p.is_all_in]
        
        if len(active_players) <= 1:
            return True
        
        # All active players must have acted and matched the current bet
        for player in active_players:
            if not player.has_acted:
                return False
            if player.bet_this_round != self.current_bet:
                return False
        
        return True
    
    def start_new_betting_round(self, round_name: BettingRound):
        """Start a new betting round"""
        self.current_round = round_name
        self.current_bet = 0
        self.minimum_raise = self.big_blind
        
        # Reset all players' round state
        for player in self.players.values():
            player.reset_round()
    
    def create_side_pots(self) -> List[Pot]:
        """
        Create side pots when players are all-in with different amounts
        
        Returns:
            List of all pots (main + side pots)
        """
        # Get all players sorted by total bet amount
        all_players = [p for p in self.players.values() if not p.has_folded]
        if not all_players:
            return self.pots
        
        # Sort by total bet in pot
        all_players.sort(key=lambda p: p.total_bet_in_pot)
        
        pots = []
        remaining_amount = self.get_total_pot()
        previous_bet = 0
        eligible_players = [p.player_id for p in all_players]
        
        for player in all_players:
            if player.total_bet_in_pot > previous_bet and eligible_players:
                # Calculate pot amount
                bet_level = player.total_bet_in_pot - previous_bet
                pot_amount = bet_level * len(eligible_players)
                
                if pot_amount > 0:
                    is_main = len(pots) == 0
                    pot = Pot(
                        amount=pot_amount,
                        eligible_players=eligible_players.copy(),
                        is_main_pot=is_main
                    )
                    pots.append(pot)
                
                previous_bet = player.total_bet_in_pot
            
            # Remove player from eligible list if they're all-in
            if player.is_all_in and player.player_id in eligible_players:
                eligible_players.remove(player.player_id)
        
        self.pots = pots if pots else [Pot(amount=remaining_amount, 
                                            eligible_players=[p.player_id for p in all_players],
                                            is_main_pot=True)]
        return self.pots
    
    def get_total_pot(self) -> int:
        """Get total amount in all pots"""
        return sum(pot.amount for pot in self.pots)
    
    def distribute_pot(self, winners: List[Tuple[str, int]]) -> Dict[str, int]:
        """
        Distribute pot(s) to winners
        
        Args:
            winners: List of (player_id, hand_rank) tuples, sorted best to worst
        
        Returns:
            Dictionary of player_id -> chips_won
        """
        winnings = {player_id: 0 for player_id, _ in winners}
        
        for pot in self.pots:
            # Find eligible winners for this pot
            eligible_winners = [
                (pid, rank) for pid, rank in winners 
                if pid in pot.eligible_players
            ]
            
            if not eligible_winners:
                continue
            
            # Get best hand rank among eligible winners
            best_rank = min(rank for _, rank in eligible_winners)
            pot_winners = [pid for pid, rank in eligible_winners if rank == best_rank]
            
            # Split pot among winners
            chips_per_winner = pot.amount // len(pot_winners)
            remainder = pot.amount % len(pot_winners)
            
            for i, winner_id in enumerate(pot_winners):
                winnings[winner_id] += chips_per_winner
                # Give remainder to first winner (closest to dealer button)
                if i == 0:
                    winnings[winner_id] += remainder
        
        return winnings
    
    def get_active_players(self) -> List[str]:
        """Get list of active players (not folded)"""
        return [p.player_id for p in self.players.values() if not p.has_folded]
    
    def get_player_state(self, player_id: str) -> Dict:
        """Get betting state for a specific player"""
        player = self.players.get(player_id)
        if not player:
            return None
        
        return {
            "player_id": player.player_id,
            "chips": player.chips,
            "bet_this_round": player.bet_this_round,
            "total_bet_in_pot": player.total_bet_in_pot,
            "is_all_in": player.is_all_in,
            "has_folded": player.has_folded,
            "has_acted": player.has_acted,
            "can_check": self.can_check(player_id),
            "can_call": self.can_call(player_id),
            "can_raise": self.can_raise(player_id),
            "call_amount": self.get_call_amount(player_id) if self.can_call(player_id) else 0,
            "min_raise": self.get_min_raise_amount(player_id) if self.can_raise(player_id) else 0
        }
    
    def get_all_states(self) -> Dict:
        """Get complete betting state"""
        return {
            "current_bet": self.current_bet,
            "minimum_raise": self.minimum_raise,
            "total_pot": self.get_total_pot(),
            "pots": [{"amount": p.amount, "eligible_players": p.eligible_players} 
                     for p in self.pots],
            "current_round": self.current_round.value,
            "players": {pid: self.get_player_state(pid) for pid in self.players.keys()}
        }


# Example usage and testing
if __name__ == "__main__":
    print("=== Betting System Testing ===\n")
    
    # Initialize betting manager
    betting = BettingManager(small_blind=10, big_blind=20)
    
    # Add 4 players
    betting.add_player("player1", 1000)
    betting.add_player("player2", 1000)
    betting.add_player("player3", 1000)
    betting.add_player("player4", 1000)
    
    print("1. Post Blinds:")
    blinds = betting.post_blinds("player1", "player2")
    print(f"Small Blind: ${blinds['small_blind']['amount']}")
    print(f"Big Blind: ${blinds['big_blind']['amount']}")
    print(f"Current Bet: ${blinds['current_bet']}\n")
    
    print("2. Player 3 calls:")
    result = betting.call("player3")
    print(f"Called ${result['amount']}, Pot: ${result['pot']}\n")
    
    print("3. Player 4 raises to $60:")
    result = betting.bet_raise("player4", 60)
    print(f"Raised to ${result['raise_to']}, Pot: ${result['pot']}\n")
    
    print("4. Player 1 folds:")
    result = betting.fold("player1")
    print(f"Player 1 folded\n")
    
    print("5. Player 2 calls:")
    result = betting.call("player2")
    print(f"Called ${result['amount']}, Pot: ${result['pot']}\n")
    
    print("6. Player 3 calls:")
    result = betting.call("player3")
    print(f"Called ${result['amount']}, Pot: ${result['pot']}\n")
    
    print("7. Betting round complete?", betting.is_betting_round_complete())
    
    print("\n8. Final State:")
    state = betting.get_all_states()
    print(f"Total Pot: ${state['total_pot']}")
    print(f"Active Players: {betting.get_active_players()}")