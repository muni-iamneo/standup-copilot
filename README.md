# 🚀 StandupCopilot

<div align="center">

![StandupCopilot Banner](https://img.shields.io/badge/StandupCopilot-AI%20Voice%20Standups-6366f1?style=for-the-badge&logo=robot&logoColor=white)

**AI-Powered Voice Standup Meetings with Real-Time Integration**

Transform your daily standups with AI voice facilitation, automatic Linear updates, and intelligent Slack summaries.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice%20AI-black?style=flat-square)](https://elevenlabs.io/)
[![Jitsi](https://img.shields.io/badge/Jitsi-Meet-97979A?style=flat-square&logo=jitsi)](https://jitsi.org/)

</div>

---

## ✨ What is StandupCopilot?

StandupCopilot is an **AI-powered standup automation platform** that conducts voice-based standup meetings using ElevenLabs AI, automatically extracts updates, posts them to Linear, and sends beautiful summaries to Slack. No more manual note-taking or forgotten updates!

### 🎯 Key Highlights

- 🎙️ **AI Voice Agent** conducts standups via Jitsi video calls
- 📝 **Automatic Transcription** of all conversations
- 🔄 **Real-time Linear Updates** with comments and status changes
- 📊 **Intelligent Slack Summaries** in digest format
- 🤖 **LLM-Powered Extraction** using Claude or Gemini 3
- 📅 **Scheduled Automation** with APScheduler

---

## 🌟 Features

### 🎤 Voice-First Standup Experience
- **ElevenLabs AI Agent** asks team members about their assigned issues
- **Natural Conversation** - speak naturally, AI understands context
- **Real-time Transcription** - see what's being discussed live
- **Jitsi Video Integration** - optional video for remote teams
- **WebSocket Audio Streaming** - low-latency voice interaction

### 🧠 Intelligent Processing
- **LLM Extraction** - Claude Haiku 4.5 or Gemini 3 extracts structured updates
- **Automatic Issue Matching** - links discussions to Linear issues
- **Blocker Detection** - identifies and flags blockers automatically
- **Escalation Recommendations** - suggests when issues need escalation
- **Status Inference** - determines issue status from conversation

### � Linear Integration
- **Auto-fetch Active Issues** - pulls issues assigned to team members
- **Post Comments** - adds standup updates as Linear comments
- **Status Updates** - updates issue status based on discussion
- **Escalation Tickets** - creates new tickets for escalated issues
- **Full Audit Trail** - tracks all automated changes

### � Slack Integration
- **Standup Notifications** - alerts team when standup starts
- **Simple Digest Format** - clean, readable summary format:
  ```
  📋 Daily Standup Digest — Dec 11
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  Issue: NEO-10 (Rate Limit UI changes)
  Status: Progressing
  ETA: Today EOD
  Blockers: None
  Action: Complete styling
  Working Person: manikandan@iamneo.ai
  ```
- **Channel Notifications** - posts to configured Slack channels
- **Rich Formatting** - uses Slack markdown for clarity

### 📊 Dashboard & Analytics
- **Beautiful Blue Gradient Hero** - modern, professional UI
- **Real-time Stats** - total standups, active count
- **Active Standup Cards** - join ongoing meetings
- **Upcoming Schedule** - see what's next
- **Clean White Cards** - easy-to-read design

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **APScheduler** - Job scheduling
- **WebSockets** - Real-time audio streaming
- **httpx** - Async HTTP client

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Lucide Icons** - Icon library

### AI & Voice
- **ElevenLabs** - Conversational AI agent
- **Anthropic Claude Haiku 4.5** - LLM reasoning
- **Gemini 3** - Alternative LLM
- **WebRTC** - Audio capture

### Integrations
- **Linear API** - Issue tracking (GraphQL)
- **Slack API** - Team communication
- **Jitsi Meet** - Video conferencing
- **8x8 Jitsi** - Hosted Jitsi service

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     StandupCopilot Platform                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React UI   │◄──►│  FastAPI     │◄──►│  PostgreSQL  │      │
│  │  TypeScript  │    │   Python     │    │   Database   │      │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘      │
│         │                   │                                    │
│         │ WebSocket         │ REST APIs                          │
│         ▼                   ▼                                    │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              External Services Layer                 │        │
│  ├──────────┬──────────┬──────────┬──────────┬─────────┤        │
│  │ ElevenLabs│  Linear  │  Slack   │  Jitsi   │ Claude  │        │
│  │ Voice AI │   API    │   API    │   Meet   │ Haiku   │        │
│  │ (Agent)  │ (GraphQL)│  (REST)  │  (WebRTC)│  4.5    │        │
│  └──────────┴──────────┴──────────┴──────────┴─────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Audio Flow Architecture

```
User Microphone → Browser → WebSocket → Backend → ElevenLabs Agent
                                                         ↓
                                                    AI Response
                                                         ↓
Backend ← WebSocket ← Browser ← Audio Playback ← ElevenLabs
   ↓
Transcript Storage → LLM Processing → Linear Updates → Slack Summary
```

---

## 📂 Project Structure

```
standup-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app + WebSocket
│   │   ├── config.py                    # Environment configuration
│   │   ├── database.py                  # PostgreSQL connection
│   │   ├── models.py                    # SQLAlchemy models
│   │   ├── schemas.py                   # Pydantic schemas
│   │   ├── services/
│   │   │   ├── elevenlabs_service.py    # ElevenLabs integration
│   │   │   ├── voice_endpoint.py        # Voice WebSocket handler
│   │   │   ├── linear_service.py        # Linear GraphQL client
│   │   │   ├── slack_service.py         # Slack Web API
│   │   │   ├── reasoning_service.py     # LLM extraction (Claude/GPT)
│   │   │   ├── standup_summary_service.py # Summary generation
│   │   │   ├── jitsi_service.py         # Jitsi URL generation
│   │   │   └── scheduler_service.py     # APScheduler jobs
│   │   └── routes/
│   │       ├── standup.py               # Standup CRUD
│   │       ├── config.py                # Configuration endpoints
│   │       └── analytics.py             # Dashboard stats
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── DashboardPage.tsx        # Blue gradient hero + stats
    │   │   ├── ConfigPage.tsx           # Schedule standup wizard
    │   │   ├── StandupMeetingPage.tsx   # Voice meeting UI (dark theme)
    │   │   └── HistoryPage.tsx          # Past standups
    │   ├── components/
    │   │   ├── Common/
    │   │   │   ├── Sidebar.tsx          # Dark sidebar with copilot icon
    │   │   │   └── Navbar.tsx           # Light navbar
    │   │   └── Dashboard/
    │   ├── services/
    │   │   └── audioPlaybackService.ts  # Audio playback management
    │   ├── api/
    │   │   └── client.ts                # API client
    │   └── types/
    │       └── index.ts                 # TypeScript types
    ├── assets/
    │   └── copilot.svg                  # Custom logo
    └── package.json
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **API Keys:**
  - ElevenLabs API key
  - Linear API key
  - Slack Bot token
  - Anthropic API key (or OpenAI)
  - Jitsi domain (optional)

### 1. Clone Repository

```bash
git clone https://github.com/muni-iamneo/standup-copilot.git
cd standup-copilot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb standupcopilot

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run migrations
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 4. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

Create `backend/.env`:

```env
# Application
APP_NAME=StandupCopilot
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/standupcopilot

# Linear
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
LINEAR_API_URL=https://api.linear.app/graphql

# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx
SLACK_APP_ID=your_app_id
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret

# ElevenLabs
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx
ELEVENLABS_AGENT_ID=agent_xxxxxxxxxxxxx

# Jitsi (optional - uses 8x8 hosted)
JITSI_DOMAIN=8x8.vc
JITSI_APP_ID=vpaas-magic-cookie-xxxxxxxxxxxxx

# LLM (choose one)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
LLM_PROVIDER=anthropic  # or "openai"

# CORS
CORS_ORIGINS=["http://localhost:5173"]
```

### ElevenLabs Agent Configuration

Configure your ElevenLabs agent with:

**System Prompt:**
```
You are Neo, an AI standup moderator.

TEAM ISSUES:
{{issues_list}}

RULES:
1. Ask for user's name
2. Match their name to ASSIGNEE field
3. Use EXACT issue ID and TITLE from the list
4. NEVER invent fake issues
5. Discuss: status, blockers, ETA
```

**Dynamic Variables:**
- `issues_list` - Populated at runtime with team issues

See `docs/elevenlabs_agent_config.md` for full configuration.

---

## 🔄 How It Works

### 1. Schedule Standup
1. Select Linear team
2. Choose Slack channel
3. Pick date/time
4. Select team members
5. Auto-fetch or manually select issues

### 2. Standup Execution
1. At scheduled time, Slack notification sent
2. Team joins Jitsi meeting
3. AI agent starts conversation
4. Agent asks about each assigned issue
5. Team members respond naturally
6. Real-time transcription displayed

### 3. Automatic Processing
1. LLM extracts structured data from conversation
2. Matches discussions to Linear issues
3. Posts comments to Linear
4. Updates issue statuses
5. Creates escalation tickets if needed

### 4. Summary Generation
1. Generates digest format summary
2. Posts to Slack channel
3. Stores in database
4. Available in dashboard

---

## � Slack Summary Format

```
📋 Daily Standup Digest — Dec 11

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: NEO-12 (Backend - Ops & Telemetry)
Status: Progressing
ETA: End of week
Blockers: None
Action: Complete Prometheus integration
Working Person: muniyappan.mani@iamneo.ai

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: NEO-10 (Rate Limit UI changes)
Status: Blocked 🔴
Blockers: Waiting for API endpoint
Working Person: manikandan@iamneo.ai

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 Escalations Created:
• NEO-13: Created for NEO-10
```

---

## 🎨 UI Design

### Dashboard (Light Theme)
- **Blue gradient hero** with StandupCopilot branding
- **Stats cards** showing total standups and active count
- **White cards** for active and upcoming standups
- **Clean, professional** design

### Meeting Page (Dark Theme)
- **Dark background** (#0a0a0f, #0f0f1a)
- **White text** for high contrast
- **Jitsi video embed** for face-to-face
- **Live transcript sidebar** showing conversation
- **Voice controls** (mute, video, end call)

### Sidebar
- **Dark gradient** background
- **Custom copilot icon** (purple SVG)
- **Minimal navigation** (Dashboard, Schedule)

---

## 📖 API Documentation

### Key Endpoints

#### Voice WebSocket
```
WS /standup/{id}/voice?team_id={team_id}&slack_channel_id={channel_id}
```
Handles real-time audio streaming and transcription.

#### Standup Management
- `POST /api/standups/configs` - Create configuration
- `GET /api/standups/configs` - List configurations
- `GET /api/analytics/dashboard` - Dashboard stats
- `GET /api/analytics/active` - Active standups

#### Integration Health
- `GET /api/config/health` - Check Linear/Slack connectivity
- `GET /api/config/linear/teams` - Get Linear teams
- `GET /api/config/slack/channels` - Get Slack channels

Full API docs: http://localhost:8000/docs

---

## � Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production

```bash
# Backend
cd backend
docker build -t standupcopilot-backend .

# Frontend
cd frontend
npm run build
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

MIT License - see LICENSE file for details.

---

## � Acknowledgments

Built with amazing tools:
- [ElevenLabs](https://elevenlabs.io/) - Conversational AI
- [Linear](https://linear.app/) - Issue tracking
- [Slack](https://slack.com/) - Team communication
- [Jitsi](https://jitsi.org/) - Video conferencing
- [Anthropic](https://anthropic.com/) - Claude AI
- [FastAPI](https://fastapi.tiangolo.com/) - Python framework
- [React](https://react.dev/) - UI framework

---

<div align="center">

**Built with ❤️ for better standups**

[Report Bug](https://github.com/muni-iamneo/standup-copilot/issues) • [Request Feature](https://github.com/muni-iamneo/standup-copilot/issues)

</div>
