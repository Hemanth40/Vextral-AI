'use client';

import Link from 'next/link';

import './home.css';

export default function Home() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#06080f',
      fontFamily: "'Inter', -apple-system, system-ui, sans-serif",
      color: '#f0f4f8',
      position: 'relative',
      overflow: 'hidden',
    }}>

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
          Powered by NVIDIA NIM + Groq
        </div>
        <h1 className="hero-title">
          Your Documents,<br />Supercharged by AI
        </h1>
        <p className="hero-sub">
          Upload any document and have an intelligent conversation with it.
          Powered by cutting-edge vision models that understand text, tables, charts, and complex layouts.
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
          <h3 className="feature-title">Dual AI Intelligence</h3>
          <p className="feature-desc">
            Document chat powered by Groq Llama 3.3 70B for blazing speed. General AI powered by Kimi K2.5 for creative conversations.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon purple">📊</div>
          <h3 className="feature-title">Deep Document Understanding</h3>
          <p className="feature-desc">
            Extracts headings, tables, bold text, and structure from PDFs, DOCX, TXT, CSV, and images with 90%+ accuracy.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon green">⚡</div>
          <h3 className="feature-title">Lightning Fast Answers</h3>
          <p className="feature-desc">
            Responses in 2-5 seconds powered by Groq&apos;s custom LPU hardware. Vector search finds relevant content instantly.
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
            <div className="stat-value">90%+</div>
            <div className="stat-label">Extraction Accuracy</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">7+</div>
            <div className="stat-label">File Formats</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">2</div>
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
            <div className="tech-dot" style={{ background: '#f55036' }} />
            Groq
          </div>
          <div className="tech-item">
            <div className="tech-dot" style={{ background: '#24b47e' }} />
            Qdrant
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
