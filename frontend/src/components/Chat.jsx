import React, { useState, useRef, useEffect } from 'react'

// Simple XSS protection utility
const sanitizeContent = (content) => {
  if (typeof content !== 'string') return ''
  
  // Remove any HTML tags and decode entities for safety
  const cleanContent = content
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
  
  // Limit content length to prevent display issues
  return cleanContent.length > 2000 ? cleanContent.substring(0, 2000) + '...' : cleanContent
}

const Chat = () => {
  const [isOpen, setIsOpen] = useState(false)
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

    // Sanitize user input before storing and sending
    const cleanedInput = sanitizeContent(inputMessage.trim())
    if (!cleanedInput) return

    const userMessage = { type: 'user', content: cleanedInput }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: cleanedInput })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const aiMessage = { type: 'ai', content: data.answer }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = { 
        type: 'ai', 
        content: 'Sorry, I encountered an error processing your question. Please try again.' 
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

  return (
    <div className="chat-widget">
      {/* Chat Toggle Button */}
      <button
        className={`chat-toggle ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Ask questions about your data"
      >
        💬
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <h3>Ask about your data</h3>
            <button onClick={() => setIsOpen(false)} className="close-btn">×</button>
          </div>
          
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>👋 Hi! I can help you analyze your sales data.</p>
                <p>Try asking:</p>
                <ul>
                  <li>"What were total sales in 2023?"</li>
                  <li>"Which reseller had the highest revenue?"</li>
                  <li>"Show monthly sales trends"</li>
                </ul>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.type}`}>
                <div className="message-content">
                  {sanitizeContent(message.content)}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message ai">
                <div className="message-content loading">
                  <span>Analyzing your data...</span>
                  <div className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your data..."
              disabled={isLoading}
              rows={2}
            />
            <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
              Send
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .chat-widget {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 1000;
        }

        .chat-toggle {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: #007bff;
          border: none;
          color: white;
          font-size: 24px;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          transition: all 0.3s ease;
        }

        .chat-toggle:hover {
          background: #0056b3;
          transform: scale(1.05);
        }

        .chat-window {
          position: absolute;
          bottom: 70px;
          right: 0;
          width: 400px;
          height: 500px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .chat-header {
          background: #007bff;
          color: white;
          padding: 15px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .chat-header h3 {
          margin: 0;
          font-size: 16px;
        }

        .close-btn {
          background: none;
          border: none;
          color: white;
          font-size: 20px;
          cursor: pointer;
          padding: 0;
          width: 24px;
          height: 24px;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 15px;
        }

        .welcome-message {
          color: #666;
          text-align: center;
        }

        .welcome-message ul {
          text-align: left;
          display: inline-block;
          margin: 10px 0;
        }

        .welcome-message li {
          margin: 5px 0;
          font-style: italic;
        }

        .message {
          margin-bottom: 15px;
        }

        .message.user .message-content {
          background: #007bff;
          color: white;
          margin-left: 50px;
          border-radius: 18px 18px 4px 18px;
        }

        .message.ai .message-content {
          background: #f1f1f1;
          color: #333;
          margin-right: 50px;
          border-radius: 18px 18px 18px 4px;
        }

        .message-content {
          padding: 12px 16px;
          word-wrap: break-word;
          white-space: pre-wrap;
        }

        .loading-dots {
          display: inline-block;
          margin-left: 5px;
        }

        .loading-dots span {
          animation: loading 1.4s infinite ease-in-out;
        }

        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes loading {
          0%, 80%, 100% { opacity: 0; }
          40% { opacity: 1; }
        }

        .chat-input {
          padding: 15px;
          border-top: 1px solid #eee;
          display: flex;
          gap: 10px;
        }

        .chat-input textarea {
          flex: 1;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 10px;
          resize: none;
          font-family: inherit;
          font-size: 14px;
        }

        .chat-input button {
          background: #007bff;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 10px 20px;
          cursor: pointer;
          font-size: 14px;
        }

        .chat-input button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .chat-input button:not(:disabled):hover {
          background: #0056b3;
        }

        @media (max-width: 480px) {
          .chat-window {
            width: calc(100vw - 40px);
            height: 400px;
            bottom: 80px;
            right: 20px;
          }
        }
      `}</style>
    </div>
  )
}

export default Chat