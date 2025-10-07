import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { createSocket } from '../lib/socket'

const HomePage = () => {
  const navigate = useNavigate()
  const [lobbies, setLobbies] = useState([])
  const [playerName, setPlayerName] = useState('')
  const [gameName, setGameName] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadLobbies()
    const socket = createSocket()
    
    socket.on('lobby:update', (lobby) => {
      setLobbies(prev => {
        const exists = prev.find(l => l.lobby_id === lobby.lobby_id)
        if (exists) {
          return prev.map(l => l.lobby_id === lobby.lobby_id ? lobby : l)
        }
        return [...prev, lobby]
      })
    })

    return () => {
      socket.off('lobby:update')
    }
  }, [])

  const loadLobbies = async () => {
    try {
      const data = await api.listLobbies()
      setLobbies(data)
    } catch (error) {
      console.error('Failed to load lobbies:', error)
    }
  }

  const createGame = async () => {
    if (!gameName.trim() || !playerName.trim()) {
      alert('Please enter both game name and your name')
      return
    }

    setLoading(true)
    try {
      const lobby = await api.createLobby(gameName.trim())
      const playerId = `player_${Date.now()}`
      await api.joinLobby(lobby.lobby_id, playerId, playerName.trim())
      
      navigate(`/game/${lobby.lobby_id}/${playerId}`)
    } catch (error) {
      alert('Failed to create game: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const joinGame = async (lobbyId) => {
    if (!playerName.trim()) {
      alert('Please enter your name')
      return
    }

    setLoading(true)
    try {
      const playerId = `player_${Date.now()}`
      await api.joinLobby(lobbyId, playerId, playerName.trim())
      
      navigate(`/game/${lobbyId}/${playerId}`)
    } catch (error) {
      alert('Failed to join game: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="text-center mb-8">
        <h1 className="text-large text-white mb-4">🎰 Quantum Poker</h1>
        <p className="text-white opacity-90">Play Texas Hold'em with quantum twists!</p>
      </div>

      <div className="card mb-8">
        <h2 className="text-medium mb-4">👤 Player Setup</h2>
        <div className="grid grid-2 mb-4">
          <input
            type="text"
            placeholder="Your Name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="input"
          />
          <input
            type="text"
            placeholder="Game Name"
            value={gameName}
            onChange={(e) => setGameName(e.target.value)}
            className="input"
          />
        </div>
        <button
          onClick={createGame}
          disabled={loading || !gameName.trim() || !playerName.trim()}
          className="btn btn-success"
        >
          {loading ? 'Creating...' : '🆕 Create New Game'}
        </button>
      </div>

      <div className="card">
        <div className="flex-between mb-4">
          <h2 className="text-medium">🎯 Available Games</h2>
          <button onClick={loadLobbies} className="btn btn-secondary">
            🔄 Refresh
          </button>
        </div>

        {lobbies.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-large mb-2">🎲</div>
            <p>No games available yet. Create one above!</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {lobbies.map(lobby => (
              <div key={lobby.lobby_id} className="flex-between p-4 bg-gray-50 rounded-lg border">
                <div>
                  <h3 className="font-semibold">🎮 {lobby.name}</h3>
                  <p className="text-small">
                    Players: {lobby.players?.length || 0} / {lobby.max_players} • 
                    Status: {lobby.in_game ? '🟢 In Progress' : '🟡 Waiting'}
                  </p>
                </div>
                <button
                  onClick={() => joinGame(lobby.lobby_id)}
                  disabled={loading || !playerName.trim()}
                  className="btn btn-primary"
                >
                  Join Game
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default HomePage
