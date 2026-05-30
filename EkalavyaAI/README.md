# 🎯 EkalavyaAI — Learn Like a Topper

<div align="center">

![EkalavyaAI Banner](https://img.shields.io/badge/EkalavyaAI-Learn%20Like%20a%20Topper-7C3AED?style=for-the-badge&logo=graduation-cap)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=nextdotjs)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1E40AF?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Claude](https://img.shields.io/badge/Claude_3.5_Sonnet-Primary_AI-D97706?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)](LICENSE)

**India's first AI Education Operating System for CA, JEE & NEET students**

[🚀 Live Demo](#) · [📖 API Docs](#api-documentation) · [🛠 Setup Guide](#quick-start) · [📊 Architecture](#architecture)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Seven-Agent System](#seven-agent-system)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [RAG Pipeline](#rag-pipeline)
- [Deployment](#deployment)
- [Development Roadmap](#development-roadmap)

---

## 🌟 Overview

EkalavyaAI is a **multi-agent AI education platform** that delivers personalized, exam-quality coaching for:

| Exam | Level | Coverage |
|------|-------|----------|
| CA Foundation | Entry Level | Full Agent System |
| CA Intermediate | Mid Level | Full Agent System |
| CA Final | Advanced | Full Agent System |
| JEE Mains + Advanced | Engineering | Full Agent System |
| NEET | Medical | Full Agent System |

### Key Differentiators
- 🧠 **7 Specialized AI Agents** coordinated by LangGraph
- 📝 **Premium Notes** with handwriting font, ruled background, logo
- 🎯 **Anti-Hallucination** 5-layer protection system
- 💾 **Shared Notes Cache** — 90% API cost reduction
- 🌍 **Multi-language** — English, Bengali, Hindi, Tamil, Telugu
- 📊 **Student Memory** — long-term personalization via Pinecone
- 🔄 **Auto-Fallback** — never fails even when primary AI is down

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STUDENT INTERFACE LAYER                          │
│           Next.js 14 (App Router) + Tailwind CSS + PWA              │
│    Web App  │  Mobile PWA  │  Study Chat  │  Notes Library           │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTPS / WebSocket
┌─────────────────────────▼───────────────────────────────────────────┐
│                       API GATEWAY LAYER                              │
│              FastAPI + JWT Auth + Rate Limiting                      │
│         Redis Session  │  Request Router  │  API Versioning          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
│              LangGraph Stateful Multi-Agent Graph                    │
│    Celery Task Queue  │  Agent Coordinator  │  State Management      │
└────┬────────┬──────────┬──────────┬──────────┬───────────┬──────────┘
     │        │          │          │          │           │
┌────▼──┐ ┌──▼───┐ ┌────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌───▼───┐
│SYLLAB.│ │RESRCH│ │  PYQ  │ │TEACHER│ │ NOTES │ │DIGRM  │ │MEMORY │
│AGENT  │ │AGENT │ │ AGENT │ │ AGENT │ │ AGENT │ │AGENT  │ │AGENT  │
│Gemini │ │GPT4o │ │ GPT4o │ │Claude │ │Claude │ │Claude │ │Groq   │
│  1.5  │ │OpenR.│ │ OpenR.│ │  3.5  │ │  3.5  │ │  3.5  │ │Llama  │
└───────┘ └──────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                      AI MODEL LAYER                                  │
│  OpenRouter │ Groq │ Google AI Studio │ Kimi AI │ NVIDIA NIM         │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                    KNOWLEDGE & STORAGE LAYER                         │
│  PostgreSQL  │  Pinecone (Vector)  │  Neo4j (Graph)  │  Redis Cache  │
│              │  ElasticSearch      │  AWS S3 / R2    │               │
└─────────────────────────────────────────────────────────────────────┘
```

### Request Flow — Notes Generation

```mermaid
sequenceDiagram
    participant S as Student
    participant API as FastAPI
    participant ORC as LangGraph Orchestrator
    participant MEM as Memory Agent
    participant SYL as Syllabus Agent
    participant RES as Research Agent
    participant PYQ as PYQ Agent
    participant TCH as Teacher Agent (Claude)
    participant NTS as Notes Agent (Claude)
    participant DGM as Diagram Agent (Claude)
    participant PDF as WeasyPrint
    participant S3 as AWS S3

    S->>API: POST /api/v1/notes/generate
    API->>ORC: Route to orchestrator
    ORC->>MEM: Read student profile
    MEM-->>ORC: Student context (level, weak chapters, language)
    
    par Parallel Execution (~3 seconds)
        ORC->>SYL: Get syllabus structure
        ORC->>RES: RAG retrieval (top-8 chunks)
        ORC->>PYQ: Get PYQ patterns + frequency
    end
    
    ORC->>ORC: Aggregate + deduplicate outputs
    ORC->>TCH: Generate teacher voice content
    TCH-->>ORC: Human-style educational content
    ORC->>NTS: Format into notes structure
    NTS-->>ORC: Structured JSON notes
    ORC->>DGM: Detect visual triggers → generate SVGs
    DGM-->>ORC: Inline SVG diagrams
    ORC->>ORC: Anti-hallucination validation (5 layers)
    ORC->>PDF: Render HTML → PDF (handwriting font + logo)
    PDF-->>S3: Upload PDF + DOCX
    ORC->>MEM: Update student profile + revision schedule
    ORC-->>API: Stream notes page-by-page
    API-->>S: SSE stream → rendered notes
```

### LangGraph Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> IntentClassification
    IntentClassification --> NotesGeneration: intent=notes
    IntentClassification --> QuestionSolving: intent=question
    IntentClassification --> PYQPractice: intent=pyq
    IntentClassification --> GeneralChat: intent=general
    
    NotesGeneration --> MemoryRead
    MemoryRead --> ParallelAgents
    
    state ParallelAgents {
        [*] --> SyllabusAgent
        [*] --> ResearchAgent
        [*] --> PYQAgent
    }
    
    ParallelAgents --> Aggregation
    Aggregation --> TeacherAgent
    TeacherAgent --> NotesAgent
    NotesAgent --> DiagramAgent
    DiagramAgent --> AntiHallucination
    AntiHallucination --> PDFGeneration: confidence >= 0.75
    AntiHallucination --> ExpertReview: confidence < 0.75
    ExpertReview --> PDFGeneration
    PDFGeneration --> MemoryWrite
    MemoryWrite --> StreamResponse
    StreamResponse --> [*]
```

---

## 🤖 Seven-Agent System

```mermaid
graph TB
    subgraph "Agent 1 — Syllabus Agent"
        SA[Gemini 1.5 Pro<br/>1M context window]
        SA --> SA1[Read ICAI PDFs]
        SA --> SA2[Build Knowledge Graph]
        SA --> SA3[Topic Importance Scoring]
    end
    
    subgraph "Agent 2 — Research Agent"
        RA[GPT-4o via OpenRouter]
        RA --> RA1[Pinecone Vector Search top-20]
        RA --> RA2[ElasticSearch BM25 top-20]
        RA --> RA3[Cohere Rerank → top-8]
    end
    
    subgraph "Agent 3 — PYQ Agent"
        PA[GPT-4o via OpenRouter]
        PA --> PA1[10 Years PYQ Analysis]
        PA --> PA2[Topic Frequency Mapping]
        PA --> PA3[Examiner Pattern Detection]
    end
    
    subgraph "Agent 4 — Teacher Agent ⭐ CRITICAL"
        TA[Claude 3.5 Sonnet<br/>PRIMARY - NO EXCEPTIONS]
        TA --> TA1[Human Voice Generation]
        TA --> TA2[Level Adaptation W/A/T]
        TA --> TA3[Mnemonics + Analogies]
    end
    
    subgraph "Agent 5 — Notes Agent"
        NA[Claude 3.5 Sonnet]
        NA --> NA1[Structured JSON Notes]
        NA --> NA2[PDF Generation WeasyPrint]
        NA --> NA3[DOCX Generation python-docx]
    end
    
    subgraph "Agent 6 — Diagram Agent"
        DA[Claude 3.5 Sonnet]
        DA --> DA1[SVG T-Accounts CA]
        DA --> DA2[Physics Diagrams JEE]
        DA --> DA3[Biology Charts NEET]
    end
    
    subgraph "Agent 7 — Memory Agent"
        MA[Groq Llama 3.1 70B<br/>ALWAYS FREE]
        MA --> MA1[PostgreSQL Profile R/W]
        MA --> MA2[Pinecone Semantic Memory]
        MA --> MA3[Spaced Repetition SM-2]
    end
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI 0.111 | Async API server |
| Agent Orchestration | LangGraph 0.2 | Multi-agent coordination |
| Task Queue | Celery 5.3 + Redis | Background jobs |
| AI Routing | OpenRouter | Claude, GPT-4o, Gemini via one key |
| Fast/Free AI | Groq | Llama 3.1 70B — always free |
| Vector DB | Pinecone | RAG + semantic memory |
| Search | ElasticSearch | BM25 hybrid retrieval |
| Graph DB | Neo4j | Syllabus knowledge graph |
| PDF Generation | WeasyPrint | HTML→PDF with custom fonts |
| DOCX | python-docx | Word document generation |
| Reranking | Cohere | RAG quality improvement |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 14 (App Router) | Web application |
| Styling | Tailwind CSS + shadcn/ui | UI design system |
| State | Zustand | Client state management |
| Auth | Supabase Auth | Email + Google OAuth |
| Streaming | SSE / WebSocket | Real-time notes streaming |
| Animations | Framer Motion | Smooth UI transitions |

### Infrastructure
| Service | Provider | Cost |
|---------|----------|------|
| Backend | AWS EC2 Mumbai (ap-south-1) | Free tier → ₹2,500/mo |
| Frontend | Vercel | Free tier |
| Database | AWS RDS PostgreSQL | Free tier 12mo |
| Cache | AWS ElastiCache Redis | Free tier 12mo |
| Storage | Cloudflare R2 | ~₹200-500/mo |
| CDN | Cloudflare | Free |
| Domain | Cloudflare | ₹700/year |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/ekalavya-ai.git
cd ekalavya-ai

# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

### 2. Configure Environment

Edit `.env` with your API keys (see [Environment Variables](#environment-variables))

### 3. Start with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed initial data (syllabus structure)
docker-compose exec backend python -m scripts.seed_data

# Ingest ICAI PDFs (place PDFs in /data/source_pdfs/)
docker-compose exec backend python -m scripts.ingest_pdfs
```

### 4. Manual Setup (Development)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 5. Start Celery Worker

```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info
celery -A tasks.celery_app beat --loglevel=info  # Scheduler
```

### Access Points
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 🔑 Environment Variables

```env
# ============================================
# AI MODEL APIs
# ============================================
OPENROUTER_API_KEY=sk-or-...          # openrouter.ai
GROQ_API_KEY=gsk_...                  # console.groq.com
GOOGLE_AI_STUDIO_API_KEY=AIza...      # aistudio.google.com
NVIDIA_NIM_API_KEY=nvapi-...          # build.nvidia.com
COHERE_API_KEY=...                    # cohere.com

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ekalavya
REDIS_URL=redis://localhost:6379/0
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...

# ============================================
# AUTH & SECURITY
# ============================================
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# ============================================
# STORAGE
# ============================================
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=ekalavya-notes
AWS_REGION=ap-south-1
CLOUDFLARE_R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
CLOUDFLARE_R2_ACCESS_KEY=...
CLOUDFLARE_R2_SECRET_KEY=...

# ============================================
# PAYMENT
# ============================================
CASHFREE_APP_ID=...
CASHFREE_SECRET_KEY=...
CASHFREE_ENV=TEST  # Change to PROD for production

# ============================================
# EMAIL
# ============================================
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@ekalavya.ai

# ============================================
# MONITORING
# ============================================
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=ekalavya-ai
SENTRY_DSN=https://xxx@sentry.io/xxx

# ============================================
# APP CONFIG
# ============================================
ENVIRONMENT=development  # production
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 📡 API Documentation

### Authentication
```
POST   /api/v1/auth/signup          Register new student
POST   /api/v1/auth/login           Login with email/password
POST   /api/v1/auth/google          Google OAuth login
POST   /api/v1/auth/refresh         Refresh JWT token
POST   /api/v1/auth/logout          Logout
```

### Notes
```
POST   /api/v1/notes/generate       Generate chapter notes (SSE stream)
GET    /api/v1/notes/               List student's notes
GET    /api/v1/notes/{id}           Get specific note
GET    /api/v1/notes/{id}/pdf       Download PDF
GET    /api/v1/notes/{id}/docx      Download DOCX
GET    /api/v1/notes/cache/{key}    Check cache hit
```

### Chat (Doubt Solving)
```
POST   /api/v1/chat/message         Send question (SSE stream)
GET    /api/v1/chat/history         Chat history
DELETE /api/v1/chat/session/{id}    Clear session
```

### Practice (PYQ)
```
GET    /api/v1/practice/questions   Get PYQ questions (filtered)
POST   /api/v1/practice/attempt     Submit answer
GET    /api/v1/practice/feedback    AI feedback on attempt
GET    /api/v1/practice/mistakes    Student mistake history
```

### Progress
```
GET    /api/v1/progress/readiness   Readiness score (0-100%)
GET    /api/v1/progress/syllabus    Syllabus coverage heatmap
GET    /api/v1/progress/revision    Upcoming revision schedule
GET    /api/v1/progress/report      Weekly AI report
```

### Student
```
GET    /api/v1/student/profile      Get student profile
PUT    /api/v1/student/profile      Update profile
GET    /api/v1/student/credits      Credit balance
POST   /api/v1/student/referral     Apply referral code
GET    /api/v1/student/referral     Get referral code + stats
```

### Admin
```
GET    /api/v1/admin/cache          Manage notes cache
POST   /api/v1/admin/ingest         Trigger PDF ingestion
GET    /api/v1/admin/analytics      Platform analytics
POST   /api/v1/admin/verify-notes   Expert verification
```

---

## 🗄️ Database Schema

```mermaid
erDiagram
    USERS {
        uuid id PK
        string name
        string email
        string phone
        string plan
        timestamp created_at
    }
    
    STUDENT_PROFILES {
        uuid id PK
        uuid user_id FK
        string exam_target
        date exam_date
        string level
        string language
        json weak_chapters
        json learning_style
    }
    
    CHAPTERS {
        uuid id PK
        string exam
        string subject
        int chapter_no
        string name
        float importance_score
    }
    
    NOTES {
        uuid id PK
        uuid student_id FK
        uuid chapter_id FK
        string language
        json content_json
        string pdf_url
        string docx_url
        float quality_score
        bool cached
    }
    
    MASTER_NOTES_CACHE {
        string cache_key PK
        uuid chapter_id FK
        string language
        string pdf_url
        float quality_score
        bool expert_verified
        int view_count
    }
    
    QUESTIONS {
        uuid id PK
        string exam
        int year
        int marks
        uuid chapter_id FK
        text question_text
        text solution
        text explanation
    }
    
    REVISION_SCHEDULE {
        uuid id PK
        uuid student_id FK
        uuid chapter_id FK
        date due_date
        int sm2_level
        int priority
    }
    
    CREDITS {
        uuid id PK
        uuid student_id FK
        int balance
        json transaction_history
    }
    
    USERS ||--|| STUDENT_PROFILES : has
    USERS ||--o{ NOTES : creates
    CHAPTERS ||--o{ NOTES : covers
    CHAPTERS ||--|| MASTER_NOTES_CACHE : cached_as
    CHAPTERS ||--o{ QUESTIONS : contains
    USERS ||--o{ REVISION_SCHEDULE : has
    USERS ||--|| CREDITS : owns
```

---

## 🔍 RAG Pipeline

```mermaid
flowchart LR
    subgraph INGESTION["📥 Ingestion Pipeline (Offline)"]
        PDF[Source PDFs\nICAI, NCERT] --> PARSE[PyMuPDF\n+ Gemini Vision]
        PARSE --> CLEAN[Clean\nNormalize]
        CLEAN --> CHUNK[Semantic Chunking\n300-600 tokens]
        CHUNK --> EMBED[voyage-2\nEmbeddings]
        EMBED --> STORE[Pinecone\n+ PostgreSQL\n+ ElasticSearch]
    end
    
    subgraph RETRIEVAL["🔍 Retrieval Pipeline (Real-time)"]
        Q[Student Query] --> ENRICH[Query Enrichment\n+ exam context]
        ENRICH --> VECT[Pinecone\nVector top-20]
        ENRICH --> BM25[ElasticSearch\nBM25 top-20]
        VECT --> RERANK[Cohere Rerank\n→ top-8]
        BM25 --> RERANK
        RERANK --> DEDUP[Dedup\n+ Sort by\nCredibility]
        DEDUP --> CTX[Context Assembly\n+ Citations]
        CTX --> LLM[LLM Generation\nGrounded Only]
    end
```

---

## 🚀 Deployment

### AWS Production Setup

```bash
# 1. Launch EC2 t3.medium (Mumbai ap-south-1)
# 2. Install Docker
sudo apt update && sudo apt install docker.io docker-compose -y

# 3. Clone repo
git clone https://github.com/yourusername/ekalavya-ai.git

# 4. Set environment variables
cp .env.example .env
nano .env  # Fill all values

# 5. Launch
docker-compose -f docker-compose.prod.yml up -d

# 6. Setup SSL with Certbot
sudo certbot --nginx -d api.ekalavya.ai
```

### Environment Targets

| Environment | Backend | Frontend | Database |
|------------|---------|----------|----------|
| Development | localhost:8000 | localhost:3000 | localhost:5432 |
| Staging | staging-api.ekalavya.ai | staging.ekalavya.ai | AWS RDS |
| Production | api.ekalavya.ai | ekalavya.ai | AWS RDS Multi-AZ |

---

## 📅 Development Roadmap

```mermaid
gantt
    title EkalavyaAI Development Timeline (16 Weeks)
    dateFormat  YYYY-MM-DD
    section Phase 0 - Foundation
    FastAPI Setup          :p0a, 2025-01-01, 7d
    Database + Redis       :p0b, after p0a, 3d
    LangGraph Framework    :p0c, after p0b, 4d
    PDF Ingestion Start    :p0d, after p0c, 3d
    
    section Phase 1 - CA Foundation AI
    Syllabus Agent         :p1a, after p0d, 5d
    Research Agent + RAG   :p1b, after p1a, 5d
    Teacher Agent (Claude) :p1c, after p1b, 5d
    Notes Agent + PDF      :p1d, after p1c, 6d
    
    section Phase 2 - PYQ + Quality
    PYQ Database           :p2a, after p1d, 4d
    PYQ Agent              :p2b, after p2a, 3d
    Diagram Agent          :p2c, after p2b, 4d
    Anti-Hallucination     :p2d, after p2c, 3d
    
    section Phase 3 - Memory + Multi-lang
    Memory Agent Full      :p3a, after p2d, 5d
    Onboarding Flow        :p3b, after p3a, 3d
    Referral + Credits     :p3c, after p3b, 4d
    Bengali + Hindi        :p3d, after p3c, 2d
    
    section Phase 4 - JEE + NEET
    JEE Syllabus + NCERT   :p4a, after p3d, 5d
    NEET Syllabus          :p4b, after p4a, 4d
    Diagram Templates      :p4c, after p4b, 5d
    Code Interpreter       :p4d, after p4c, 2d
    
    section Phase 5 - Full Launch
    CA Inter + Final       :p5a, after p4d, 5d
    Next.js Frontend       :p5b, after p5a, 5d
    Payment Integration    :p5c, after p5b, 3d
    Beta 50 Students       :p5d, after p5c, 7d
```

---

## 📁 Project Structure

```
EkalavyaAI/
├── backend/
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Settings + environment config
│   ├── requirements.txt           # Python dependencies
│   ├── alembic.ini               # DB migration config
│   ├── migrations/               # Alembic migrations
│   ├── api/
│   │   ├── dependencies.py       # JWT auth, DB session injection
│   │   ├── middleware.py         # CORS, rate limiting, logging
│   │   └── routes/
│   │       ├── auth.py           # Authentication endpoints
│   │       ├── notes.py          # Notes generation + download
│   │       ├── chat.py           # Doubt solving chat
│   │       ├── practice.py       # PYQ practice
│   │       ├── progress.py       # Analytics + readiness
│   │       └── student.py        # Profile + credits + referral
│   ├── agents/
│   │   ├── base.py               # Base agent class + fallback logic
│   │   ├── orchestrator.py       # LangGraph state machine
│   │   ├── syllabus_agent.py     # Agent 1: Gemini 1.5 Pro
│   │   ├── research_agent.py     # Agent 2: GPT-4o + RAG
│   │   ├── pyq_agent.py          # Agent 3: PYQ patterns
│   │   ├── teacher_agent.py      # Agent 4: Claude 3.5 Sonnet ⭐
│   │   ├── notes_agent.py        # Agent 5: Notes formatting
│   │   ├── diagram_agent.py      # Agent 6: SVG generation
│   │   └── memory_agent.py       # Agent 7: Groq Llama
│   ├── rag/
│   │   ├── ingestion.py          # PDF parsing + chunking + indexing
│   │   ├── retrieval.py          # Hybrid vector + BM25 retrieval
│   │   ├── chunking.py           # Semantic chunking strategies
│   │   └── embeddings.py         # Embedding model wrapper
│   ├── models/
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── user.py               # User + Profile models
│   │   ├── notes.py              # Notes + Cache models
│   │   ├── questions.py          # PYQ + Attempts models
│   │   └── memory.py             # Study sessions + Mistakes
│   ├── services/
│   │   ├── pdf_generator.py      # WeasyPrint HTML→PDF
│   │   ├── cache_service.py      # Master notes cache logic
│   │   ├── payment_service.py    # Cashfree integration
│   │   ├── email_service.py      # Resend email service
│   │   └── anti_hallucination.py # 5-layer validation system
│   ├── tasks/
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── memory_tasks.py       # Nightly memory compression
│   │   └── report_tasks.py       # Weekly AI report generation
│   └── utils/
│       ├── model_router.py       # AI model + fallback routing
│       └── logger.py             # Structured logging
├── frontend/
│   ├── src/app/
│   │   ├── layout.tsx            # Root layout + providers
│   │   ├── page.tsx              # Landing page
│   │   ├── dashboard/page.tsx    # Student dashboard
│   │   ├── chat/page.tsx         # AI study chat
│   │   ├── notes/page.tsx        # Notes library
│   │   ├── practice/page.tsx     # PYQ practice
│   │   ├── progress/page.tsx     # Analytics
│   │   └── onboarding/page.tsx   # 5-step onboarding
│   ├── src/components/
│   │   ├── layout/               # Navbar, Sidebar, Footer
│   │   ├── features/             # Domain-specific components
│   │   └── ui/                   # Reusable UI primitives
│   ├── src/lib/
│   │   ├── api.ts               # API client + streaming
│   │   └── utils.ts             # Shared utilities
│   └── src/types/index.ts        # TypeScript type definitions
├── docker-compose.yml             # Development services
├── docker-compose.prod.yml        # Production config
├── .env.example                   # Environment template
├── .gitignore
└── README.md
```

---

## 🤝 Contributing

This is a proprietary platform. Internal team only.

## 📄 License

Proprietary — EkalavyaAI 2025. All Rights Reserved.

---

<div align="center">
Made with ❤️ for India's exam warriors | <strong>EkalavyaAI — Learn Like a Topper</strong>
</div>
