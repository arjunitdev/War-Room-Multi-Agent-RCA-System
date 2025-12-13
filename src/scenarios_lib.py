"""Scenario payload library - Independent webhook scenarios for each agent type."""

from typing import Dict, Any

# Each scenario is completely independent and triggers only its respective agent(s)
SCENARIOS: Dict[str, Dict[str, Any]] = {
    # ============================================
    # NETWORK CATEGORY - Triggers Network Agent
    # ============================================
    
    "NET_TIMEOUT": {
        "alert_name": "Gateway Timeout (504) - Standard Network Issue",
        "severity": "CRITICAL",
        "triggered_agents": ["Network Engineer"],  # Only Network agent analyzes this
        "logs": {
            "db": "No database errors detected. All connections healthy.",
            "network": "504 Gateway Timeout - Request ID: req-789. Timestamp: 2024-01-15T14:23:47Z. Response time: 30000ms. Load balancer: lb-prod-01. Target server: app-server-03. Connection timeout after 30 seconds. Retry attempts: 3 failed.",
            "app_code_diff": "No recent code changes. Last deployment: 2024-01-14 10:00:00 (24 hours ago)."
        }
    },
    
    "NET_DNS_FAIL": {
        "alert_name": "DNS Resolution Failure - Cascading Network Issue",
        "severity": "CRITICAL",
        "triggered_agents": ["Network Engineer"],  # Only Network agent analyzes this
        "logs": {
            "db": "Connection successful (Localhost). Database operations normal. No errors in transaction logs.",
            "network": "ERROR: getaddrinfo EAI_AGAIN (DNS Lookup Failed for internal-api.svc.cluster.local). Timestamp: 2024-01-15T14:25:12Z. Service discovery failure. All external API calls failing. Retry attempts exhausted. Error code: EAI_AGAIN - Temporary failure in name resolution.",
            "app_code_diff": "No recent changes. Codebase stable. Last commit: 2024-01-13 (2 days ago)."
        }
    },
    
    "NET_PACKET_LOSS": {
        "alert_name": "Intermittent Packet Loss (15%) - Subtle Network Degradation",
        "severity": "WARNING",
        "triggered_agents": ["Network Engineer"],  # Only Network agent analyzes this
        "logs": {
            "db": "Database connections stable. Query performance normal. No connection drops detected.",
            "network": "Packet loss detected: 15% average over last 5 minutes. Intermittent connectivity issues. Latency spikes: 50ms baseline → 200ms peaks. Network interface: eth0 showing retransmissions. TCP retries increasing. No complete connection failures, but degraded performance.",
            "app_code_diff": "No code changes. Application code unchanged for 3 days."
        }
    },
    
    # ============================================
    # DATABASE CATEGORY - Triggers DBA Agent
    # ============================================
    
    "DB_DEADLOCK": {
        "alert_name": "Database Deadlock Detected - Standard DB Issue",
        "severity": "CRITICAL",
        "triggered_agents": ["DBA"],  # Only DBA agent analyzes this
        "logs": {
            "db": "ERROR 1213: Deadlock found when trying to get lock; try restarting transaction. Process ID 402 waiting for access. Transaction started at 2024-01-15 14:23:45. Lock wait timeout exceeded. Query: SELECT * FROM Users WHERE id = 123 FOR UPDATE; Conflicting transaction: Process ID 401 holding lock on same row.",
            "network": "504 Gateway Timeout - Request ID: req-789. Timestamp: 2024-01-15T14:23:47Z. Response time: 2000ms. Load balancer: lb-prod-01. Target server: app-server-03. Connection timeout after 2000ms. (Note: This is a SYMPTOM caused by the deadlock)",
            "app_code_diff": "Commit #404: Added explicit table locking in user_update.py. Changed transaction isolation level. File: src/api/users.py, Lines: 45-52."
        }
    },
    
    "DB_POOL_EXHAUSTED": {
        "alert_name": "Database Connection Pool Exhausted - Cascading DB Issue",
        "severity": "CRITICAL",
        "triggered_agents": ["DBA"],  # Only DBA agent analyzes this
        "logs": {
            "db": "ERROR: Connection pool exhausted. Max connections: 100, Active: 100, Waiting: 45. All database connections in use. Traffic spike detected: 5000 requests/min (normal: 500). Connection wait queue full. New connection requests being rejected.",
            "network": "503 Service Unavailable - All backend servers reporting connection failures. Load balancer health checks failing. Response time: N/A (no connections available).",
            "app_code_diff": "No recent code changes. Last deployment: 2024-01-14. Traffic spike from external source detected."
        }
    },
    
    "DB_SLOW_QUERY": {
        "alert_name": "Missing Index / Slow Query - Subtle DB Performance Issue",
        "severity": "WARNING",
        "triggered_agents": ["DBA"],  # Only DBA agent analyzes this
        "logs": {
            "db": "Slow query detected: SELECT * FROM orders WHERE customer_email = ? AND status = ? ORDER BY created_at DESC. Execution time: 8.5 seconds. Table: orders (2.5M rows). Missing index on (customer_email, status). Full table scan performed. Query frequency: 120 queries/minute.",
            "network": "Latency increasing gradually: 100ms → 500ms → 2000ms over last 30 minutes. No timeouts yet, but response times degrading.",
            "app_code_diff": "No recent code changes. Query pattern unchanged. Application code stable."
        }
    },
    
    # ============================================
    # CODE CATEGORY - Triggers Code Auditor Agent
    # ============================================
    
    "CODE_SYNTAX": {
        "alert_name": "Syntax/Logic Crash - Immediate 500 Error",
        "severity": "CRITICAL",
        "triggered_agents": ["Code Auditor"],  # Only Code Auditor analyzes this
        "logs": {
            "db": "Database connection healthy. No database errors.",
            "network": "500 Internal Server Error - Request ID: req-890. Timestamp: 2024-01-15T14:30:00Z. Application crashed during request processing.",
            "app_code_diff": "Commit #505: Modified user_authentication.py. Added new validation logic. Error: NameError: name 'validate_user' is not defined. File: src/auth/user_authentication.py, Line 45. Syntax error introduced in latest deployment."
        }
    },
    
    "CODE_MEM_LEAK": {
        "alert_name": "Memory Leak (OOM) - Cascading Code Issue",
        "severity": "CRITICAL",
        "triggered_agents": ["Code Auditor"],  # Only Code Auditor analyzes this
        "logs": {
            "db": "Connection dropped. Database connections being terminated due to application memory pressure. Out of memory errors in application logs.",
            "network": "Latency increasing: 100ms → 5s → Timeout. Application response times degrading. Memory exhaustion causing process slowdowns.",
            "app_code_diff": "Commit #506: Created global list cache but never cleared it. File: src/cache/global_cache.py. Added: global_cache = [] in module scope. Items appended but never removed. Memory usage: 500MB → 2GB → 4GB over 2 hours."
        }
    },
    
    "CODE_INFINITE_LOOP": {
        "alert_name": "Infinite Loop - CPU Spike, No Crash",
        "severity": "WARNING",
        "triggered_agents": ["Code Auditor"],  # Only Code Auditor analyzes this
        "logs": {
            "db": "Database connections stable. No database errors. Query performance normal.",
            "network": "Response times increasing: 200ms → 2s → 10s. CPU usage: 95% on app-server-02. No crashes, but application unresponsive.",
            "app_code_diff": "Commit #507: Added retry logic in payment_processor.py. File: src/payments/processor.py, Lines: 120-135. While loop condition: while retry_count < max_retries: but retry_count never incremented inside loop. Infinite loop detected in payment retry logic."
        }
    }
}


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Get a scenario by ID.
    
    Args:
        scenario_id: Scenario identifier (e.g., "DB_DEADLOCK")
    
    Returns:
        Scenario payload dictionary
    
    Raises:
        KeyError: If scenario not found
    """
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Scenario '{scenario_id}' not found. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]


def get_scenarios_by_category() -> Dict[str, Dict[str, str]]:
    """
    Get scenarios organized by category.
    
    Returns:
        Dictionary with category keys and scenario mappings
    """
    return {
        "Network": {
            "NET_TIMEOUT": "Gateway Timeout (504) - Standard",
            "NET_DNS_FAIL": "DNS Resolution Fail - Cascading",
            "NET_PACKET_LOSS": "Packet Loss (15%) - Subtle"
        },
        "Database": {
            "DB_DEADLOCK": "Deadlock Detected - Standard",
            "DB_POOL_EXHAUSTED": "Connection Pool Exhausted - Cascading",
            "DB_SLOW_QUERY": "Missing Index / Slow Query - Subtle"
        },
        "Code": {
            "CODE_SYNTAX": "Syntax/Logic Crash - Standard",
            "CODE_MEM_LEAK": "Memory Leak (OOM) - Cascading",
            "CODE_INFINITE_LOOP": "Infinite Loop - Subtle"
        }
    }


def list_all_scenarios() -> list[str]:
    """List all available scenario IDs."""
    return list(SCENARIOS.keys())

