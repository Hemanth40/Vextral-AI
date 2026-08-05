# ⚡ Vextral AI

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Storage-3ecf8e?style=for-the-badge&logo=supabase)](https://supabase.com)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-Multi--Model-76b900?style=for-the-badge&logo=nvidia)](https://build.nvidia.com)
[![Groq](https://img.shields.io/badge/Groq-GPT--OSS%20120B-f55036?style=for-the-badge&logo=groq)](https://groq.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=for-the-badge&logo=vercel)](https://vextral-ai.vercel.app/)

A premium, production-ready, multi-tenant RAG platform that allows users to upload complex documents and chat with them using advanced AI — styled in a custom, dark Neumorphic design system.

🔗 **Live URL**: [https://vextral-ai.vercel.app/](https://vextral-ai.vercel.app/)

---

## 🚀 Key Features

* 🧬 **Zero-Loss Native Scan RAG**: Replaced heavy vector chunk indexing (Qdrant / LanceDB) with **Gemini File API direct document scans**. Full multi-modal files (up to 1M tokens) are analyzed natively — tables, layouts, charts, and cross-references preserved exactly as they exist.
* 🧠 **7-Model AI Grid**: Integrated the latest top-tier models:
  - **`Gemini 3.5 & Gemma 4`** — Primary document readers with full multimodal visual perception.
  - **`nvidia/nemotron-3-ultra-550b-a55b`** — 550B reasoning model with chain-of-thought logs.
  - **`minimaxai/minimax-m3`** — Multimodal model (text, image, video).
  - **`z-ai/glm-5.1`** — Expert coding & software debugging.
  - **`moonshotai/kimi-k2.6`** — Multi-turn general conversation specialist.
  - **`openai/gpt-oss-120b`** (via Groq) — Ultra-fast 120B open-source GPT model.
* 💡 **Interactive Thinking Drawer**: Collapsible UI panel capturing Nemotron's chain-of-thought tokens inside a glassmorphic expander drawer before the final answer.
* 🎨 **Dark Neumorphic (Soft UI) Design**: Entire interface (Home, Chat, Documents) built with realistic double-shadow elements, inset inputs, and beveled metadata badges.
* 📦 **Cloud-Native Storage**: Supabase Storage Buckets for document lifecycle management with automatic Google Gemini URI renewal (48h expiry handled transparently).

---

## 🏗️ Architecture

```
                                  ┌───────────────────────────┐
                                  │    Next.js 15 Frontend    │
                                  │  • Neumorphic Design      │
                                  │  • Collapsible Think Box  │
                                  │  • Auto-Expanding Input   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │      FastAPI Backend      │
                                  │                           │
                                  │   ┌───────────────────┐   │
                                  │   │  Chat & Ask API   │   │
                                  │   └─────────┬─────────┘   │
                                  │             │             │
                                  │             ▼             │
                                  │   ┌───────────────────┐   │
                                  │   │ Gemini File RAG   │   │
                                  │   │ • 48h Auto-Refresh│   │
                                  │   └─────────┬─────────┘   │
                                  └─────────────┼─────────────┘
                                                │
                                  ┌─────────────┼─────────────┐
                                  ▼             ▼             ▼
                    ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
                    │ NVIDIA NIM       │ │ Groq API     │ │ Supabase Cloud   │
                    │ • Nemotron 550B  │ │ • GPT-OSS    │ │ • Postgres Meta  │
                    │ • MiniMax-M3     │ │   120B       │ │ • Storage Bucket │
                    └──────────────────┘ └──────────────┘ └──────────────────┘
```

---

## 🔑 Environment Variables

Set up your backend API keys in `backend/.env`:

```env
# Google GenAI API
GEMINI_API_KEY="your-google-api-key"

# NVIDIA NIM API Keys
NVIDIA_API_KEY_GLM="nvapi-glm-key"
NVIDIA_API_KEY_KIMI="nvapi-kimi-key"
NVIDIA_API_KEY_MINIMAX="nvapi-minimax-key"
NVIDIA_API_KEY_NEMOTRON="nvapi-nemotron-key"

# Groq API
GROQ_API_KEY="gsk-your-groq-key"

# Database (Supabase)
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-anon-or-service-key"
```

---

## 🛠️ Run Locally

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
