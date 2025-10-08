import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import { createSocket } from '../lib/socket'

const HomePage = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [lobbies, setLobbies] = useState([])
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

    // Periodic cleanup check every 30 seconds
    const cleanupInterval = setInterval(async () => {
      try {
        await api.cleanupEmptyLobbies()
        await loadLobbies() // Refresh the list
      } catch (error) {
        console.error('Cleanup failed:', error)
      }
    }, 30000)

    return () => {
      socket.off('lobby:update')
      clearInterval(cleanupInterval)
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
    if (!gameName.trim()) {
      alert('Please enter a game name')
      return
    }

    setLoading(true)
    try {
      const lobby = await api.createLobby(gameName.trim())
      await api.joinLobby(lobby.lobby_id, user.id, user.username)
      
      navigate(`/game/${lobby.lobby_id}/${user.id}`)
    } catch (error) {
      alert('Failed to create game: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const joinGame = async (lobbyId) => {
    setLoading(true)
    try {
      await api.joinLobby(lobbyId, user.id, user.username)
      
      navigate(`/game/${lobbyId}/${user.id}`)
    } catch (error) {
      alert('Failed to join game: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="text-center mb-8">
        <div className="flex justify-between items-center mb-4">
          <div></div>
          <h1 className="text-large text-white">🎰 Quantum Poker</h1>
          <button
            onClick={logout}
            className="text-white/80 hover:text-white text-sm underline"
          >
            Logout
          </button>
        </div>
        <p className="text-white opacity-90">Welcome back, {user?.username}! Play Texas Hold'em with quantum twists!</p>
      </div>

      <div className="card mb-8">
        <h2 className="text-medium mb-4">👤 Welcome, {user?.username}!</h2>
        
        <div className="grid grid-2 gap-4">
          <div>
            <h3 className="text-small mb-2">🆕 Create New Game</h3>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Game Name"
                value={gameName}
                onChange={(e) => setGameName(e.target.value)}
                className="input flex-1"
              />
              <button
                onClick={createGame}
                disabled={loading || !gameName.trim()}
                className="btn btn-success"
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
          
          <div>
            <h3 className="text-small mb-2">🎯 Quick Join</h3>
            <button
              onClick={loadLobbies}
              className="btn btn-primary w-full"
            >
              🔄 Refresh Available Games
            </button>
          </div>
        </div>
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
            <p className="text-xs mt-2">💡 Empty lobbies are automatically removed after 30 seconds</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {lobbies.map(lobby => (
              <div key={lobby.lobby_id} className="flex-between p-4 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">🎮 {lobby.name}</h3>
                  <p className="text-small text-gray-600">
                    Players: {lobby.players?.length || 0} / {lobby.max_players} • 
                    Status: {lobby.in_game ? '🟢 In Progress' : '🟡 Waiting'}
                    {lobby.waiting_players?.length > 0 && ` • ${lobby.waiting_players.length} waiting`}
                  </p>
                  {lobby.player_names && Object.values(lobby.player_names).length > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      Active: {Object.values(lobby.player_names).join(', ')}
                    </p>
                  )}
                  {lobby.waiting_player_names && Object.values(lobby.waiting_player_names).length > 0 && (
                    <p className="text-xs text-blue-500 mt-1">
                      Waiting: {Object.values(lobby.waiting_player_names).join(', ')}
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => joinGame(lobby.lobby_id)}
                    disabled={loading}
                    className="btn btn-primary"
                  >
                    {lobby.in_game ? 'Join & Wait' : 'Join Game'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default HomePage
