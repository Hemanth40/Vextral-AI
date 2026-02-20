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
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        .chat-ambient { position: fixed; top: -30%; left: -15%; width: 60%; height: 60%; background: radial-gradient(ellipse, rgba(99, 102, 241, 0.05) 0%, transparent 70%); pointer-events: none; z-index: 0; }
        .chat-ambient-2 { position: fixed; bottom: -20%; right: -15%; width: 50%; height: 50%; background: radial-gradient(ellipse, rgba(139, 92, 246, 0.04) 0%, transparent 70%); pointer-events: none; z-index: 0; }

        /* Nav */
        .glass-nav { position: sticky; top: 0; z-index: 100; background: rgba(6, 8, 15, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.06); }
        .nav-inner { max-width: 1200px; margin: 0 auto; padding: 12px 32px; display: flex; align-items: center; justify-content: space-between; }
        .logo-group { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #f0f4f8; }
        .logo-mark { width: 32px; height: 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 16px; color: #fff; box-shadow: 0 0 16px rgba(139, 92, 246, 0.3); }
        .logo-text { font-weight: 700; font-size: 18px; letter-spacing: -0.5px; }
        .nav-links { display: flex; align-items: center; gap: 6px; }
        .nav-link { color: #8899a6; text-decoration: none; font-size: 13px; font-weight: 500; padding: 6px 14px; border-radius: 6px; transition: all 0.2s; }
        .nav-link:hover { color: #f0f4f8; background: rgba(255,255,255,0.05); }
        .nav-link.active { color: #a5b4fc; background: rgba(99, 102, 241, 0.1); }
        .doc-badge { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; padding: 1px 7px; border-radius: 8px; font-size: 11px; font-weight: 600; margin-left: 4px; }
        .clear-btn { background: none; border: 1px solid rgba(255,255,255,0.06); color: #556677; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
        .clear-btn:hover { border-color: rgba(239, 68, 68, 0.3); color: #f87171; }

        /* Doc Selector */
        .selector-bar { padding: 12px 32px; border-bottom: 1px solid rgba(255,255,255,0.04); background: rgba(6, 8, 15, 0.5); position: relative; z-index: 10; }
        .selector-inner { max-width: 900px; margin: 0 auto; display: flex; align-items: center; gap: 12px; }
        .selector-label { font-size: 12px; font-weight: 600; color: #556677; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }
        .selector-select { flex: 1; max-width: 360px; padding: 8px 14px; background: rgba(15, 20, 35, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; color: #c9d1d9; font-size: 14px; font-family: inherit; cursor: pointer; outline: none; transition: border-color 0.2s; }
        .selector-select:focus { border-color: rgba(99, 102, 241, 0.4); }
        .selector-select option { background: #0c1018; color: #c9d1d9; }
        .mode-pill { padding: 4px 12px; border-radius: 100px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px; }
        .mode-pill.rag { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
        .mode-pill.ai { background: rgba(139, 92, 246, 0.12); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.2); }

        /* Messages */
        .messages-container { flex: 1; overflow-y: auto; position: relative; z-index: 1; }
        .messages-inner { max-width: 800px; margin: 0 auto; padding: 24px 24px; }

        /* Empty State */
        .empty-chat { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px 24px; text-align: center; }
        .empty-orb { width: 80px; height: 80px; border-radius: 20px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; font-size: 36px; position: relative; }
        .empty-orb.doc { background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05)); border: 1px solid rgba(16, 185, 129, 0.2); }
        .empty-orb.ai { background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05)); border: 1px solid rgba(139, 92, 246, 0.2); }
        .empty-orb::after { content: ''; position: absolute; inset: -8px; border-radius: 24px; background: inherit; opacity: 0.3; filter: blur(12px); z-index: -1; }
        .empty-title { font-size: 22px; font-weight: 700; color: #f0f4f8; margin-bottom: 8px; letter-spacing: -0.5px; }
        .empty-desc { font-size: 14px; color: #556677; max-width: 380px; line-height: 1.6; }
        .empty-suggestions { margin-top: 32px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
        .suggestion-chip { padding: 8px 16px; background: rgba(15, 20, 35, 0.8); border: 1px solid rgba(255,255,255,0.06); border-radius: 100px; color: #8899a6; font-size: 13px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
        .suggestion-chip:hover { border-color: rgba(99, 102, 241, 0.3); color: #a5b4fc; background: rgba(99, 102, 241, 0.05); }

        /* Message Rows */
        .msg-row { display: flex; gap: 14px; margin-bottom: 28px; animation: msgIn 0.35s ease; }
        @keyframes msgIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.assistant { justify-content: flex-start; }

        .msg-avatar { width: 32px; height: 32px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; margin-top: 4px; }
        .msg-avatar.ai { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; box-shadow: 0 0 12px rgba(139, 92, 246, 0.2); }
        .msg-avatar.usr { background: rgba(255,255,255,0.08); color: #8899a6; }

        /* User bubble */
        .user-bubble { background: linear-gradient(135deg, #4f46e5, #6366f1); color: #fff; padding: 12px 20px; border-radius: 18px 18px 4px 18px; max-width: 65%; font-size: 14px; line-height: 1.6; box-shadow: 0 4px 20px rgba(99, 102, 241, 0.2); }

        /* AI bubble */
        .ai-container { max-width: 100%; flex: 1; min-width: 0; }
        .ai-bubble { background: rgba(15, 20, 35, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 4px 16px 16px 16px; padding: 20px 24px; font-size: 14px; line-height: 1.8; overflow: hidden; }
        .ai-bubble:hover { border-color: rgba(255,255,255,0.09); }

        /* Markdown in AI bubble */
        .ai-bubble h1, .ai-bubble h2, .ai-bubble h3 { color: #f0f4f8; margin: 16px 0 8px; font-weight: 700; letter-spacing: -0.3px; }
        .ai-bubble h1 { font-size: 18px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px; }
        .ai-bubble h2 { font-size: 16px; }
        .ai-bubble h3 { font-size: 15px; }
        .ai-bubble p { margin-bottom: 10px; color: #c9d1d9; }
        .ai-bubble p:last-child { margin-bottom: 0; }
        .ai-bubble strong { color: #e8edf2; font-weight: 600; }
        .ai-bubble em { color: #8899a6; font-style: italic; }
        .ai-bubble ul, .ai-bubble ol { margin: 8px 0 12px; padding-left: 20px; }
        .ai-bubble li { margin-bottom: 4px; color: #c9d1d9; }
        .ai-bubble li::marker { color: #6366f1; }

        .ai-bubble code { background: rgba(99, 102, 241, 0.08); color: #a5b4fc; padding: 2px 7px; border-radius: 5px; font-size: 13px; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
        .ai-bubble pre { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 16px 20px; overflow-x: auto; margin: 12px 0; }
        .ai-bubble pre code { background: none; padding: 0; font-size: 13px; line-height: 1.7; color: #c9d1d9; }

        .ai-bubble table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
        .ai-bubble th { background: rgba(99, 102, 241, 0.08); color: #a5b4fc; padding: 8px 14px; text-align: left; font-weight: 600; border: 1px solid rgba(255,255,255,0.06); }
        .ai-bubble td { padding: 8px 14px; border: 1px solid rgba(255,255,255,0.04); color: #c9d1d9; }
        .ai-bubble tr:hover td { background: rgba(99, 102, 241, 0.03); }

        .ai-bubble blockquote { border-left: 3px solid #6366f1; padding: 10px 16px; margin: 12px 0; background: rgba(99, 102, 241, 0.04); border-radius: 0 8px 8px 0; color: #8899a6; font-style: italic; }
        .ai-bubble a { color: #818cf8; text-decoration: none; }
        .ai-bubble a:hover { text-decoration: underline; }
        .ai-bubble hr { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 16px 0; }

        .source-line { display: flex; align-items: center; gap: 8px; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.04); font-size: 11px; color: #556677; }
        .source-indicator { width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.4); }

        /* Loading */
        .thinking-dots { display: flex; gap: 5px; padding: 6px 0; }
        .thinking-dot { width: 7px; height: 7px; background: #6366f1; border-radius: 50%; animation: thinkBounce 1.4s infinite ease-in-out; }
        .thinking-dot:nth-child(1) { animation-delay: 0ms; }
        .thinking-dot:nth-child(2) { animation-delay: 160ms; }
        .thinking-dot:nth-child(3) { animation-delay: 320ms; }
        @keyframes thinkBounce { 0%, 80%, 100% { transform: scale(0.5); opacity: 0.3; } 40% { transform: scale(1); opacity: 1; } }

        .loader-spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-radius: 50%; border-top-color: #6366f1; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Input */
        .input-zone { position: sticky; bottom: 0; z-index: 10; padding: 16px 24px 24px; }
        .input-zone::before { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 120px; background: linear-gradient(transparent, #06080f); pointer-events: none; z-index: -1; }
        .input-wrapper { max-width: 800px; margin: 0 auto; }
        .input-glass { background: rgba(15, 20, 35, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; backdrop-filter: blur(12px); overflow: hidden; transition: border-color 0.2s; }
        .input-glass:focus-within { border-color: rgba(99, 102, 241, 0.3); box-shadow: 0 0 30px rgba(99, 102, 241, 0.05); }
        .input-textarea { width: 100%; padding: 16px 20px; background: transparent; border: none; color: #e8edf2; font-size: 14px; resize: none; outline: none; font-family: 'Inter', system-ui, sans-serif; line-height: 1.6; }
        .input-textarea::placeholder { color: #3a4555; }
        .input-footer { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; border-top: 1px solid rgba(255,255,255,0.04); }
        .input-meta { font-size: 11px; color: #3a4555; display: flex; align-items: center; gap: 8px; }
        .input-meta strong { color: #556677; }
        .input-meta kbd { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); padding: 1px 5px; border-radius: 3px; font-size: 10px; color: #556677; font-family: inherit; }
        .send-btn { padding: 8px 24px; border: none; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.3s; font-family: inherit; display: flex; align-items: center; gap: 6px; }
        .send-btn.ready { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; box-shadow: 0 4px 16px rgba(99, 102, 241, 0.25); }
        .send-btn.ready:hover { box-shadow: 0 6px 24px rgba(99, 102, 241, 0.35); transform: translateY(-1px); }
        .send-btn:disabled { background: rgba(255,255,255,0.04); color: #3a4555; cursor: not-allowed; box-shadow: none; transform: none; }
      `}</style>

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
