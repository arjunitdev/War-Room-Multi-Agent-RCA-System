"""Multi-payload scenario library for Chaos Simulator.

Each scenario contains 3 sequential payloads that fire with delays
to simulate cascading incidents in real-world systems.
"""

from typing import Dict, List, Any

SCENARIOS: Dict[str, List[Dict[str, Any]]] = {
    "Classic DB Deadlock": [
        {
            "source": "CODE",
            "alert_name": "App-Health-Check",
            "severity": "HEALTHY",
            "delay": 0,
            "logs": "Health Check: PASS. No recent deployments."
        },
        {
            "source": "DATABASE",
            "alert_name": "DB-Deadlock-Critical",
            "severity": "CRITICAL",
            "delay": 1,
            "logs": """2025-12-12 10:00:01 [INFO] TxID 991: UPDATE users SET bal=bal-10 WHERE id=1
2025-12-12 10:00:01 [INFO] TxID 992: UPDATE users SET bal=bal+10 WHERE id=2
2025-12-12 10:00:02 [ERROR] ERROR 1213: Deadlock found. TxID 991 waiting for lock held by 992.
2025-12-12 10:00:02 [ERROR] Transaction Rolled Back."""
        },
        {
            "source": "NETWORK",
            "alert_name": "API-Gateway-Timeout",
            "severity": "WARNING",
            "delay": 3,
            "logs": """10:00:01 [INFO] POST /transfer - Forwarding to DB
10:00:04 [ERROR] 504 Gateway Timeout: Upstream closed connection unexpectedly."""
        }
    ],
    
    "Cascading Table Lock": [
        {
            "source": "CODE",
            "alert_name": "Job-Scheduler-Log",
            "severity": "WARNING",
            "delay": 0,
            "logs": """10:15:00 [INFO] Starting Job: Monthly_Analytics_Report
10:15:00 [WARN] Running unoptimized full-table scan on 'orders' table."""
        },
        {
            "source": "DATABASE",
            "alert_name": "DB-Lock-Wait-Timeout",
            "severity": "CRITICAL",
            "delay": 5,
            "logs": """10:15:05 [WARN] Process 502 (INSERT INTO orders) blocked for 5000ms.
10:15:05 [WARN] Process 503 (INSERT INTO orders) blocked for 5000ms.
10:15:05 [INFO] Blocking Process: 400 (SELECT * FROM orders) - Time: 5s"""
        },
        {
            "source": "NETWORK",
            "alert_name": "High-Latency-Alert",
            "severity": "CRITICAL",
            "delay": 6,
            "logs": """10:15:06 [ERROR] Average API Latency: 5200ms (Threshold: 200ms).
10:15:06 [ERROR] Queue Depth: 500 requests pending."""
        }
    ],
    
    "Zombie Transaction": [
        {
            "source": "CODE",
            "alert_name": "App-Exception-Log",
            "severity": "CRITICAL",
            "delay": 0,
            "logs": """10:30:00 [INFO] Transaction Started.
10:30:00 [ERROR] JSONDecodeError: Expecting value: line 1 column 1 (char 0).
10:30:00 [WARN] Thread terminated without closing DB connection context!"""
        },
        {
            "source": "DATABASE",
            "alert_name": "DB-Connection-Warning",
            "severity": "WARNING",
            "delay": 10,
            "logs": """10:30:10 [INFO] Active Connections: 45/50.
10:30:10 [WARN] 15 connections in 'Sleep' state for > 10 seconds holding locks."""
        },
        {
            "source": "NETWORK",
            "alert_name": "503-Service-Unavailable",
            "severity": "CRITICAL",
            "delay": 15,
            "logs": """10:30:15 [ERROR] 503 Service Unavailable: No DB connections available in pool."""
        }
    ]
}


def get_scenario(scenario_name: str) -> List[Dict[str, Any]]:
    """
    Get a scenario by name.
    
    Args:
        scenario_name: Name of the scenario (e.g., "Classic DB Deadlock")
    
    Returns:
        List of payload dictionaries for the scenario
    
    Raises:
        KeyError: If scenario not found
    """
    if scenario_name not in SCENARIOS:
        raise KeyError(f"Scenario '{scenario_name}' not found. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_name]


def list_all_scenarios() -> List[str]:
    """List all available scenario names."""
    return list(SCENARIOS.keys())
