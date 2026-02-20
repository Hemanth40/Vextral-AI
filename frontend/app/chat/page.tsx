'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useToast } from '@/components/ui/use-toast';

const TENANT_ID = 'demo_user';
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chunks_used?: number;
  sources?: string[];
  mode?: string;
  timestamp: Date;
}

interface Document {
  id: string;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

interface HistoryItem {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

import './chat.css';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { showToast, ToastContainer } = useToast();

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchDocuments(); }, []);


  useEffect(() => {
    setMessages([]);
    loadHistory();
  }, [selectedDoc]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/upload/list/${TENANT_ID}`);
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      showToast('Failed to load documents', 'error');
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      let url = `${BACKEND_URL}/api/chat/history/${TENANT_ID}?limit=20`;
      if (selectedDoc) url += `&source_file=${encodeURIComponent(selectedDoc)}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();
      const historyMessages: Message[] = (data.history || []).flatMap((item: HistoryItem) => [
        { id: `${item.id}-q`, role: 'user' as const, content: item.question, timestamp: new Date(item.created_at) },
        { id: `${item.id}-a`, role: 'assistant' as const, content: item.answer, timestamp: new Date(item.created_at) },
      ]);
      setMessages(historyMessages);
    } catch (error) {
      console.error('Error loading history:', error);
      showToast('Failed to load chat history', 'error');
      setMessages([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build chat history for context (last 10 messages)
      const recentHistory = [...messages, userMessage]
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await fetch(`${BACKEND_URL}/api/chat/ask`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, tenant_id: TENANT_ID, source_file: selectedDoc, chat_history: recentHistory }),
      });

      if (!response.ok) throw new Error('Failed to get answer');

      const data = await response.json();
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(), role: 'assistant', content: data.answer,
        chunks_used: data.chunks_used, sources: data.sources || [], mode: data.mode, timestamp: new Date(),
      }]);
    } catch (error) {
      console.error('Error:', error);
      showToast('Failed to generate answer. Please try again.', 'error');
      setMessages((prev) => [...prev, { id: (Date.now() + 2).toString(), role: 'assistant', content: 'Sorry, something went wrong. Please try again.', timestamp: new Date() }]);
    } finally { setLoading(false); }
  };

  const handleClearHistory = async () => {
    if (!confirm('Clear chat history?')) return;
    try {
      let url = `${BACKEND_URL}/api/chat/history/${TENANT_ID}`;
      if (selectedDoc) url += `?source_file=${encodeURIComponent(selectedDoc)}`;

      const response = await fetch(url, { method: 'DELETE' });
      if (response.ok) {
        setMessages([]);
        showToast('Chat history cleared', 'success');
      } else {
        throw new Error('Failed to clear');
      }
    } catch (error) {
      console.error('Error clearing history:', error);
      showToast('Failed to clear history', 'error');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#06080f', fontFamily: "'Inter', system-ui, sans-serif", color: '#f0f4f8', display: 'flex', flexDirection: 'column' }}>

      <ToastContainer />
      <div className="chat-ambient" />
      <div className="chat-ambient-2" />

      {/* Nav */}
      <nav className="glass-nav">
        <div className="nav-inner">
          <Link href="/" className="logo-group">
            <div className="logo-mark">V</div>
            <span className="logo-text">Vextral AI</span>
          </Link>
          <div className="nav-links">
            <Link href="/chat" className="nav-link active">💬 Chat</Link>
            <Link href="/documents" className="nav-link">
              📄 Documents{documents.length > 0 && <span className="doc-badge">{documents.length}</span>}
            </Link>
            <button onClick={handleClearHistory} className="clear-btn">🗑️ Clear</button>
          </div>
        </div>
      </nav>

      {/* Selector */}
      <div className="selector-bar">
        <div className="selector-inner">
          <span className="selector-label">Chat with</span>
          <select
            value={selectedDoc || '__general__'}
            onChange={(e) => setSelectedDoc(e.target.value === '__general__' ? null : e.target.value)}
            className="selector-select"
          >
            <option value="__general__">🤖 General AI Chat (Kimi K2.5)</option>
            {documents.length > 0 && (
              <optgroup label="📂 Your Documents">
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.filename}>📄 {doc.filename}</option>
                ))}
              </optgroup>
            )}
          </select>
          <span className={`mode-pill ${selectedDoc ? 'rag' : 'ai'}`}>
            {selectedDoc ? '⚡ RAG Mode' : '🌙 AI Mode'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        <div className="messages-inner">
          {historyLoading ? (
            <div className="empty-chat">
              <div className="loader-spinner" />
              <p className="text-gray-500">Loading history...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="empty-chat">
              <div className={`empty-orb ${selectedDoc ? 'doc' : 'ai'}`}>
                {selectedDoc ? '📄' : '✨'}
              </div>
              <h2 className="empty-title">
                {selectedDoc ? selectedDoc : 'General AI Chat'}
              </h2>
              <p className="empty-desc">
                {selectedDoc
                  ? 'Ask anything about this document. I\'ll find answers and supplement with broader knowledge.'
                  : 'Ask me anything — I\'m powered by Kimi K2.5 AI.'}
              </p>
              <div className="empty-suggestions">
                {selectedDoc ? (
                  <>
                    <button className="suggestion-chip" onClick={() => { setInput('Summarize this document'); }}>📝 Summarize this document</button>
                    <button className="suggestion-chip" onClick={() => { setInput('What are the key findings?'); }}>🔍 Key findings</button>
                    <button className="suggestion-chip" onClick={() => { setInput('What is the conclusion?'); }}>📊 Conclusion</button>
                  </>
                ) : (
                  <>
                    <button className="suggestion-chip" onClick={() => { setInput('What can you help me with?'); }}>💡 What can you do?</button>
                    <button className="suggestion-chip" onClick={() => { setInput('Explain machine learning'); }}>🧠 Explain ML</button>
                    <button className="suggestion-chip" onClick={() => { setInput('Write a Python function'); }}>🐍 Write Python code</button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.id} className={`msg-row ${message.role}`}>
                  {message.role === 'assistant' && <div className="msg-avatar ai">V</div>}
                  {message.role === 'user' ? (
                    <div className="user-bubble">{message.content}</div>
                  ) : (
                    <div className="ai-container">
                      <div className="ai-bubble">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                        {message.chunks_used !== undefined && message.chunks_used > 0 && (
                          <div className="source-line">
                            <span className="source-indicator" />
                            {message.sources && message.sources.length > 0
                              ? `Sources: ${message.sources.slice(0, 3).join(' · ')}`
                              : `Sourced from ${selectedDoc || 'documents'} · ${message.chunks_used} chunks analyzed`}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {message.role === 'user' && <div className="msg-avatar usr">U</div>}
                </div>
              ))}
              {loading && (
                <div className="msg-row assistant">
                  <div className="msg-avatar ai">V</div>
                  <div className="ai-container">
                    <div className="ai-bubble">
                      <div className="thinking-dots">
                        <div className="thinking-dot" />
                        <div className="thinking-dot" />
                        <div className="thinking-dot" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="input-zone">
        <div className="input-wrapper">
          <div className="input-glass">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={selectedDoc ? `Ask about ${selectedDoc}...` : 'Ask me anything...'}
              className="input-textarea"
              rows={3}
              disabled={loading}
            />
            <div className="input-footer">
              <span className="input-meta">
                <strong>{selectedDoc ? `📄 ${selectedDoc}` : '🌙 General AI'}</strong> · <kbd>Enter</kbd> to send
              </span>
              <button onClick={handleSend} disabled={!input.trim() || loading} className={`send-btn ${input.trim() && !loading ? 'ready' : ''}`}>
                {loading ? '⏳ Thinking...' : '✨ Send'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
