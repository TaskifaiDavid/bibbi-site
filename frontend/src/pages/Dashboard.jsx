import React, { useState } from 'react'
import Upload from '../components/Upload'
import StatusList from '../components/StatusList'
import AnalyticsDashboard from '../components/AnalyticsDashboard'
import ChatSection from '../components/ChatSection'

function Dashboard({ user, onLogout }) {
  const [activeView, setActiveView] = useState('upload')

  console.log('Dashboard rendered with user:', user)

  const handleLogout = () => {
    console.log('Logout clicked')
    if (onLogout) {
      onLogout()
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <h1>BIBBI</h1>
          <nav className="dashboard-nav">
            <button
              className={activeView === 'upload' ? 'active' : ''}
              onClick={() => setActiveView('upload')}
            >
              Upload Files
            </button>
            <button
              className={activeView === 'status' ? 'active' : ''}
              onClick={() => setActiveView('status')}
            >
              Processing Status
            </button>
            <button
              className={activeView === 'analytics' ? 'active' : ''}
              onClick={() => setActiveView('analytics')}
            >
              Analytics
            </button>
            <button
              className={activeView === 'chat' ? 'active' : ''}
              onClick={() => setActiveView('chat')}
            >
              Data Chat
            </button>
          </nav>
        </div>
        <div className="user-info">
          <span>{user?.email || 'Unknown User'}</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-main">
        <main className="dashboard-content">
        {activeView === 'upload' ? (
          <Upload />
        ) : activeView === 'status' ? (
          <StatusList />
        ) : activeView === 'analytics' ? (
          <AnalyticsDashboard />
        ) : activeView === 'chat' ? (
          <ChatSection />
        ) : (
          <Upload />
        )}
        </main>
      </div>
    </div>
  )
}

export default Dashboard