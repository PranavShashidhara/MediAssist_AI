import React, { useState, useEffect, useRef } from "react";
import { Send, Mic, Paperclip, X, FileText, Zap, Bot, User, Sparkles, Wifi, WifiOff, AlertCircle } from "lucide-react";
import './AppStyles.css';

export default function App() {
  const [history, setHistory] = useState([]);
  const [inputText, setInputText] = useState("");
  const [thinking, setThinking] = useState(false);
  const [recording, setRecording] = useState(false);
  const [useLocalLLM, setUseLocalLLM] = useState(false);
  const [internetStatus, setInternetStatus] = useState('checking');
  const [serverStatus, setServerStatus] = useState('unknown');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const audioChunksRef = useRef([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [currentTypingText, setCurrentTypingText] = useState("");
  const [sessionId, setSessionId] = useState(null);

  // Add custom scrollbar styles and remove outer scrollbar
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      body {
        overflow: hidden;
        margin: 0;
        padding: 0;
      }
      .chat-area::-webkit-scrollbar {
        width: 6px;
      }
      .chat-area::-webkit-scrollbar-track {
        background: transparent;
      }
      .chat-area::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
      }
      .chat-area::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
      }
      @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
      }
      @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .message-enter {
        animation: slideIn 0.3s ease-out;
      }
      .thinking-dots {
        animation: pulse 1.5s infinite;
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      .loading-spinner {
        animation: spin 1s linear infinite;
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  // Check internet connectivity and create session on startup
  useEffect(() => {
    checkInternetConnectivity();
    checkServerConnection();
    createNewSession();
    
    // Check internet connectivity every 30 seconds
    const internetInterval = setInterval(() => {
      checkInternetConnectivity();
    }, 30000);

    // Check server connection every 15 seconds (for status display)
    const serverInterval = setInterval(() => {
      checkServerConnection();
    }, 15000);

    return () => {
      clearInterval(internetInterval);
      clearInterval(serverInterval);
    };
  }, []);

  // Auto-switch to local LLM when internet is lost
  useEffect(() => {
    if (internetStatus === 'disconnected' || internetStatus === 'error') {
      if (!useLocalLLM) {
        setUseLocalLLM(true);
        // Add a message to history about the switch
        setHistory(prev => [...prev, {
          sender: "system",
          message: "🔄 Internet connection lost. Automatically switched to Local LLM mode.",
          timestamp: new Date().toLocaleTimeString(),
          isSystem: true
        }]);
      }
    } else if (internetStatus === 'connected') {
      if (useLocalLLM) {
        setUseLocalLLM(false);
        // Add a message to history about the switch
        setHistory(prev => [...prev, {
          sender: "system", 
          message: "🔄 Internet connection restored. Automatically switched to Online RAG mode.",
          timestamp: new Date().toLocaleTimeString(),
          isSystem: true
        }]);
      }
    }
  }, [internetStatus, useLocalLLM]);

  const checkInternetConnectivity = async () => {
    try {
      setInternetStatus('checking');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      
      // Check multiple reliable endpoints for internet connectivity
      const testUrls = [
        'https://www.google.com/favicon.ico',
        'https://httpbin.org/get',
        'https://jsonplaceholder.typicode.com/posts/1'
      ];

      let connected = false;
      
      for (const url of testUrls) {
        try {
          const response = await fetch(url, {
            method: 'HEAD',
            signal: controller.signal,
            mode: 'no-cors', // Allow cross-origin requests
            cache: 'no-cache'
          });
          
          // For no-cors mode, we just check if the request didn't fail
          connected = true;
          break;
        } catch (error) {
          // Try next URL
          continue;
        }
      }
      
      clearTimeout(timeoutId);
      
      if (connected) {
        setInternetStatus('connected');
      } else {
        setInternetStatus('disconnected');
      }
    } catch (error) {
      setInternetStatus('error');
      console.error('Internet connectivity check failed:', error);
    }
  };

  const checkServerConnection = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch('http://localhost:8000/', {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        setServerStatus('online');
      } else {
        setServerStatus('error');
      }
    } catch (error) {
      setServerStatus('offline');
      console.error('Server connection check failed:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/session/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        console.log('Created new session:', data.session_id);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      // Generate a fallback session ID
      setSessionId(`session_${Date.now()}`);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, thinking, isTyping, currentTypingText]);

  // Smooth typing function
  const smoothTypeMessage = (message, delay = 20) => {
    return new Promise((resolve) => {
      message = message.replace(/^\s+/, "");  // ✅ Trim leading whitespace/newlines

      setThinking(false);
      setIsTyping(true);
      setCurrentTypingText("");

      let currentText = "";
      let index = 0;

      const typeNextChar = () => {
        if (index < message.length) {
          currentText += message[index];
          setCurrentTypingText(currentText);
          index++;
          setTimeout(typeNextChar, delay);
        } else {
          setHistory((h) => [...h, { sender: "bot", message: message }]);
          setIsTyping(false);
          setCurrentTypingText("");
          resolve();
        }
      };

      typeNextChar();
    });
  };

  const handleSubmit = async () => {
    if (!inputText.trim() && !selectedFile) return;
    
    // Check internet connectivity before sending
    await checkInternetConnectivity();
    
    const currentText = inputText;
    const currentFile = selectedFile;
    
    // Create combined user message
    let userMessage = "";
    if (currentFile && currentText.trim()) {
      userMessage = `${currentFile.name}\n${currentText}`;
    } else if (currentFile) {
      userMessage = `File: ${currentFile.name}`;
    } else {
      userMessage = currentText;
    }
    
    // Add combined user message to history
    setHistory((h) => [...h, { 
      sender: "user", 
      message: userMessage, 
      hasFile: !!currentFile,
      timestamp: new Date().toLocaleTimeString()
    }]);

    setThinking(true);
    setInputText("");
    setSelectedFile(null);

    try {
      let response, data;
      
      if (currentFile) {
        // Send file and message together
        const formData = new FormData();
        formData.append("file", currentFile);
        formData.append("question", currentText || "");
        formData.append("use_rag", (!useLocalLLM).toString());
        formData.append("voice", "Joanna");
        formData.append("session_id", sessionId || "");

        response = await fetch("http://localhost:8000/ask_with_file", {
          method: "POST",
          body: formData,
        });
      } else {
        // Send text only
        response = await fetch("http://localhost:8000/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: currentText,
            use_rag: !useLocalLLM,
            voice: "Joanna",
            session_id: sessionId || "",
          }),
        });
      }

      data = await response.json();
      
      if (data.error) {
        await smoothTypeMessage(`❌ Error: ${data.error}`);
      } else {
        // Show which mode was actually used - REDUCED SPACING HERE
        let modeIndicator = "";
        if (data.mode) {
          switch (data.mode) {
            case "offline":
              modeIndicator = "🔒 Local LLM - ";
              break;
            case "online_with_rag":
              modeIndicator = "🌐 Online RAG - ";
              break;
            case "online_no_rag":
              modeIndicator = "🌐 Online - ";
              break;
            case "file_extraction":
              modeIndicator = "📄 File Analysis - ";
              break;
          }
        }
        
        // Remove extra space - just concatenate directly
        await smoothTypeMessage(`${modeIndicator}${data.answer}`);
        
        // Update session ID if provided
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
        }
      }
    } catch (err) {
      console.error("Request failed:", err);
      setThinking(false);
      await smoothTypeMessage("❌ Connection failed. Please try again.");
    }
  };

  const handleTextChange = (e) => {
    setInputText(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleStartRecording = async () => {
    // Check connectivity before recording
    await checkInternetConnectivity();
    
    setRecording(true);
    if (!navigator.mediaDevices) {
      alert("Media Devices API not supported");
      setRecording(false);
      return;
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      setMediaRecorder(recorder);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      recorder.start();
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Error accessing microphone. Please check permissions.');
      setRecording(false);
    }
  };

  const handleStopRecording = () => {
    if (!mediaRecorder) return;

    mediaRecorder.onstop = async () => {
      setRecording(false);
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm;codecs=opus" });
      console.log("Blob size (bytes):", audioBlob.size);

      if (audioBlob.size === 0) {
        alert("Recorded audio blob is empty!");
        return;
      }

      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");
      formData.append("session_id", sessionId || "");

      setHistory((h) => [...h, { 
        sender: "user", 
        message: "🎤 Processing voice input...", 
        isVoice: true,
        timestamp: new Date().toLocaleTimeString()
      }]);

      try {
        const res = await fetch("http://localhost:8000/transcribe", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();

        setHistory((h) => {
          const newHist = [...h];
          newHist[newHist.length - 1] = {
            sender: "user",
            message: `🎤 "${data.transcript || "(No transcript)"}"`,
            isVoice: true,
            timestamp: new Date().toLocaleTimeString()
          };
          return newHist;
        });

        // Show mode indicator for voice responses too - REDUCED SPACING HERE
        let modeIndicator = "";
        if (data.mode) {
          switch (data.mode) {
            case "offline":
              modeIndicator = "🔒 Local LLM ";
              break;
            case "online_with_rag":
              modeIndicator = "🌐 Online RAG ";
              break;
            case "online_no_rag":
              modeIndicator = "🌐 Online ";
              break;
          }
        }

        // Remove extra space - just concatenate directly
        await smoothTypeMessage(`${modeIndicator}${data.answer || "(No answer)"}`);
        
        // Update session ID if provided
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
        }
      } catch (err) {
        console.error("Transcription failed:", err);
        await smoothTypeMessage("❌ Transcription failed. Please try again.");
      }
    };

    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
    e.target.value = '';
  };

  const handleCancelFile = () => {
    setSelectedFile(null);
  };

  const getInternetStatusDisplay = () => {
    switch (internetStatus) {
      case 'checking':
        return { icon: <Sparkles size={16} className="loading-spinner" />, text: 'Checking Internet...', color: '#f59e0b' };
      case 'connected':
        return { icon: <Wifi size={16} />, text: 'Online', color: '#10b981' };
      case 'disconnected':
        return { icon: <WifiOff size={16} />, text: 'Offline', color: '#ef4444' };
      case 'error':
        return { icon: <AlertCircle size={16} />, text: 'Connection Error', color: '#ef4444' };
      default:
        return { icon: <AlertCircle size={16} />, text: 'Unknown', color: '#6b7280' };
    }
  };

  const connectionDisplay = getInternetStatusDisplay();

  // Manual toggle function with confirmation for connectivity status
  const handleManualToggle = () => {
    if (internetStatus === 'disconnected' && !useLocalLLM) {
      // User is trying to switch to online mode while offline
      alert("No internet connection detected. Staying in Local LLM mode.");
      return;
    }
    setUseLocalLLM(!useLocalLLM);
  };

  const getSessionInfo = () => {
    if (!sessionId) return null;
    return (
      <div className="session-info">
        Session: {sessionId.slice(0, 8)}...
      </div>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">
              <Bot size={24} color="#10b981" />
            </div>
            <div>
              <h1 className="title">MedAssist AI</h1>
              <div className="connection-status" style={{color: connectionDisplay.color}}>
                {connectionDisplay.icon}
                <span>{connectionDisplay.text}</span>
                {serverStatus === 'offline' && (
                  <span style={{ color: '#ef4444', marginLeft: 8 }}>• Server Offline</span>
                )}
              </div>
            </div>
          </div>
          <div className="controls-section">
            <div className="mode-toggle">
              <button
                onClick={handleManualToggle}
                className="toggle-button"
                style={{
                  backgroundColor: useLocalLLM ? '#374151' : '#10b981',
                  opacity: internetStatus === 'disconnected' && !useLocalLLM ? 0.5 : 1
                }}
                title={
                  internetStatus === 'disconnected' 
                    ? 'Offline - Using Local LLM' 
                    : useLocalLLM 
                      ? 'Click to switch to Online RAG' 
                      : 'Click to switch to Local LLM'
                }
              >
                {useLocalLLM ? <FileText size={16} /> : <Zap size={16} />}
                <span className="toggle-text">
                  {useLocalLLM ? 'Local LLM' : 'Online RAG'}
                </span>
              </button>
            </div>
            <button
              onClick={checkInternetConnectivity}
              className="refresh-button"
              title="Check internet connection"
              disabled={internetStatus === 'checking'}
            >
              <Sparkles 
                size={16} 
                className={internetStatus === 'checking' ? 'loading-spinner' : ''}
              />
            </button>
          </div>
        </div>
      </header>

      <main className="chat-container">
        <div className="chat-area">
          {history.length === 0 && (
            <div className="welcome-message">
              <Bot size={48} color="#10b981" />
              <h2 className="welcome-title">Welcome to MedAssist AI</h2>
              <p className="welcome-text">
                I'm here to help you with medical questions and information. 
                You can type, upload files, or use voice input.
              </p>
              <div className="mode-info">
                <div className="mode-item">
                  <Zap size={16} color="#10b981" />
                  <span>Online RAG: Advanced medical knowledge base</span>
                </div>
                <div className="mode-item">
                  <FileText size={16} color="#6b7280" />
                  <span>Local LLM: Private, offline processing</span>
                </div>
              </div>
            </div>
          )}

          {history.map((chat, i) => {
            const isUser = chat.sender === "user";
            const isSystem = chat.isSystem;
            return (
              <div
                key={i}
                className="message-container message-enter"
              >
                <div className="message-wrapper">
                  <div className="avatar">
                    {isSystem ? (
                      <AlertCircle size={20} color="#f59e0b" />
                    ) : isUser ? (
                      <User size={20} color="#6b7280" />
                    ) : (
                      <Bot size={20} color="#10b981" />
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <div className="message-sender">
                        {isSystem ? 'System' : isUser ? 'You' : 'MedAssist AI'}
                      </div>
                      {chat.timestamp && (
                        <div className="timestamp">
                          {chat.timestamp}
                        </div>
                      )}
                    </div>
                    <div className="message-text" style={{
                      color: isSystem ? '#f59e0b' : '#f3f4f6',
                      fontStyle: isSystem ? 'italic' : 'normal'
                    }}>
                      {chat.hasFile && (
                        <div className="file-indicator">
                          <Paperclip size={14} />
                          <span>File attached</span>
                        </div>
                      )}
                      {chat.isVoice && (
                        <div className="voice-indicator">
                          <Mic size={14} />
                          <span>Voice message</span>
                        </div>
                      )}
                      {chat.message}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {(thinking || isTyping) && (
            <div className="message-container">
              <div className="message-wrapper">
                <div className="avatar">
                  <Bot size={20} color="#10b981" />
                </div>
                <div className="message-content">
                  <div className="message-sender">MedAssist AI</div>
                  <div className="message-text">
                    {thinking ? (
                      <div className="thinking-content thinking-dots">
                        <Sparkles size={16} />
                        <span>
                          {useLocalLLM ? '🔒 Processing with Local LLM' : '🌐 Processing with Online RAG'}
                          {selectedFile ? " and analyzing file" : ""}...
                        </span>
                      </div>
                    ) : (
                      <>
                        {currentTypingText}
                        <span className="cursor">|</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-section">
          {selectedFile && (
            <div className="file-preview">
              <div className="file-info">
                <Paperclip size={16} />
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">
                  ({(selectedFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <button
                type="button"
                onClick={handleCancelFile}
                className="cancel-button"
              >
                <X size={16} />
              </button>
            </div>
          )}

          <div className="input-form">
            <textarea
              placeholder={
                selectedFile 
                  ? `Ask about ${selectedFile.name}...` 
                  : useLocalLLM 
                    ? "Ask me anything (Local LLM)..."
                    : "Ask me anything about medicine..."
              }
              value={inputText}
              onChange={handleTextChange}
              onKeyPress={handleKeyPress}
              className="input-box"
              disabled={thinking || isTyping}
              autoFocus
              rows={1}
            />
            <div className="button-group">
              <button 
                type="button" 
                onClick={handleUploadClick} 
                className="action-button"
                disabled={thinking || isTyping}
                title="Upload file"
              >
                <Paperclip size={18} />
              </button>
              <button 
                type="button" 
                onClick={handleStartRecording} 
                className="action-button"
                style={{
                  color: recording ? '#ef4444' : '#9ca3af'
                }}
                disabled={thinking || recording || isTyping}
                title="Voice input"
              >
                <Mic size={18} />
              </button>
              <button
                onClick={handleSubmit}
                className="send-button"
                style={{
                  backgroundColor: (!inputText.trim() && !selectedFile) || thinking || isTyping
                    ? '#374151' 
                    : '#10b981'
                }}
                disabled={thinking || (!inputText.trim() && !selectedFile) || isTyping}
                title="Send message"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
          
          {getSessionInfo()}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: "none" }}
          accept="image/*,.pdf,.doc,.docx,.txt"
        />
      </main>

      {recording && (
        <div className="overlay">
          <div className="recording-modal">
            <div className="recording-icon">
              <Mic size={32} color="#ef4444" />
            </div>
            <p className="recording-text">Recording in progress...</p>
            <button onClick={handleStopRecording} className="stop-button">
              Stop Recording
            </button>
          </div>
        </div>
      )}
    </div>
  );
}