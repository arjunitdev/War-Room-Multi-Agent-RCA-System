"""War Room - Multi-Agent RCA System with Chaos Simulator.

Two-tab Streamlit application:
- Tab 1: ⚡ Chaos Simulator - Trigger incidents via webhook
- Tab 2: 🔥 War Room - Auto-polling dashboard that analyzes incidents
"""

import json
import time
import logging
import os
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.utils import get_google_ai_client
from src.scenarios_lib import SCENARIOS, get_scenarios_by_category, get_scenario
from src.agents import SpecialistAgent, DBA_ROLE, NETWORK_ROLE, CODE_AUDITOR_ROLE
from src.judge import JudgeAgent
from src.schemas import AgentAnalysis, JudgeVerdict
from src.db import init_db, get_active_incidents

# Load environment variables
try:
    load_dotenv(encoding='utf-8')
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not load .env file: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
APP_TITLE = "War Room - Multi-Agent RCA"
APP_ICON = "🔥"
MAX_WORKERS = 3
WEBHOOK_URL = "http://localhost:8000/webhook/trigger"
POLL_INTERVAL = 2  # seconds - SQLite can handle fast polling


def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    # Auto-load API key from environment if available
    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    
    defaults = {
        "agent_results": None,
        "judge_verdict": None,
        "incident_data": None,
        "api_key": env_api_key,  # Auto-load from .env
        "last_incident_check": None,
        "check_timestamps": {
            "DBA": None,
            "Network Engineer": None,
            "Code Auditor": None,
        },
        "last_incident_count": 0,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def check_incident_file() -> Dict[str, list]:
    """
    Check SQLite database for active incidents.
    Returns all active incidents grouped by category.
    
    Returns:
        Dictionary with categories as keys and lists of incidents as values
    """
    try:
        # Initialize DB if needed
        init_db()
        
        # Get active incidents from SQLite
        incidents_by_category = get_active_incidents()
        
        # Ensure all categories exist
        for cat in ["Network", "Database", "Code"]:
            if cat not in incidents_by_category:
                incidents_by_category[cat] = []
        
        total = sum(len(v) for v in incidents_by_category.values())
        logger.info(f"Database query: Found {total} active incidents")
        if total > 0:
            logger.info(f"  Network: {len(incidents_by_category.get('Network', []))}")
            logger.info(f"  Database: {len(incidents_by_category.get('Database', []))}")
            logger.info(f"  Code: {len(incidents_by_category.get('Code', []))}")
        return incidents_by_category
        
    except Exception as e:
        logger.error(f"Error reading incidents from database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty structure on error
        return {"Network": [], "Database": [], "Code": []}


def run_category_agent_analysis(
    api_key: str,
    incidents_by_category: Dict[str, list],
    category: str,
    agent_name: str,
    agent_role: str,
    force_analysis: bool = False
) -> Optional[AgentAnalysis]:
    """
    Run agent analysis for all incidents in a specific category.
    
    Args:
        api_key: Google API key
        incidents_by_category: Dictionary with categories as keys and lists of incidents
        category: Category to analyze (Network, Database, or Code)
        agent_name: Name of the agent
        agent_role: Role definition for the agent
        force_analysis: If True, analyze even if no incidents (for troubleshoot mode)
        
    Returns:
        AgentAnalysis object or None if no incidents in category (unless force_analysis=True)
    """
    incidents = incidents_by_category.get(category, []) if incidents_by_category else []
    
    # If no incidents and not forcing, return None
    if not incidents and not force_analysis:
        return None
    
    # If no incidents but force_analysis, create a placeholder context
    if not incidents and force_analysis:
        if category == "Network":
            combined_context = "No active network incidents detected. System appears healthy from network perspective. All network connections stable, no timeouts or errors reported."
        elif category == "Database":
            combined_context = "No active database incidents detected. Database connections and queries appear normal. No deadlocks, connection pool issues, or slow queries reported."
        else:  # Code
            combined_context = "No active code-related incidents detected. Application code appears stable. No syntax errors, memory leaks, or infinite loops reported."
    else:
        combined_context = None
    
    # Validate API key
    try:
        get_google_ai_client(api_key)
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        raise ValueError(f"Invalid API key: {e}")
    
    # Initialize agent
    agent = SpecialistAgent(agent_name, agent_role)
    
    # Prepare analysis context if not already set (for force_analysis mode)
    if combined_context is None:
        # Combine all incidents from this category into a single analysis context
        # BLIND SPECIALIST ARCHITECTURE: Each agent only sees their domain-specific logs
        # This ensures independent analysis without cross-domain knowledge
        context_parts = []
        for idx, incident in enumerate(incidents, 1):
            alert_name = incident.get("alert_name", "Unknown")
            severity = incident.get("severity", "UNKNOWN")
            logs = incident.get("logs", {})
            
            # Each specialist only sees their domain-specific log (blind to other domains)
            if category == "Network":
                log_data = logs.get("network", "")
            elif category == "Database":
                log_data = logs.get("db", "")
            else:  # Code
                log_data = logs.get("app_code_diff", "")
            
            context_parts.append(f"=== Incident {idx}: {alert_name} (Severity: {severity}) ===\n{log_data}")
        
        combined_context = "\n\n".join(context_parts)
    
    # Run analysis
    try:
        start_time = datetime.now()
        result = agent.analyze(combined_context)
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        # Note: Timestamps are stored in main thread after agent completes
        # (Session state is not thread-safe, so we can't access it from worker threads)
        
        logger.info(f"Agent {agent_name} completed analysis of {len(incidents)} {category} incident(s) in {elapsed:.1f}s")
        return result
    except Exception as e:
        error_msg = f"Agent {agent_name} failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def display_agent_analysis(analysis: AgentAnalysis, container) -> None:
    """Display a single agent's analysis."""
    with container:
        status_config = {
            "Critical": ("🚨", st.error),
            "Warning": ("⚠️", st.warning),
            "Healthy": ("✅", st.success),
        }
        icon, display_func = status_config.get(analysis.status, ("❓", st.info))
        display_func(f"{icon} {analysis.status}")
        
        st.markdown(f"**Agent:** {analysis.agent_name}")
        st.markdown(f"**Hypothesis:** {analysis.hypothesis}")
        st.markdown(f"**Confidence:** {analysis.confidence_score:.1%}")
        
        with st.expander("📝 Evidence", expanded=False):
            for evidence in analysis.evidence_cited:
                st.markdown(f"- {evidence}")
        
        with st.expander("🧠 Reasoning", expanded=False):
            st.markdown(analysis.reasoning)


def render_chaos_simulator_tab(api_key: str) -> None:
    """Render the Chaos Simulator tab."""
    st.header("⚡ Chaos Simulator")
    st.markdown("Trigger incidents to test the War Room system")
    st.markdown("---")
    
    # Get scenarios by category
    scenarios_by_category = get_scenarios_by_category()
    
    # Category selector
    category = st.selectbox(
        "Select Scenario Category",
        options=list(scenarios_by_category.keys()),
        help="Choose the category of incident to simulate"
    )
    
    # Issue selector (radio buttons)
    if category:
        issues = scenarios_by_category[category]
        selected_issue_id = st.radio(
            "Select Specific Issue",
            options=list(issues.keys()),
            format_func=lambda x: issues[x],
            help="Choose the specific incident scenario"
        )
        
        # Display payload preview
        if selected_issue_id:
            scenario = get_scenario(selected_issue_id)
            
            st.markdown("### 📋 Payload Preview")
            st.json(scenario)
            
            st.markdown("### 🎯 Triggered Agents")
            triggered = scenario.get("triggered_agents", [])
            for agent in triggered:
                st.markdown(f"- **{agent}**")
            
            # Trigger button
            st.markdown("---")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                trigger_button = st.button(
                    "🚀 TRIGGER INCIDENT (SEND POST)",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.button("🔄 Clear All Incidents", use_container_width=True):
                    try:
                        response = requests.post(
                            "http://localhost:8000/webhook/clear",
                            timeout=5
                        )
                        if response.status_code == 200:
                            result = response.json()
                            count = result.get('count', 0)
                            st.success(f"✅ All incidents cleared ({count} incidents)")
                            
                            # Clear ALL session state to force fresh read in both tabs
                            st.session_state.incident_data = None
                            st.session_state.agent_results = None
                            st.session_state.judge_verdict = None
                            st.session_state.last_incident_check = None
                            st.session_state.force_troubleshoot = False
                            
                            # Verify the clear worked
                            from src.db import get_active_incidents
                            verify_incidents = get_active_incidents()
                            verify_total = sum(len(v) for v in verify_incidents.values())
                            logger.info(f"After clear: {verify_total} active incidents remaining in database")
                            
                            if verify_total > 0:
                                st.warning(f"⚠️ Warning: {verify_total} incident(s) still active. Database may not have cleared properly.")
                            else:
                                st.info("✅ Database verified: All incidents cleared")
                            
                            # Force immediate rerun to update both tabs
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"Failed to clear incidents: Status {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to webhook server. Is `server.py` running?")
                    except Exception as e:
                        st.error(f"Failed to clear: {e}")
                        logger.error(f"Clear incidents error: {e}", exc_info=True)
            
            # Send webhook
            if trigger_button:
                # Note: API key not required for sending webhook, only for analysis
                try:
                    with st.spinner("Sending webhook..."):
                        # Ensure proper JSON serialization
                        payload = json.dumps(scenario)
                        headers = {"Content-Type": "application/json"}
                        
                        logger.info(f"Sending POST to {WEBHOOK_URL} with payload: {scenario.get('alert_name')}")
                        response = requests.post(
                            WEBHOOK_URL,
                            json=scenario,
                            headers=headers,
                            timeout=10
                        )
                        
                        logger.info(f"Response status: {response.status_code}, Response: {response.text}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result.get('message', 'Incident triggered successfully')}")
                            st.info(f"Triggered agents: {', '.join(triggered)}")
                            
                            # Clear previous analysis
                            st.session_state.agent_results = None
                            st.session_state.judge_verdict = None
                            st.session_state.incident_data = None
                            
                            # Small delay then rerun to show in War Room tab
                            # SQLite writes are instant, so we can rerun quickly
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to trigger incident: Status {response.status_code}, {response.text}")
                            logger.error(f"Webhook failed: {response.status_code} - {response.text}")
                            
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to webhook server. Is `server.py` running?")
                    st.info("💡 Start the server with: `python server.py` or `uvicorn server:app --reload`")
                    logger.error("Connection error to webhook server")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Webhook error: {e}", exc_info=True)


def render_war_room_tab(api_key: str) -> None:
    """Render the War Room tab with auto-polling."""
    st.header("🔥 War Room")
    st.markdown("Real-time incident analysis dashboard")
    st.markdown("---")
    
    # Timer/Status indicator with manual refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.info(f"🕐 Last check: {current_time} | Polling every {POLL_INTERVAL} seconds (SQLite)")
    with col2:
        if st.button("🔄 Check Now", use_container_width=True, type="secondary"):
            # Force immediate check by clearing cached data
            st.session_state.incident_data = None
            st.session_state.agent_results = None
            st.session_state.judge_verdict = None
            st.rerun()
    with col3:
        if st.button("🔧 Troubleshoot", use_container_width=True, type="primary"):
            # Force all 3 agents to run - this is the ONLY way agents are called
            st.session_state.force_troubleshoot = True
            st.session_state.agent_results = None
            st.session_state.judge_verdict = None
            st.rerun()
    
    # Auto-polling: Check for new incidents from SQLite (always query fresh)
    incidents_by_category = check_incident_file()
    
    # Ensure it's a dict with all required keys (defensive checks)
    if not isinstance(incidents_by_category, dict):
        logger.error(f"check_incident_file() returned non-dict: {type(incidents_by_category)}")
        incidents_by_category = {"Network": [], "Database": [], "Code": []}
    
    # Ensure all categories exist and are lists
    for cat in ["Network", "Database", "Code"]:
        if cat not in incidents_by_category:
            incidents_by_category[cat] = []
        # Ensure each category value is a list
        if not isinstance(incidents_by_category[cat], list):
            logger.warning(f"Category {cat} is not a list: {type(incidents_by_category[cat])}")
            incidents_by_category[cat] = []
    
    # Debug: Log what we found
    total_incidents = sum(len(v) for v in incidents_by_category.values())
    logger.info(f"War Room: Found {total_incidents} active incidents (Network: {len(incidents_by_category.get('Network', []))}, Database: {len(incidents_by_category.get('Database', []))}, Code: {len(incidents_by_category.get('Code', []))})")
    
    # Always update session state with fresh data from database (don't cache - SQLite is fast)
    # This ensures that when incidents are cleared, the dashboard immediately reflects the change
    st.session_state.incident_data = incidents_by_category
    st.session_state.last_incident_check = datetime.now()
    
    # Track incident count changes to detect when incidents are cleared
    previous_count = st.session_state.get("last_incident_count", -1)
    if previous_count != total_incidents:
        logger.info(f"Incident count changed: {previous_count} -> {total_incidents}")
        st.session_state.last_incident_count = total_incidents
    
    # If incidents were cleared (no incidents found), also clear agent results
    if total_incidents == 0:
        if st.session_state.agent_results:
            logger.info("No incidents found - clearing agent results")
            st.session_state.agent_results = None
            st.session_state.judge_verdict = None
    
    # Check if any incidents are active
    has_incidents = any(
        isinstance(incidents, list) and len(incidents) > 0 
        for incidents in incidents_by_category.values()
    )
    
    # Enhanced debug logging for troubleshooting
    logger.info(f"=== Dashboard Status Check ===")
    logger.info(f"has_incidents: {has_incidents}")
    logger.info(f"total_incidents: {total_incidents}")
    logger.info(f"incidents_by_category type: {type(incidents_by_category)}")
    logger.info(f"incidents_by_category keys: {list(incidents_by_category.keys()) if isinstance(incidents_by_category, dict) else 'Not a dict'}")
    for cat in ["Network", "Database", "Code"]:
        cat_incidents = incidents_by_category.get(cat, [])
        logger.info(f"  {cat}: {len(cat_incidents)} incidents (type: {type(cat_incidents)})")
        if cat_incidents and len(cat_incidents) > 0:
            for idx, inc in enumerate(cat_incidents[:2]):  # Log first 2 incidents
                logger.info(f"    [{idx}] {inc.get('alert_name', 'Unknown')} (category: {inc.get('category', 'Unknown')}, severity: {inc.get('severity', 'Unknown')})")
    
    # Display status dashboard - always show category tiles
    st.markdown("---")
    st.subheader("📊 Status Dashboard")
    st.markdown(f"**Real-time status of incidents by category (checks POST requests every {POLL_INTERVAL} seconds via SQLite)**")
    
    # Debug info (always visible for troubleshooting)
    with st.expander("🔍 Debug Info", expanded=False):
        total = sum(len(v) for v in incidents_by_category.values())
        st.write(f"**Total incidents found:** {total}")
        st.write(f"**Network:** {len(incidents_by_category.get('Network', []))}")
        st.write(f"**Database:** {len(incidents_by_category.get('Database', []))}")
        st.write(f"**Code:** {len(incidents_by_category.get('Code', []))}")
        st.write(f"**has_incidents:** {has_incidents}")
        st.write(f"**incidents_by_category type:** {type(incidents_by_category)}")
        if total > 0:
            st.success(f"✅ Database has {total} incident(s) - they should be displayed above")
            # Show detailed breakdown
            for cat in ["Network", "Database", "Code"]:
                cat_incidents = incidents_by_category.get(cat, [])
                if cat_incidents:
                    st.write(f"**{cat} incidents:**")
                    for inc in cat_incidents:
                        st.write(f"  - {inc.get('alert_name', 'Unknown')} (severity: {inc.get('severity', 'Unknown')}, category: {inc.get('category', 'Unknown')})")
            st.json(incidents_by_category)
        else:
            st.warning("⚠️ No incidents in database")
    
    # Create three columns for the three category tiles
    col1, col2, col3 = st.columns(3)
    
    category_cols = {
        "Network": col1,
        "Database": col2,
        "Code": col3
    }
    
    # Show category tiles regardless of incident status
    for category_name in ["Network", "Database", "Code"]:
        # Get incidents for this category - ensure we have a list
        if not isinstance(incidents_by_category, dict):
            incidents = []
            logger.warning(f"incidents_by_category is not a dict, it's {type(incidents_by_category)}")
        else:
            incidents = incidents_by_category.get(category_name, [])
            # Ensure it's a list
            if not isinstance(incidents, list):
                logger.warning(f"Incidents for {category_name} is not a list, it's {type(incidents)}: {incidents}")
                incidents = []
        
        col = category_cols[category_name]
        
        # Debug logging
        logger.info(f"Rendering {category_name} tile: {len(incidents)} incidents, type: {type(incidents)}")
        if incidents and len(incidents) > 0:
            logger.info(f"  First incident alert_name: {incidents[0].get('alert_name', 'Unknown')}")
            logger.info(f"  First incident category: {incidents[0].get('category', 'Unknown')}")
        
        with col:
            # Category tile - check if incidents is a non-empty list
            if isinstance(incidents, list) and len(incidents) > 0:
                # Active incidents tile - red border
                st.markdown(
                    f"""
                    <div style="border: 3px solid #ff4444; border-radius: 10px; padding: 15px; background-color: #fff5f5; margin-bottom: 10px;">
                        <h3 style="color: #cc0000; margin-top: 0;">{category_name}</h3>
                        <p style="font-size: 24px; font-weight: bold; color: #cc0000; margin: 10px 0;">{len(incidents)} Active</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Show active incidents in this category
                for incident in incidents:
                    alert_name = incident.get("alert_name", "Unknown")
                    severity = incident.get("severity", "UNKNOWN")
                    received_at = incident.get("received_at", "")
                    
                    # Format time
                    if received_at:
                        try:
                            dt = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
                            time_str = dt.strftime("%H:%M:%S")
                        except:
                            time_str = received_at[:8] if len(received_at) > 8 else received_at
                    else:
                        time_str = "Unknown"
                    
                    # Severity color
                    severity_color = "#cc0000" if severity == "CRITICAL" else "#ff8800" if severity == "WARNING" else "#666666"
                    
                    st.markdown(
                        f"""
                        <div style="border-left: 4px solid {severity_color}; padding: 10px; margin: 5px 0; background-color: #f9f9f9; border-radius: 5px;">
                            <p style="margin: 0; font-weight: bold; color: {severity_color}; font-size: 14px;">{alert_name}</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Severity: {severity} | {time_str}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                # No active incidents tile - green border
                st.markdown(
                    f"""
                    <div style="border: 3px solid #44ff44; border-radius: 10px; padding: 15px; background-color: #f5fff5; margin-bottom: 10px;">
                        <h3 style="color: #00cc00; margin-top: 0;">{category_name}</h3>
                        <p style="font-size: 24px; font-weight: bold; color: #00cc00; margin: 10px 0;">✅ No Active Issues</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # If no incidents, show message and return early (but tiles are already shown above)
    if not has_incidents:
        st.markdown("---")
        st.success("## ✅ All Systems Operational")
        st.info("No active incidents detected. Use the Chaos Simulator tab to trigger an incident via POST request.")
        return
    
    # Incidents detected! Show alert banner
    st.warning("## 🚨 ACTIVE INCIDENTS DETECTED")
    st.markdown("**Incidents received via POST request to webhook. Click '🔧 Troubleshoot' button to analyze.**")
    
    st.markdown("---")
    
    # Show message if no agents have run yet
    if not st.session_state.agent_results:
        st.info("💡 **Click the '🔧 Troubleshoot' button above to trigger agent analysis**")
        st.markdown("---")
    
    # Run agent analysis ONLY when Troubleshoot button is clicked
    if api_key and st.session_state.get("force_troubleshoot", False):
        # Reset the flag immediately
        st.session_state.force_troubleshoot = False
        
        # Determine which agents to call based on active incidents
        agents_to_call = []
        
        # Only call agents for categories that have active incidents
        if incidents_by_category.get("Network") and len(incidents_by_category.get("Network", [])) > 0:
            agents_to_call.append(("Network Engineer", NETWORK_ROLE, "Network"))
        if incidents_by_category.get("Database") and len(incidents_by_category.get("Database", [])) > 0:
            agents_to_call.append(("DBA", DBA_ROLE, "Database"))
        if incidents_by_category.get("Code") and len(incidents_by_category.get("Code", [])) > 0:
            agents_to_call.append(("Code Auditor", CODE_AUDITOR_ROLE, "Code"))
        
        # If no incidents, still run all 3 agents (troubleshoot mode)
        if len(agents_to_call) == 0:
            agents_to_call = [
                ("Network Engineer", NETWORK_ROLE, "Network"),
                ("DBA", DBA_ROLE, "Database"),
                ("Code Auditor", CODE_AUDITOR_ROLE, "Code")
            ]
            # Ensure all categories exist
            if not incidents_by_category:
                incidents_by_category = {"Network": [], "Database": [], "Code": []}
            for cat in ["Network", "Database", "Code"]:
                if cat not in incidents_by_category:
                    incidents_by_category[cat] = []
        
        # Run analysis
        if agents_to_call:
            try:
                # Ensure check_timestamps is initialized before starting threads
                if "check_timestamps" not in st.session_state:
                    st.session_state.check_timestamps = {
                        "DBA": None,
                        "Network Engineer": None,
                        "Code Auditor": None,
                    }
                
                with st.spinner(f"🔍 {len(agents_to_call)} agent(s) analyzing incidents..."):
                    start_time = time.time()
                    
                    # Run agents in parallel
                    agent_results = {}
                    with ThreadPoolExecutor(max_workers=len(agents_to_call)) as executor:
                        # Determine if we're in troubleshoot mode (all 3 agents called)
                        is_troubleshoot = len(agents_to_call) == 3
                        
                        futures = {
                            executor.submit(
                                run_category_agent_analysis,
                                api_key,
                                incidents_by_category,
                                category,
                                agent_name,
                                agent_role,
                                force_analysis=(is_troubleshoot and len(incidents_by_category.get(category, [])) == 0)
                            ): (agent_name, category)
                            for agent_name, agent_role, category in agents_to_call
                        }
                        
                        # Track timestamps for each agent (collected in main thread)
                        agent_timestamps = {}
                        
                        for future in as_completed(futures):
                            agent_name, category = futures[future]
                            try:
                                result = future.result()
                                if result:
                                    agent_results[agent_name] = result
                                    # Store timestamp in main thread (thread-safe)
                                    agent_timestamps[agent_name] = {
                                        "start": datetime.now().strftime("%H:%M:%S"),  # Approximate
                                        "end": datetime.now().strftime("%H:%M:%S"),
                                        "elapsed": "N/A"  # Will be calculated below
                                    }
                            except Exception as e:
                                st.error(f"❌ Agent {agent_name} failed: {str(e)}")
                                logger.error(f"Agent {agent_name} failed: {e}")
                        
                        # Store all timestamps in session state (main thread, thread-safe)
                        if "check_timestamps" not in st.session_state:
                            st.session_state.check_timestamps = {
                                "DBA": None,
                                "Network Engineer": None,
                                "Code Auditor": None,
                            }
                        
                        # Update timestamps for successful agents
                        for agent_name, timestamp_data in agent_timestamps.items():
                            st.session_state.check_timestamps[agent_name] = timestamp_data
                    
                    elapsed = time.time() - start_time
                    st.session_state.agent_results = agent_results
                    logger.info(f"Analysis completed for {len(agent_results)} agent(s) in {elapsed:.2f}s")
                    
                    completion_time = datetime.now().strftime("%H:%M:%S")
                    st.success(f"✅ Analysis completed at {completion_time} ({elapsed:.1f}s)")
                    
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                logger.error(f"Analysis failed: {e}")
                return
    
    # Show agent reasoning section only if agents have been run (via Troubleshoot button)
    if st.session_state.agent_results:
        st.markdown("---")
        st.subheader("⚖️ Agent Reasoning & Analysis")
        st.markdown("**Each agent presents their independent analysis based on their domain expertise.**")
        
        # Show check timestamps
        if "check_timestamps" in st.session_state and st.session_state.check_timestamps:
            timestamp_info = []
            for agent_name in st.session_state.agent_results.keys():
                timestamp_data = st.session_state.check_timestamps.get(agent_name)
                if timestamp_data and isinstance(timestamp_data, dict):
                    info = f"**{agent_name}**: Started {timestamp_data['start']}, Completed {timestamp_data['end']} ({timestamp_data['elapsed']})"
                    timestamp_info.append(info)
            
            if timestamp_info:
                with st.expander("🕐 Agent Check Timestamps", expanded=False):
                    for info in timestamp_info:
                        st.markdown(f"- {info}")
            
            # Display all agent hypotheses in a debate format
            num_agents = len(st.session_state.agent_results)
            if num_agents > 0:
                # Show agents side-by-side
                cols = st.columns(num_agents)
                for idx, (agent_name, analysis) in enumerate(st.session_state.agent_results.items()):
                    if idx < len(cols):
                        with cols[idx]:
                            # Agent presentation card
                            st.markdown(f"### 👤 {agent_name}")
                            st.markdown(f"**Hypothesis:** {analysis.hypothesis}")
                            st.markdown(f"**Confidence:** {analysis.confidence_score:.1%}")
                            
                            # Status badge
                            status_colors = {
                                "Critical": "🔴",
                                "Warning": "🟡", 
                                "Healthy": "🟢"
                            }
                            st.markdown(f"{status_colors.get(analysis.status, '⚪')} **{analysis.status}**")
                            
                            with st.expander("📋 Evidence & Reasoning", expanded=True):
                                st.markdown("**Evidence Cited:**")
                                for evidence in analysis.evidence_cited:
                                    st.markdown(f"- {evidence}")
                                st.markdown("---")
                                st.markdown("**Detailed Reasoning:**")
                                st.markdown(analysis.reasoning)
            
            # Show agent comparison/debate
            st.markdown("---")
            st.subheader("💬 Agent Debate & Perspectives")
            st.markdown("**Comparing agent hypotheses to identify agreements, disagreements, and causal relationships.**")
            
            # Create comparison matrix
            agent_list = list(st.session_state.agent_results.items())
            if len(agent_list) > 1:
                # Show hypothesis comparison
                st.markdown("#### Hypothesis Comparison")
                comparison_data = []
                for agent_name, analysis in agent_list:
                    comparison_data.append({
                        "Agent": agent_name,
                        "Hypothesis": analysis.hypothesis,
                        "Status": analysis.status,
                        "Confidence": f"{analysis.confidence_score:.1%}"
                    })
                
                df = pd.DataFrame(comparison_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show potential conflicts/agreements
                st.markdown("#### Key Observations")
                hypotheses = [analysis.hypothesis for _, analysis in agent_list]
                statuses = [analysis.status for _, analysis in agent_list]
                
                # Check for conflicts
                if len(set(statuses)) > 1:
                    st.warning("⚠️ **Conflicting Severity Assessments**: Agents disagree on the severity of the issue.")
                
                # Check for agreement
                if all("timeout" in h.lower() or "latency" in h.lower() for h in hypotheses):
                    st.info("✅ **Consensus**: All agents identify performance/connectivity issues.")
                elif any("deadlock" in h.lower() for h in hypotheses) and any("timeout" in h.lower() for h in hypotheses):
                    st.warning("🔍 **Causal Relationship Detected**: Database deadlock may be causing network timeouts.")
                
                # Show evidence overlap
                all_evidence = []
                for agent_name, analysis in agent_list:
                    all_evidence.extend([(agent_name, e) for e in analysis.evidence_cited])
                
                st.markdown("#### Evidence Summary")
                for agent_name, analysis in agent_list:
                    with st.expander(f"📝 {agent_name}'s Evidence", expanded=False):
                        for evidence in analysis.evidence_cited:
                            st.markdown(f"- {evidence}")
            
            # Run Judge with visible synthesis process
            # Judge runs when we have agent results but no verdict yet
            if st.session_state.agent_results and st.session_state.judge_verdict is None:
                st.markdown("---")
                st.subheader("⚖️ Judge Deliberation: Synthesis Process")
                st.markdown("**The Judge analyzes all agent findings, identifies causal relationships, and determines the root cause.**")
                
                # Show what the Judge is considering
                with st.expander("🔍 What the Judge is Analyzing", expanded=True):
                    st.markdown("**Input to Judge:**")
                    for agent_name, analysis in st.session_state.agent_results.items():
                        st.markdown(f"**{agent_name}**: {analysis.hypothesis} (Confidence: {analysis.confidence_score:.1%})")
                    st.markdown("---")
                    st.markdown("**Judge's Task:**")
                    st.markdown("""
                    1. Identify the PRIMARY root cause (not just symptoms)
                    2. Map causal relationships between agent findings
                    3. Determine which agent(s) identified the root cause vs symptoms
                    4. Create a prioritized remediation plan
                    5. Assess each agent's correctness
                    """)
                
                try:
                    with st.spinner("⚖️ Judge is deliberating and synthesizing findings from all agents..."):
                        judge = JudgeAgent()
                        analyses_list = list(st.session_state.agent_results.values())
                        verdict = judge.adjudicate(analyses_list)
                        st.session_state.judge_verdict = verdict
                        logger.info("Judge completed adjudication")
                except Exception as e:
                    st.error(f"❌ Judge failed: {str(e)}")
                    logger.error(f"Judge failed: {e}")
                    return
            
            # Display verdict with reasoning process
            if st.session_state.judge_verdict:
                st.markdown("---")
                st.subheader("🎯 Final Verdict: Judge's Synthesis")
                st.markdown("**The Judge synthesizes all agent findings to determine the true root cause.**")
                
                verdict = st.session_state.judge_verdict
                
                # Show the synthesis process
                st.success("## ⚖️ FINAL VERDICT")
                
                # Root Cause - Most important
                st.markdown("### 🎯 Root Cause Determination")
                st.info(f"**{verdict.root_cause}**")
                st.markdown("---")
                
                # Show how Judge synthesized the findings
                st.markdown("### 🔍 Synthesis Process")
                st.markdown("**How the Judge reached this conclusion:**")
                
                # Parse the verdict to show reasoning
                verdict_parts = verdict.final_verdict.split("\n")
                for part in verdict_parts[:5]:  # Show first 5 lines
                    if part.strip():
                        st.markdown(f"- {part.strip()}")
                
                st.markdown("---")
                
                # Full Verdict
                st.markdown("### 📊 Complete Verdict")
                with st.expander("📄 Full Verdict Details", expanded=False):
                    st.markdown(verdict.final_verdict)
                
                st.markdown("---")
                
                # Remediation Plan
                st.markdown("### 🔧 Remediation Plan")
                st.markdown("**Prioritized steps to fix the root cause:**")
                remediation_lines = verdict.remediation_plan.split("\n")
                for line in remediation_lines:
                    if line.strip():
                        st.markdown(f"- {line.strip()}")
                
                st.markdown("---")
                
                # Agent Assessment - Show who was right/wrong
                st.markdown("### 📈 Agent Assessment: Who Was Right?")
                st.markdown("**The Judge evaluates each agent's analysis:**")
                
                assessment_cols = st.columns(len(verdict.agent_assessment))
                for col, (agent_name, assessment) in zip(assessment_cols, verdict.agent_assessment.items()):
                    with col:
                        # Color code the assessment
                        if "correct" in assessment.lower() or "right" in assessment.lower():
                            st.success(f"✅ **{agent_name}**\n\n{assessment}")
                        elif "partial" in assessment.lower():
                            st.warning(f"⚠️ **{agent_name}**\n\n{assessment}")
                        else:
                            st.info(f"ℹ️ **{agent_name}**\n\n{assessment}")
                
                # Show the reasoning chain
                st.markdown("---")
                st.markdown("### 🔗 Causal Chain Analysis")
                st.markdown("**How the Judge identified the root cause vs symptoms:**")
                
                # Extract key insights from root_cause
                root_cause_text = verdict.root_cause
                if "symptom" in root_cause_text.lower() or "caused" in root_cause_text.lower():
                    st.info("🔍 The Judge identified a causal relationship - one issue caused others.")
                if "deadlock" in root_cause_text.lower() and "timeout" in root_cause_text.lower():
                    st.warning("📊 **Example**: Database deadlock → Network timeout (symptom)")
                if "memory" in root_cause_text.lower() or "leak" in root_cause_text.lower():
                    st.warning("📊 **Example**: Memory leak → Performance degradation (symptom)")
                
                st.markdown(f"**Full Analysis:** {root_cause_text}")
    else:
        st.warning("⚠️ Enter your Google API Key in the sidebar to analyze incidents")
    
    # Auto-refresh mechanism
    time.sleep(POLL_INTERVAL)
    st.rerun()


def render_sidebar() -> str:
    """Render sidebar and return API key."""
    with st.sidebar:
        st.title(f"{APP_ICON} War Room")
        st.markdown("---")
        
        # API Key input (optional - auto-loaded from .env)
        env_api_key = os.getenv("GOOGLE_API_KEY", "")
        if env_api_key:
            st.success("✅ API Key loaded from .env")
            if not st.session_state.api_key:
                st.session_state.api_key = env_api_key
        else:
            st.warning("⚠️ No API key in .env file")
            api_key_input = st.text_input(
                "Google API Key (Optional)",
                type="password",
                value=st.session_state.api_key or "",
                help="Enter API key manually or set GOOGLE_API_KEY in .env file",
                key="api_key_input"
            )
            if api_key_input:
                st.session_state.api_key = api_key_input
        
        # Return the API key (from env or session state)
        return st.session_state.api_key or env_api_key
        
        st.markdown("---")
        
        # Server status
        st.subheader("🔌 Server Status")
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                st.success("✅ Webhook server online")
            else:
                st.warning("⚠️ Server responding with errors")
        except:
            st.error("❌ Webhook server offline")
            st.info("💡 Start server: `python server.py`")
        
        st.markdown("---")
        
        # Help
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            **Chaos Simulator Tab:**
            1. Select scenario category and issue
            2. Click "TRIGGER INCIDENT"
            3. Incident sent to webhook server
            
            **War Room Tab:**
            1. Auto-detects new incidents
            2. Triggers only relevant agents
            3. Judge synthesizes findings
            """)


def main() -> None:
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    api_key = render_sidebar()
    
    # Create tabs
    tab1, tab2 = st.tabs(["⚡ Chaos Simulator", "🔥 War Room"])
    
    with tab1:
        render_chaos_simulator_tab(api_key)
    
    with tab2:
        render_war_room_tab(api_key)
    
    # Footer
    st.markdown("---")
    st.caption(
        f"**{APP_ICON} War Room** | Multi-Agent Root Cause Analysis System | "
        "Powered by Google Gemini"
    )


if __name__ == "__main__":
    main()
