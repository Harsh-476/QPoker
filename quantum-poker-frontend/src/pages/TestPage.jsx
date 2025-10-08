import React from 'react'

const TestPage = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: 'red', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      fontSize: '48px',
      color: 'white',
      fontWeight: 'bold'
    }}>
      <div>
        <h1>🎰 THIS IS A TEST PAGE 🎰</h1>
        <p>If you see this, the server is working!</p>
        <p>Background should be RED</p>
      </div>
    </div>
  )
}

export default TestPage
