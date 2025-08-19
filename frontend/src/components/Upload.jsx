import React, { useState, useRef } from 'react'
import { Upload as UploadIcon, File, X, CheckCircle, AlertCircle, FileSpreadsheet, Activity } from 'lucide-react'
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
    <div className="upload-container">
      <div className="upload-header">
        <div className="header-content">
          <h2 className="text-heading">
            UPLOAD DATA FILES
          </h2>
          <p className="text-body">
            Upload Excel files to process, clean, and analyze your data automatically
          </p>
        </div>
      </div>
      
      <div className="upload-mode-selector">
        <div className="selector-header">
          <h3 className="text-subheading">
            SELECT UPLOAD MODE
          </h3>
          <p className="text-body">
            Choose whether to process one file or multiple files at once
          </p>
        </div>
        <div className="mode-toggle-group">
          <button 
            className={`mode-toggle ${uploadMode === 'single' ? 'active' : ''}`} 
            onClick={() => setUploadMode('single')}
          >
            <File size={20} />
            <div className="toggle-content">
              <span className="toggle-label text-uppercase">Single File Upload</span>
              <span className="toggle-desc">Perfect for individual reports or one-off data processing</span>
            </div>
          </button>
          <button 
            className={`mode-toggle ${uploadMode === 'multiple' ? 'active' : ''}`} 
            onClick={() => setUploadMode('multiple')}
          >
            <FileSpreadsheet size={20} />
            <div className="toggle-content">
              <span className="toggle-label text-uppercase">Multiple Files Upload</span>
              <span className="toggle-desc">Batch process multiple files for efficiency and analysis</span>
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
                <h4 className="text-subheading">{files.length} FILE{files.length > 1 ? 'S' : ''} SELECTED</h4>
                <p className="text-body">Ready to upload and process</p>
                {uploadMode === 'single' && (
                  <span className="file-info text-small-caps">Size: {(files[0].size / 1024 / 1024).toFixed(2)} MB</span>
                )}
              </div>
            </div>
          ) : (
            <div className="upload-prompt">
              <UploadIcon size={48} className="upload-icon" />
              <div className="prompt-content">
                <h4 className="text-subheading">DROP YOUR EXCEL FILE{uploadMode === 'multiple' ? 'S' : ''} HERE</h4>
                <p className="text-body">or <span className="browse-link">click to browse</span></p>
                <div className="upload-info">
                  <span className="supported-format text-small-caps">Supports: .xlsx files only</span>
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
            <h4 className="text-subheading">SELECTED FILES</h4>
            <span className="files-count text-small-caps">{files.length} file{files.length > 1 ? 's' : ''}</span>
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
        <div className="upload-actions">
          <div className="action-info">
            <h4 className="text-subheading">
              READY TO PROCESS
            </h4>
            <p className="text-body">
              {files.length} file{files.length > 1 ? 's' : ''} selected • Click to start data processing
            </p>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`btn-primary btn-large text-uppercase ${uploading ? 'btn-loading' : ''}`}
          >
            {uploading ? 'Processing Files...' : (
              <>
                <UploadIcon size={20} />
                Start Processing
              </>
            )}
          </button>
        </div>
      )}

      {uploadResults.length > 0 && (
        <div className="upload-results">
          <div className="results-header">
            <div className="success-icon">
              <CheckCircle size={32} />
            </div>
            <div className="results-content">
              <h3 className="text-heading" style={{color: 'var(--success-600)'}}>
                FILES SUCCESSFULLY UPLOADED
              </h3>
              <p className="text-body">
                {uploadResults.length} file{uploadResults.length > 1 ? 's' : ''} uploaded and queued for processing
              </p>
            </div>
          </div>
          <div className="results-grid">
            {uploadResults.map((result, index) => (
              <div key={index} className="result-card">
                <div className="result-icon">
                  <FileSpreadsheet size={20} />
                </div>
                <div className="result-details">
                  <div className="result-filename text-body">{result.filename}</div>
                  <div className="result-meta">
                    <span className="status-badge success text-small-caps">{result.status}</span>
                    <span className="result-id text-small-caps">ID: {result.id}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="results-footer">
            <div className="next-steps">
              <h4 className="text-subheading">
                WHAT HAPPENS NEXT?
              </h4>
              <p className="text-body">
                Your files are now being processed automatically. Monitor progress in the <strong>Processing Status</strong> section.
              </p>
            </div>
            <button 
              onClick={() => window.location.hash = '#status'}
              className="btn-secondary text-uppercase"
            >
              <Activity size={16} />
              View Processing Status
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Upload