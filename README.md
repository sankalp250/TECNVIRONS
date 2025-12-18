<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white" alt="LangChain"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

<h1 align="center">🤖 TECNVIRONS</h1>
<h3 align="center">Realtime AI Conversational Backend</h3>

<p align="center">
  <strong>A production-ready backend demonstrating realtime conversational AI with WebSockets, LangGraph orchestration, Groq LLM integration, and Supabase persistence.</strong>
</p>

<p align="center">
  <a href="https://tecnvirons.onrender.com/healthz">
    <img src="https://img.shields.io/badge/Backend-Live-brightgreen?style=flat-square" alt="Backend Status"/>
  </a>
  <a href="https://tecnvirons-git-master-sankalp-singhs-projects-08580eee.vercel.app/">
    <img src="https://img.shields.io/badge/Frontend-Live-blue?style=flat-square" alt="Frontend Status"/>
  </a>
  <a href="https://github.com/sankalp250/TECNVIRONS/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
  </a>
</p>

---

## 📖 Overview

TECNVIRONS is a sophisticated realtime AI backend that streams Groq LLM tokens to clients via WebSockets while maintaining comprehensive session logs in Supabase. The system leverages LangGraph for intelligent routing and tool execution, enabling extensible conversational workflows.

### ✨ Key Features

- 🔄 **Real-time Streaming** — WebSocket-based token streaming for low-latency responses
- 🧠 **LangGraph Orchestration** — Intelligent routing with tool execution capabilities
- 💾 **Persistent Sessions** — Full conversation history stored in Supabase
- ⚡ **Async Architecture** — Non-blocking IO for high concurrency
- 📝 **Auto-Summarization** — Automatic session summaries on disconnect
- 🚀 **Production Ready** — Deployed on Render (backend) + Vercel (frontend)

---

## 🏗️ Architecture

```
┌─────────────────┐     WebSocket      ┌──────────────────────────────────────┐
│                 │◄──────────────────►│           FastAPI Server             │
│   Frontend UI   │    Token Stream    │                                      │
│    (Vanilla)    │                    │  ┌────────────────────────────────┐  │
└─────────────────┘                    │  │     LangGraph Router           │  │
                                       │  │  ┌─────────┐  ┌─────────────┐  │  │
                                       │  │  │Classify │─►│ Tool Node   │  │  │
                                       │  │  └─────────┘  └─────────────┘  │  │
                                       │  │       │              │         │  │
                                       │  │       └──────┬───────┘         │  │
                                       │  │              ▼                 │  │
                                       │  │       ┌─────────────┐          │  │
                                       │  │       │ Prepare     │          │  │
                                       │  │       │ Response    │          │  │
                                       │  │       └─────────────┘          │  │
                                       │  └────────────────────────────────┘  │
                                       │                 │                    │
                                       │                 ▼                    │
                                       │  ┌────────────────────────────────┐  │
                                       │  │        Groq Streamer           │  │
                                       │  │    (LangChain ChatGroq)        │  │
                                       │  └────────────────────────────────┘  │
                                       └──────────────────────────────────────┘
                                                         │
                                                         ▼
                                       ┌──────────────────────────────────────┐
                                       │         Supabase Postgres            │
                                       │  ┌──────────────┐ ┌───────────────┐  │
                                       │  │   sessions   │ │session_events │  │
                                       │  └──────────────┘ └───────────────┘  │
                                       └──────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Groq API Key](https://console.groq.com/)
- [Supabase Project](https://supabase.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/sankalp250/TECNVIRONS.git
cd TECNVIRONS

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your credentials
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ |
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key with insert/update permissions | ✅ |
| `GROQ_MODEL` | Model override (default: `llama-3.1-70b-versatile`) | ❌ |
| `SUPABASE_SCHEMA` | Schema name (default: `public`) | ❌ |

### Database Setup

Execute the following SQL in your Supabase SQL Editor:

```sql
-- Sessions table
CREATE TABLE public.sessions (
  session_id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  start_time TIMESTAMPTZ DEFAULT NOW(),
  end_time TIMESTAMPTZ,
  summary TEXT
);

-- Session events table
CREATE TABLE public.session_events (
  id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES public.sessions(session_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for performance
CREATE INDEX session_events_session_idx 
  ON public.session_events(session_id, occurred_at);
```

### Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Reference

### WebSocket Endpoint

```
ws://localhost:8000/ws/session/{session_id}?user_id={user_id}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | UUID | Unique session identifier |
| `user_id` | String | User identifier |

### Message Format

**Send:**
```json
{ "message": "Your prompt here" }
```
Or plain text: `"Your prompt here"`

**Receive:**
- Streaming tokens as text frames
- `[END_OF_RESPONSE]` marker signals completion

### Health Check

```
GET /healthz
```

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Backend API** | [tecnvirons.onrender.com](https://tecnvirons.onrender.com) |
| **Health Check** | [tecnvirons.onrender.com/healthz](https://tecnvirons.onrender.com/healthz) |
| **Frontend** | [Vercel App](https://tecnvirons-git-master-sankalp-singhs-projects-08580eee.vercel.app/) |
| **WebSocket** | `wss://tecnvirons.onrender.com/ws/session/{session_id}?user_id={user_id}` |

---

## 🧪 Testing

1. **Trigger Tool Execution** — Send prompts containing "weather", "pricing", or "co2"
2. **Verify Persistence** — Check Supabase tables for session and event records
3. **Test Summarization** — Disconnect to trigger automatic summary generation

---

## 📁 Project Structure

```
TECNVIRONS/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py             # Environment configuration
│   ├── main.py               # FastAPI application & WebSocket
│   ├── langgraph_flow.py     # LangGraph routing logic
│   ├── llm_stream.py         # Groq streaming wrapper
│   ├── session_manager.py    # Session lifecycle management
│   └── supabase_client.py    # Async Supabase operations
├── frontend/
│   ├── index.html            # Chat UI
│   ├── style.css             # Styles
│   └── app.js                # WebSocket client logic
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment config
├── env.example               # Environment template
└── README.md
```

---

## 🏛️ Design Decisions

| Decision | Rationale |
|----------|-----------|
| **LangGraph over ad-hoc logic** | Transparent routing, easily extensible for future tools |
| **Streaming-first Groq integration** | Low-latency token delivery without blocking the event loop |
| **Async Supabase wrapper** | Uses `asyncio.to_thread` to prevent synchronous client from blocking |
| **Deterministic automation trigger** | Ensures summaries run exactly once per disconnect |

---

## 🚢 Deployment

### Backend (Render)

1. Create new Web Service from GitHub repo
2. Set environment to **Python**
3. Configure environment variables
4. Render uses `render.yaml` configuration
5. Health check endpoint: `/healthz`

### Frontend (Vercel)

1. Create new project pointing to `frontend/`
2. Framework: **Other** (no build required)
3. Output directory: `frontend`
4. Update WebSocket URL to production endpoint

---

## 🛣️ Roadmap

- [ ] JWT / Supabase Auth integration
- [ ] Extended function-calling with real API integrations
- [ ] Server-Sent Events for analytics dashboards
- [ ] Rate limiting and usage quotas
- [ ] Multi-model support

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/sankalp250">Sankalp Singh</a></strong>
</p>
