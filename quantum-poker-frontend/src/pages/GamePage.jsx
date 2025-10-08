import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { createSocket } from '../lib/socket'
import Card from '../ui/Card'

const GamePage = () => {
  const { lobbyId, playerId } = useParams()
  const navigate = useNavigate()
  const [gameState, setGameState] = useState(null)
  const [lobby, setLobby] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [gatePreview, setGatePreview] = useState(null)
  const [cardHistory, setCardHistory] = useState({})
  const [showWinnerPopup, setShowWinnerPopup] = useState(false)
  const [winnerInfo, setWinnerInfo] = useState(null)

  useEffect(() => {
    loadGameData()
    const socket = createSocket()
    
    // Wait a bit for lobby to be ready before joining socket room
    const joinRoom = () => {
      console.log('Joining socket room:', { lobby_id: lobbyId, player_id: playerId })
      socket.emit('join', { lobby_id: lobbyId, player_id: playerId })
    }
    
    // Join immediately, but also retry after a short delay
    joinRoom()
    const retryTimer = setTimeout(() => {
      // Only retry if we haven't gotten a permanent error
      if (!error || !error.includes('already started')) {
        joinRoom()
      }
    }, 1000)
    
    socket.on('game:update', (payload) => {
      setGameState(payload.state)
      setGatePreview(null) // Clear any existing preview
      
      // Check if game is complete and show winner popup
      if (payload.state.phase === 'complete') {
        let winnerInfo = null
        
        // Handle auto-win scenario (when someone folds and remaining player wins)
        if (payload.result?.auto_win && payload.result?.winner) {
          const winnerId = payload.result.winner
          const winnerPlayer = payload.state.players[winnerId]
          
          winnerInfo = {
            playerName: winnerPlayer?.name || `Player ${winnerId}`,
            handDescription: "Auto-win (all others folded)",
            handRank: 0,
            winnings: payload.result.winnings || 0,
            isCurrentPlayer: winnerId === playerId,
            isTie: false,
            isAutoWin: true,
            allWinners: [{
              name: winnerPlayer?.name || `Player ${winnerId}`,
              description: "Auto-win (all others folded)",
              winnings: payload.result.winnings || 0
            }]
          }
        }
        // Handle normal showdown scenario
        else if (payload.result?.winners) {
          const winners = payload.result.winners
          const winner = winners[0] // Get the first winner
          const winnerPlayer = payload.state.players[winner.player_id]
          
          // Check if current player is among the winners
          const currentPlayerWon = winners.some(w => w.player_id === playerId)
          
          winnerInfo = {
            playerName: winnerPlayer?.name || `Player ${winner.player_id}`,
            handDescription: winner.description,
            handRank: winner.hand_rank,
            winnings: winner.winnings,
            isCurrentPlayer: currentPlayerWon,
            isTie: winners.length > 1,
            isAutoWin: false,
            allWinners: winners.map(w => ({
              name: payload.state.players[w.player_id]?.name || `Player ${w.player_id}`,
              description: w.description,
              winnings: w.winnings
            }))
          }
        }
        
        if (winnerInfo) {
          setWinnerInfo(winnerInfo)
          setShowWinnerPopup(true)
        }
      }
      
      // Track card changes when gates are applied
      if (payload.result?.gate_applied && payload.result?.gate_info) {
        const gateInfo = payload.result.gate_info
        const currentPlayerId = playerId
        
        if (payload.state.players[currentPlayerId]) {
          setCardHistory(prev => {
            const newHistory = { ...prev }
            if (!newHistory[currentPlayerId]) newHistory[currentPlayerId] = []
            
            // Create a unique key for this transformation to prevent duplicates
            const transformationKey = `${gateInfo.original_card}-${gateInfo.result_card}-${gateInfo.gate}-${payload.state.phase}-${Date.now()}`
            
            // Check if this exact transformation already exists to prevent duplicates
            const existingEntry = newHistory[currentPlayerId].find(entry => 
              entry.originalCard === gateInfo.original_card && 
              entry.resultCard === gateInfo.result_card && 
              entry.gate === gateInfo.gate &&
              entry.phase === payload.state.phase
            )
            
            if (!existingEntry) {
              newHistory[currentPlayerId].push({
                id: transformationKey,
                timestamp: new Date().toLocaleTimeString('en-US', {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'}),
                gate: gateInfo.gate,
                originalCard: gateInfo.original_card || 'Unknown',
                resultCard: gateInfo.result_card,
                phase: payload.state.phase
              })
            }
            
            return newHistory
          })
        }
      }
    })
    
    socket.on('lobby:update', (lobbyData) => {
      if (lobbyData.lobby_id === lobbyId) {
        setLobby(lobbyData)
      }
    })
    
    socket.on('error', (error) => {
      console.log('Socket error:', error)
      // Don't set error for "Lobby not found" - it might be a timing issue
      if (error.detail !== 'Lobby not found') {
        if (error.detail === 'Lobby already in game') {
          setError('This game has already started. You cannot join an ongoing game.')
        } else {
          setError(error.detail)
        }
      }
    })

    socket.on('gate_preview', (preview) => {
      console.log('Gate preview received:', preview)
      setGatePreview(preview)
    })

    return () => {
      clearTimeout(retryTimer)
      socket.off('game:update')
      socket.off('lobby:update')
      socket.off('error')
      socket.off('gate_preview')
    }
  }, [lobbyId, playerId])

  const loadGameData = async () => {
    try {
      const [gameData, lobbyData] = await Promise.all([
        api.getState(lobbyId).catch(() => null),
        api.getLobby(lobbyId)
      ])
      
      setGameState(gameData)
      setLobby(lobbyData)
    } catch (error) {
      setError('Failed to load game data')
    } finally {
      setLoading(false)
    }
  }

  const startGame = async () => {
    try {
      // Use socket to start game so all players get the update
      const socket = createSocket()
      socket.emit('start_game', { lobby_id: lobbyId })
    } catch (error) {
      alert('Failed to start game: ' + error.message)
    }
  }

  const playerAction = async (action, amount = 0) => {
    try {
      // Use socket for actions so all players get updates
      const socket = createSocket()
      socket.emit('action', { lobby_id: lobbyId, player_id: playerId, action, amount })
    } catch (error) {
      alert('Action failed: ' + error.message)
    }
  }

  const isBettingRoundComplete = () => {
    // Check if all active players have acted and betting is complete
    const activePlayers = Object.values(gameState.players).filter(p => p.is_active)
    const bettingPlayers = Object.values(gameState.betting_state?.players || {})
      .filter(p => !p.has_folded && !p.is_all_in)
    
    // If no active betting players, round is complete
    if (bettingPlayers.length <= 1) return true
    
    // Check if all active players have acted
    return bettingPlayers.every(p => p.has_acted)
  }


  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="card text-center">
          <h2 className="text-medium mb-4 text-red-600">⚠️ Cannot Join Game</h2>
          <p className="mb-4">{error}</p>
          <div className="mb-4">
            <button onClick={() => navigate('/')} className="btn btn-primary">
              🏠 Back to Home
            </button>
          </div>
          <div className="text-small text-gray-500">
            💡 Tip: Create a new game or wait for the current game to finish
          </div>
        </div>
      </div>
    )
  }

  // Check if player is in waiting list
  const isWaiting = lobby?.waiting_players?.includes(playerId)
  const isActive = lobby?.players?.includes(playerId)

  // Waiting room (no game started yet or player is waiting)
  if (!gameState || isWaiting) {
    return (
      <div className="container">
        <div className="text-center mb-8">
          <h1 className="text-large text-white mb-4">🎰 {lobby?.name || lobbyId}</h1>
          {isWaiting ? (
            <div>
              <p className="text-white opacity-90 mb-2">⏳ You're in the waiting room!</p>
              <p className="text-white opacity-75 text-sm">The game is in progress. You'll join automatically when the current round ends.</p>
            </div>
          ) : (
            <p className="text-white opacity-90">Waiting for players to join...</p>
          )}
        </div>

        {/* Active Players */}
        <div className="card mb-8">
          <h2 className="text-medium mb-4">🎮 Active Players ({lobby?.players?.length || 0})</h2>
          {lobby?.player_names && Object.keys(lobby.player_names).length > 0 ? (
            <div className="grid gap-4">
              {Object.entries(lobby.player_names).map(([pid, name]) => (
                <div key={pid} className="flex-center p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="w-10 h-10 bg-green-500 text-white rounded-full flex-center mr-3 font-bold">
                    {name ? name.charAt(0).toUpperCase() : '?'}
                  </div>
                  <div>
                    <div className="font-semibold text-green-800">{name || pid}</div>
                    <div className="text-small text-green-600">Playing</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-large mb-2">🎲</div>
              <p>No active players yet. Share the link below!</p>
            </div>
          )}
        </div>

        {/* Waiting Players */}
        {lobby?.waiting_player_names && Object.keys(lobby.waiting_player_names).length > 0 && (
          <div className="card mb-8">
            <h2 className="text-medium mb-4">⏳ Waiting Players ({lobby?.waiting_players?.length || 0})</h2>
            <div className="grid gap-4">
              {Object.entries(lobby.waiting_player_names).map(([pid, name]) => (
                <div key={pid} className={`flex-center p-3 rounded-lg border ${pid === playerId ? 'bg-blue-50 border-blue-200' : 'bg-yellow-50 border-yellow-200'}`}>
                  <div className={`w-10 h-10 rounded-full flex-center mr-3 font-bold ${pid === playerId ? 'bg-blue-500 text-white' : 'bg-yellow-500 text-white'}`}>
                    {name ? name.charAt(0).toUpperCase() : '?'}
                  </div>
                  <div>
                    <div className={`font-semibold ${pid === playerId ? 'text-blue-800' : 'text-yellow-800'}`}>
                      {name || pid} {pid === playerId && '(You)'}
                    </div>
                    <div className={`text-small ${pid === playerId ? 'text-blue-600' : 'text-yellow-600'}`}>
                      {pid === playerId ? 'Waiting to join' : 'Waiting'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="card mb-8">
          <h2 className="text-medium mb-4">🔗 Invite Other Players</h2>
          <div className="bg-blue-50 p-4 rounded-lg mb-4">
            <p className="text-small mb-2">Share this link with friends:</p>
            <div className="bg-white p-3 rounded border font-mono text-sm break-all relative">
              {window.location.origin}/game/{lobbyId}/player2
              <button
                onClick={() => {
                  navigator.clipboard.writeText(`${window.location.origin}/game/${lobbyId}/player2`)
                  alert('Link copied!')
                }}
                className="absolute right-2 top-2 px-2 py-1 bg-blue-500 text-white text-xs rounded"
              >
                Copy
              </button>
            </div>
            <p className="text-small text-gray-600 mt-2">
              💡 Change "player2" to "player3", "player4", etc. for different players
            </p>
          </div>
        </div>

        {/* Only show start button to active players, not waiting players */}
        {!isWaiting && (
          <div className="text-center">
            <button
              onClick={startGame}
              disabled={(lobby?.players?.length || 0) < 2}
              className="btn btn-success"
            >
              🚀 Start Game
            </button>
            {(lobby?.players?.length || 0) < 2 && (
              <p className="text-small text-gray-500 mt-2">Need at least 2 players to start</p>
            )}
          </div>
        )}
        
        {/* Show waiting message for waiting players */}
        {isWaiting && (
          <div className="text-center">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="text-4xl mb-4">⏳</div>
              <h3 className="text-lg font-semibold text-blue-800 mb-2">Waiting to Join</h3>
              <p className="text-blue-600 mb-4">
                The game is currently in progress. You'll be automatically added to the next round when it ends.
              </p>
              <div className="flex items-center justify-center space-x-2 text-sm text-blue-500">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span>Waiting for current round to finish...</span>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Game in progress
  const currentPlayer = gameState.players?.[playerId]
  const isMyTurn = gameState.current_player === playerId
  const activePlayers = Object.values(gameState.players).filter(p => p.is_active)
  
  // Get betting state for current player
  const bettingState = gameState.betting_state?.players?.[playerId]
  const canCheck = bettingState?.can_check || false
  const canCall = bettingState?.can_call || false
  const canRaise = bettingState?.can_raise || false
  const callAmount = bettingState?.call_amount || 0
  const minRaise = bettingState?.min_raise || 0

  return (
    <div className="container">
      <div className="text-center mb-8">
        <h1 className="text-large text-white mb-4">🎰 {lobby?.name || lobbyId}</h1>
        <div className="text-white opacity-90">
          Phase: {gameState.phase} • Pot: ${gameState.pot} • Current Bet: ${gameState.current_bet}
        </div>
      </div>

      {/* Community Cards */}
      <div className="card mb-8">
        <h2 className="text-medium mb-4 text-center flex items-center justify-center">
          <span className="mr-2">🎯</span>
          Community Cards
        </h2>
        <div className="flex-center gap-4">
          {gameState.community_cards?.map((card, index) => (
            <div key={index} className="transform hover:scale-105 transition-transform">
              <Card card={card} size="large" />
            </div>
          ))}
          {(!gameState.community_cards || gameState.community_cards.length === 0) && (
            <div className="text-gray-500 bg-gray-100 p-4 rounded-lg">
              <div className="text-center">
                <div className="text-2xl mb-2">🃏</div>
                <div>No community cards yet</div>
                <div className="text-xs text-gray-400 mt-1">Cards will appear as the game progresses</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Players */}
      <div className="card mb-8">
        <h2 className="text-medium mb-4">Players</h2>
        <div className="grid gap-4">
          {Object.entries(gameState.players).map(([pid, player]) => (
            <div key={pid} className={`p-4 rounded-lg border ${
              pid === playerId ? 'bg-blue-50 border-blue-300' : 'bg-gray-50'
            } ${pid === gameState.current_player ? 'ring-2 ring-yellow-400' : ''}`}>
              <div className="flex-between">
                <div>
                  <div className="font-semibold">
                    {player.name} {pid === playerId && '(You)'}
                    {player.is_dealer && ' 👑'}
                    {player.is_small_blind && ' SB'}
                    {player.is_big_blind && ' BB'}
                  </div>
                  <div className="text-small text-gray-500">
                    Chips: ${player.chips} • 
                    {player.is_active ? 'Active' : 'Folded'}
                  </div>
                </div>
                <div className="flex gap-2">
                  {player.hole_cards?.map((card, index) => (
                    <Card 
                      key={index} 
                      card={card} 
                      faceDown={pid !== playerId}
                      size="medium"
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      {isMyTurn && gameState.phase !== 'complete' && (
        <div className="card">
          <h2 className="text-medium mb-4">Your Turn - Choose Action</h2>
          <div className="grid grid-2 gap-4">
            <button 
              onClick={() => playerAction('fold')} 
              className="btn btn-danger"
            >
              Fold
            </button>
            <button 
              onClick={() => playerAction('check')} 
              disabled={!canCheck}
              className={`btn ${canCheck ? 'btn-secondary' : 'btn-secondary'}`}
            >
              Check {!canCheck && '(Not Available)'}
            </button>
            <button 
              onClick={() => playerAction('call')} 
              disabled={!canCall}
              className={`btn ${canCall ? 'btn-primary' : 'btn-secondary'}`}
            >
              Call ${callAmount} {!canCall && '(Not Available)'}
            </button>
            <button 
              onClick={() => playerAction('raise', gameState.current_bet + minRaise)} 
              disabled={!canRaise}
              className={`btn ${canRaise ? 'btn-success' : 'btn-secondary'}`}
            >
              Raise to ${gameState.current_bet + minRaise} {!canRaise && '(Not Available)'}
            </button>
          </div>
          <div className="mt-4 text-small text-gray-600">
            <div>Current bet: ${gameState.current_bet}</div>
            <div>Your bet this round: ${bettingState?.bet_this_round || 0}</div>
            <div>Your chips: ${currentPlayer?.chips || 0}</div>
          </div>
          
          {/* Quantum Gate Actions */}
          {currentPlayer?.can_apply_gate && (
            <div className="mt-4 pt-4 border-t">
              <h3 className="text-medium mb-3">🔮 Quantum Gate Actions</h3>
              
              {/* Card Selection */}
              <div className="mb-6">
                <label className="text-small font-semibold mb-3 block flex items-center">
                  <span className="mr-2">🃏</span>
                  Your Cards - Select One to Apply Gate:
                </label>
                <div className="flex gap-6 justify-center">
                  {currentPlayer.hole_cards?.map((card, index) => (
                    <div key={index} className="flex flex-col items-center bg-white p-3 rounded-lg shadow-sm border-2 border-gray-200 hover:border-purple-300 transition-colors">
                      <Card card={card} size="large" />
                      <span className="text-sm mt-2 font-medium text-gray-700">Card {index + 1}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Gate Actions */}
              <div className="grid grid-2 gap-3">
                <div className="space-y-2">
                  <h4 className="text-small font-semibold">X Gate (Flip Qubit)</h4>
                  <div className="grid grid-2 gap-2">
                    {currentPlayer.hole_cards?.map((card, index) => (
                      <div key={index} className="space-y-1">
                        <button 
                          onClick={() => {
                            const socket = createSocket()
                            socket.emit('apply_gate', { 
                              lobby_id: lobbyId, 
                              player_id: playerId, 
                              gate: 'X', 
                              card_indices: [index], 
                              preview_only: true 
                            })
                          }}
                          className="btn btn-secondary text-xs"
                        >
                          Preview X on Card {index + 1}
                        </button>
                        <button 
                          onClick={() => {
                            const socket = createSocket()
                            socket.emit('apply_gate', { 
                              lobby_id: lobbyId, 
                              player_id: playerId, 
                              gate: 'X', 
                              card_indices: [index], 
                              preview_only: false 
                            })
                          }}
                          className="btn btn-primary text-xs"
                        >
                          Apply X to Card {index + 1}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-small font-semibold">Z Gate (Phase Flip)</h4>
                  <div className="grid grid-2 gap-2">
                    {currentPlayer.hole_cards?.map((card, index) => (
                      <div key={index} className="space-y-1">
                        <button 
                          onClick={() => {
                            const socket = createSocket()
                            socket.emit('apply_gate', { 
                              lobby_id: lobbyId, 
                              player_id: playerId, 
                              gate: 'Z', 
                              card_indices: [index], 
                              preview_only: true 
                            })
                          }}
                          className="btn btn-secondary text-xs"
                        >
                          Preview Z on Card {index + 1}
                        </button>
                        <button 
                          onClick={() => {
                            const socket = createSocket()
                            socket.emit('apply_gate', { 
                              lobby_id: lobbyId, 
                              player_id: playerId, 
                              gate: 'Z', 
                              card_indices: [index], 
                              preview_only: false 
                            })
                          }}
                          className="btn btn-primary text-xs"
                        >
                          Apply Z to Card {index + 1}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="text-small text-gray-500 mt-3">
                Gates used this round: {currentPlayer.gates_used_this_round}/2 • 
                Gates used this game: {currentPlayer.gates_used_this_game}/4
              </div>

              {/* Gate Preview Display */}
              {gatePreview && (
                <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg shadow-sm">
                  <h4 className="text-sm font-semibold mb-3 flex items-center">
                    <span className="mr-2">🔮</span>
                    Gate Preview
                  </h4>
                  
                  {/* Visual Card Comparison */}
                  <div className="flex items-center justify-center gap-6 mb-4">
                    <div className="text-center">
                      <div className="text-xs text-gray-600 mb-2 font-medium">Original Card</div>
                      <Card card={gatePreview.gate_info?.original_card} size="large" />
                    </div>
                    
                    <div className="flex flex-col items-center space-y-2">
                      <div className="text-3xl text-purple-600 font-bold">→</div>
                      <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-bold shadow">
                        {gatePreview.gate_info?.gate} GATE
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-gray-600 mb-2 font-medium">Result Card</div>
                      <Card card={gatePreview.gate_info?.result_card} size="large" />
                    </div>
                  </div>

                  {/* Gate Description */}
                  <div className="bg-white rounded-lg p-3 shadow-sm mb-3">
                    <div className="text-xs text-gray-700 text-center">
                      {gatePreview.gate_info?.gate === 'X' && (
                        <div>
                          <div className="font-semibold text-purple-700 mb-1">X Gate (Bit Flip)</div>
                          <div>Flips one qubit, potentially changing the card to a different rank or suit</div>
                        </div>
                      )}
                      {gatePreview.gate_info?.gate === 'Z' && (
                        <div>
                          <div className="font-semibold text-purple-700 mb-1">Z Gate (Phase Flip)</div>
                          <div>Flips the quantum phase, keeping the same card but changing its quantum state</div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => setGatePreview(null)}
                    className="btn btn-secondary text-xs px-4 py-2"
                  >
                    Close Preview
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Card History */}
      {cardHistory[playerId] && cardHistory[playerId].length > 0 && (
        <div className="card mt-4">
          <h2 className="text-medium mb-4 flex items-center">
            <span className="mr-2">🔄</span>
            Your Card Transformations
          </h2>
          <div className="space-y-3">
            {cardHistory[playerId].map((change, index) => (
              <div key={change.id || index} className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 shadow-sm">
                
                <div className="flex items-center justify-center space-x-4">
                  {/* Original Card */}
                  <div className="text-center">
                    <div className="text-xs text-gray-600 mb-1">Original</div>
                    <Card card={change.originalCard} size="medium" />
                  </div>
                  
                  {/* Transformation Arrow */}
                  <div className="flex flex-col items-center space-y-1">
                    <div className="text-2xl text-purple-600">→</div>
                    <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-bold shadow">
                      {change.gate} GATE
                    </div>
                  </div>
                  
                  {/* Result Card */}
                  <div className="text-center">
                    <div className="text-xs text-gray-600 mb-1">Result</div>
                    <Card card={change.resultCard} size="medium" />
                  </div>
                </div>
                
                {/* Transformation Details */}
                <div className="mt-3 text-center">
                  <div className="text-xs text-gray-500 bg-white px-3 py-1 rounded-full inline-block shadow">
                    {change.originalCard} transformed to {change.resultCard} using {change.gate} gate
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Game Status */}
      {gameState.phase !== 'complete' && (
        <div className="card mt-4">
          <h2 className="text-medium mb-4">Game Status</h2>
          <div className="text-center">
            {isBettingRoundComplete() ? (
              <div className="text-sm text-green-600 bg-green-50 p-3 rounded mb-2">
                ✅ Betting round complete - Next street will be dealt automatically
              </div>
            ) : (
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded mb-2">
                ⏳ Waiting for betting round to complete
              </div>
            )}
            <div className="text-small text-gray-500">
              Current phase: {gameState.phase} • 
              Betting round: {gameState.betting_state?.current_round}
            </div>
          </div>
        </div>
      )}

      {/* Game Complete */}
      {gameState.phase === 'complete' && (
        <div className="card">
          <h2 className="text-medium mb-4 text-center">🎉 Game Complete!</h2>
          <div className="text-center">
            <button onClick={() => navigate('/')} className="btn btn-primary">
              Back to Home
            </button>
          </div>
        </div>
      )}

      {/* Winner Popup */}
      {showWinnerPopup && winnerInfo && (
        <div className="popup-backdrop">
          <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-10 shadow-2xl winner-popup border border-gray-200">
            <div className="text-center">
              {/* Animated Winner Icon */}
              <div className="text-8xl mb-6 animate-bounce">
                {winnerInfo.isTie ? '🤝' : (winnerInfo.isCurrentPlayer ? '🎉' : '🏆')}
              </div>
              
              {/* Winner Title */}
              <h2 className="text-3xl font-bold mb-6 gradient-text">
                {winnerInfo.isTie ? 'Tie Game!' : (winnerInfo.isCurrentPlayer ? 'You Won!' : `${winnerInfo.playerName} Won!`)}
              </h2>
              
              {/* Hand Information */}
              {winnerInfo.isTie ? (
                <div className="bg-gradient-to-r from-blue-100 to-purple-100 border-2 border-blue-300 rounded-xl p-6 mb-6 shadow-lg">
                  <div className="text-xl font-bold text-blue-800 mb-3 flex items-center justify-center">
                    <span className="mr-2">🎯</span>
                    Tied Hands
                  </div>
                  {winnerInfo.allWinners.map((winner, index) => (
                    <div key={index} className="text-lg font-semibold text-blue-900 mb-2 bg-white rounded-lg p-2 shadow-sm">
                      {winner.name}: {winner.description}
                    </div>
                  ))}
                </div>
              ) : winnerInfo.isAutoWin ? (
                <div className="bg-gradient-to-r from-green-100 to-emerald-100 border-2 border-green-300 rounded-xl p-6 mb-6 shadow-lg">
                  <div className="text-xl font-bold text-green-800 mb-3 flex items-center justify-center">
                    <span className="mr-2">🏃‍♂️</span>
                    Auto-Win
                  </div>
                  <div className="text-2xl font-bold text-green-900 mb-2">
                    {winnerInfo.handDescription}
                  </div>
                  <div className="text-sm text-green-700 bg-white rounded-lg p-2 shadow-sm">
                    All other players folded
                  </div>
                </div>
              ) : (
                <div className="bg-gradient-to-r from-yellow-100 to-orange-100 border-2 border-yellow-300 rounded-xl p-6 mb-6 shadow-lg">
                  <div className="text-xl font-bold text-yellow-800 mb-3 flex items-center justify-center">
                    <span className="mr-2">🃏</span>
                    Winning Hand
                  </div>
                  <div className="text-2xl font-bold text-yellow-900 mb-2">
                    {winnerInfo.handDescription}
                  </div>
                  <div className="text-sm text-yellow-700 bg-white rounded-lg p-2 shadow-sm">
                    Hand Rank: {winnerInfo.handRank}
                  </div>
                </div>
              )}
              
              {/* Winnings */}
              <div className="bg-gradient-to-r from-green-100 to-emerald-100 border-2 border-green-300 rounded-xl p-6 mb-8 shadow-lg">
                <div className="text-xl font-bold text-green-800 mb-2 flex items-center justify-center">
                  <span className="mr-2">💰</span>
                  {winnerInfo.isTie ? 'Split Pot' : (winnerInfo.isAutoWin ? 'Pot Won' : 'Winnings')}
                </div>
                <div className="text-4xl font-bold text-green-900 bg-white rounded-lg p-3 shadow-sm pulse-animation">
                  ${winnerInfo.winnings}
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => {
                    setShowWinnerPopup(false)
                    navigate('/')
                  }}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200"
                >
                  🎮 New Game
                </button>
                <button
                  onClick={() => setShowWinnerPopup(false)}
                  className="bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200"
                >
                  👀 Continue Watching
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GamePage
