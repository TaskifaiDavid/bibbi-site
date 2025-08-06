const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiService {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token')
    
    const requestInfo = {
      endpoint,
      method: options.method || 'GET',
      hasToken: !!token,
      tokenLength: token ? token.length : 0,
      tokenPreview: token ? `***...${token.slice(-4)}` : 'none',
      url: `${API_URL}${endpoint}`,
      timestamp: new Date().toISOString()
    }
    
    console.log('🚀 API Request:', requestInfo)
    
    const config = {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': token ? `Bearer ${token}` : '',
      },
    }

    let response
    try {
      response = await fetch(`${API_URL}${endpoint}`, config)
      console.log('📡 API Response received:', {
        endpoint,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        url: response.url
      })
    } catch (fetchError) {
      console.error('🔥 Network/Fetch Error:', {
        endpoint,
        error: fetchError.message,
        type: fetchError.name,
        stack: fetchError.stack
      })
      throw new Error(`Network error: ${fetchError.message}`)
    }
    
    if (!response.ok) {
      console.error('API Error:', {
        status: response.status,
        statusText: response.statusText,
        endpoint
      })
      
      // Handle authentication errors specifically
      if (response.status === 401) {
        console.warn('Authentication failed - clearing token')
        localStorage.removeItem('access_token')
        // Redirect to login or trigger auth refresh
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      
      try {
        const error = await response.json()
        throw new Error(error.error || `Request failed with status ${response.status}`)
      } catch (parseError) {
        throw new Error(`Request failed with status ${response.status}`)
      }
    }

    return response.json()
  }

  async uploadFile(file) {
    const token = localStorage.getItem('access_token')
    console.log('Upload File:', {
      fileName: file.name,
      hasToken: !!token,
      tokenLength: token ? token.length : 0
    })
    
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_URL}/api/upload/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      console.error('Upload Error:', {
        status: response.status,
        statusText: response.statusText
      })
      
      if (response.status === 401) {
        console.warn('Upload authentication failed - clearing token')
        localStorage.removeItem('access_token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      
      try {
        const error = await response.json()
        throw new Error(error.error || 'Upload failed')
      } catch (parseError) {
        throw new Error(`Upload failed with status ${response.status}`)
      }
    }

    return response.json()
  }

  async uploadMultipleFiles(files) {
    const token = localStorage.getItem('access_token')
    console.log('Upload Multiple Files:', {
      fileCount: files.length,
      fileNames: files.map(f => f.name),
      hasToken: !!token
    })
    
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    const response = await fetch(`${API_URL}/api/upload/multiple`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      console.error('Multiple Upload Error:', {
        status: response.status,
        statusText: response.statusText
      })
      
      if (response.status === 401) {
        console.warn('Upload authentication failed - clearing token')
        localStorage.removeItem('access_token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      
      try {
        const error = await response.json()
        throw new Error(error.error || 'Multiple upload failed')
      } catch (parseError) {
        throw new Error(`Multiple upload failed with status ${response.status}`)
      }
    }

    return response.json()
  }

  async getStatus(uploadId) {
    return this.request(`/api/status/${uploadId}`)
  }

  async getUserUploads() {
    return this.request('/api/status/uploads')
  }

  // Email and Reporting methods
  async generateReport(reportRequest) {
    return this.request('/api/reports/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reportRequest),
    })
  }

  async sendReportEmail(emailRequest) {
    return this.request('/api/reports/email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(emailRequest),
    })
  }

  async sendNotificationEmail(emailRequest) {
    return this.request('/api/email/notification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(emailRequest),
    })
  }

  async getEmailLogs(limit = 50, offset = 0) {
    return this.request(`/api/email/logs?limit=${limit}&offset=${offset}`)
  }


  // Dashboard methods
  async getDashboardConfigs() {
    return this.request('/api/dashboards/configs')
  }

  async saveDashboardConfig(config) {
    return this.request('/api/dashboards/configs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    })
  }

  async updateDashboardConfig(configId, config) {
    return this.request(`/api/dashboards/configs/${configId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    })
  }

  async deleteDashboardConfig(configId) {
    console.log('🗑️ API SERVICE: Starting dashboard deletion request')
    console.log('🗑️ API SERVICE: Config ID:', configId)
    
    const result = await this.request(`/api/dashboards/configs/${configId}`, {
      method: 'DELETE',
    })
    
    console.log('🗑️ API SERVICE: Delete request response:', result)
    console.log('🗑️ API SERVICE: Delete success:', result?.success)
    console.log('🗑️ API SERVICE: Delete message:', result?.message)
    console.log('🗑️ API SERVICE: Deleted ID:', result?.deleted_id)
    
    return result
  }
}

const apiService = new ApiService()

// Export individual methods with proper this binding
export const uploadFile = apiService.uploadFile.bind(apiService)
export const uploadMultipleFiles = apiService.uploadMultipleFiles.bind(apiService)
export const getStatus = apiService.getStatus.bind(apiService)
export const getUserUploads = apiService.getUserUploads.bind(apiService)
export const generateReport = apiService.generateReport.bind(apiService)
export const sendReportEmail = apiService.sendReportEmail.bind(apiService)
export const sendNotificationEmail = apiService.sendNotificationEmail.bind(apiService)
export const getEmailLogs = apiService.getEmailLogs.bind(apiService)
export const getDashboardConfigs = apiService.getDashboardConfigs.bind(apiService)
export const saveDashboardConfig = apiService.saveDashboardConfig.bind(apiService)
export const updateDashboardConfig = apiService.updateDashboardConfig.bind(apiService)
export const deleteDashboardConfig = apiService.deleteDashboardConfig.bind(apiService)

export default apiService