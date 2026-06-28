# ⚡ Vextral AI

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Storage-3ecf8e?style=for-the-badge&logo=supabase)](https://supabase.com)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-Multi--Model-76b900?style=for-the-badge&logo=nvidia)](https://build.nvidia.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=for-the-badge&logo=vercel)](https://vextral-ai.vercel.app/)

A premium, production-ready, multi-tenant RAG platform that allows users to upload complex documents and chat with them using advanced AI — styled in a custom, dark Neumorphic design system.

🔗 **Live URL**: [https://vextral-ai.vercel.app/](https://vextral-ai.vercel.app/)

---

## 🚀 Key Features

* 🧬 **Zero-Loss Native Scan RAG**: Swapped heavy, lossy vector chunk indexing (removed Qdrant and LanceDB) for **Gemini File API direct document scans**. The platform handles full multi-modal files (up to 1M tokens) natively, preserving tables, layouts, charts, and cross-references exactly as they exist.
* 🧠 **Flagship Multi-Model Grid**: Integrated the latest top-tier models via NVIDIA NIM:
  - **`nvidia/nemotron-3-ultra-550b-a55b`**: Powerful 550B reasoning model with chain-of-thought logs enabled.
  - **`minimaxai/minimax-m3`**: Highly capable multimodal model (text, image, video).
  - **`z-ai/glm-5.1`**: Expert coding, software debugging, and logical layout expert.
  - **`moonshotai/kimi-k2.6`**: Multi-turn general conversation specialist.
  - **`Gemini 3.5 & Gemma 4`**: Primary document readers with full multimodal visual perception.
* 💡 **Interactive Thinking Drawer**: Built a custom collapsible UI panel that captures Nemotron's logical chain-of-thought tokens, displaying live reasoning logs inside a glassmorphic expander drawer before the final answer is shown.
* 🎨 **Dark Neumorphic (Soft UI) System**: Refactored the entire interface (Home, Chat, and Documents) into a state-of-the-art dark neumorphic layout with realistic double-shadow elements, inset typing inputs, and beveled pill-styled metadata badges.
* 📦 **Cloud-Native Storage**: Integrated the HTTP-based **Supabase SDK client** and Supabase Private Storage Buckets to handle document lifetime registrations and automatic Google URI renewals (re-uploading expired 48-hour links seamlessly behind the scenes).

---

## 🏗️ Architecture

```
                                  ┌───────────────────────────┐
                                  │    Next.js 15 Frontend    │
                                  │  • Neumorphic Design      │
                                  │  • Collapsible Think Box  │
                                  │  • Auto-Expanding Input   │
                                  └─────────────#─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │      FastAPI Backend      │
                                  │                           │
                                  │   ┌───────────────────┐   │
                                  │   │  Chat & Ask API   │   │
                                  │   └─────────#─────────┘   │
                                  │             │             │
                                  │             ▼             │
                                  │   ┌───────────────────┐   │
                                  │   │ Gemini File RAG   │   │
                                  │   │ • 48h Auto-Refresh│   │
                                  │   └─────────#─────────┘   │
                                  └─────────────#─────────────┘
                                                │
                                       ┌────────┴────────┐
                                       ▼                 ▼
                        ┌─────────────────────┐   ┌─────────────────────┐
                        │ NVIDIA NIM Endpoint │   │  Supabase Cloud     │
                        │ • Nemotron 550B     │   │  • Postgres Metadata│
                        │ • MiniMax-M3        │   │  • Storage Buckets  │
                        └─────────────────────┘   └─────────────────────┘
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
Open **[http://localhost:3000](http://localhost:3000)** and start chatting!

Built with ❤️ by **Hemanth Kumar G**
