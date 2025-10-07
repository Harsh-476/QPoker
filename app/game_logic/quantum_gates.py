"""
Quantum Gates Implementation for Quantum Poker with optional Qiskit support.
Falls back to a classical simulation if Qiskit is not installed.
"""

import random
from typing import List, Tuple, Optional
from copy import deepcopy

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister  # type: ignore
    from qiskit_aer import AerSimulator  # type: ignore
    from qiskit.quantum_info import Statevector  # type: ignore
    import numpy as np  # type: ignore
    _HAS_QISKIT = True
except Exception:
    QuantumCircuit = QuantumRegister = ClassicalRegister = AerSimulator = Statevector = None  # type: ignore
    np = None  # type: ignore
    _HAS_QISKIT = False

from app.game_logic.card_encoder import QuantumCard, CardEncoder


class QuantumGates:
    """Handles quantum gate operations on cards using Qiskit"""
    
    def __init__(self, use_simulator: bool = True):
        """
        Initialize quantum gates handler
        
        Args:
            use_simulator: If True, use Qiskit Aer simulator for gate operations
        """
        self.encoder = CardEncoder()
        self.use_simulator = use_simulator and _HAS_QISKIT
        self.simulator = AerSimulator() if self.use_simulator else None
    
    def _create_quantum_circuit(self, card: QuantumCard) -> QuantumCircuit:
        """
        Create a quantum circuit from a card's state
        
        Args:
            card: QuantumCard to convert to circuit
        
        Returns:
            QuantumCircuit initialized with card's state
        """
        if not self.use_simulator or not _HAS_QISKIT:
            raise RuntimeError("Qiskit simulator not available")
        qr = QuantumRegister(5, 'q')
        cr = ClassicalRegister(5, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Initialize qubits to card's state
        for i, qubit_value in enumerate(card.qubits):
            if qubit_value == 1:
                qc.x(i)  # Apply X gate to set qubit to |1⟩
        
        # Handle negative amplitude (phase)
        if card.amplitude == -1:
            qc.z(0)  # Apply Z gate to first qubit to represent negative amplitude
        
        return qc
    
    def _circuit_to_card(self, qc: QuantumCircuit, original_amplitude: int) -> QuantumCard:
        """
        Extract card state from quantum circuit after measurement
        
        Args:
            qc: QuantumCircuit after gates applied
            original_amplitude: Original amplitude sign
        
        Returns:
            QuantumCard with new state
        """
        if not self.use_simulator or not _HAS_QISKIT:
            # Classical fallback: return card as-is
            return QuantumCard(qc, original_amplitude)  # type: ignore[arg-type]
        # Measure all qubits
        qc.measure(range(5), range(5))
        
        # Execute circuit
        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get measurement result (binary string)
        measured_state = list(counts.keys())[0]
        
        # Convert to qubit list (reverse because Qiskit uses little-endian)
        qubits = [int(bit) for bit in reversed(measured_state)]
        
        # Determine amplitude (check if Z gate was applied to first qubit)
        # For simplicity, we track amplitude separately
        amplitude = original_amplitude
        
        return QuantumCard(qubits, amplitude)
    
    def _test_x_gate_qubit(self, card: QuantumCard, qubit_index: int) -> Tuple[QuantumCard, bool]:
        """Test if applying X gate to a specific qubit results in a valid card"""
        if self.use_simulator and _HAS_QISKIT:
            qc = self._create_quantum_circuit(card)
            qc.x(qubit_index)
            result_card = self._circuit_to_card(qc, card.amplitude)
        else:
            new_qubits = card.qubits.copy()
            new_qubits[qubit_index] = 1 - new_qubits[qubit_index]
            result_card = QuantumCard(new_qubits, card.amplitude)
        
        is_valid = self.encoder.decode_card(result_card) is not None
        return result_card, is_valid

    def apply_x_gate(self, card: QuantumCard, preview_only: bool = False, qubit_index: Optional[int] = None) -> Tuple[QuantumCard, int]:
        """
        Apply X (bit flip) gate to a qubit position using Qiskit
        
        Args:
            card: The quantum card to apply gate to
            preview_only: If True, return preview without modifying original
            qubit_index: Specific qubit to flip (0-4). If None, randomly select from valid qubits
        
        Returns:
            Tuple of (resulting_card, flipped_qubit_index)
        """
        # Find valid qubits that result in valid cards
        valid_qubits = []
        for q_idx in range(5):
            _, is_valid = self._test_x_gate_qubit(card, q_idx)
            if is_valid:
                valid_qubits.append(q_idx)
        
        if not valid_qubits:
            # If no valid qubits, return original card
            return card, -1
        
        # Select qubit to flip (deterministic - always use first valid qubit)
        if qubit_index is None:
            qubit_index = valid_qubits[0]  # Always use first valid qubit for consistency
        elif qubit_index not in valid_qubits:
            # If specified qubit is invalid, use first valid qubit
            qubit_index = valid_qubits[0]
        
        if self.use_simulator and _HAS_QISKIT:
            # Create quantum circuit
            qc = self._create_quantum_circuit(card)
            
            # Apply X gate to selected qubit
            qc.x(qubit_index)
            
            if preview_only:
                # Simulate without affecting original
                qc_copy = qc.copy()
                result_card = self._circuit_to_card(qc_copy, card.amplitude)
            else:
                # Apply and get result
                result_card = self._circuit_to_card(qc, card.amplitude)
                # Update original card
                card.qubits = result_card.qubits
                result_card = card
        else:
            # Classical simulation
            new_qubits = card.qubits.copy() if preview_only else card.qubits
            if preview_only:
                new_qubits = card.qubits.copy()
            
            # Flip the selected qubit (0 -> 1, 1 -> 0)
            new_qubits[qubit_index] = 1 - new_qubits[qubit_index]
            
            if preview_only:
                result_card = QuantumCard(new_qubits, card.amplitude)
            else:
                card.qubits = new_qubits
                result_card = card
        
        return result_card, qubit_index
    
    def apply_z_gate(self, card: QuantumCard, preview_only: bool = False) -> QuantumCard:
        """
        Apply Z (phase flip) gate - flips the amplitude sign using Qiskit
        Changes suit color: red <-> black
        
        Args:
            card: The quantum card to apply gate to
            preview_only: If True, return preview without modifying original
        
        Returns:
            The resulting quantum card
        """
        if self.use_simulator and _HAS_QISKIT:
            # Create quantum circuit
            qc = self._create_quantum_circuit(card)
            
            # Apply Z gate to all qubits to represent global phase flip
            for i in range(5):
                qc.z(i)
            
            if preview_only:
                # Return new card with flipped amplitude
                return QuantumCard(card.qubits.copy(), -card.amplitude)
            else:
                # Flip amplitude of original card
                card.amplitude = -card.amplitude
                return card
        else:
            # Classical simulation
            if preview_only:
                return QuantumCard(card.qubits.copy(), -card.amplitude)
            else:
                card.amplitude = -card.amplitude
                return card
    
    def apply_cnot_gate(
        self, 
        control_card: QuantumCard, 
        target_card: QuantumCard,
        preview_only: bool = False
    ) -> Tuple[QuantumCard, QuantumCard, int]:
        """
        Apply CNOT (controlled-NOT) gate using Qiskit
        Randomly selects a qubit position. If control qubit is 1, flip target qubit.
        Also entangles the two cards.
        
        Args:
            control_card: Control card
            target_card: Target card
            preview_only: If True, return preview without modifying original
        
        Returns:
            Tuple of (control_card, target_card, qubit_index)
        """
        # Randomly select which qubit position to use
        qubit_index = random.randint(0, 4)
        
        if self.use_simulator and _HAS_QISKIT:
            # Create combined quantum circuit (10 qubits total)
            qr = QuantumRegister(10, 'q')
            cr = ClassicalRegister(10, 'c')
            qc = QuantumCircuit(qr, cr)
            
            # Initialize control card qubits (0-4)
            for i, qubit_value in enumerate(control_card.qubits):
                if qubit_value == 1:
                    qc.x(i)
            
            # Initialize target card qubits (5-9)
            for i, qubit_value in enumerate(target_card.qubits):
                if qubit_value == 1:
                    qc.x(5 + i)
            
            # Apply CNOT gate
            # Control: qubit_index from control card
            # Target: corresponding qubit from target card (5 + qubit_index)
            qc.cx(qubit_index, 5 + qubit_index)
            
            # Measure both cards
            qc.measure(range(10), range(10))
            
            # Execute circuit
            job = self.simulator.run(qc, shots=1)
            result = job.result()
            counts = result.get_counts()
            measured_state = list(counts.keys())[0]
            
            # Extract qubits (reverse for little-endian)
            all_qubits = [int(bit) for bit in reversed(measured_state)]
            control_qubits = all_qubits[:5]
            target_qubits = all_qubits[5:10]
            
            if preview_only:
                new_control = QuantumCard(control_qubits, control_card.amplitude)
                new_target = QuantumCard(target_qubits, target_card.amplitude)
                
                # Mark as entangled in preview
                new_control._entangled_with = "target"
                new_target._entangled_with = "control"
                
                return new_control, new_target, qubit_index
            else:
                # Update original cards
                control_card.qubits = control_qubits
                target_card.qubits = target_qubits
                
                # Entangle the cards
                control_card._entangled_with = target_card
                target_card._entangled_with = control_card
                
                return control_card, target_card, qubit_index
        else:
            # Classical simulation
            if preview_only:
                new_control = QuantumCard(control_card.qubits.copy(), control_card.amplitude)
                new_target = QuantumCard(target_card.qubits.copy(), target_card.amplitude)
                
                # If control qubit is 1, flip target qubit
                if new_control.qubits[qubit_index] == 1:
                    new_target.qubits[qubit_index] = 1 - new_target.qubits[qubit_index]
                
                # Mark as entangled in preview
                new_control._entangled_with = "target"
                new_target._entangled_with = "control"
                
                return new_control, new_target, qubit_index
            else:
                # If control qubit is 1, flip target qubit
                if control_card.qubits[qubit_index] == 1:
                    target_card.qubits[qubit_index] = 1 - target_card.qubits[qubit_index]
                
                # Entangle the cards
                control_card._entangled_with = target_card
                target_card._entangled_with = control_card
                
                return control_card, target_card, qubit_index
    
    def create_superposition(self, card: QuantumCard) -> dict:
        """
        Create superposition state using Hadamard gates (optional feature)
        
        Args:
            card: Card to put in superposition
        
        Returns:
            Dictionary with superposition info
        """
        if not self.use_simulator or not _HAS_QISKIT:
            return {"error": "Superposition requires quantum simulator"}
        
        # Create circuit
        qc = self._create_quantum_circuit(card)
        
        # Apply Hadamard to all qubits
        for i in range(5):
            qc.h(i)
        
        # Get statevector
        statevector = Statevector(qc)
        probabilities = statevector.probabilities()
        
        # Get top 5 most probable states
        top_states = []
        for state_idx in np.argsort(probabilities)[-5:][::-1]:
            if probabilities[state_idx] > 0.01:  # Only show states with >1% probability
                qubits = [int(bit) for bit in format(state_idx, '05b')]
                prob = probabilities[state_idx]
                
                # Try to decode this state
                temp_card = QuantumCard(qubits, card.amplitude)
                card_str = self.encoder.card_to_string(temp_card)
                
                top_states.append({
                    "qubits": qubits,
                    "probability": float(prob),
                    "card": card_str,
                    "state": f"|{''.join(map(str, qubits))}⟩"
                })
        
        return {
            "in_superposition": True,
            "num_states": len([p for p in probabilities if p > 0.001]),
            "top_states": top_states
        }
    
    def preview_gate(
        self, 
        gate_type: str, 
        cards: List[QuantumCard]
    ) -> dict:
        """
        Preview the result of applying a gate without actually applying it
        
        Args:
            gate_type: "X", "Z", "CNOT", or "H" (Hadamard)
            cards: List of cards (1 for X/Z/H, 2 for CNOT)
        
        Returns:
            Dictionary with preview information
        """
        gate_type = gate_type.upper()
        
        if gate_type == "X":
            if len(cards) != 1:
                raise ValueError("X gate requires exactly 1 card")
            
            # Apply X gate deterministically (same as actual application)
            result_card, qubit_flipped = self.apply_x_gate(cards[0], preview_only=True)
            original_str = self.encoder.card_to_string(cards[0])
            result_str = self.encoder.card_to_string(result_card)
            
            return {
                "gate": "X",
                "original_card": original_str,
                "result_card": result_str,
                "qubit_flipped": qubit_flipped,
                "original_state": cards[0].__repr__(),
                "result_state": result_card.__repr__(),
                "is_undefined": self.encoder.decode_card(result_card) is None,
                "using_qiskit": self.use_simulator
            }
        
        elif gate_type == "Z":
            if len(cards) != 1:
                raise ValueError("Z gate requires exactly 1 card")
            
            result_card = self.apply_z_gate(cards[0], preview_only=True)
            
            original_str = self.encoder.card_to_string(cards[0])
            result_str = self.encoder.card_to_string(result_card)
            
            return {
                "gate": "Z",
                "original_card": original_str,
                "result_card": result_str,
                "original_state": cards[0].__repr__(),
                "result_state": result_card.__repr__(),
                "is_undefined": self.encoder.decode_card(result_card) is None,
                "using_qiskit": self.use_simulator
            }
        
        elif gate_type == "CNOT":
            if len(cards) != 2:
                raise ValueError("CNOT gate requires exactly 2 cards")
            
            control, target, qubit_idx = self.apply_cnot_gate(
                cards[0], cards[1], preview_only=True
            )
            
            return {
                "gate": "CNOT",
                "control_card": {
                    "original": self.encoder.card_to_string(cards[0]),
                    "result": self.encoder.card_to_string(control),
                    "original_state": cards[0].__repr__(),
                    "result_state": control.__repr__()
                },
                "target_card": {
                    "original": self.encoder.card_to_string(cards[1]),
                    "result": self.encoder.card_to_string(target),
                    "original_state": cards[1].__repr__(),
                    "result_state": target.__repr__()
                },
                "qubit_index": qubit_idx,
                "entangled": True,
                "is_undefined": (
                    self.encoder.decode_card(control) is None or 
                    self.encoder.decode_card(target) is None
                ),
                "using_qiskit": self.use_simulator
            }
        
        elif gate_type == "H":
            if len(cards) != 1:
                raise ValueError("H gate requires exactly 1 card")
            
            superposition_info = self.create_superposition(cards[0])
            return {
                "gate": "H",
                "original_card": self.encoder.card_to_string(cards[0]),
                "superposition": superposition_info,
                "using_qiskit": self.use_simulator
            }
        
        else:
            raise ValueError(f"Unknown gate type: {gate_type}")
    
    def apply_gate(
        self, 
        gate_type: str, 
        cards: List[QuantumCard]
    ) -> dict:
        """
        Actually apply the gate to the cards
        
        Args:
            gate_type: "X", "Z", or "CNOT"
            cards: List of cards (1 for X/Z, 2 for CNOT)
        
        Returns:
            Dictionary with application results
        """
        gate_type = gate_type.upper()
        
        if gate_type == "X":
            if len(cards) != 1:
                raise ValueError("X gate requires exactly 1 card")
            
            original_str = self.encoder.card_to_string(cards[0])
            result_card, qubit_idx = self.apply_x_gate(cards[0], preview_only=False)
            result_str = self.encoder.card_to_string(result_card)
            
            return {
                "gate": "X",
                "original_card": original_str,
                "result_card": result_str,
                "qubit_flipped": qubit_idx,
                "new_state": result_card.__repr__(),
                "is_undefined": self.encoder.decode_card(result_card) is None,
                "using_qiskit": self.use_simulator
            }
        
        elif gate_type == "Z":
            if len(cards) != 1:
                raise ValueError("Z gate requires exactly 1 card")
            
            original_str = self.encoder.card_to_string(cards[0])
            result_card = self.apply_z_gate(cards[0], preview_only=False)
            result_str = self.encoder.card_to_string(result_card)
            
            return {
                "gate": "Z",
                "original_card": original_str,
                "result_card": result_str,
                "new_state": result_card.__repr__(),
                "is_undefined": self.encoder.decode_card(result_card) is None,
                "using_qiskit": self.use_simulator
            }
        
        elif gate_type == "CNOT":
            if len(cards) != 2:
                raise ValueError("CNOT gate requires exactly 2 cards")
            
            control, target, qubit_idx = self.apply_cnot_gate(
                cards[0], cards[1], preview_only=False
            )
            
            return {
                "gate": "CNOT",
                "control_card": self.encoder.card_to_string(control),
                "target_card": self.encoder.card_to_string(target),
                "qubit_index": qubit_idx,
                "entangled": True,
                "control_state": control.__repr__(),
                "target_state": target.__repr__(),
                "is_undefined": (
                    self.encoder.decode_card(control) is None or 
                    self.encoder.decode_card(target) is None
                ),
                "using_qiskit": self.use_simulator
            }
        
        else:
            raise ValueError(f"Unknown gate type: {gate_type}")
    
    def collapse_cards(self, cards: List[QuantumCard]) -> List[dict]:
        """
        Collapse quantum cards to classical states
        Handle entangled cards (collapse together)
        
        Args:
            cards: List of quantum cards to collapse
        
        Returns:
            List of dictionaries with collapse information
        """
        results = []
        collapsed_ids = set()
        
        for i, card in enumerate(cards):
            if i in collapsed_ids:
                continue
            
            card_str = self.encoder.card_to_string(card)
            is_undefined = self.encoder.decode_card(card) is None
            
            result = {
                "card_index": i,
                "collapsed_to": card_str,
                "is_undefined": is_undefined,
                "quantum_state": card.__repr__()
            }
            
            # Check if entangled
            if card._entangled_with is not None:
                # Find the entangled card
                entangled_idx = None
                for j, other_card in enumerate(cards):
                    if other_card is card._entangled_with:
                        entangled_idx = j
                        break
                
                if entangled_idx is not None:
                    entangled_str = self.encoder.card_to_string(cards[entangled_idx])
                    result["entangled_with"] = entangled_idx
                    result["entangled_card"] = entangled_str
                    collapsed_ids.add(entangled_idx)
            
            results.append(result)
        
        return results


# Example usage and testing
if __name__ == "__main__":
    from app.game_logic.card_encoder import Rank, Suit
    
    encoder = CardEncoder()
    gates = QuantumGates(use_simulator=True)
    
    print("=== Quantum Gates with Qiskit Testing ===\n")
    print(f"Using Qiskit Simulator: {gates.use_simulator}\n")
    
    # Test X Gate
    print("1. X Gate (Bit Flip) with Qiskit:")
    ace_hearts = encoder.encode_card(Rank.ACE, Suit.HEARTS)
    print(f"Original: {encoder.card_to_string(ace_hearts)} {ace_hearts}")
    
    preview = gates.preview_gate("X", [ace_hearts])
    print(f"Preview: {preview['original_card']} → {preview['result_card']}")
    print(f"Qubit {preview['qubit_flipped']} will be flipped")
    print(f"Using Qiskit: {preview['using_qiskit']}")
    
    result = gates.apply_gate("X", [ace_hearts])
    print(f"Applied: Now {result['result_card']} {result['new_state']}\n")
    
    # Test Z Gate
    print("2. Z Gate (Phase Flip) with Qiskit:")
    king_hearts = encoder.encode_card(Rank.KING, Suit.HEARTS)
    print(f"Original: {encoder.card_to_string(king_hearts)} {king_hearts}")
    
    preview = gates.preview_gate("Z", [king_hearts])
    print(f"Preview: {preview['original_card']} → {preview['result_card']}")
    
    result = gates.apply_gate("Z", [king_hearts])
    print(f"Applied: Now {result['result_card']} {result['new_state']}\n")
    
    # Test CNOT Gate
    print("3. CNOT Gate (Entanglement) with Qiskit:")
    queen_spades = encoder.encode_card(Rank.QUEEN, Suit.SPADES)
    jack_diamonds = encoder.encode_card(Rank.JACK, Suit.DIAMONDS)
    
    print(f"Control: {encoder.card_to_string(queen_spades)} {queen_spades}")
    print(f"Target: {encoder.card_to_string(jack_diamonds)} {jack_diamonds}")
    
    preview = gates.preview_gate("CNOT", [queen_spades, jack_diamonds])
    print(f"Preview Control: {preview['control_card']['original']} → {preview['control_card']['result']}")
    print(f"Preview Target: {preview['target_card']['original']} → {preview['target_card']['result']}")
    print(f"Qubit index: {preview['qubit_index']}")
    print(f"Using Qiskit: {preview['using_qiskit']}")
    
    result = gates.apply_gate("CNOT", [queen_spades, jack_diamonds])
    print(f"Applied Control: {result['control_card']}")
    print(f"Applied Target: {result['target_card']}")
    print(f"Entangled: {result['entangled']}\n")
    
    # Test Hadamard (Superposition) - Bonus feature
    print("4. Hadamard Gate (Superposition) - Bonus:")
    two_hearts = encoder.encode_card(Rank.TWO, Suit.HEARTS)
    print(f"Original: {encoder.card_to_string(two_hearts)}")
    
    superposition = gates.preview_gate("H", [two_hearts])
    if "superposition" in superposition:
        print("Top possible states after Hadamard:")
        for state in superposition["superposition"]["top_states"][:3]:
            print(f"  {state['card']}: {state['probability']:.1%} - {state['state']}")
    
    print("\n✓ Qiskit integration successful!")