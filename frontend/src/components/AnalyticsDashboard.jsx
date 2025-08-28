import React, { useState, useEffect, useRef } from 'react'
import { getDashboardConfigs, saveDashboardConfig, updateDashboardConfig, deleteDashboardConfig } from '../services/api'

const AnalyticsDashboard = () => {
  const [dashboards, setDashboards] = useState([])
  const [activeDashboard, setActiveDashboard] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showFloatingMenu, setShowFloatingMenu] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const iframeRef = useRef(null)
  
  // Form state for adding/editing dashboards
  const [dashboardForm, setDashboardForm] = useState({
    dashboardName: '',
    dashboardType: 'looker',
    dashboardUrl: '',
    authenticationMethod: 'none',
    authenticationConfig: {},
    permissions: [],
    isActive: true
  })

  useEffect(() => {
    fetchDashboards()

    // Handle fullscreen exit to clean up styles
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        const container = document.querySelector('.dashboard-viewer-main');
        const iframe = document.querySelector('.dashboard-iframe-container iframe');
        
        if (container) {
          container.classList.remove('fullscreen-active');
        }
        
        if (iframe) {
          iframe.style.width = '100%';
          iframe.style.height = '600px';
        }
      }
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }
  }, [])

  const fetchDashboards = async () => {
    try {
      setLoading(true)
      console.log('📊 Fetching dashboard configurations...')
      
      const response = await getDashboardConfigs()
      console.log('📊 Dashboard API response:', response)
      console.log('📊 Dashboard configs received:', response.configs?.length || 0)
      
      setDashboards(response.configs || [])
      
      // Set first active dashboard as default
      const activeConfig = response.configs?.find(d => d.isActive)
      if (activeConfig && !activeDashboard) {
        console.log('📊 Setting active dashboard:', activeConfig.dashboardName)
        setActiveDashboard(activeConfig)
      }
    } catch (err) {
      console.error('❌ Error fetching dashboards:', err)
      setError('Failed to load dashboard configurations')
    } finally {
      setLoading(false)
    }
  }

  const handleAddDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await saveDashboardConfig(dashboardForm)
      setDashboards(prev => [...prev, response.config])
      setShowAddModal(false)
      resetForm()
      setSuccess('Dashboard connected successfully')
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error adding dashboard:', err)
      setError('Failed to connect dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteDashboard = async (dashboardId) => {
    if (!confirm('Are you sure you want to delete this dashboard?')) return
    
    try {
      setLoading(true)
      setError(null)
      
      console.log('🗑️ Deleting dashboard with ID:', dashboardId)
      
      const result = await deleteDashboardConfig(dashboardId)
      console.log('🗑️ Delete API response:', result)
      
      // Remove from local state
      setDashboards(prev => prev.filter(d => d.id !== dashboardId))
      
      if (activeDashboard && activeDashboard.id === dashboardId) {
        setActiveDashboard(null)
      }
      
      setSuccess('Dashboard deleted successfully')
      setTimeout(() => setSuccess(null), 3000)
      
      // Optionally refresh the dashboard list to ensure consistency
      console.log('🔄 Refreshing dashboard list after deletion')
      setTimeout(() => {
        fetchDashboards()
      }, 500)
      
    } catch (err) {
      console.error('❌ Error deleting dashboard:', err)
      console.error('❌ Full error details:', {
        message: err.message,
        stack: err.stack,
        dashboardId: dashboardId
      })
      setError(`Failed to delete dashboard: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setDashboardForm({
      dashboardName: '',
      dashboardType: 'looker',
      dashboardUrl: '',
      authenticationMethod: 'none',
      authenticationConfig: {},
      permissions: [],
      isActive: true
    })
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setDashboardForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const DashboardModal = () => (
    <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Connect New Dashboard</h3>
          <button onClick={() => setShowAddModal(false)} className="modal-close">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="modal-body">
          <div className="form-field">
            <label className="form-label">Dashboard Name</label>
            <input
              type="text"
              name="dashboardName"
              value={dashboardForm.dashboardName}
              onChange={handleInputChange}
              placeholder="e.g., Sales Performance"
              className="form-input"
              required
            />
          </div>
          
          <div className="form-field">
            <label className="form-label">Dashboard URL</label>
            <input
              type="url"
              name="dashboardUrl"
              value={dashboardForm.dashboardUrl}
              onChange={handleInputChange}
              placeholder="https://your-dashboard-url.com"
              className="form-input"
              required
            />
          </div>
          
          <div className="form-field">
            <div className="form-checkbox-group">
              <input
                type="checkbox"
                name="isActive"
                checked={dashboardForm.isActive}
                onChange={handleInputChange}
                id="isActiveCheckbox"
                className="form-checkbox"
              />
              <label htmlFor="isActiveCheckbox" className="form-checkbox-label">
                Set as primary dashboard
              </label>
            </div>
          </div>
        </div>
        
        <div className="modal-footer">
          <button onClick={() => setShowAddModal(false)} className="btn btn-ghost">
            Cancel
          </button>
          <button 
            onClick={handleAddDashboard} 
            disabled={loading || !dashboardForm.dashboardName || !dashboardForm.dashboardUrl}
            className={`btn btn-primary ${loading ? 'loading' : ''}`}
          >
            {loading ? 'Connecting...' : 'Connect Dashboard'}
          </button>
        </div>
      </div>
    </div>
  )

  const handleFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      const dashboardContainer = document.querySelector('.dashboard-viewport')
      if (dashboardContainer) {
        dashboardContainer.requestFullscreen()
      }
    }
  }

  const FloatingActions = () => (
    <div className="floating-actions">
      {activeDashboard && (
        <>
          <button 
            className="fab fab-primary"
            onClick={handleFullscreen}
            title="Toggle Fullscreen"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
          
          <button 
            className="fab fab-secondary"
            onClick={() => window.open(activeDashboard.dashboardUrl, '_blank')}
            title="Open External"
          >
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
          
          <button 
            className="fab fab-tertiary"
            onClick={() => setShowFloatingMenu(!showFloatingMenu)}
            title="More Options"
          >
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
          
          {showFloatingMenu && (
            <div className="floating-menu">
              <button 
                onClick={() => {
                  if (confirm(`Disconnect "${activeDashboard.dashboardName}"?`)) {
                    handleDeleteDashboard(activeDashboard.id)
                  }
                  setShowFloatingMenu(false)
                }}
              >
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Disconnect
              </button>
            </div>
          )}
        </>
      )}
      
      <button 
        className="fab fab-add"
        onClick={() => setShowAddModal(true)}
        title="Add Dashboard"
      >
        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  )

  if (loading && dashboards.length === 0) {
    return (
      <div className="analytics-dashboard">
        <div className="loading-state">
          <p>Loading dashboards...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      {/* Compact Header with Tabs */}
      <div className="dashboard-header">
        <div className="dashboard-tabs">
          {dashboards.map((dashboard, index) => (
            <button
              key={dashboard.id}
              className={`dashboard-tab ${activeDashboard?.id === dashboard.id ? 'active' : ''}`}
              onClick={() => setActiveDashboard(dashboard)}
              title={dashboard.dashboardName}
            >
              <span className="tab-name">{dashboard.dashboardName}</span>
              {dashboard.isActive && <div className="primary-indicator" />}
            </button>
          ))}
          
          {dashboards.length === 0 && (
            <div className="empty-tabs">
              <span>No dashboards connected</span>
            </div>
          )}
        </div>
        
        {/* Status indicators */}
        <div className="header-status">
          {error && (
            <div className="status-error">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}
          
          {success && (
            <div className="status-success">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{success}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Main Dashboard Viewport */}
      <div className="dashboard-viewport">
        {dashboards.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg width="64" height="64" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="empty-state-content">
              <h2>Connect Your First Dashboard</h2>
              <p>Start monitoring your business metrics by connecting your analytics dashboard</p>
              <button 
                onClick={() => setShowAddModal(true)} 
                className="btn btn-primary btn-large"
              >
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Connect Dashboard
              </button>
            </div>
          </div>
        ) : activeDashboard ? (
          <div className="dashboard-frame">
            {loading && (
              <div className="dashboard-loading">
                <div className="loading-spinner"></div>
                <p>Loading dashboard...</p>
              </div>
            )}
            <iframe
              ref={iframeRef}
              src={activeDashboard.dashboardUrl}
              className="dashboard-iframe"
              title={activeDashboard.dashboardName}
              sandbox="allow-scripts allow-same-origin allow-forms"
              onLoad={() => setLoading(false)}
              onError={() => {
                setLoading(false)
                setError('Failed to load dashboard')
              }}
            />
          </div>
        ) : null}
      </div>
      
      {/* Floating Action Buttons */}
      <FloatingActions />
      
      {/* Add Dashboard Modal */}
      {showAddModal && <DashboardModal />}
      
    </div>
  )
}

export default AnalyticsDashboard