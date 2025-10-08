import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const PokerLoginPage = () => {
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
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 50%, #15803d 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Floating Poker Chips */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '48px',
        height: '48px',
        backgroundColor: '#dc2626',
        borderRadius: '50%',
        border: '4px solid #991b1b',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        animation: 'bounce 2s infinite',
        zIndex: 1
      }}>
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '24px',
            height: '24px',
            backgroundColor: 'white',
            borderRadius: '50%'
          }}></div>
        </div>
      </div>

      <div style={{
        position: 'absolute',
        top: '20%',
        right: '20%',
        width: '40px',
        height: '40px',
        backgroundColor: '#2563eb',
        borderRadius: '50%',
        border: '4px solid #1d4ed8',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        animation: 'bounce 2s infinite 0.5s',
        zIndex: 1
      }}>
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '16px',
            height: '16px',
            backgroundColor: 'white',
            borderRadius: '50%'
          }}></div>
        </div>
      </div>

      <div style={{
        position: 'absolute',
        bottom: '20%',
        left: '20%',
        width: '56px',
        height: '56px',
        backgroundColor: '#eab308',
        borderRadius: '50%',
        border: '4px solid #a16207',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        animation: 'bounce 2s infinite 1s',
        zIndex: 1
      }}>
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            backgroundColor: 'white',
            borderRadius: '50%'
          }}></div>
        </div>
      </div>

      {/* Casino Symbols */}
      <div style={{
        position: 'absolute',
        top: '25%',
        left: '25%',
        fontSize: '48px',
        color: 'rgba(234, 179, 8, 0.2)',
        animation: 'pulse 2s infinite',
        zIndex: 1
      }}>♠</div>

      <div style={{
        position: 'absolute',
        top: '33%',
        right: '25%',
        fontSize: '40px',
        color: 'rgba(239, 68, 68, 0.2)',
        animation: 'pulse 2s infinite 0.5s',
        zIndex: 1
      }}>♥</div>

      <div style={{
        position: 'absolute',
        bottom: '25%',
        left: '33%',
        fontSize: '32px',
        color: 'rgba(239, 68, 68, 0.2)',
        animation: 'pulse 2s infinite 1s',
        zIndex: 1
      }}>♦</div>

      <div style={{
        position: 'absolute',
        bottom: '33%',
        right: '33%',
        fontSize: '40px',
        color: 'rgba(234, 179, 8, 0.2)',
        animation: 'pulse 2s infinite 1.5s',
        zIndex: 1
      }}>♣</div>

      {/* Main Login Card */}
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(20px)',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        padding: '32px',
        width: '100%',
        maxWidth: '400px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Header Section */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ position: 'relative', marginBottom: '16px' }}>
            <div style={{
              width: '64px',
              height: '64px',
              background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              border: '2px solid #eab308'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ color: '#dc2626', fontSize: '20px' }}>♠</span>
                <span style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>QP</span>
                <span style={{ color: '#dc2626', fontSize: '20px' }}>♥</span>
              </div>
            </div>
            <div style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              width: '16px',
              height: '16px',
              backgroundColor: '#eab308',
              borderRadius: '50%',
              animation: 'ping 1s infinite'
            }}></div>
          </div>
          
          <h1 style={{
            fontSize: '48px',
            fontWeight: 'bold',
            color: '#dc2626',
            marginBottom: '8px',
            animation: 'pulse 2s infinite'
          }}>
            🎰 POKER CASINO 🎰
          </h1>
          
          <p style={{
            color: '#eab308',
            fontSize: '24px',
            fontWeight: 'bold'
          }}>
            {isLogin ? 'Welcome to the Table!' : 'Join the Game!'}
          </p>
        </div>

        {/* Form Section */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Username/Email Field */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '14px', fontWeight: '500' }}>
              Username or Email
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'rgba(255, 255, 255, 0.6)'
              }}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  paddingLeft: '40px',
                  paddingRight: '16px',
                  paddingTop: '12px',
                  paddingBottom: '12px',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '16px'
                }}
                placeholder="Enter username or email"
              />
            </div>
          </div>

          {/* Email Field - Only for Registration */}
          {!isLogin && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '14px', fontWeight: '500' }}>
                Email
              </label>
              <div style={{ position: 'relative' }}>
                <div style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'rgba(255, 255, 255, 0.6)'
                }}>
                  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  style={{
                    width: '100%',
                    paddingLeft: '40px',
                    paddingRight: '16px',
                    paddingTop: '12px',
                    paddingBottom: '12px',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '8px',
                    color: 'white',
                    fontSize: '16px'
                  }}
                  placeholder="Enter email"
                />
              </div>
            </div>
          )}

          {/* Password Field */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '14px', fontWeight: '500' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'rgba(255, 255, 255, 0.6)'
              }}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  paddingLeft: '40px',
                  paddingRight: '16px',
                  paddingTop: '12px',
                  paddingBottom: '12px',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '16px'
                }}
                placeholder="Enter password"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '12px',
              animation: 'shake 0.5s ease-in-out'
            }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20" style={{ color: '#fca5a5', marginRight: '8px' }}>
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p style={{ color: '#fecaca', fontSize: '14px' }}>{error}</p>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
              color: 'white',
              paddingTop: '12px',
              paddingBottom: '12px',
              paddingLeft: '24px',
              paddingRight: '24px',
              borderRadius: '8px',
              fontWeight: '600',
              border: '2px solid rgba(234, 179, 8, 0.3)',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              fontSize: '16px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid transparent',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  marginRight: '8px'
                }}></div>
                <span>{isLogin ? 'Signing in...' : 'Creating account...'}</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ marginRight: '8px' }}>{isLogin ? '♠' : '♥'}</span>
                <span>{isLogin ? 'Enter Game' : 'Join Now'}</span>
                <span style={{ marginLeft: '8px' }}>{isLogin ? '♣' : '♦'}</span>
              </div>
            )}
          </button>
        </form>

        {/* Footer Section */}
        <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Toggle Login/Register */}
          <div style={{ textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin)
                setFormData({ username: '', email: '', password: '' })
                setError('')
              }}
              style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '14px',
                background: 'none',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>

          {/* Features */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#22c55e' }}>🔒</span>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Secure</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#3b82f6' }}>⚡</span>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Fast</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#a855f7' }}>🎯</span>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Fun</span>
            </div>
          </div>
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes bounce {
          0%, 20%, 53%, 80%, 100% {
            transform: translate3d(0, 0, 0);
          }
          40%, 43% {
            transform: translate3d(0, -30px, 0);
          }
          70% {
            transform: translate3d(0, -15px, 0);
          }
          90% {
            transform: translate3d(0, -4px, 0);
          }
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        
        @keyframes ping {
          0% {
            transform: scale(1);
            opacity: 1;
          }
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
          20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default PokerLoginPage
