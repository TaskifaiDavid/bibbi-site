import React, { useState, useEffect } from 'react'
import { getDashboardConfigs, saveDashboardConfig, updateDashboardConfig, deleteDashboardConfig } from '../services/api'

const AnalyticsDashboard = () => {
  const [dashboards, setDashboards] = useState([])
  const [activeDashboard, setActiveDashboard] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
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
      setShowAddForm(false)
      resetForm()
      setSuccess('Dashboard added successfully')
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error adding dashboard:', err)
      setError('Failed to add dashboard')
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

  const DashboardConfigForm = () => (
    <div className="card analytics-form-card">
      <div className="card-header">
        <h3 style={{margin: 0, fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--text-primary)'}}>
          Connect Analytics Dashboard
        </h3>
        <p style={{margin: '8px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)'}}>
          Connect your business intelligence dashboard to view insights and metrics
        </p>
      </div>
      
      <div className="card-body">
        <div className="form-group">
          <label className="form-label">Dashboard Name</label>
          <input
            type="text"
            name="dashboardName"
            value={dashboardForm.dashboardName}
            onChange={handleInputChange}
            placeholder="e.g., Sales Performance, Monthly Analytics"
            autoComplete="off"
            autoFocus={false}
            className="form-input"
            required
          />
          <span className="form-help">
            Give your dashboard a descriptive name to identify it easily
          </span>
        </div>
        
        <div className="form-group">
          <label className="form-label">Dashboard URL</label>
          <input
            type="url"
            name="dashboardUrl"
            value={dashboardForm.dashboardUrl}
            onChange={handleInputChange}
            placeholder="https://your-dashboard-url.com"
            autoComplete="off"
            autoFocus={false}
            className="form-input"
            required
          />
          <span className="form-help">
            Paste the embed URL from your analytics platform (Looker, Tableau, etc.)
          </span>
        </div>
        
        <div className="form-group">
          <div className="form-checkbox">
            <input
              type="checkbox"
              name="isActive"
              checked={dashboardForm.isActive}
              onChange={handleInputChange}
              id="isActiveCheckbox"
            />
            <label htmlFor="isActiveCheckbox" className="form-label" style={{marginBottom: 0}}>
              Make this my primary dashboard
            </label>
          </div>
          <span className="form-help">
            Primary dashboards are displayed first and highlighted in the interface
          </span>
        </div>
      </div>
      
      <div className="card-footer">
        <button onClick={() => setShowAddForm(false)} className="btn-secondary">
          Cancel
        </button>
        <button 
          onClick={handleAddDashboard} 
          disabled={loading || !dashboardForm.dashboardName || !dashboardForm.dashboardUrl}
          className={`btn-primary ${loading ? 'btn-loading' : ''}`}
        >
          {loading ? 'Connecting...' : 'Connect Dashboard'}
        </button>
      </div>
    </div>
  )

  const DashboardViewer = ({ dashboard }) => {
    const [iframeLoading, setIframeLoading] = useState(true)
    const [iframeError, setIframeError] = useState(false)

    const handleIframeLoad = () => {
      setIframeLoading(false)
      setIframeError(false)
    }

    const handleIframeError = () => {
      setIframeLoading(false)
      setIframeError(true)
    }

    return (
      <div className="dashboard-viewer">
        <div className="viewer-header">
          <h3>{dashboard.dashboardName}</h3>
          <span className="dashboard-type">{dashboard.dashboardType}</span>
        </div>
        
        {iframeLoading && (
          <div className="iframe-loading">
            <p>Loading dashboard...</p>
          </div>
        )}
        
        {iframeError && (
          <div className="iframe-error">
            <p>Failed to load dashboard. Please check the URL and authentication settings.</p>
            <button onClick={() => window.open(dashboard.dashboardUrl, '_blank')}>
              Open in New Tab
            </button>
          </div>
        )}
        
        <iframe
          src={dashboard.dashboardUrl}
          width="100%"
          height="600"
          frameBorder="0"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          style={{ display: iframeError ? 'none' : 'block' }}
          sandbox="allow-scripts allow-same-origin allow-forms"
          title={dashboard.dashboardName}
        />
      </div>
    )
  }

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
    <div className="analytics-dashboard-layout">
      {/* Left Sidebar */}
      <div className="analytics-sidebar">
        <div className="sidebar-header">
          <h2 style={{margin: 0, fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--text-primary)'}}>
            Analytics Dashboards
          </h2>
        </div>
        
        <div className="sidebar-content">
          {dashboards.length > 0 && (
            <div className="dashboard-list">
              {dashboards.map((dashboard, index) => (
                <div
                  key={dashboard.id}
                  className={`dashboard-item ${activeDashboard?.id === dashboard.id ? 'active' : ''}`}
                  onClick={() => setActiveDashboard(dashboard)}
                >
                  <div className="dashboard-info">
                    <span className="dashboard-name">Dashboard {index + 1}</span>
                    <span className="dashboard-subtitle">{dashboard.dashboardName}</span>
                  </div>
                  <button
                    className="btn-icon btn-ghost btn-small delete-dashboard-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (confirm(`Are you sure you want to disconnect "${dashboard.dashboardName}"?`)) {
                        handleDeleteDashboard(dashboard.id)
                      }
                    }}
                    title="Disconnect dashboard"
                  >
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
              
              {dashboards.length < 10 && (
                <div className="dashboard-item-placeholder">
                  <span className="dashboard-name">Etc</span>
                </div>
              )}
            </div>
          )}
          
          <div className="sidebar-footer">
            <button 
              onClick={() => setShowAddForm(true)} 
              className="btn-secondary btn-full"
              style={{fontSize: 'var(--text-sm)'}}
            >
              Add new dashboard
            </button>
          </div>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="analytics-main">
        {/* Top Action Bar */}
        <div className="analytics-actions">
          <div className="actions-right">
            <button className="btn-primary btn-compact">
              Create report
            </button>
            <button 
              onClick={() => activeDashboard && window.open(activeDashboard.dashboardUrl, '_blank')}
              className="btn-secondary btn-compact"
              disabled={!activeDashboard}
            >
              Open Looker Studio
            </button>
            {activeDashboard && (
              <button 
                onClick={() => {
                  const dashboardElement = document.querySelector('.dashboard-viewer-main');
                  if (dashboardElement) {
                    if (document.fullscreenElement) {
                      document.exitFullscreen();
                    } else {
                      dashboardElement.requestFullscreen();
                    }
                  }
                }}
                className="btn-ghost btn-compact"
                title="Toggle fullscreen"
              >
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                Fullscreen
              </button>
            )}
          </div>
        </div>
        
        {/* Main Content */}
        <div className="main-content">
          {error && (
            <div className="alert alert-error">
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{success}</span>
            </div>
          )}

          {showAddForm && <DashboardConfigForm />}

          {dashboards.length === 0 && !showAddForm ? (
            <div className="empty-state-main">
              <div className="empty-icon">
                <svg width="64" height="64" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3>No Dashboards Connected</h3>
              <p>Connect your first analytics dashboard to start monitoring your business metrics and performance.</p>
            </div>
          ) : (
            !showAddForm && activeDashboard && (
              <div className="dashboard-viewer-main">
                <DashboardViewer dashboard={activeDashboard} />
              </div>
            )
          )}
        </div>
      </div>
    </div>
  )
}

export default AnalyticsDashboard