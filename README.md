# Sentinel - Multi-Agent Root Cause Analysis Platform

**Autonomous Root Cause Analysis. Separating Signal from Noise.**

Sentinel is an incident response platform designed to solve "Alert Fatigue" in distributed systems. It uses a novel **Multi-Agent "Blind Specialist" Architecture** to deconstruct complex, cascading failures and identify the single true root cause within seconds.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Development](#development)
- [How It Works](#how-it-works)
- [Contributing](#contributing)

## Overview

In distributed systems, one bad database query can lock up an entire table. Seconds later, your site slows down, and error messages start piling up. Your monitoring tools start shouting about network and database problems at the same time. Everyone panics in the "War Room," and it takes hours of digging through logs to find the one query that started it all.

**Sentinel solves this by:**
- Ingesting the entire failure stream
- Assigning specialized AI agents to analyze Network, Database, and Application layers in isolation
- Using a "Judge" agent to reconstruct the timeline using forensic timestamps
- Delivering a final verdict: *"The network didn't fail; an application logic error caused a deadlock at T+0s."*

## Architecture

### The "Blind Specialist" Model

In a real War Room, human biases lead to the "blame game." If the network engineer panics, everyone panics. By forcing agents to work in total isolation, we guarantee unbiased, purely evidence-based reporting from each domain.

### Causal Precedence Hierarchy

Infrastructure rarely breaks on its own. Sentinel uses a strict decision tree:
1. **Code Logic is King** - Logic errors (JSONDecodeError, KeyError, etc.) are root causes
2. **Infrastructure Exceptions are Nuanced** - Connectivity errors require checking DBA reports
3. **Database is Secondary** - Deadlocks and lock wait timeouts are root causes if code is healthy

### Temporal Forensics (T+0s)

Root cause is a function of time. The Sentinel engine timestamps every signal. The event that occurs at T+0s is mathematically identified as the trigger that started the cascade.

## Features

### 1. Chaos Simulator
- **Sequential Chaos Injection**: Creates realistic, time-delayed failure narratives
- Root cause event fired at T+0s, followed by cascading symptomatic faults at T+2s, T+5s, etc.
- Pre-built scenarios: Classic DB Deadlock, Cascading Table Lock, Zombie Transaction
- Standardized payload delivery with configurable delays

### 2. Multi-Agent Analysis
- **DBA Agent**: Analyzes database logs, locks, deadlocks, query performance
- **Network Engineer Agent**: Analyzes network traces, latency, timeouts, load balancer issues
- **Code Auditor Agent**: Analyzes code changes, logic errors, performance anti-patterns
- **Strict Data Isolation**: Each agent sees only their domain-specific logs

### 3. Judge Synthesis
- **Temporal Forensics**: Analyzes T+ timeline offsets to identify the "First Mover" event
- **Causal Precedence Logic**: Applies hierarchy to rule out downstream symptoms
- **Definitive Root Cause**: Determines the primary failure point

### 4. Actionable Remediation
- Pinpoints root cause component
- Suggests specific code/config fixes
- Verifies against SRE best practices
- Generates executive summary

## Tech Stack

### Backend
- **Python 3.10+** / **FastAPI** (Async)
- **Google Gemini Pro** (AI Engine)
- **SQLite** (Embedded, Low-Latency Database)
- **Pydantic** (Strict Schema Validation)
- **ThreadPoolExecutor** (Concurrent Agent Execution)
- **Mangum** (AWS Lambda/Vercel Compatibility)

### Frontend
- **React 18** with **TypeScript**
- **Vite** (Build Tool)
- **Tailwind CSS** (Styling)
- **Radix UI** (Component Library)
- **Lucide React** (Icons)

### Infrastructure
- **Vercel** (Serverless Deployment)
- **SQLite** (State Management)

## Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Google Gemini API key

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd War_room
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd Frontend
```

2. Install dependencies:
```bash
npm install
```

3. Build the frontend:
```bash
npm run build
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
WEBHOOK_URL=http://localhost:8001/webhook/trigger  # Optional, for local development
VERCEL=1  # Set automatically in Vercel deployment
```

### Database Configuration

The application uses SQLite for incident storage:
- **Local Development**: `state/war_room.db`
- **Vercel Deployment**: `/tmp/war_room.db` (ephemeral)

## Usage

### Quick Start

Use the unified launcher script:

```bash
# Production mode (builds frontend and starts both servers)
python run.py

# Development mode (frontend dev server + backend servers)
python run.py --dev

# Force rebuild frontend
python run.py --build

# Run only webhook server
python run.py --webhook-only

# Run only main server
python run.py --main-only
```

### Manual Start

**Option 1: Separate Servers (Development)**

Terminal 1 - Webhook Server:
```bash
python server.py
# Runs on http://localhost:8001
```

Terminal 2 - Main Application:
```bash
python main.py
# Runs on http://localhost:8000
```

Terminal 3 - Frontend Dev Server:
```bash
cd Frontend
npm run dev
# Runs on http://localhost:5173
```

**Option 2: Integrated Server (Production)**

```bash
# Build frontend first
cd Frontend
npm run build
cd ..

# Start main server (includes webhook endpoints)
python main.py
# Runs on http://localhost:8000
```

### Accessing the Application

- **Main Application**: http://localhost:8000
- **Webhook API**: http://localhost:8001 (if running separately)
- **API Documentation**: http://localhost:8000/docs (FastAPI Swagger UI)

## API Endpoints

### Health & Configuration

- `GET /api/health` - Health check
- `GET /api/config` - Get application configuration

### Scenarios

- `GET /api/scenarios` - List all available chaos scenarios
- `POST /api/scenarios/execute` - Execute a chaos scenario
  ```json
  {
    "scenario_name": "Classic DB Deadlock"
  }
  ```

### Incidents

- `GET /api/incidents/status` - Get current incident status
- `POST /api/incidents/clear` - Clear all active incidents
- `POST /api/webhook/trigger` - Trigger an incident (webhook)
  ```json
  {
    "alert_name": "DB-Deadlock-Critical",
    "severity": "CRITICAL",
    "source": "DATABASE",
    "logs": {
      "db": "database log content",
      "network": "",
      "app_code_diff": ""
    }
  }
  ```
- `POST /api/webhook/clear` - Clear all incidents
- `POST /api/webhook/clear/{category}` - Clear incidents by category

### Troubleshooting

- `POST /api/troubleshoot` - Run multi-agent analysis
  ```json
  {
    "api_key": "optional_api_key_override",
    "force_all_agents": false
  }
  ```

## Project Structure

```
War_room/
├── api/                      # Vercel serverless function
│   └── index.py             # Mangum wrapper for FastAPI
├── Frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── WarRoom.tsx  # Main war room dashboard
│   │   │   ├── ChaosSimulator.tsx  # Chaos scenario runner
│   │   │   ├── AboutSection.tsx     # About/landing page
│   │   │   └── ui/          # Radix UI components
│   │   ├── App.tsx          # Main app component
│   │   └── main.tsx         # Entry point
│   ├── public/              # Static assets
│   ├── package.json         # Frontend dependencies
│   └── vite.config.ts       # Vite configuration
├── src/                      # Python backend source
│   ├── agents.py            # Specialist agent classes
│   ├── judge.py             # Judge agent for synthesis
│   ├── db.py                # SQLite database operations
│   ├── scenarios_lib.py    # Chaos scenario definitions
│   ├── schemas.py           # Pydantic data models
│   ├── schema_utils.py     # Schema utilities
│   └── utils.py            # Utility functions
├── scenarios/               # Scenario JSON files
│   └── deadlock.json
├── state/                   # Local state (SQLite DB)
│   └── war_room.db
├── main.py                  # Main FastAPI application
├── server.py                # Separate webhook server (optional)
├── run.py                   # Unified launcher script
├── requirements.txt         # Python dependencies
├── vercel.json              # Vercel deployment config
└── README.md               # This file
```

## Deployment

### Vercel Deployment

1. **Install Vercel CLI**:
```bash
npm i -g vercel
```

2. **Deploy**:
```bash
vercel
```

3. **Set Environment Variables** in Vercel dashboard:
   - `GOOGLE_API_KEY`: Your Google Gemini API key

4. **Build Configuration**:
   - Build Command: `cd Frontend && npm install && npm run build`
   - Output Directory: `Frontend/build`
   - Install Command: `pip install -r requirements.txt`

The `vercel.json` file configures:
- API route rewrites to `/api`
- Webhook route rewrites
- SPA routing for frontend

### Environment-Specific Behavior

- **Vercel**: Uses `/tmp` for SQLite database (ephemeral)
- **Local**: Uses `state/war_room.db` (persistent)
- **Webhook Integration**: In Vercel, webhook endpoints are integrated into main app

## Development

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd Frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Adding New Scenarios

Edit `src/scenarios_lib.py`:

```python
SCENARIOS = {
    "Your Scenario Name": [
        {
            "source": "CODE",  # or "DATABASE" or "NETWORK"
            "alert_name": "Alert-Name",
            "severity": "CRITICAL",  # or "WARNING" or "HEALTHY"
            "delay": 0,  # Seconds delay before this payload
            "logs": "Your log content here"
        },
        # ... more payloads
    ]
}
```

### Database Schema

The SQLite database uses the following schema:

```sql
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    alert_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    triggered_agents TEXT NOT NULL,
    logs TEXT NOT NULL,
    received_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## How It Works

### 1. Incident Ingestion

When an incident webhook is received:
- Payload is validated using Pydantic schemas
- Category is determined from `source` field (DATABASE, NETWORK, CODE)
- Incident is stored in SQLite database
- Appropriate agents are triggered based on category

### 2. Agent Analysis

Each specialist agent:
- Receives only domain-specific logs (isolation)
- Uses Google Gemini Pro for analysis
- Returns structured `AgentAnalysis` with:
  - Status (Critical/Warning/Healthy)
  - Hypothesis
  - Confidence score
  - Evidence cited
  - Reasoning

### 3. Judge Synthesis

The Judge agent:
- Receives all agent analyses
- Applies causal precedence hierarchy
- Analyzes temporal relationships (T+ timestamps)
- Determines root cause agent
- Generates remediation plan

### 4. Frontend Display

The React frontend:
- Polls `/api/incidents/status` every 2 seconds
- Displays incidents by category
- Allows triggering chaos scenarios
- Shows agent analyses and judge verdict
- Provides API key input (stored in localStorage)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Author

**Arjun Selvam**
- LinkedIn: [arjun-selvam](https://www.linkedin.com/in/arjun-selvam/)

## Acknowledgments

- Google Gemini API for AI capabilities
- FastAPI for the excellent async web framework
- React and Vite for the modern frontend stack
- Radix UI for accessible component primitives

