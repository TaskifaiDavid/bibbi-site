import React, { useState, useRef } from 'react'
import { Upload as UploadIcon, File, X, CheckCircle, AlertCircle, FileSpreadsheet } from 'lucide-react'
import api from '../services/api'

function Upload() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState([])
  const [error, setError] = useState(null)
  const [uploadMode, setUploadMode] = useState('single') // 'single' or 'multiple'
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files)
    
    if (uploadMode === 'single') {
      const selectedFile = selectedFiles[0]
      if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
        setFiles([selectedFile])
        setError(null)
      } else {
        setError('Please select a valid .xlsx file')
        setFiles([])
      }
    } else {
      // Multiple mode - validate all files
      const validFiles = selectedFiles.filter(file => file.name.endsWith('.xlsx'))
      const invalidFiles = selectedFiles.filter(file => !file.name.endsWith('.xlsx'))
      
      if (invalidFiles.length > 0) {
        setError(`${invalidFiles.length} file(s) skipped - only .xlsx files are allowed`)
      } else {
        setError(null)
      }
      
      setFiles(validFiles)
    }
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    
    if (uploadMode === 'single') {
      const droppedFile = droppedFiles[0]
      if (droppedFile && droppedFile.name.endsWith('.xlsx')) {
        setFiles([droppedFile])
        setError(null)
      } else {
        setError('Please drop a valid .xlsx file')
        setFiles([])
      }
    } else {
      // Multiple mode
      const validFiles = droppedFiles.filter(file => file.name.endsWith('.xlsx'))
      const invalidFiles = droppedFiles.filter(file => !file.name.endsWith('.xlsx'))
      
      if (invalidFiles.length > 0) {
        setError(`${invalidFiles.length} file(s) skipped - only .xlsx files are allowed`)
      } else {
        setError(null)
      }
      
      setFiles(validFiles)
    }
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setError(null)
    setUploadResults([])

    try {
      let results
      if (uploadMode === 'single') {
        results = [await api.uploadFile(files[0])]
      } else {
        results = await api.uploadMultipleFiles(files)
      }
      
      setUploadResults(results)
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  return (
    <div className="upload-container-modern">
      <div className="upload-header-modern">
        <div className="header-content">
          <h2 style={{margin: 0, fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--text-primary)'}}>
            Upload Data Files
          </h2>
          <p style={{margin: '8px 0 0 0', fontSize: 'var(--text-base)', color: 'var(--text-secondary)'}}>
            Upload Excel files to process, clean, and analyze your data automatically
          </p>
        </div>
      </div>
      
      {/* Upload Mode Toggle */}
      <div className="upload-mode-section">
        <div className="section-header">
          <h3 style={{margin: 0, fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--text-primary)'}}>
            Select Upload Mode
          </h3>
          <p style={{margin: '4px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)'}}>
            Choose whether to process one file or multiple files at once
          </p>
        </div>
        <div className="mode-toggle-modern">
          <button 
            className={`mode-option ${uploadMode === 'single' ? 'active' : ''}`} 
            onClick={() => setUploadMode('single')}
          >
            <div className="mode-icon">
              <File size={24} />
            </div>
            <div className="mode-content">
              <span className="mode-label">Single File Upload</span>
              <span className="mode-description">Perfect for individual reports or one-off data processing</span>
            </div>
            <div className="mode-indicator">
              {uploadMode === 'single' && (
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </button>
          <button 
            className={`mode-option ${uploadMode === 'multiple' ? 'active' : ''}`} 
            onClick={() => setUploadMode('multiple')}
          >
            <div className="mode-icon">
              <FileSpreadsheet size={24} />
            </div>
            <div className="mode-content">
              <span className="mode-label">Multiple Files Upload</span>
              <span className="mode-description">Batch process multiple files for efficiency and analysis</span>
            </div>
            <div className="mode-indicator">
              {uploadMode === 'multiple' && (
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </button>
        </div>
      </div>
      
      <div
        className={`upload-dropzone ${dragActive ? 'drag-active' : ''} ${files.length > 0 ? 'has-files' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          multiple={uploadMode === 'multiple'}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          id="file-input"
        />
        
        <label htmlFor="file-input" className="upload-label">
          {files.length > 0 ? (
            <div className="upload-success">
              <CheckCircle size={48} className="success-icon" />
              <div className="success-content">
                <h4>{files.length} file{files.length > 1 ? 's' : ''} selected</h4>
                <p>Ready to upload and process</p>
                {uploadMode === 'single' && (
                  <span className="file-info">Size: {(files[0].size / 1024 / 1024).toFixed(2)} MB</span>
                )}
              </div>
            </div>
          ) : (
            <div className="upload-prompt">
              <UploadIcon size={48} className="upload-icon" />
              <div className="prompt-content">
                <h4>Drop your Excel file{uploadMode === 'multiple' ? 's' : ''} here</h4>
                <p>or <span className="browse-link">click to browse</span></p>
                <div className="upload-info">
                  <span className="supported-format">Supports: .xlsx files only</span>
                </div>
              </div>
            </div>
          )}
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="selected-files">
          <div className="files-header">
            <h4>Selected Files</h4>
            <span className="files-count">{files.length} file{files.length > 1 ? 's' : ''}</span>
          </div>
          <div className="files-list">
            {files.map((file, index) => (
              <div key={index} className="file-card">
                <div className="file-info">
                  <FileSpreadsheet size={20} className="file-icon" />
                  <div className="file-details">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
                {uploadMode === 'multiple' && (
                  <button 
                    className="remove-file-btn" 
                    onClick={() => removeFile(index)}
                    disabled={uploading}
                    title="Remove file"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="upload-actions-modern">
          <div className="action-info">
            <h4 style={{margin: 0, fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--text-primary)'}}>
              Ready to Process
            </h4>
            <p style={{margin: '4px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)'}}>
              {files.length} file{files.length > 1 ? 's' : ''} selected • Click to start data processing
            </p>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`btn-success btn-large ${uploading ? 'btn-loading' : ''}`}
          >
            {uploading ? 'Processing Files...' : (
              <>
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                </svg>
                Start Processing
              </>
            )}
          </button>
        </div>
      )}

      {uploadResults.length > 0 && (
        <div className="upload-results-modern">
          <div className="results-header-modern">
            <div className="success-icon-modern">
              <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="results-content">
              <h3 style={{margin: 0, fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--success-700)'}}>
                Files Successfully Uploaded
              </h3>
              <p style={{margin: '4px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)'}}>
                {uploadResults.length} file{uploadResults.length > 1 ? 's' : ''} uploaded and queued for processing
              </p>
            </div>
          </div>
          <div className="results-grid">
            {uploadResults.map((result, index) => (
              <div key={index} className="result-card-modern">
                <div className="result-icon">
                  <FileSpreadsheet size={20} />
                </div>
                <div className="result-details-modern">
                  <div className="result-filename">{result.filename}</div>
                  <div className="result-meta">
                    <span className="status-badge success">{result.status}</span>
                    <span className="result-id">ID: {result.id}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="results-footer-modern">
            <div className="next-steps">
              <h4 style={{margin: 0, fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--text-primary)'}}>
                What happens next?
              </h4>
              <p style={{margin: '4px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)'}}>
                Your files are now being processed automatically. Monitor progress in the <strong>Processing Status</strong> section.
              </p>
            </div>
            <button 
              onClick={() => window.location.hash = '#status'}
              className="btn-primary"
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              View Processing Status
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Upload