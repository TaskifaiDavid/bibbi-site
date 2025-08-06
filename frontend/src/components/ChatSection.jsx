import React, { useState, useRef, useEffect } from 'react'
import { MessageSquare, Send, Copy, Trash2, User, Bot, Lightbulb, Sparkles } from 'lucide-react'

const ChatSection = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const currentMessage = inputMessage.trim() // Store current message
    const userMessage = { type: 'user', content: currentMessage, timestamp: new Date() }
    
    // Update state immediately
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      console.log('Chat request - Token check:', { 
        hasToken: !!token,
        tokenLength: token ? token.length : 0 
      })

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({ message: currentMessage })
      })

      if (!response.ok) {
        if (response.status === 401) {
          // Clear invalid token and prompt re-login
          localStorage.removeItem('access_token')
          throw new Error('Your session has expired. Please refresh the page and login again.')
        }
        
        // Try to get error details from response
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            errorMessage = errorData.detail
          }
        } catch (e) {
          // Keep default error message if can't parse JSON
        }
        
        throw new Error(errorMessage)
      }

      const data = await response.json()
      console.log('🤖 Chat API Response:', data) // Debug the full response structure
      
      // Show full response including any breakdown or detailed analysis
      let fullContent = data.answer || data.response || ''
      
      // If there are additional details in the response, include them
      if (data.analysis) {
        fullContent += '\n\n--- Analysis ---\n' + data.analysis
      }
      if (data.breakdown) {
        fullContent += '\n\n--- Breakdown ---\n' + data.breakdown
      }
      if (data.reasoning) {
        fullContent += '\n\n--- Reasoning ---\n' + data.reasoning
      }
      if (data.details) {
        fullContent += '\n\n--- Details ---\n' + data.details
      }
      if (data.sql_query) {
        fullContent += '\n\n--- SQL Query ---\n' + data.sql_query
      }
      if (data.query_explanation) {
        fullContent += '\n\n--- Query Explanation ---\n' + data.query_explanation
      }
      if (data.data_insights) {
        fullContent += '\n\n--- Data Insights ---\n' + data.data_insights
      }
      
      // If we still only have the basic answer, try to show all available fields
      if (fullContent === (data.answer || data.response || '')) {
        const additionalFields = Object.keys(data).filter(key => 
          key !== 'answer' && key !== 'response' && key !== 'status' && 
          typeof data[key] === 'string' && data[key].length > 0
        )
        
        for (const field of additionalFields) {
          fullContent += `\n\n--- ${field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ')} ---\n` + data[field]
        }
      }
      
      const aiMessage = { type: 'ai', content: fullContent, timestamp: new Date() }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = { 
        type: 'ai', 
        content: `Error: ${error.message || 'Unable to process your question. Please try again.'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
  }

  const sampleQuestions = [
    "What were our total sales in 2024?",
    "Which reseller has the highest revenue?",
    "Show me monthly sales trends",
    "What are our top-selling products?",
    "Compare Q1 vs Q2 performance",
    "Which months had the best sales?"
  ]

  return (
    <div className="chat-section">
      <div className="chat-header">
        <div className="header-content">
          <div className="header-title">
            <MessageSquare size={24} className="header-icon" />
            <div>
              <h2>Data Chat</h2>
              <p>Ask questions about your sales data and get AI-powered insights</p>
            </div>
          </div>
        </div>
        <div className="chat-actions">
          <button 
            onClick={clearChat} 
            className="clear-btn" 
            disabled={messages.length === 0}
            title="Clear conversation"
          >
            <Trash2 size={16} />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages" style={{height: '100%', overflowY: 'auto', maxHeight: 'calc(100vh - 300px)'}}>
          {messages.length === 0 && (
            <div className="welcome-section">
              <div className="welcome-message">
                <div className="welcome-header">
                  <Sparkles size={32} className="welcome-icon" />
                  <div>
                    <h3>Welcome!</h3>
                    <p>I can help you analyze your sales data and provide insights</p>
                  </div>
                </div>
              </div>
              
              <div className="sample-questions">
                <div className="questions-header">
                  <Lightbulb size={20} />
                  <h4>Try asking:</h4>
                </div>
                <div className="question-grid">
                  {sampleQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="sample-question"
                      onClick={() => setInputMessage(question)}
                    >
                      <span className="question-text">{question}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? (
                  <User size={20} />
                ) : (
                  <Bot size={20} />
                )}
              </div>
              <div className="message-body">
                <div className="message-header">
                  <span className="message-sender">
                    {message.type === 'user' ? 'You' : 'AI Assistant'}
                  </span>
                  <span className="message-time">
                    {message.timestamp?.toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.content.split('\n').map((line, index) => (
                      <div key={index} className="message-line">
                        {line.startsWith('---') ? (
                          <div className="section-divider">
                            <span className="section-title">{line.replace(/---/g, '').trim()}</span>
                          </div>
                        ) : line.trim() ? (
                          <p>{line}</p>
                        ) : (
                          <br />
                        )}
                      </div>
                    ))}
                  </div>
                  {message.type === 'ai' && !isLoading && (
                    <button 
                      className="copy-btn"
                      onClick={() => copyMessage(message.content)}
                      title="Copy response"
                    >
                      <Copy size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="analyzing-container">
              <div className="analyzing-indicator">
                <div className="analyzing-text">
                  <span className="analyzing-message">Analyzing your request...</span>
                  <div className="analyzing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-section">
          <div className="input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your sales data..."
              disabled={isLoading}
              rows={1}
              className="chat-input"
            />
            <button 
              onClick={sendMessage} 
              disabled={isLoading || !inputMessage.trim()}
              className="send-btn"
              title="Send message"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="input-hint">
            <span>Press Enter to send • Shift+Enter for new line</span>
          </div>
        </div>
      </div>

    </div>
  )
}

export default ChatSection