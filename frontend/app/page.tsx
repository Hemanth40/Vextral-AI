'use client';

import Link from 'next/link';

import './home.css';

export default function Home() {
  return (
    <div className="home-main-container">

      {/* Ambient Glows */}
      <div className="ambient-glow" />
      <div className="ambient-glow-2" />

      {/* Navigation */}
      <nav className="glass-nav">
        <div className="nav-inner">
          <Link href="/" className="logo-group">
            <div className="logo-mark">V</div>
            <span className="logo-text">Vextral AI</span>
          </Link>
          <div className="nav-links">
            <Link href="/chat" className="nav-link">💬 Chat</Link>
            <Link href="/documents" className="nav-link">📄 Documents</Link>
            <Link href="/chat" className="nav-cta">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          Powered by Gemini 3.5 + Kimi K2.6 + GLM-5.1 + MiniMax-M3 + Nemotron-3
        </div>
        <h1 className="hero-title">
          Your Documents,<br />Supercharged by AI
        </h1>
        <p className="hero-sub">
          Upload any document and have an intelligent conversation with it.
          Powered by Gemini File API that understands text, tables, charts, and complex layouts.
        </p>
        <div className="hero-buttons">
          <Link href="/chat" className="btn-primary">
            ✨ Start Chatting
          </Link>
          <Link href="/documents" className="btn-secondary">
            📄 Manage Documents
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <div className="feature-card">
          <div className="feature-icon blue">🧠</div>
          <h3 className="feature-title">Multi-Model Intelligence</h3>
          <p className="feature-desc">
            Document chat powered by Gemini 3.5 with 1M context. General chat powered by Kimi K2.6, GLM-5.1, MiniMax-M3, and Nemotron 3 550B.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon purple">📊</div>
          <h3 className="feature-title">Native Scan RAG</h3>
          <p className="feature-desc">
            Direct full-document analysis via Gemini File API. Feeds entire files (text + tables + charts) into the context window for zero-loss RAG queries.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon green">⚡</div>
          <h3 className="feature-title">Logical Thinking Logs</h3>
          <p className="feature-desc">
            Experience Nemotron 3 550B's live chain-of-thought traces inside a collapsible, glassmorphic dropdown box before reading final answers.
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">2-5s</div>
            <div className="stat-label">Response Time</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">1M</div>
            <div className="stat-label">Context Window Tokens</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">9+</div>
            <div className="stat-label">File Formats</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">6</div>
            <div className="stat-label">AI Models</div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="tech-section">
        <p className="tech-label">Built With</p>
        <div className="tech-row">
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#76b900' }} />
            NVIDIA NIM
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#4285F4' }} />
            Google Gemini
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#f55036' }} />
            Groq
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#0070f3' }} />
            Next.js
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#009688' }} />
            FastAPI
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#3ecf8e' }} />
            Supabase
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="glass-footer">
        Vextral AI © 2026 · Built with advanced AI by Hemanth Kumar G
      </footer>
    </div>
  );
}
