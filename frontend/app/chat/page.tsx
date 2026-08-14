'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useToast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chunks_used?: number;
  sources?: string[];
  mode?: string;
  timestamp: Date;
  reasoning?: string;
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
  const [selectedModel, setSelectedModel] = useState<string>('gemini');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { showToast, ToastContainer } = useToast();
  const [tenantId, setTenantId] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let tenant = params.get('tenant');
    if (!tenant) {
      tenant = localStorage.getItem('vextral_tenant_id');
    }
    if (!tenant) {
      tenant = 'user_' + Math.random().toString(36).substring(2, 11);
      localStorage.setItem('vextral_tenant_id', tenant);
    }
    setTenantId(tenant);
  }, []);

  useEffect(() => {
    if (tenantId) {
      fetchDocuments();
      loadHistory();
    }
  }, [tenantId, selectedDoc]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchDocuments = async () => {
    if (!tenantId) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/upload/list/${tenantId}`);
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      showToast('Failed to load documents', 'error');
    }
  };

  const loadHistory = async () => {
    if (!tenantId) return;
    setHistoryLoading(true);
    try {
      let url = `${BACKEND_URL}/api/chat/history/${tenantId}?limit=20`;
      if (selectedDoc) url += `&source_file=${encodeURIComponent(selectedDoc)}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();
      const historyMessages: Message[] = (data.history || []).flatMap((item: HistoryItem) => {
        const contentStr = item.answer || '';
        let answer = contentStr;
        let reasoning = undefined;
        if (contentStr.includes('<think>') && contentStr.includes('</think>')) {
          const thinkStart = contentStr.indexOf('<think>') + 7;
          const thinkEnd = contentStr.indexOf('</think>');
          reasoning = contentStr.substring(thinkStart, thinkEnd).trim();
          answer = contentStr.substring(thinkEnd + 8).trim();
        }

        return [
          { id: `${item.id}-q`, role: 'user' as const, content: item.question, timestamp: new Date(item.created_at) },
          { id: `${item.id}-a`, role: 'assistant' as const, content: answer, reasoning, timestamp: new Date(item.created_at) },
        ];
      });
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
    if (textareaRef.current) {
      textareaRef.current.style.height = '42px';
    }
    setLoading(true);

    try {
      // Build chat history for context (last 10 messages)
      const recentHistory = [...messages, userMessage]
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await fetch(`${BACKEND_URL}/api/chat/ask`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, tenant_id: tenantId, source_file: selectedDoc, chat_history: recentHistory, model: selectedModel }),
      });

      if (!response.ok) throw new Error('Failed to get answer');

      const data = await response.json();
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(), role: 'assistant', content: data.answer,
        reasoning: data.reasoning,
        chunks_used: data.chunks_used, sources: data.sources || [], mode: data.mode, timestamp: new Date(),
      }]);
    } catch (error) {
      console.error('Error:', error);
      showToast('Failed to generate answer. Please try again.', 'error');
      setMessages((prev) => [...prev, { id: (Date.now() + 2).toString(), role: 'assistant', content: 'Sorry, something went wrong. Please try again.', timestamp: new Date() }]);
    } finally { setLoading(false); }
  };

  const handleClearHistory = async () => {
    if (!tenantId) return;
    if (!confirm('Clear chat history?')) return;
    try {
      let url = `${BACKEND_URL}/api/chat/history/${tenantId}`;
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
    <div className="chat-main-container">

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
          <div className="selector-group">
            <span className="selector-label">Chat with</span>
            <select
              value={selectedDoc || '__general__'}
              onChange={(e) => setSelectedDoc(e.target.value === '__general__' ? null : e.target.value)}
              className="selector-select"
            >
              <option value="__general__">🤖 General AI Chat</option>
              {documents.length > 0 && (
                <optgroup label="📂 Your Documents">
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.filename}>📄 {doc.filename}</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>

          <div className="selector-group">
            <span className="selector-label">AI Model</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="selector-select model-select"
            >
              <option value="gemini">👑 Gemini 3.5 (Primary)</option>
              <option value="groq">⚡ GPT-OSS 120B (Groq)</option>
              <option value="minimax">🎨 MiniMax-M3 (NVIDIA NIM)</option>
              <option value="nemotron-550b">🧠 Nemotron 3 550B (Reasoning)</option>
            </select>
          </div>

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
                  : `Ask me anything — I'm powered by ${
                      selectedModel === 'gemini'
                        ? '👑 Gemini 3.5'
                        : selectedModel === 'groq'
                        ? '⚡ GPT-OSS 120B'
                        : selectedModel === 'minimax'
                        ? '🎨 MiniMax-M3'
                        : '🧠 Nemotron 3 550B'
                    } AI.`}
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
                        {message.reasoning && (
                          <details className="reasoning-details" open>
                            <summary className="reasoning-summary">
                              💡 Thinking Process...
                            </summary>
                            <div className="reasoning-content">
                              {message.reasoning}
                            </div>
                          </details>
                        )}
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
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${e.target.scrollHeight}px`;
              }}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={selectedDoc ? `Ask about ${selectedDoc}...` : 'Ask me anything...'}
              className="input-textarea"
              rows={1}
              disabled={loading}
            />
            <button onClick={handleSend} disabled={!input.trim() || loading} className={`send-btn ${input.trim() && !loading ? 'ready' : ''}`}>
              {loading ? '⏳' : '✨ Send'}
            </button>
          </div>
          {selectedDoc && (
            <div className="input-active-doc-badge">
              📄 Active Document: <strong>{selectedDoc}</strong>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
