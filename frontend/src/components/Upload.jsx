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
    <div className="upload-section">
      <div className="upload-header">
        <h2>Upload Data Files</h2>
        <p>Upload Excel files to process, clean, and analyze your data automatically</p>
      </div>
      
      <div className="upload-mode-selector">
        <h3>Select Upload Mode</h3>
        <div className="upload-mode-buttons">
          <button 
            className={`upload-mode-button ${uploadMode === 'single' ? 'active' : ''}`} 
            onClick={() => setUploadMode('single')}
          >
            <File size={24} />
            <div className="upload-mode-content">
              <h4>Single File Upload</h4>
              <p>Perfect for individual reports or one-off data processing</p>
            </div>
          </button>
          <button 
            className={`upload-mode-button ${uploadMode === 'multiple' ? 'active' : ''}`} 
            onClick={() => setUploadMode('multiple')}
          >
            <FileSpreadsheet size={24} />
            <div className="upload-mode-content">
              <h4>Multiple Files Upload</h4>
              <p>Batch process multiple files for efficiency and analysis</p>
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
        
        <label htmlFor="file-input" style={{ cursor: 'pointer', display: 'block', width: '100%' }}>
          {files.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-4)' }}>
              <CheckCircle size={48} style={{ color: 'var(--success-600)' }} />
              <div style={{ textAlign: 'center' }}>
                <h4 style={{ marginBottom: 'var(--space-2)', color: 'var(--success-700)' }}>
                  {files.length} FILE{files.length > 1 ? 'S' : ''} SELECTED
                </h4>
                <p>Ready to upload and process</p>
                {uploadMode === 'single' && (
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--neutral-500)', marginTop: 'var(--space-2)' }}>
                    Size: {(files[0].size / 1024 / 1024).toFixed(2)} MB
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-4)' }}>
              <UploadIcon className="upload-icon" />
              <div style={{ textAlign: 'center' }}>
                <h4 className="upload-text">
                  Drop your Excel file{uploadMode === 'multiple' ? 's' : ''} here
                </h4>
                <p className="upload-subtext">
                  or <span style={{ color: 'var(--primary-600)', fontWeight: 'var(--font-medium)' }}>click to browse</span>
                </p>
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--neutral-500)', marginTop: 'var(--space-2)' }}>
                  Supports: .xlsx files only
                </p>
              </div>
            </div>
          )}
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="card" style={{ marginTop: 'var(--space-8)' }}>
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h4>Selected Files</h4>
              <span className="badge badge-primary">{files.length} file{files.length > 1 ? 's' : ''}</span>
            </div>
          </div>
          <div className="card-body">
            <div className="grid gap-4">
              {files.map((file, index) => (
                <div key={index} className="card">
                  <div className="card-body">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileSpreadsheet size={20} style={{ color: 'var(--primary-600)' }} />
                        <div>
                          <div style={{ fontWeight: 'var(--font-medium)', marginBottom: 'var(--space-1)' }}>
                            {file.name}
                          </div>
                          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--neutral-500)' }}>
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </div>
                        </div>
                      </div>
                      {uploadMode === 'multiple' && (
                        <button 
                          className="btn btn-ghost btn-sm" 
                          onClick={() => removeFile(index)}
                          disabled={uploading}
                          title="Remove file"
                        >
                          <X size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginTop: 'var(--space-8)' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="card" style={{ marginTop: 'var(--space-8)' }}>
          <div className="card-header">
            <h4>Ready to Process</h4>
            <p style={{ margin: 0 }}>
              {files.length} file{files.length > 1 ? 's' : ''} selected • Click to start data processing
            </p>
          </div>
          <div className="card-footer">
            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className={`btn btn-primary btn-lg ${uploading ? 'loading' : ''}`}
              >
                {uploading ? (
                  <>
                    <div className="spinner" />
                    Processing Files...
                  </>
                ) : (
                  <>
                    <UploadIcon size={20} />
                    Start Processing
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {uploadResults.length > 0 && (
        <div className="card" style={{ marginTop: 'var(--space-8)' }}>
          <div className="card-header">
            <div className="flex items-center gap-4">
              <div style={{ 
                width: '3rem', 
                height: '3rem', 
                borderRadius: 'var(--radius-full)', 
                background: 'var(--success-100)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <CheckCircle size={24} style={{ color: 'var(--success-600)' }} />
              </div>
              <div>
                <h3 style={{ color: 'var(--success-700)', marginBottom: 'var(--space-2)' }}>
                  Files Successfully Uploaded
                </h3>
                <p style={{ margin: 0 }}>
                  {uploadResults.length} file{uploadResults.length > 1 ? 's' : ''} uploaded and queued for processing
                </p>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3">
              {uploadResults.map((result, index) => (
                <div key={index} className="card">
                  <div className="card-body">
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet size={20} style={{ color: 'var(--primary-600)' }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'var(--font-medium)', marginBottom: 'var(--space-1)' }}>
                          {result.filename}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="badge badge-success">{result.status}</span>
                          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--neutral-500)' }}>
                            ID: {result.id}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card-footer">
            <div className="flex items-center justify-between">
              <div>
                <h4 style={{ marginBottom: 'var(--space-2)' }}>What happens next?</h4>
                <p style={{ margin: 0, fontSize: 'var(--text-sm)', color: 'var(--neutral-600)' }}>
                  Your files are being processed automatically. Monitor progress in the <strong>Processing Status</strong> section.
                </p>
              </div>
              <button 
                onClick={() => window.location.hash = '#status'}
                className="btn btn-secondary"
              >
                <Activity size={16} />
                View Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Upload