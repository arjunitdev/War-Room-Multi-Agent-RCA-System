"""SQLite database for War Room incidents.

Replaces JSON file storage with SQLite for better concurrency, performance, and query capabilities.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database file location
DB_DIR = Path(__file__).parent.parent / "state"
DB_FILE = DB_DIR / "war_room.db"


def ensure_db_dir() -> None:
    """Ensure database directory exists."""
    DB_DIR.mkdir(exist_ok=True)
    logger.info(f"Database directory ensured: {DB_DIR}")


def init_db() -> None:
    """Initialize the SQLite database and create tables if they don't exist."""
    ensure_db_dir()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create incidents table
    c.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            alert_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            triggered_agents TEXT NOT NULL,
            logs TEXT NOT NULL,
            received_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for faster queries
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_status_category 
        ON incidents(status, category)
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {DB_FILE}")


def save_incident(
    category: str,
    alert_name: str,
    severity: str,
    triggered_agents: List[str],
    logs: Dict[str, str]
) -> int:
    """
    Save an incident to the database.
    
    Args:
        category: Incident category (Network, Database, Code)
        alert_name: Name of the alert
        severity: Severity level (CRITICAL, WARNING, etc.)
        triggered_agents: List of agent names that should analyze this
        logs: Dictionary of log data (db, network, app_code_diff)
        
    Returns:
        The ID of the inserted incident
    """
    ensure_db_dir()
    init_db()  # Ensure table exists
    
    logger.info(f"Saving incident to {DB_FILE.absolute()}")
    
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10.0)  # Add timeout for concurrent access
        c = conn.cursor()
        
        # Convert lists/dicts to JSON strings for storage
        triggered_agents_json = json.dumps(triggered_agents)
        logs_json = json.dumps(logs)
        received_at = datetime.now().isoformat()
        
        logger.debug(f"Inserting: category={category}, alert={alert_name}, severity={severity}")
        
        c.execute('''
            INSERT INTO incidents 
            (category, alert_name, severity, triggered_agents, logs, received_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            category,
            alert_name,
            severity,
            triggered_agents_json,
            logs_json,
            received_at,
            'active'
        ))
        
        incident_id = c.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Incident saved to database: ID={incident_id}, category={category}, alert={alert_name}")
        
        # Verify it was saved
        verify_conn = sqlite3.connect(DB_FILE)
        verify_c = verify_conn.cursor()
        verify_c.execute("SELECT COUNT(*) FROM incidents WHERE status='active'")
        count = verify_c.fetchone()[0]
        verify_conn.close()
        logger.info(f"Database verification: {count} active incident(s) in database")
        
        return incident_id
    except Exception as e:
        logger.error(f"❌ Failed to save incident: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def get_active_incidents() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all active incidents grouped by category.
    
    Returns:
        Dictionary with categories as keys and lists of incidents as values
    """
    if not DB_FILE.exists():
        return {"Network": [], "Database": [], "Code": []}
    
    # Use a fresh connection with proper isolation to see latest changes
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    c = conn.cursor()
    
    # Enable WAL mode for better concurrency (if not already enabled)
    c.execute("PRAGMA journal_mode=WAL")
    
    # Get all active incidents, ordered by most recent first
    c.execute('''
        SELECT * FROM incidents 
        WHERE status = 'active' 
        ORDER BY received_at DESC
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    # Group by category
    incidents_by_category = {"Network": [], "Database": [], "Code": []}
    
    for row in rows:
        incident = dict(row)
        category = incident.get('category', 'Unknown')
        
        # Parse JSON fields back to Python objects
        try:
            incident['triggered_agents'] = json.loads(incident.get('triggered_agents', '[]'))
            incident['logs'] = json.loads(incident.get('logs', '{}'))
        except (json.JSONDecodeError, TypeError):
            incident['triggered_agents'] = []
            incident['logs'] = {}
        
        # Add to appropriate category
        if category in incidents_by_category:
            incidents_by_category[category].append(incident)
        else:
            # Unknown category - add to first available or create new
            incidents_by_category.setdefault(category, []).append(incident)
    
    return incidents_by_category


def clear_all_incidents() -> int:
    """
    Clear all active incidents by setting status to 'cleared'.
    
    Returns:
        Number of incidents cleared
    """
    if not DB_FILE.exists():
        return 0
    
    # Use isolation_level=None for autocommit mode to ensure immediate visibility
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    c = conn.cursor()
    
    # Enable WAL mode for better concurrency
    c.execute("PRAGMA journal_mode=WAL")
    
    c.execute("UPDATE incidents SET status = 'cleared' WHERE status = 'active'")
    count = c.rowcount
    
    # Explicitly commit and close to ensure changes are visible immediately
    conn.commit()
    conn.close()
    
    logger.info(f"Cleared {count} active incidents (changes committed and connection closed)")
    return count


def clear_category_incidents(category: str) -> int:
    """
    Clear all active incidents for a specific category.
    
    Args:
        category: Category to clear (Network, Database, Code)
        
    Returns:
        Number of incidents cleared
    """
    if not DB_FILE.exists():
        return 0
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute(
        "UPDATE incidents SET status = 'cleared' WHERE status = 'active' AND category = ?",
        (category,)
    )
    count = c.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Cleared {count} active incidents for category: {category}")
    return count


def get_incident_count() -> Dict[str, int]:
    """Get count of active incidents by category."""
    if not DB_FILE.exists():
        return {"Network": 0, "Database": 0, "Code": 0}
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        SELECT category, COUNT(*) as count 
        FROM incidents 
        WHERE status = 'active' 
        GROUP BY category
    ''')
    
    counts = {"Network": 0, "Database": 0, "Code": 0}
    for row in c.fetchall():
        category, count = row
        if category in counts:
            counts[category] = count
    
    conn.close()
    return counts
