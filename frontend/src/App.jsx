import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      console.log('🔍 Checking authentication status...')
      const token = localStorage.getItem('access_token')
      console.log('Auth check:', { 
        hasToken: !!token,
        tokenLength: token ? token.length : 0 
      })
      
      if (!token) {
        console.log('❌ No token found, user not authenticated')
        setLoading(false)
        return
      }

      console.log('🔗 Validating token with backend...')
      // Validate token with backend using status endpoint which requires auth
      const response = await fetch('http://localhost:8000/api/status/uploads', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // If we can fetch uploads, the token is valid
      const uploads = await response.json()
      console.log('✅ Auth validation successful, got uploads:', uploads.length)
      
      console.log('✅ User authenticated successfully')
      setIsAuthenticated(true)
      
      // Extract user info from token (basic decode for display)
      try {
        const tokenPayload = JSON.parse(atob(token.split('.')[1]))
        setUser({
          email: tokenPayload.email,
          id: tokenPayload.sub
        })
      } catch (e) {
        console.warn('Could not parse token payload:', e)
        setUser({ email: 'Unknown', id: 'Unknown' })
      }
    } catch (error) {
      console.error('❌ Auth check failed:', error)
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      })
      localStorage.removeItem('access_token')
      setIsAuthenticated(false)
    } finally {
      console.log('✅ Auth check completed')
      setLoading(false)
    }
  }

  // Handle route changes from login
  useEffect(() => {
    const handleStorageChange = () => {
      checkAuthStatus()
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  if (loading) {
    console.log('🔄 App loading...')
    return <div className="loading">Loading...</div>
  }

  console.log('🎯 App render:', { 
    isAuthenticated, 
    user: user?.email || 'none' 
  })

  return (
    <div className="app">
      {!isAuthenticated ? (
        <Login onLoginSuccess={checkAuthStatus} />
      ) : (
        <Dashboard user={user} onLogout={() => {
          console.log('🚪 Logging out...')
          localStorage.removeItem('access_token')
          setIsAuthenticated(false)
          setUser(null)
        }} />
      )}
    </div>
  )
}

export default App