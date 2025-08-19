import React, { useState } from 'react'
import { Eye, EyeOff, Mail, Lock } from 'lucide-react'
import apiService from '../services/api'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showPassword, setShowPassword] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      console.log('Attempting login with backend API...')
      
      // Use backend API for login
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Login failed')
      }

      console.log('Login successful:', { 
        hasToken: !!data.access_token,
        tokenLength: data.access_token?.length,
        userEmail: data.user?.email 
      })

      // Store the access token for API calls
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        console.log('Token stored in localStorage')
        
        // Trigger auth check in parent component
        if (onLoginSuccess) {
          onLoginSuccess()
        }
      } else {
        throw new Error('No access token received')
      }
    } catch (error) {
      console.error('Login error:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="logo-container">
            <h1 className="text-heading">BIBBI</h1>
          </div>
          <p className="subtitle text-small-caps">Data Analytics Platform</p>
        </div>
        
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="email" className="text-small-caps">Email Address</label>
            <div className="input-container">
              <Mail size={16} className="input-icon" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="Enter your email address"
                className="input-with-icon"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password" className="text-small-caps">Password</label>
            <div className="input-container">
              <Lock size={16} className="input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
                className="input-with-icon input-with-action"
              />
              <button
                type="button"
                className="input-action-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              <span>{error}</span>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary login-btn text-uppercase">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="login-footer">
          <p className="text-small-caps">Secure access to your data analytics dashboard</p>
        </div>
      </div>
    </div>
  )
}

export default Login