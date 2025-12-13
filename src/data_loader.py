"""Data loader for incident scenarios."""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class IncidentScenario:
    """Represents an incident scenario with DB logs, network logs, and code diff."""
    
    def __init__(self, name: str, db_logs: str, network_logs: str, code_diff: str):
        """
        Initialize an incident scenario.
        
        Args:
            name: Name of the scenario
            db_logs: Database log content
            network_logs: Network log content
            code_diff: Code diff content
        """
        self.name = name
        self.db_logs = db_logs
        self.network_logs = network_logs
        self.code_diff = code_diff
    
    def to_dict(self) -> Dict[str, str]:
        """Convert scenario to dictionary."""
        return {
            "name": self.name,
            "db_logs": self.db_logs,
            "network_logs": self.network_logs,
            "code_diff": self.code_diff
        }


def load_scenario(filename: str) -> Dict[str, str]:
    """
    Load a scenario from a JSON file in the scenarios/ directory.
    
    Args:
        filename: Name of the scenario file (e.g., "deadlock.json")
    
    Returns:
        Dictionary with keys: name, db_logs, network_logs, code_diff
    
    Raises:
        FileNotFoundError: If scenario file doesn't exist
        ValueError: If scenario file is invalid JSON or missing required fields
    """
    # Get the scenarios directory (parent of src/)
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenario_path = scenarios_dir / filename
    
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    
    try:
        with open(scenario_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in scenario file: {e}")
    
    # Validate required fields
    required_fields = ["name", "db_logs", "network_logs", "code_diff"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in scenario: {field}")
    
    return {
        "name": data["name"],
        "db_logs": data["db_logs"],
        "network_logs": data["network_logs"],
        "code_diff": data["code_diff"]
    }


def list_scenarios() -> list[str]:
    """
    List all available scenario files in the scenarios/ directory.
    
    Returns:
        List of scenario filenames (e.g., ["deadlock.json"])
    """
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    if not scenarios_dir.exists():
        return []
    
    return [
        f.name for f in scenarios_dir.iterdir()
        if f.is_file() and f.suffix == ".json"
    ]



