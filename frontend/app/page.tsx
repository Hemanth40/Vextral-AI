'use client';

import Link from 'next/link';

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
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* Ambient Glow Background */
        .ambient-glow {
          position: fixed;
          top: -40%;
          left: -20%;
          width: 80%;
          height: 80%;
          background: radial-gradient(ellipse, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
          pointer-events: none;
          z-index: 0;
        }
        .ambient-glow-2 {
          position: fixed;
          bottom: -30%;
          right: -20%;
          width: 70%;
          height: 70%;
          background: radial-gradient(ellipse, rgba(139, 92, 246, 0.06) 0%, transparent 70%);
          pointer-events: none;
          z-index: 0;
        }

        /* Glass Navbar */
        .glass-nav {
          position: sticky;
          top: 0;
          z-index: 100;
          background: rgba(6, 8, 15, 0.75);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .nav-inner {
          max-width: 1200px;
          margin: 0 auto;
          padding: 16px 32px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .logo-group {
          display: flex;
          align-items: center;
          gap: 12px;
          text-decoration: none;
          color: #f0f4f8;
        }
        .logo-mark {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 18px;
          color: #fff;
          box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }
        .logo-text {
          font-weight: 700;
          font-size: 20px;
          letter-spacing: -0.5px;
        }
        .nav-links {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .nav-link {
          color: #8899a6;
          text-decoration: none;
          font-size: 14px;
          font-weight: 500;
          padding: 8px 16px;
          border-radius: 8px;
          transition: all 0.2s;
        }
        .nav-link:hover { color: #f0f4f8; background: rgba(255,255,255,0.05); }
        .nav-cta {
          padding: 8px 20px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: #fff;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          text-decoration: none;
          transition: all 0.3s;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        }
        .nav-cta:hover {
          box-shadow: 0 0 30px rgba(99, 102, 241, 0.4);
          transform: translateY(-1px);
        }

        /* Hero */
        .hero {
          position: relative;
          z-index: 1;
          max-width: 900px;
          margin: 0 auto;
          padding: 100px 32px 60px;
          text-align: center;
        }
        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 16px;
          border-radius: 100px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
          color: #a5b4fc;
          font-size: 13px;
          font-weight: 500;
          margin-bottom: 32px;
        }
        .hero-badge-dot {
          width: 6px;
          height: 6px;
          background: #6366f1;
          border-radius: 50%;
          animation: pulse-dot 2s infinite;
        }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(99, 102, 246, 0.4); }
          50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(99, 102, 246, 0); }
        }
        .hero-title {
          font-size: 64px;
          font-weight: 800;
          letter-spacing: -2px;
          line-height: 1.1;
          margin-bottom: 24px;
          background: linear-gradient(135deg, #f0f4f8 0%, #c7d2fe 40%, #a78bfa 80%, #8b5cf6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .hero-sub {
          font-size: 18px;
          color: #8899a6;
          line-height: 1.7;
          max-width: 600px;
          margin: 0 auto 40px;
          font-weight: 400;
        }
        .hero-buttons {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
        }
        .btn-primary {
          padding: 14px 32px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: #fff;
          border: none;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          text-decoration: none;
          transition: all 0.3s;
          box-shadow: 0 4px 30px rgba(99, 102, 241, 0.3);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 40px rgba(99, 102, 241, 0.4);
        }
        .btn-secondary {
          padding: 14px 32px;
          background: rgba(255,255,255,0.04);
          color: #c9d1d9;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          font-size: 16px;
          font-weight: 500;
          text-decoration: none;
          transition: all 0.3s;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .btn-secondary:hover {
          background: rgba(255,255,255,0.08);
          border-color: rgba(255,255,255,0.2);
          transform: translateY(-2px);
        }

        /* Features */
        .features {
          position: relative;
          z-index: 1;
          max-width: 1100px;
          margin: 0 auto;
          padding: 40px 32px 80px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
        }
        .feature-card {
          background: rgba(15, 20, 35, 0.5);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 32px 28px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
        }
        .feature-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), transparent);
          opacity: 0;
          transition: opacity 0.4s;
        }
        .feature-card:hover {
          border-color: rgba(255,255,255,0.1);
          background: rgba(15, 20, 35, 0.8);
          transform: translateY(-4px);
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .feature-card:hover::before { opacity: 1; }
        .feature-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 20px;
          font-size: 22px;
        }
        .feature-icon.blue { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); }
        .feature-icon.purple { background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); }
        .feature-icon.green { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); }
        .feature-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 10px;
          color: #f0f4f8;
        }
        .feature-desc {
          font-size: 14px;
          color: #8899a6;
          line-height: 1.7;
        }

        /* Stats */
        .stats-section {
          position: relative;
          z-index: 1;
          max-width: 1100px;
          margin: 0 auto;
          padding: 40px 32px 80px;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
        }
        .stat-card {
          text-align: center;
          padding: 32px 20px;
          background: rgba(15, 20, 35, 0.4);
          border: 1px solid rgba(255,255,255,0.04);
          border-radius: 16px;
          transition: all 0.3s;
        }
        .stat-card:hover { border-color: rgba(255,255,255,0.08); }
        .stat-value {
          font-size: 36px;
          font-weight: 800;
          letter-spacing: -1px;
          background: linear-gradient(135deg, #a5b4fc, #8b5cf6);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .stat-label {
          font-size: 13px;
          color: #556677;
          margin-top: 6px;
          font-weight: 500;
        }

        /* Tech Row */
        .tech-section {
          position: relative;
          z-index: 1;
          padding: 60px 32px;
          text-align: center;
          border-top: 1px solid rgba(255,255,255,0.04);
        }
        .tech-label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 3px;
          color: #556677;
          margin-bottom: 24px;
          font-weight: 600;
        }
        .tech-row {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 40px;
          flex-wrap: wrap;
        }
        .tech-item {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #8899a6;
          font-size: 14px;
          font-weight: 500;
        }
        .tech-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        /* Footer */
        .glass-footer {
          position: relative;
          z-index: 1;
          border-top: 1px solid rgba(255,255,255,0.04);
          padding: 24px 32px;
          text-align: center;
          color: #556677;
          font-size: 13px;
        }

        @media (max-width: 768px) {
          .hero-title { font-size: 40px; }
          .features { grid-template-columns: 1fr; }
          .stats-grid { grid-template-columns: repeat(2, 1fr); }
          .hero-buttons { flex-direction: column; }
        }
      `}</style>

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
