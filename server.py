"""FastAPI backend server - Webhook receiver for incident triggers.

Mimics the Firetiger ingestion engine. Receives POST requests with incident payloads
and stores them in SQLite database for the War Room dashboard to analyze.
"""

import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.db import init_db, save_incident, clear_all_incidents, clear_category_incidents, get_active_incidents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="War Room Webhook Receiver",
    description="Receives incident webhooks and stores them in SQLite for analysis",
    version="2.0.0",
    lifespan=lifespan
)


class IncidentPayload(BaseModel):
    """Pydantic model for incident webhook payload."""
    alert_name: str
    severity: str
    triggered_agents: list[str]  # List of agent names that should analyze this
    logs: Dict[str, str]  # Dictionary with db, network, app_code_diff logs


def get_category_from_incident(payload: Dict[str, Any]) -> str:
    """Determine category from incident payload."""
    triggered_agents = payload.get("triggered_agents", [])
    alert_name = payload.get("alert_name", "")
    
    logger.info(f"Determining category for: alert_name='{alert_name}', triggered_agents={triggered_agents}")
    
    # Check triggered_agents first (most reliable indicator)
    if isinstance(triggered_agents, list) and len(triggered_agents) > 0:
        for agent in triggered_agents:
            agent_str = str(agent)
            agent_lower = agent_str.lower()
            
            # Check for Network Engineer
            if "network" in agent_lower and "engineer" in agent_lower:
                logger.info(f"✅ Category: Network (from agent: '{agent_str}')")
                return "Network"
            # Check for DBA
            elif "dba" in agent_lower:
                logger.info(f"✅ Category: Database (from agent: '{agent_str}')")
                return "Database"
            # Check for Code Auditor
            elif "code" in agent_lower and "auditor" in agent_lower:
                logger.info(f"✅ Category: Code (from agent: '{agent_str}')")
                return "Code"
    
    # Fallback to alert_name if triggered_agents didn't match
    alert_name_lower = alert_name.lower()
    if "network" in alert_name_lower or alert_name.startswith("NET_"):
        logger.info(f"✅ Category: Network (from alert_name)")
        return "Network"
    elif "database" in alert_name_lower or "db_" in alert_name_lower or alert_name.startswith("DB_"):
        logger.info(f"✅ Category: Database (from alert_name)")
        return "Database"
    elif "code" in alert_name_lower or alert_name.startswith("CODE_"):
        logger.info(f"✅ Category: Code (from alert_name)")
        return "Code"
    
    logger.warning(f"⚠️ Could not determine category for incident: alert_name='{alert_name}', triggered_agents={triggered_agents}")
    return "Unknown"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "war-room-webhook-receiver"}


@app.post("/webhook/trigger")
async def trigger_incident(payload: IncidentPayload):
    """
    Receive incident webhook and store it in SQLite database.
    
    This endpoint mimics the Firetiger ingestion engine.
    Each webhook is completely independent and triggers only its specified agents.
    """
    try:
        logger.info(f"🔥 Alert Received: {payload.alert_name}")
        logger.info(f"   Severity: {payload.severity}")
        logger.info(f"   Triggered Agents: {payload.triggered_agents}")
        
        # Determine category
        payload_dict = payload.model_dump()
        category = get_category_from_incident(payload_dict)
        
        # Save to SQLite database (thread-safe!)
        try:
            logger.info(f"Attempting to save incident: category={category}, alert={payload.alert_name}")
            logger.info(f"  triggered_agents={payload.triggered_agents}")
            logger.info(f"  severity={payload.severity}")
            
            incident_id = save_incident(
                category=category,
                alert_name=payload.alert_name,
                severity=payload.severity,
                triggered_agents=payload.triggered_agents,
                logs=payload.logs
            )
            
            logger.info(f"✅ Incident saved to database: ID={incident_id}, category={category}")
            
            # Verify it was saved immediately
            from src.db import get_active_incidents, DB_FILE
            logger.info(f"Verifying save in database: {DB_FILE.absolute()}")
            verify_incidents = get_active_incidents()
            total = sum(len(v) for v in verify_incidents.values())
            logger.info(f"Database now contains {total} active incident(s)")
            
            # Double-check by querying the specific incident
            import sqlite3
            verify_conn = sqlite3.connect(DB_FILE)
            verify_c = verify_conn.cursor()
            verify_c.execute("SELECT id, category, alert_name, status FROM incidents WHERE id = ?", (incident_id,))
            verify_row = verify_c.fetchone()
            verify_conn.close()
            
            if verify_row:
                logger.info(f"✅ Verification successful: Incident ID {incident_id} found in database")
            else:
                logger.error(f"❌ Verification FAILED: Incident ID {incident_id} NOT found in database!")
                raise Exception(f"Incident was not saved to database (ID: {incident_id})")
            
        except Exception as save_error:
            logger.error(f"❌ Failed to save incident to database: {save_error}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        return {
            "status": "success",
            "message": f"Incident '{payload.alert_name}' received and stored",
            "triggered_agents": payload.triggered_agents,
            "incident_id": incident_id
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/clear")
async def clear_current_incident():
    """Clear all active incidents."""
    count = clear_all_incidents()
    return {"status": "success", "message": f"All incidents cleared", "count": count}


@app.post("/webhook/clear/{category}")
async def clear_category_incidents(category: str):
    """Clear incidents for a specific category."""
    count = clear_category_incidents(category)
    if count > 0:
        return {"status": "success", "message": f"{category} incidents cleared", "count": count}
    return {"status": "info", "message": f"No active incidents found for category {category}", "count": 0}


@app.get("/incidents/current")
async def get_current_incidents():
    """Get all active incidents grouped by category."""
    incidents = get_active_incidents()
    if not any(incidents.values()):
        return {"status": "clear", "message": "No active incidents", "data": {"Network": [], "Database": [], "Code": []}}
    return {"status": "incidents", "data": incidents}


if __name__ == "__main__":
    import uvicorn
    from src.db import ensure_db_dir
    ensure_db_dir()  # Ensure database directory exists
    logger.info("Starting War Room Webhook Receiver on http://localhost:8000")
    logger.info("Server code version: Enhanced with verification logging")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

