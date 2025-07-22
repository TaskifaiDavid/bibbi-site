import React, { useState, useRef, useEffect } from 'react'

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
      const aiMessage = { type: 'ai', content: data.answer, timestamp: new Date() }
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
          <h2>💬 Data Chat</h2>
          <p>Ask questions about your sales data and get AI-powered insights</p>
        </div>
        <div className="chat-actions">
          <button onClick={clearChat} className="btn-secondary" disabled={messages.length === 0}>
            Clear Chat
          </button>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-section">
              <div className="welcome-message">
                <h3>👋 Welcome to Data Chat!</h3>
                <p>I can help you analyze your sales data. Here are some questions you can ask:</p>
              </div>
              
              <div className="sample-questions">
                <h4>Sample Questions:</h4>
                <div className="question-grid">
                  {sampleQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="sample-question"
                      onClick={() => setInputMessage(question)}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-header">
                <span className="message-sender">
                  {message.type === 'user' ? '👤 You' : '🤖 AI Assistant'}
                </span>
                <span className="message-time">
                  {message.timestamp?.toLocaleTimeString()}
                </span>
              </div>
              <div className="message-content">
                <pre>{message.content}</pre>
                {message.type === 'ai' && (
                  <button 
                    className="copy-btn"
                    onClick={() => copyMessage(message.content)}
                    title="Copy response"
                  >
                    📋
                  </button>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message ai">
              <div className="message-header">
                <span className="message-sender">🤖 AI Assistant</span>
                <span className="message-time">Thinking...</span>
              </div>
              <div className="message-content loading">
                <div className="loading-animation">
                  <span>Thinking</span>
                  <div className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
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
              placeholder="Ask a question about your sales data... (Press Enter to send, Shift+Enter for new line)"
              disabled={isLoading}
              rows={3}
              className="chat-input"
            />
            <button 
              onClick={sendMessage} 
              disabled={isLoading || !inputMessage.trim()}
              className="send-btn"
            >
              {isLoading ? '⏳' : '📤'} Send
            </button>
          </div>
        </div>
      </div>

    </div>
  )
}

export default ChatSection