import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const NewLoginPage = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (isLogin) {
        // Login
        const response = await fetch('/api/auth/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            username: formData.username,
            password: formData.password,
          }).toString(),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Login failed')
        }

        const tokenData = await response.json()
        
        // Get user info
        const userResponse = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${tokenData.access_token}`
          }
        })
        
        if (userResponse.ok) {
          const userData = await userResponse.json()
          login(tokenData, userData)
          navigate('/home')
        } else {
          throw new Error('Failed to get user information')
        }
      } else {
        // Register
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Registration failed')
        }

        alert('Registration successful! Please log in.')
        setIsLogin(true)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-red-500 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Poker Table Background */}
      <div className="absolute inset-0">
        {/* Green Felt Table Effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-green-800/90 via-green-700/80 to-green-900/90"></div>
        
        {/* Table Texture Pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_25%,rgba(255,255,255,0.1)_1px,transparent_1px),radial-gradient(circle_at_75%_75%,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[length:50px_50px]"></div>
        </div>
        
        {/* Casino Lighting Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-yellow-400/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-0 right-1/4 w-80 h-80 bg-red-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
          <div className="absolute bottom-0 left-1/3 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        </div>
      </div>

      {/* Poker Elements */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Floating Poker Chips */}
        <div className="absolute top-10 left-10 w-12 h-12 bg-red-600 rounded-full border-4 border-red-800 shadow-lg animate-bounce" style={{animationDelay: '0s'}}>
          <div className="w-full h-full rounded-full border-2 border-white/30 flex items-center justify-center">
            <div className="w-6 h-6 bg-white rounded-full"></div>
          </div>
        </div>
        
        <div className="absolute top-20 right-20 w-10 h-10 bg-blue-600 rounded-full border-4 border-blue-800 shadow-lg animate-bounce" style={{animationDelay: '0.5s'}}>
          <div className="w-full h-full rounded-full border-2 border-white/30 flex items-center justify-center">
            <div className="w-4 h-4 bg-white rounded-full"></div>
          </div>
        </div>
        
        <div className="absolute bottom-20 left-20 w-14 h-14 bg-yellow-500 rounded-full border-4 border-yellow-700 shadow-lg animate-bounce" style={{animationDelay: '1s'}}>
          <div className="w-full h-full rounded-full border-2 border-white/30 flex items-center justify-center">
            <div className="w-8 h-8 bg-white rounded-full"></div>
          </div>
        </div>
        
        <div className="absolute bottom-10 right-10 w-11 h-11 bg-green-600 rounded-full border-4 border-green-800 shadow-lg animate-bounce" style={{animationDelay: '1.5s'}}>
          <div className="w-full h-full rounded-full border-2 border-white/30 flex items-center justify-center">
            <div className="w-5 h-5 bg-white rounded-full"></div>
          </div>
        </div>

        {/* Casino Symbols */}
        <div className="absolute top-1/4 left-1/4 text-6xl text-yellow-400/20 animate-pulse">♠</div>
        <div className="absolute top-1/3 right-1/4 text-5xl text-red-500/20 animate-pulse" style={{animationDelay: '0.5s'}}>♥</div>
        <div className="absolute bottom-1/4 left-1/3 text-4xl text-red-500/20 animate-pulse" style={{animationDelay: '1s'}}>♦</div>
        <div className="absolute bottom-1/3 right-1/3 text-5xl text-yellow-400/20 animate-pulse" style={{animationDelay: '1.5s'}}>♣</div>
        
        {/* Dice */}
        <div className="absolute top-1/2 left-10 w-8 h-8 bg-white rounded shadow-lg flex items-center justify-center text-black font-bold text-sm animate-spin" style={{animationDuration: '3s'}}>
          <div className="flex flex-wrap w-4 h-4">
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
          </div>
        </div>
        
        <div className="absolute top-1/3 right-10 w-8 h-8 bg-white rounded shadow-lg flex items-center justify-center text-black font-bold text-sm animate-spin" style={{animationDuration: '4s', animationDirection: 'reverse'}}>
          <div className="flex flex-wrap w-4 h-4">
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
            <div className="w-1 h-1 bg-black rounded-full m-0.5"></div>
          </div>
        </div>
      </div>

      {/* Main Login Card */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/20 relative z-10">
        {/* Header Section */}
        <div className="text-center mb-6">
          <div className="relative mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-800 rounded-xl flex items-center justify-center mx-auto shadow-lg border-2 border-yellow-400">
              <div className="flex items-center space-x-1">
                <span className="text-red-600 text-xl">♠</span>
                <span className="text-white text-xl font-bold">QP</span>
                <span className="text-red-600 text-xl">♥</span>
              </div>
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full animate-ping"></div>
          </div>
          
          <h1 className="text-7xl font-bold text-red-500 mb-2 animate-pulse">
            🎰 FINAL TEST! 🎰
          </h1>
          
          <p className="text-yellow-400 text-3xl font-bold">
            {isLogin ? 'BRIGHT GREEN BACKGROUND!' : 'POKER TABLE THEME!'}
          </p>
        </div>

        {/* Form Section */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username Field */}
          <div className="space-y-2">
            <label className="block text-white/90 text-sm font-medium">
              Username
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                required
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300"
                placeholder="Enter username"
              />
            </div>
          </div>

          {/* Email Field - Only for Registration */}
          {!isLogin && (
            <div className="space-y-2">
              <label className="block text-white/90 text-sm font-medium">
                Email
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300"
                  placeholder="Enter email"
                />
              </div>
            </div>
          )}

          {/* Password Field */}
          <div className="space-y-2">
            <label className="block text-white/90 text-sm font-medium">
              Password
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300"
                placeholder="Enter password"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 animate-shake">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-red-600 to-red-800 text-white py-3 px-6 rounded-lg font-semibold hover:from-red-700 hover:to-red-900 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] relative overflow-hidden group border-2 border-yellow-400/30"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-400/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            {loading ? (
              <div className="flex items-center justify-center relative z-10">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                <span>{isLogin ? 'Signing in...' : 'Creating account...'}</span>
              </div>
            ) : (
              <div className="flex items-center justify-center relative z-10">
                <span className="mr-2">{isLogin ? '♠' : '♥'}</span>
                <span>{isLogin ? 'Enter Game' : 'Join Now'}</span>
                <span className="ml-2">{isLogin ? '♣' : '♦'}</span>
              </div>
            )}
          </button>
        </form>

        {/* Footer Section */}
        <div className="mt-6 space-y-4">
          {/* Toggle Login/Register */}
          <div className="text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin)
                setFormData({ username: '', email: '', password: '' })
                setError('')
              }}
              className="text-white/70 hover:text-white text-sm transition-colors duration-300 flex items-center justify-center mx-auto group"
            >
              <span className="mr-2 group-hover:scale-110 transition-transform duration-300">
                {isLogin ? '🆕' : '↩️'}
              </span>
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>

          {/* Features */}
          <div className="flex justify-center space-x-6 text-xs">
            <div className="flex items-center space-x-1">
              <span className="text-green-400">🔒</span>
              <span className="text-white/60">Secure</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-blue-400">⚡</span>
              <span className="text-white/60">Fast</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-purple-400">🎯</span>
              <span className="text-white/60">Fun</span>
            </div>
          </div>

          {/* Terms */}
          <div className="text-center">
            <p className="text-white/50 text-xs">
              By continuing, you agree to our{' '}
              <a href="#" className="text-blue-400 hover:text-blue-300 underline">Terms</a>
              {' '}and{' '}
              <a href="#" className="text-blue-400 hover:text-blue-300 underline">Privacy</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NewLoginPage
