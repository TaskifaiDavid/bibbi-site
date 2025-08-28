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
      <div className="login-background-gradient"></div>
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
      
      <style jsx>{`
        .login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          position: relative;
          overflow: hidden;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        .login-background-gradient {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 50%, var(--primary-800) 100%);
          opacity: 0.05;
          z-index: -1;
        }

        .login-box {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 24px;
          padding: 3rem;
          width: 100%;
          max-width: 480px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.05);
          position: relative;
          animation: slideUp 0.6s ease-out;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .login-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        .logo-container h1 {
          font-family: var(--font-display);
          font-size: 3rem;
          font-weight: 800;
          color: var(--primary-600);
          margin: 0;
          letter-spacing: -0.02em;
          background: linear-gradient(135deg, var(--primary-600), var(--primary-500));
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .subtitle {
          margin-top: 0.5rem;
          color: var(--neutral-600);
          font-size: 1rem;
          font-weight: 500;
          letter-spacing: 0.5px;
        }

        .login-form {
          space-y: 1.5rem;
        }

        .form-group {
          margin-bottom: 1.5rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          color: var(--neutral-700);
          font-weight: 600;
          font-size: 0.875rem;
          letter-spacing: 0.5px;
        }

        .input-container {
          position: relative;
          display: flex;
          align-items: center;
        }

        .input-icon {
          position: absolute;
          left: 16px;
          color: var(--neutral-400);
          z-index: 2;
          transition: color 0.2s ease;
        }

        .input-with-icon {
          width: 100%;
          padding: 16px 16px 16px 48px;
          border: 2px solid var(--neutral-200);
          border-radius: 12px;
          font-size: 1rem;
          transition: all 0.3s ease;
          background: var(--neutral-0);
        }

        .input-with-icon:focus {
          outline: none;
          border-color: var(--primary-500);
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .input-with-icon:focus + .input-icon {
          color: var(--primary-500);
        }

        .input-with-action {
          padding-right: 48px;
        }

        .input-action-btn {
          position: absolute;
          right: 16px;
          background: none;
          border: none;
          color: var(--neutral-400);
          cursor: pointer;
          padding: 4px;
          border-radius: 6px;
          transition: all 0.2s ease;
        }

        .input-action-btn:hover {
          color: var(--primary-500);
          background: var(--primary-50);
        }

        .error-message {
          background: var(--error-50);
          border: 1px solid var(--error-200);
          border-radius: 8px;
          padding: 12px 16px;
          margin: 1rem 0;
          color: var(--error-700);
          font-size: 0.875rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .login-btn {
          width: 100%;
          background: linear-gradient(135deg, var(--primary-600), var(--primary-500));
          color: white;
          border: none;
          border-radius: 12px;
          padding: 16px 24px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          letter-spacing: 0.5px;
          margin-top: 2rem;
          position: relative;
          overflow: hidden;
        }

        .login-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
        }

        .login-btn:active {
          transform: translateY(0);
        }

        .login-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
          transform: none;
        }

        .login-footer {
          text-align: center;
          margin-top: 2rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--neutral-200);
        }

        .login-footer p {
          color: var(--neutral-500);
          font-size: 0.875rem;
          margin: 0;
        }

        @media (max-width: 640px) {
          .login-container {
            padding: 1rem;
          }
          
          .login-box {
            padding: 2rem;
            border-radius: 16px;
          }
          
          .logo-container h1 {
            font-size: 2.5rem;
          }
        }
      `}</style>
    </div>
  )
}

export default Login