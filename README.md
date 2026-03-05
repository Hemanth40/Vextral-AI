<p align="center">
  <img src="https://img.shields.io/badge/Vextral-AI%20Document%20Intelligence-8b5cf6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJMMyA3djEwbDkgNSA5LTVWN2wtOS01eiIvPjwvc3ZnPg==" alt="Vextral AI"/>
</p>

<h1 align="center">⚡ Vextral AI</h1>

<p align="center">
  <strong>Ask Your Documents — Powered by Dual-Model AI</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Gemini%203.0%20Flash-Leader%20Agent-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/Groq-Llama%203.3%2070B-f55036?style=flat-square" alt="Groq" />
  <img src="https://img.shields.io/badge/NVIDIA%20NIM-Kimi%20K2.5-76b900?style=flat-square&logo=nvidia&logoColor=white" alt="NVIDIA" />
  <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-dc382d?style=flat-square" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ecf8e?style=flat-square&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License" />
</p>

<p align="center">
  A production-ready, multi-tenant RAG SaaS platform that lets users upload documents and chat with them using advanced AI — or switch to a general-purpose AI assistant.
</p>

---

## ✨ Features

| Feature | Description |
|---|---|
| 👑 **Multi-Agent Review** | **Leader/Worker Architecture:** Groq drafts instantly; Gemini 3.0 Flash reviews, strictly fact-checks, and polishes |
| 🧩 **Parent-Child Retrieval** | **Zero Information Loss:** Embeds precision child chunks, but feeds massive full parent chunks to the LLMs |
| ⚡ **Extreme Speed** | **Parallel OCR:** Multi-threaded Vision AI transcription + High-volume vector database batching for <1min huge uploads |
| 🧠 **Tri-Model AI** | Gemini 3.0 Flash (Leader), Llama 3.3 70B (Document Worker), Kimi K2.5 (General AI Worker) |
| 📄 **Multi-Format Parsing** | PDF (text + tables), DOCX, TXT, CSV, MD, JSON, PNG, JPG — all supported |
| 🎨 **Premium Dark UI** | Glassmorphism design, ambient glows, smooth animations, readable Markdown rendering |
| 🏢 **Multi-Tenant** | Isolated data per tenant with per-user Qdrant collections |
| 💬 **Chat History** | Persistent per-document and general AI chat history |
| 📊 **Table Extraction** | Automatically detects and extracts tables from PDFs as Markdown |
| 🖼️ **Vision AI** | Extracts text from images using Llama 3.2 Vision |

---

## 🏗️ Architecture

```
┌──────────────────┐     ┌──────────────────────────────────────┐
│                  │     │           FastAPI Backend             │
│   Next.js 16     │────▶│                                      │
│   Frontend       │     │  ┌─────────┐  ┌───────────────────┐  │
│                  │◀────│  │ Upload  │  │ Chat Router       │  │
│  • Premium UI    │     │  │ Router  │  │ • RAG Mode        │  │
│  • Glassmorphism │     │  └────┬────┘  │ • General AI Mode │  │
│  • Markdown Chat │     │       │       └────────┬──────────┘  │
│  • Toast Notifs  │     │       ▼                ▼             │
└──────────────────┘     │  ┌─────────┐  ┌───────────────────┐  │
                         │  │ Parser  │  │ Generator AI      │  │
                         │  │ •Parallel│ │ • Groq (Worker)   │  │
                         │  │ •Parent- │ │ • Gemini (Leader) │  │
                         │  │  Child   │ │ • Kimi (General)  │  │
                         │  └────┬────┘  └───────────────────┘  │
                         │       │       ▲                      │
                         │       ▼       │                      │
                         │  ┌─────────┐  ┌───────────────────┐  │
                         │  │Embedder │  │ Vector Store      │  │
                         │  │ NVIDIA  │──│ Qdrant Cloud      │  │
                         │  └─────────┘  └───────────────────┘  │
                         │       │       ┌───────────────────┐  │
                         │       └──────▶│ Supabase Postgres │  │
                         │               └───────────────────┘  │
                         └──────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- API keys for: Google Gemini, NVIDIA NIM, Groq, Qdrant Cloud, Supabase

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Vextral.git
cd Vextral
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file from the example:

```bash
cp .env.example .env
# Fill in your API keys in .env
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create `.env.local`:

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

### 4. Database Setup

Run the SQL in `backend/database_schema.sql` in your **Supabase SQL Editor**.

### 5. Open the App

Visit **[http://localhost:3000](http://localhost:3000)** 🎉

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google GenAI key for Gemini 3.0 Flash (Leader Agent) |
| `GROQ_API_KEY` | Groq API key for Llama 3.3 70B (Worker Agent) |
| `NVIDIA_API_KEY` | NVIDIA NIM key for embeddings (Llama-Nemotron) |
| `NVIDIA_API_KEY_KIMI` | NVIDIA NIM key for Kimi K2.5 (General AI Worker) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_KEY` | Qdrant Cloud API key |
| `DATABASE_URL` | Supabase PostgreSQL connection string |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL (`http://localhost:8000` for dev) |

---

## 📁 Project Structure

```
Vextral/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── database_schema.sql     # Supabase schema
│   ├── .env.example            # Environment template
│   ├── routers/
│   │   ├── chat.py             # Chat endpoints (RAG + General AI)
│   │   └── upload.py           # Document upload & management
│   └── services/
│       ├── generator.py        # Dual-model AI (Kimi + Groq)
│       ├── parser.py           # Multi-format document parser
│       ├── embedder.py         # NVIDIA NIM embedding service
│       ├── vector_store.py     # Qdrant vector operations
│       └── database.py         # PostgreSQL helpers
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── chat/page.tsx       # Chat interface
│   │   ├── documents/page.tsx  # Document management
│   │   ├── globals.css         # Premium dark theme
│   │   └── layout.tsx          # Root layout
│   ├── components/
│   │   └── ui/use-toast.tsx    # Toast notification system
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## 🌐 Deployment

| Component | Platform | URL |
|---|---|---|
| **Frontend** | Vercel | [vercel.com](https://vercel.com) |
| **Backend** | Render | [render.com](https://render.com) |
| **Database** | Supabase | [supabase.com](https://supabase.com) |
| **Vector DB** | Qdrant Cloud | [cloud.qdrant.io](https://cloud.qdrant.io) |

> See the deployment guide in the repository for step-by-step instructions.

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center"><strong>Frontend</strong></td>
<td align="center"><strong>Backend</strong></td>
<td align="center"><strong>AI Models</strong></td>
<td align="center"><strong>Infrastructure</strong></td>
</tr>
<tr>
<td>

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- react-markdown

</td>
<td>

- FastAPI
- Python 3.10+
- PyMuPDF
- python-docx
- psycopg2

</td>
<td>

- Gemini 3.0 Flash (Google)
- Llama 3.3 70B (Groq)
- Kimi K2.5 (NVIDIA)
- Llama-Nemotron Embed
- Llama 3.2 Vision

</td>
<td>

- Supabase (Postgres)
- Qdrant Cloud
- Vercel
- Render

</td>
</tr>
</table>

---

## 📜 License

This project is licensed under the **MIT License**.

---

<p align="center">
  Built with ❤️ by <strong>Hemanth Kumar G</strong>
</p>
