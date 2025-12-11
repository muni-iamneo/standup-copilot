# 🤖 StandupAI

<div align="center">

![StandupAI Banner](https://img.shields.io/badge/StandupAI-AI%20Powered%20Standups-6366f1?style=for-the-badge&logo=robot&logoColor=white)

**AI-Powered Standup Automation Platform**

Automate your daily standups with Linear integration, Slack notifications, Jitsi meetings, and intelligent issue tracking powered by AI.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

</div>

---

## 🌟 Features

### 📋 **Complete Standup Automation**
- Schedule standups with team, time, and channel configuration
- Auto-fetch active issues from Linear or manually select specific ones
- Automatic Jitsi meeting URL generation
- Slack notifications with rich formatting

### 🧠 **AI-Powered Intelligence**
- ElevenLabs integration for AI voice facilitation
- LLM-based transcript extraction (OpenAI GPT-4 / Anthropic Claude)
- Automatic status detection and blocker identification
- Smart escalation recommendations

### 📊 **Real-Time Linear Updates**
- Automatic comments posted to Linear issues
- Status updates based on standup discussions
- Automatic escalation ticket creation
- Full audit trail of all updates

### 📈 **Comprehensive Analytics**
- Dashboard with key metrics
- Blocked issues trend analysis
- Escalation tracking over time
- Team performance insights

### 📧 **PM Summary Generation**
- Automatic summary generation after standup completion
- Slack DM delivery to PMs
- Beautiful HTML email reports
- Progress, blocked, and at-risk categorization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        StandupAI Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React UI   │◄──►│  FastAPI     │◄──►│  PostgreSQL  │      │
│  │  (Frontend)  │    │  (Backend)   │    │  (Database)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                    │
│         │                   ▼                                    │
│         │    ┌─────────────────────────────────────────┐        │
│         │    │           External Services             │        │
│         │    ├─────────┬─────────┬─────────┬──────────┤        │
│         │    │ Linear  │  Slack  │ Jitsi   │ElevenLabs│        │
│         │    │  API    │  API    │ Meet    │   TTS    │        │
│         │    └─────────┴─────────┴─────────┴──────────┘        │
│         │                   │                                    │
│         │                   ▼                                    │
│         │    ┌─────────────────────────────────────────┐        │
│         │    │         AI/LLM Services                 │        │
│         │    │   OpenAI GPT-4 / Anthropic Claude       │        │
│         │    └─────────────────────────────────────────┘        │
│         │                                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
standup-ai/
├── backend/                          # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── main.py                   # FastAPI app + CORS
│   │   ├── config.py                 # Environment config
│   │   ├── database.py               # PostgreSQL + SQLAlchemy
│   │   ├── models.py                 # Database models
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── services/
│   │   │   ├── linear_service.py     # Linear GraphQL integration
│   │   │   ├── slack_service.py      # Slack Web API
│   │   │   ├── elevenlabs_service.py # ElevenLabs TTS/STT
│   │   │   ├── jitsi_service.py      # Jitsi URL generation
│   │   │   ├── reasoning_service.py  # LLM extraction
│   │   │   ├── email_service.py      # SMTP email
│   │   │   └── scheduler_service.py  # APScheduler
│   │   └── routes/
│   │       ├── standup.py            # Standup CRUD + execution
│   │       ├── config.py             # Configuration endpoints
│   │       └── analytics.py          # Dashboard stats
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
│
└── frontend/                         # React TypeScript + Tailwind
    ├── src/
    │   ├── pages/
    │   │   ├── DashboardPage.tsx
    │   │   ├── ConfigPage.tsx
    │   │   ├── StandupDetailPage.tsx
    │   │   ├── HistoryPage.tsx
    │   │   └── SettingsPage.tsx
    │   ├── components/
    │   │   ├── Dashboard/
    │   │   ├── Common/
    │   │   └── Config/
    │   ├── api/
    │   │   └── client.ts
    │   └── types/
    │       └── index.ts
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.ts
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **npm or yarn**

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/standupai.git
cd standupai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
createdb standupai

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Application
APP_NAME=StandupAI
APP_VERSION=1.0.0
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/standupai

# Linear Integration
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
LINEAR_API_URL=https://api.linear.app/graphql

# Slack Integration
SLACK_APP_ID=your_app_id
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret
SLACK_SIGNING_SECRET=your_signing_secret
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx

# ElevenLabs Integration
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Jitsi Configuration
JITSI_DOMAIN=meet.jit.si

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=standupai@example.com

# LLM Configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
LLM_PROVIDER=openai

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

---

## 📖 API Documentation

### Main Endpoints

#### Standup Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/standups/configs` | Create standup configuration |
| `GET` | `/api/standups/configs` | List all configurations |
| `GET` | `/api/standups/configs/{id}` | Get specific configuration |
| `PUT` | `/api/standups/configs/{id}` | Update configuration |
| `DELETE` | `/api/standups/configs/{id}` | Delete configuration |

#### Standup Execution
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/standups/start/{config_id}` | Manually start standup |
| `GET` | `/api/standups/{id}` | Get standup details |
| `POST` | `/api/standups/{id}/complete` | Complete standup |
| `POST` | `/api/standups/{id}/process-transcript` | Process developer transcript |
| `POST` | `/api/standups/{id}/summary` | Generate PM summary |

#### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/dashboard` | Get dashboard stats |
| `GET` | `/api/analytics/upcoming` | Get upcoming standups |
| `GET` | `/api/analytics/active` | Get active standups |
| `GET` | `/api/analytics/history` | Get standup history |
| `GET` | `/api/analytics/trends/blocked` | Get blocked issues trend |

#### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config/linear/teams` | Get Linear teams |
| `GET` | `/api/config/linear/teams/{id}/members` | Get team members |
| `GET` | `/api/config/linear/teams/{id}/issues` | Get team issues |
| `GET` | `/api/config/slack/channels` | Get Slack channels |
| `GET` | `/api/config/health` | Check integration health |

---

## 🔄 User Flow

### 1. Configuration Phase
1. User logs into dashboard
2. Navigates to "Schedule Standup"
3. Selects Linear team and Slack channel
4. Chooses date and time
5. Selects team members
6. Configures issue fetching (auto or manual)
7. Clicks "Schedule Standup"

### 2. Notification Phase
- At scheduled time, system triggers
- Generates unique Jitsi meeting URL
- Sends formatted Slack notification
- Team members join the meeting

### 3. Standup Execution
- AI agent facilitates discussion
- Asks about each issue status
- Records responses and extracts data
- Identifies blockers and escalations

### 4. Auto-Update Phase
- Posts comments to Linear issues
- Updates issue statuses
- Creates escalation tickets if needed
- Stores all updates in database

### 5. PM Summary
- Generates comprehensive summary
- Categorizes issues by status
- Sends via Slack DM and email
- Available in dashboard

---

## 🗄️ Database Schema

### Tables

#### `standup_configs`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| team_id | VARCHAR | Linear team ID |
| team_name | VARCHAR | Team display name |
| scheduled_time | TIMESTAMP | When to run |
| slack_channel_id | VARCHAR | Target channel |
| selected_members | JSONB | Team members array |
| auto_fetch_issues | BOOLEAN | Auto-fetch flag |
| status | VARCHAR | scheduled/completed/cancelled |

#### `standups`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| config_id | INTEGER | FK to configs |
| jitsi_url | VARCHAR | Meeting URL |
| status | VARCHAR | Status |
| total_issues | INTEGER | Issue count |
| duration_minutes | INTEGER | Duration |

#### `issue_updates`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| standup_id | INTEGER | FK to standups |
| linear_issue_id | VARCHAR | e.g., "ENG-123" |
| status | VARCHAR | Issue status |
| blockers | TEXT | Blocker details |
| escalation_needed | BOOLEAN | Needs escalation |

#### `pm_summaries`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| standup_id | INTEGER | FK to standups |
| progress_issues | JSONB | Progressing issues |
| blocked_issues | JSONB | Blocked issues |
| escalations_created | JSONB | New escalations |

---

## 🎨 UI Screenshots

### Dashboard
- Real-time stats overview
- Upcoming and active standups
- Analytics charts
- Recent history

### Schedule Standup
- Multi-step wizard
- Team and channel selection
- Member picker
- Issue configuration

### Standup Details
- Issue updates with status
- Blocker and dependency tracking
- PM summary view
- Escalation indicators

---

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Backend
cd backend
docker build -t standupai-backend .

# Frontend
cd frontend
npm run build
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

## 📞 Support

- 📧 Email: support@standupai.com
- 💬 Discord: [Join our community](https://discord.gg/standupai)
- 📖 Docs: [Documentation](https://docs.standupai.com)

---

<div align="center">

**Built with ❤️ by the StandupAI Team**

[Website](https://standupai.com) • [Documentation](https://docs.standupai.com) • [Twitter](https://twitter.com/standupai)

</div>
