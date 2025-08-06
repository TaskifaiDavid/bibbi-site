import React, { useState, useEffect } from 'react'
import { CheckCircle, Clock, AlertTriangle, XCircle, FileSpreadsheet, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'
import api from '../services/api'

function StatusList() {
  const [uploads, setUploads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedRows, setExpandedRows] = useState(new Set())

  useEffect(() => {
    fetchUploads()
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchUploads, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchUploads = async () => {
    try {
      console.log('📥 Fetching user uploads...')
      const token = localStorage.getItem('access_token')
      
      if (!token) {
        console.log('❌ No token found')
        setLoading(false)
        return
      }

      const uploadsData = await api.getUserUploads()
      console.log('✅ Uploads fetched:', uploadsData)
      setUploads(uploadsData || [])
      setError(null)
    } catch (error) {
      console.error('❌ Error fetching uploads:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading processing status...</div>
  }

  const getStatusInfo = (status) => {
    switch (status) {
      case 'completed':
        return {
          color: 'status-success',
          icon: CheckCircle,
          label: 'Completed',
          bgClass: 'status-success-bg'
        }
      case 'failed':
        return {
          color: 'status-error',
          icon: XCircle,
          label: 'Failed',
          bgClass: 'status-error-bg'
        }
      case 'processing':
        return {
          color: 'status-processing',
          icon: Clock,
          label: 'Processing',
          bgClass: 'status-processing-bg'
        }
      default:
        return {
          color: 'status-pending',
          icon: AlertTriangle,
          label: 'Pending',
          bgClass: 'status-pending-bg'
        }
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const formatDuration = (ms) => {
    if (!ms) return 'N/A'
    return `${(ms / 1000).toFixed(2)}s`
  }

  const toggleRowExpansion = (uploadId) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(uploadId)) {
      newExpanded.delete(uploadId)
    } else {
      newExpanded.add(uploadId)
    }
    setExpandedRows(newExpanded)
  }

  return (
    <div className="status-list-modern">
      <div className="status-header-modern">
        <div className="header-content">
          <h2 style={{margin: 0, fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--text-primary)'}}>
            Processing Status
          </h2>
          <p style={{margin: '8px 0 0 0', fontSize: 'var(--text-base)', color: 'var(--text-secondary)'}}>
            Real-time monitoring of your data processing pipeline
          </p>
        </div>
        <button onClick={fetchUploads} className={`btn-secondary ${loading ? 'btn-loading' : ''}`} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spinning' : ''} />
          <span style={{ color: 'var(--blue-600)' }}>Refresh Status</span>
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Error loading uploads: {error}</span>
        </div>
      )}
      
      {uploads.length === 0 ? (
        <div className="empty-state-modern">
          <div className="empty-icon">
            <svg width="64" height="64" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3>No Files Processing</h3>
          <p>Upload your first Excel file to see real-time processing status and detailed analytics here</p>
          <button onClick={() => window.location.hash = '#upload'} className="btn-primary">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
            Upload Files
          </button>
        </div>
      ) : (
        <div className="status-table-container">
          <div className="table-wrapper">
            <table className="status-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                  <th>Rows Processed</th>
                  <th>Rows Cleaned</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((upload) => {
                  const statusInfo = getStatusInfo(upload.status)
                  const StatusIcon = statusInfo.icon
                  const isExpanded = expandedRows.has(upload.id)
                  
                  return (
                    <React.Fragment key={upload.id}>
                      <tr className={`status-row ${isExpanded ? 'expanded' : ''}`}>
                        <td className="file-cell">
                          <div className="file-info-table">
                            <FileSpreadsheet size={18} className="file-icon-table" />
                            <div className="file-details-table">
                              <span className="filename-table">{upload.filename}</span>
                              <span className="file-id">ID: {upload.id}</span>
                            </div>
                          </div>
                        </td>
                        <td className="status-cell">
                          <div className={`status-badge-table ${statusInfo.color}`}>
                            <StatusIcon size={14} />
                            <span>{statusInfo.label}</span>
                          </div>
                        </td>
                        <td className="date-cell">
                          {formatDate(upload.uploaded_at)}
                        </td>
                        <td className="number-cell">
                          {upload.rows_processed ? upload.rows_processed.toLocaleString() : '-'}
                        </td>
                        <td className="number-cell">
                          {upload.rows_cleaned ? upload.rows_cleaned.toLocaleString() : '-'}
                        </td>
                        <td className="duration-cell">
                          {upload.processing_time_ms ? formatDuration(upload.processing_time_ms) : '-'}
                        </td>
                        <td className="actions-cell">
                          <div className="table-actions">
                            {(upload.rows_processed || upload.rows_cleaned || upload.processing_time_ms || (upload.status === 'failed' && upload.error_message)) && (
                              <button 
                                className="btn-ghost btn-small"
                                onClick={() => toggleRowExpansion(upload.id)}
                                title={isExpanded ? 'Hide Details' : 'Show Details'}
                              >
                                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                              </button>
                            )}
                            
                            {upload.status === 'completed' && (
                              <button className="btn-primary btn-small" title="Download Results">
                                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0l-4 4m4-4v12" />
                                </svg>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="details-row">
                          <td colSpan="7" className="details-cell">
                            <div className="expanded-details-table">
                              {upload.status === 'failed' && upload.error_message && (
                                <div className="error-section-table">
                                  <div className="error-header-table">
                                    <AlertTriangle size={16} />
                                    <span>Error Details</span>
                                  </div>
                                  <p className="error-message-table">{upload.error_message}</p>
                                </div>
                              )}
                              
                              <div className="details-grid-table">
                                {upload.rows_processed && (
                                  <div className="detail-item-table">
                                    <span className="detail-label-table">Total Rows Processed:</span>
                                    <span className="detail-value-table">{upload.rows_processed.toLocaleString()}</span>
                                  </div>
                                )}
                                {upload.rows_cleaned && (
                                  <div className="detail-item-table">
                                    <span className="detail-label-table">Data Cleaned:</span>
                                    <span className="detail-value-table">{upload.rows_cleaned.toLocaleString()} rows</span>
                                  </div>
                                )}
                                {upload.processing_time_ms && (
                                  <div className="detail-item-table">
                                    <span className="detail-label-table">Processing Time:</span>
                                    <span className="detail-value-table">{formatDuration(upload.processing_time_ms)}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default StatusList