import React, { useState } from 'react'
import { Upload as UploadIcon, Activity, BarChart3, MessageSquare, LogOut, User } from 'lucide-react'
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
        <div className="dashboard-brand">
          <h1>BIBBI</h1>
          <div className="dashboard-subtitle">Data Analytics Platform</div>
        </div>
        
        <nav className="dashboard-nav">
          {navigationItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                className={`dashboard-nav-item ${activeView === item.id ? 'active' : ''}`}
                onClick={() => setActiveView(item.id)}
                title={item.description}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
        
        <div className="dashboard-user">
          <div className="dashboard-user-info">
            <div className="dashboard-user-email">{user?.email || 'Unknown User'}</div>
            <div className="dashboard-user-role">Administrator</div>
          </div>
          <button onClick={handleLogout} className="btn btn-ghost" title="Sign out">
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      <main className="dashboard-main">
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
  )
}

export default Dashboard