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
                  <th className="col-file">
                    <div className="th-content">
                      <span>File Information</span>
                    </div>
                  </th>
                  <th className="col-status">
                    <div className="th-content">
                      <span>Status</span>
                    </div>
                  </th>
                  <th className="col-date">
                    <div className="th-content">
                      <span>Upload Time</span>
                    </div>
                  </th>
                  <th className="col-metrics">
                    <div className="th-content">
                      <span>Processing Metrics</span>
                    </div>
                  </th>
                  <th className="col-actions">
                    <div className="th-content">
                      <span>Actions</span>
                    </div>
                  </th>
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
                            <FileSpreadsheet size={20} className="file-icon-table" />
                            <div className="file-details-table">
                              <div className="filename-table">{upload.filename}</div>
                              <div className="file-meta">
                                <span className="file-id">ID: {upload.id}</span>
                                <span className="upload-date">{formatDate(upload.uploaded_at)}</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="status-cell">
                          <div className={`status-badge-modern ${statusInfo.color}`}>
                            <StatusIcon size={16} />
                            <span>{statusInfo.label}</span>
                          </div>
                        </td>
                        <td className="date-cell mobile-hidden">
                          <div className="date-display">
                            {formatDate(upload.uploaded_at)}
                          </div>
                        </td>
                        <td className="metrics-cell">
                          <div className="metrics-grid">
                            <div className="metric-item">
                              <span className="metric-label">Processed</span>
                              <span className="metric-value">
                                {upload.rows_processed ? upload.rows_processed.toLocaleString() : '-'}
                              </span>
                            </div>
                            <div className="metric-item">
                              <span className="metric-label">Cleaned</span>
                              <span className="metric-value">
                                {upload.rows_cleaned ? upload.rows_cleaned.toLocaleString() : '-'}
                              </span>
                            </div>
                            <div className="metric-item">
                              <span className="metric-label">Duration</span>
                              <span className="metric-value">
                                {upload.processing_time_ms ? formatDuration(upload.processing_time_ms) : '-'}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="actions-cell">
                          <div className="table-actions">
                            {(upload.rows_processed || upload.rows_cleaned || upload.processing_time_ms || (upload.status === 'failed' && upload.error_message)) && (
                              <button 
                                className="btn-ghost btn-small"
                                onClick={() => toggleRowExpansion(upload.id)}
                                title={isExpanded ? 'Hide Details' : 'Show Details'}
                              >
                                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                              </button>
                            )}
                            
                            {upload.status === 'completed' && (
                              <button className="btn-primary btn-small" title="Download Results">
                                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0l-4 4m4-4v12" />
                                </svg>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="details-row">
                          <td colSpan="5" className="details-cell">
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
      
      <style jsx>{`
        .status-table-container {
          background: white;
          border-radius: 16px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          border: 1px solid #e5e7eb;
        }

        .table-wrapper {
          overflow-x: auto;
        }

        .status-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        .status-table thead {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        .status-table th {
          padding: 20px 24px;
          text-align: left;
          font-weight: 600;
          color: #374151;
          border-bottom: 2px solid #e5e7eb;
          position: sticky;
          top: 0;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          z-index: 10;
        }

        .th-content {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .col-file {
          width: 35%;
          min-width: 280px;
        }

        .col-status {
          width: 15%;
          min-width: 120px;
        }

        .col-date {
          width: 20%;
          min-width: 180px;
        }

        .col-metrics {
          width: 25%;
          min-width: 250px;
        }

        .col-actions {
          width: 10%;
          min-width: 100px;
          text-align: center;
        }

        .status-row {
          background: white;
          transition: all 0.2s ease;
        }

        .status-row:hover {
          background: #f9fafb;
        }

        .status-row.expanded {
          background: #fef3c7;
        }

        .status-table td {
          padding: 20px 24px;
          border-bottom: 1px solid #f3f4f6;
          vertical-align: middle;
        }

        .file-info-table {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .file-icon-table {
          color: #6b7280;
          flex-shrink: 0;
        }

        .file-details-table {
          display: flex;
          flex-direction: column;
          gap: 4px;
          min-width: 0;
        }

        .filename-table {
          font-weight: 600;
          color: #111827;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 200px;
        }

        .file-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .file-id {
          font-size: 12px;
          color: #6b7280;
          font-family: monospace;
        }

        .upload-date {
          font-size: 12px;
          color: #9ca3af;
        }

        .status-badge-modern {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 500;
          white-space: nowrap;
        }

        .status-badge-modern.status-success {
          background: #d1fae5;
          color: #065f46;
          border: 1px solid #a7f3d0;
        }

        .status-badge-modern.status-error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
        }

        .status-badge-modern.status-processing {
          background: #dbeafe;
          color: #1e40af;
          border: 1px solid #93c5fd;
        }

        .status-badge-modern.status-pending {
          background: #fef3c7;
          color: #92400e;
          border: 1px solid #fcd34d;
        }

        .date-display {
          font-size: 13px;
          color: #6b7280;
          font-variant-numeric: tabular-nums;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 16px;
        }

        .metric-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
          text-align: center;
        }

        .metric-label {
          font-size: 11px;
          font-weight: 500;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .metric-value {
          font-size: 14px;
          font-weight: 600;
          color: #111827;
          font-variant-numeric: tabular-nums;
        }

        .table-actions {
          display: flex;
          gap: 8px;
          justify-content: center;
        }

        .btn-small {
          padding: 8px;
          border-radius: 8px;
          border: none;
          cursor: pointer;
          transition: all 0.2s ease;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }

        .btn-ghost {
          background: transparent;
          color: #6b7280;
          border: 1px solid #e5e7eb;
        }

        .btn-ghost:hover {
          background: #f3f4f6;
          color: #374151;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
          border: 1px solid #3b82f6;
        }

        .btn-primary:hover {
          background: #2563eb;
          border-color: #2563eb;
        }

        .details-row {
          background: #fffbeb;
        }

        .details-cell {
          padding: 24px;
        }

        .expanded-details-table {
          background: white;
          border-radius: 12px;
          padding: 20px;
          border: 1px solid #f59e0b;
        }

        .error-section-table {
          margin-bottom: 16px;
        }

        .error-header-table {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #dc2626;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .error-message-table {
          color: #991b1b;
          background: #fee2e2;
          padding: 12px;
          border-radius: 8px;
          border-left: 4px solid #dc2626;
          margin: 0;
        }

        .details-grid-table {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .detail-item-table {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f3f4f6;
        }

        .detail-label-table {
          font-weight: 500;
          color: #6b7280;
        }

        .detail-value-table {
          font-weight: 600;
          color: #111827;
          font-variant-numeric: tabular-nums;
        }

        /* Responsive Design */
        @media (max-width: 1024px) {
          .metrics-grid {
            grid-template-columns: 1fr 1fr;
          }
          
          .col-date {
            display: none;
          }
          
          .mobile-hidden {
            display: none;
          }
        }

        @media (max-width: 768px) {
          .status-table th,
          .status-table td {
            padding: 16px 12px;
          }

          .metrics-grid {
            grid-template-columns: 1fr;
            gap: 8px;
          }

          .metric-item {
            flex-direction: row;
            justify-content: space-between;
            text-align: left;
          }

          .filename-table {
            max-width: 150px;
          }

          .col-file {
            width: 40%;
            min-width: 200px;
          }

          .col-metrics {
            width: 35%;
            min-width: 180px;
          }
        }
      `}</style>
    </div>
  )
}

export default StatusList