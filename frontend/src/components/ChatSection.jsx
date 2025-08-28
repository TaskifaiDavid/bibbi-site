import React, { useState, useRef, useEffect } from 'react'
import { Send, Copy, User, Bot, Plus } from 'lucide-react'

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

    const currentMessage = inputMessage.trim()
    const userMessage = { type: 'user', content: currentMessage, timestamp: new Date() }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    
    // Reset textarea height after sending
    setTimeout(() => {
      const textarea = document.querySelector('.chatgpt-input-field')
      if (textarea) {
        textarea.style.height = 'auto'
        textarea.style.height = '52px' // Reset to minimum height
      }
    }, 0)

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
          localStorage.removeItem('access_token')
          throw new Error('Your session has expired. Please refresh the page and login again.')
        }
        
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
      console.log('🤖 Chat API Response:', data)
      
      let fullContent = data.answer || data.response || ''
      
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

  const handleInputChange = (e) => {
    setInputMessage(e.target.value)
    
    // Auto-resize textarea to fit content (ChatGPT style)
    const textarea = e.target
    textarea.style.height = 'auto'
    
    // Calculate new height with proper bounds
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 52), 200)
    textarea.style.height = newHeight + 'px'
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
  }

  const welcomePrompts = [
    "What were our total sales in 2024?",
    "Which reseller has the highest revenue?",
    "Show me monthly sales trends",
    "What are our top-selling products?"
  ]

  return (
    <div className="chatgpt-container">
      {/* Main Chat Area */}
      <div className="chat-conversation">
        {messages.length === 0 ? (
          <div className="chat-welcome-simple">
            <div className="welcome-content">
              <h2>Ask about your sales data</h2>
              <div className="welcome-prompts">
                {welcomePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    className="welcome-prompt"
                    onClick={() => setInputMessage(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-container">
            {messages.map((message, index) => (
              <div key={index} className={`message-group ${message.type}`}>
                <div className="message-avatar">
                  <div className="avatar-circle">
                    {message.type === 'user' ? (
                      <User size={20} />
                    ) : (
                      <Bot size={20} />
                    )}
                  </div>
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.content.split('\n').map((line, lineIndex) => (
                      <div key={lineIndex}>
                        {line.startsWith('---') ? (
                          <div className="section-divider">
                            <strong>{line.replace(/---/g, '').trim()}</strong>
                          </div>
                        ) : line.trim() ? (
                          <p>{line}</p>
                        ) : (
                          <br />
                        )}
                      </div>
                    ))}
                  </div>
                  {message.type === 'ai' && (
                    <div className="message-actions">
                      <button 
                        className="copy-btn"
                        onClick={() => copyMessage(message.content)}
                        title="Copy"
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {isLoading && (
          <div className="message-group ai">
            <div className="message-avatar">
              <div className="avatar-circle">
                <Bot size={20} />
              </div>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <div className="typing-dots">
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

      {/* ChatGPT-Style Fixed Bottom Input */}
      <div className="chatgpt-input-container">
        <div className="chatgpt-input-wrapper">
          <div className="chatgpt-input-field-container">
            {/* Plus Icon (Attachment/Options) */}
            <button 
              className="chatgpt-plus-icon" 
              type="button"
              title="Attach files"
              aria-label="Attach files or add options"
            >
              <Plus size={20} />
            </button>
            
            {/* Auto-resizing Textarea */}
            <textarea
              value={inputMessage}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              placeholder="Ask anything"
              disabled={isLoading}
              className="chatgpt-input-field"
              rows={1}
              aria-label="Message input"
              aria-describedby="input-help"
              style={{
                height: 'auto',
                minHeight: '52px',
                maxHeight: '200px'
              }}
            />
            
            {/* Send Button */}
            <button 
              onClick={sendMessage} 
              disabled={isLoading || !inputMessage.trim()}
              className="chatgpt-send-button"
              type="button"
              title={inputMessage.trim() ? "Send message" : "Enter a message to send"}
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </div>
          
          {/* Hidden helper text for screen readers */}
          <div id="input-help" className="sr-only">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatSection