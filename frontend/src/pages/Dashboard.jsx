import React, { useState } from 'react'
import { Database, Upload as UploadIcon, Activity, BarChart3, MessageSquare, LogOut, User } from 'lucide-react'
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

  const navigationItems = [
    {
      id: 'upload',
      label: 'Upload Files',
      icon: UploadIcon,
      description: 'Upload and manage data files'
    },
    {
      id: 'status',
      label: 'Processing Status',
      icon: Activity,
      description: 'View processing status and history'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      description: 'Data insights and visualizations'
    },
    {
      id: 'chat',
      label: 'Data Chat',
      icon: MessageSquare,
      description: 'Query your data with AI'
    }
  ]

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="brand-container">
            <Database size={24} className="brand-icon" />
            <div className="brand-info">
              <h1>BIBBI</h1>
              <span className="brand-subtitle">Analytics Platform</span>
            </div>
          </div>
          
          <nav className="dashboard-nav">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                  onClick={() => setActiveView(item.id)}
                  title={item.description}
                >
                  <Icon size={16} className="nav-icon" />
                  <span className="nav-label">{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
        
        <div className="header-right">
          <div className="user-menu">
            <div className="user-info">
              <User size={16} className="user-icon" />
              <div className="user-details">
                <span className="user-email">{user?.email || 'Unknown User'}</span>
                <span className="user-role">Administrator</span>
              </div>
            </div>
            <button onClick={handleLogout} className="logout-btn" title="Sign out">
              <LogOut size={16} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      <div className={`dashboard-main ${activeView === 'analytics' ? 'analytics-view' : ''}`}>
        <main className={`dashboard-content ${activeView === 'analytics' ? 'analytics-view' : ''}`}>
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