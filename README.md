# 🔥 War Room - Multi-Agent RCA System

A production-grade, web-based "War Room" dashboard featuring three specialized AI agents (DBA, Network Engineer, Code Auditor) that investigate incidents in real-time. A fourth "Judge" agent synthesizes their conflicting findings to determine the true root cause.

## 🎯 Overview

This system demonstrates **Agentic Reasoning** through:
- **Parallel Analysis**: Three specialist agents analyze different aspects of incidents simultaneously
- **Conflict Resolution**: A Judge agent synthesizes potentially conflicting findings
- **Structured Output**: Fully typed, validated responses using Pydantic models
- **Production Quality**: Retry logic, logging, error handling, and session management

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Frontend**: Streamlit (Web Interface)
- **AI Engine**: Google AI SDK (`google-generativeai`)
- **Models**:
  - `gemini-1.5-flash` - For specialist agents (fast, efficient)
  - `gemini-1.5-pro` - For the Judge (high reasoning capability)
- **Data Validation**: Pydantic 2.0+
- **Environment**: python-dotenv

## 📦 Installation

1. **Clone the repository**:
   ```bash
   cd War_room
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   # Create .env file from template
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # Linux/Mac
   
   # Add your Google API key to .env
   # Get your key from: https://makersuite.google.com/app/apikey
   ```

## 🚀 Usage

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```

2. **Access the dashboard**:
   - Open your browser to `http://localhost:8501`

3. **Run an analysis**:
   - Enter your Google API Key in the sidebar (saved in session)
   - Select an incident scenario (e.g., `deadlock.json`)
   - Click "🚀 Initialize War Room"
   - Review agent analyses and the final verdict

## 🏗️ Architecture

### Data Layer
Mock incident scenarios loaded from JSON files containing:
- **DB Logs**: Database errors, locks, transaction issues
- **Network Logs**: Timeouts, latency, connection problems
- **Code Diffs**: Recent changes that might have caused issues

### Agent Layer
Three specialist agents using `gemini-1.5-flash`:
- **DBA Agent**: Analyzes database logs for locks, deadlocks, query issues
- **Network Engineer**: Examines network traces for timeouts and connectivity
- **Code Auditor**: Reviews code changes for performance issues and bugs

### Orchestration Layer
Judge agent using `gemini-1.5-pro`:
- Receives structured output from all specialists
- Synthesizes findings to identify causal relationships
- Determines the true root cause
- Provides remediation plan and agent assessments

### UI Layer
Streamlit dashboard with:
- Evidence display (logs and code)
- Agent tribunal (parallel execution with visual feedback)
- Final verdict (root cause and remediation)

## 📁 Project Structure

```
War_room/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── src/
│   ├── __init__.py
│   ├── utils.py               # Google AI SDK initialization
│   ├── schemas.py             # Pydantic models
│   ├── schema_utils.py        # JSON schema cleaning utilities
│   ├── data_loader.py         # Scenario loading
│   ├── agents.py              # Specialist agent classes
│   └── judge.py               # Judge agent class
└── scenarios/
    └── deadlock.json          # Sample deadlock incident
```

## 🎨 Features

### Production-Grade Quality
- ✅ **Retry Logic**: Automatic retries with exponential backoff
- ✅ **Logging**: Comprehensive logging for debugging and monitoring
- ✅ **Error Handling**: Graceful error handling with user-friendly messages
- ✅ **Type Safety**: Full type hints and Pydantic validation
- ✅ **Session Management**: API key and state persistence
- ✅ **Caching**: Agent initialization caching for performance
- ✅ **Concurrent Execution**: ThreadPoolExecutor for parallel analysis
- ✅ **Timeout Protection**: Request timeouts to prevent hangs

### User Experience
- 🎯 **Clean UI**: Professional, intuitive interface
- 📊 **Visual Feedback**: Status indicators, spinners, progress updates
- 🔒 **Secure**: Password-masked API key input
- 💾 **Session Persistence**: API key saved across reruns
- 📝 **Help Documentation**: Built-in usage instructions

## 🔧 Configuration

### Adding New Scenarios

Create a JSON file in `scenarios/` directory:

```json
{
  "name": "Your Incident Name",
  "db_logs": "Database log content...",
  "network_logs": "Network log content...",
  "code_diff": "Code diff content..."
}
```

### Customizing Agent Behavior

Edit role definitions in `src/agents.py`:
- `DBA_ROLE`
- `NETWORK_ROLE`
- `CODE_AUDITOR_ROLE`

### Adjusting Retry/Timeout Settings

In `src/agents.py` and `src/judge.py`:
```python
MAX_RETRIES = 3                    # Number of retry attempts
RETRY_DELAY_SECONDS = 1            # Base delay between retries
REQUEST_TIMEOUT_SECONDS = 60       # Request timeout
```

## 📊 Example Output

The system provides:
1. **Agent Analyses**: Individual assessments with status, hypothesis, evidence, and reasoning
2. **Judge Verdict**: 
   - Root cause determination
   - Causal chain explanation
   - Remediation plan
   - Agent assessment (who was right/wrong)

## 🤝 Contributing

This is a demonstration project. Feel free to:
- Add new incident scenarios
- Enhance agent role definitions
- Improve UI/UX
- Add more agent types
- Implement additional features

## 📝 License

This project is provided as-is for demonstration purposes.

## 🙏 Acknowledgments

- **Google Gemini**: Powering the AI agents
- **Streamlit**: Enabling rapid UI development
- **Pydantic**: Providing robust data validation

---

Built with 🔥 to demonstrate multi-agent agentic reasoning systems.


