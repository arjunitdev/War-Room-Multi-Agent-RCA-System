"""Specialist agent classes for incident analysis with robust error handling."""

import json
import logging
import time
from typing import Dict, Any
import google.generativeai as genai

from .schemas import AgentAnalysis
from .schema_utils import clean_schema_for_google_ai
from .utils import get_available_model

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1
REQUEST_TIMEOUT_SECONDS = 60


class SpecialistAgent:
    """
    A specialist AI agent that analyzes specific types of incident data.
    
    This agent uses Google's Gemini model to perform structured analysis
    of logs, code diffs, or other incident-related data based on its
    specialized role and expertise.
    """
    
    def __init__(
        self,
        name: str,
        role_definition: str,
        model_name: str = None,  # Will default to gemini-pro
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize a specialist agent.
        
        Args:
            name: Name of the agent (e.g., "DBA", "Network Engineer")
            role_definition: System instruction defining the agent's role and expertise
            model_name: Gemini model to use (default: gemini-1.5-flash-latest)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.name = name
        self.role_definition = role_definition
        self.max_retries = max_retries
        self._model = None  # Lazy initialization
        self._model_name = None  # Will be set during initialization
        logger.info(f"Initialized {name} agent (model will be auto-detected on first use)")
    
    @property
    def model(self):
        """Lazy initialization of the model."""
        if self._model is None:
            self._model = self._initialize_model()
            logger.info(f"{self.name} agent model initialized: {self.model_name}")
        return self._model
    
    @property
    def model_name(self):
        """Get the model name (will be set during initialization)."""
        if self._model_name is None:
            # Trigger initialization if not done yet
            _ = self.model
        return self._model_name
    
    def _initialize_model(self):
        """
        Initialize the model by auto-detecting available models.
        
        Returns:
            Initialized GenerativeModel instance
        """
        try:
            # List available models
            logger.info(f"{self.name}: Listing available models...")
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            
            if not model_names:
                raise ValueError("No models found that support generateContent")
            
            logger.info(f"{self.name}: Found {len(model_names)} available models")
            
            # Extract model IDs (remove "models/" prefix)
            model_ids = [m.split("/")[-1] if "/" in m else m for m in model_names]
            logger.info(f"{self.name}: Available model IDs: {model_ids}")
            
            # Try models in order of preference
            # NOTE: Only include models that are known to work reliably
            preferred_order = [
                "gemini-pro",           # Most stable and widely available
                "gemini-1.5-pro",       # Newer pro (if available)
                "gemini-1.0-pro",       # Older pro (if available)
            ]
            # Removed gemini-1.5-flash as it causes 404 errors for many API keys
            
            model_to_use = None
            
            # First, try preferred models
            for preferred in preferred_order:
                if preferred in model_ids:
                    model_to_use = preferred
                    logger.info(f"{self.name}: Using preferred model: {model_to_use}")
                    break
            
            # If no preferred model found, use the first available
            if not model_to_use:
                model_to_use = model_ids[0]
                logger.info(f"{self.name}: Using first available model: {model_to_use}")
            
            # Try to initialize models, starting with preferred, then any available
            models_to_try = [model_to_use] + [m for m in model_ids if m != model_to_use]
            
            last_error = None
            for model_id in models_to_try:
                try:
                    logger.info(f"{self.name}: Attempting to initialize model: {model_id}")
                    model = genai.GenerativeModel(model_id)
                    self._model_name = model_id
                    logger.info(f"{self.name}: Successfully initialized model: {model_id}")
                    return model
                except Exception as e:
                    last_error = e
                    logger.warning(f"{self.name}: Model {model_id} failed: {e}")
                    continue
            
            # If all models failed
            raise ValueError(
                f"{self.name}: Failed to initialize any model. "
                f"Tried: {models_to_try}. "
                f"Last error: {last_error}. "
                f"Please verify your API key has access to Gemini models."
            )
            
        except Exception as e:
            error_msg = (
                f"{self.name}: Failed to initialize model. "
                f"Error: {str(e)}. "
                f"Please verify your API key has access to Gemini models."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def analyze(self, context_data: str) -> AgentAnalysis:
        """
        Analyze the provided context data and return structured analysis.
        
        This method includes retry logic for transient failures and robust
        error handling for various failure modes.
        
        Args:
            context_data: The log data or code diff to analyze
        
        Returns:
            AgentAnalysis object with the agent's findings
        
        Raises:
            ValueError: If response parsing fails
            Exception: If API call fails after all retries
        """
        if not context_data or not context_data.strip():
            raise ValueError(f"{self.name}: Cannot analyze empty context data")
        
        # Prepare schema and prompt
        schema = self._prepare_schema()
        prompt = self._construct_prompt(context_data)
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema
        )
        
        # Attempt analysis with retries
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"{self.name}: Analysis attempt {attempt}/{self.max_retries}")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": REQUEST_TIMEOUT_SECONDS}
                )
                
                # Parse and validate response
                analysis = self._parse_response(response)
                logger.info(f"{self.name}: Analysis completed successfully")
                return analysis
                
            except json.JSONDecodeError as e:
                last_exception = e
                logger.warning(f"{self.name}: JSON parsing failed on attempt {attempt}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"{self.name}: Request failed on attempt {attempt}: {e}")
            
            # Wait before retrying (except on last attempt)
            if attempt < self.max_retries:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
        
        # All retries exhausted
        error_msg = f"{self.name}: Analysis failed after {self.max_retries} attempts"
        logger.error(f"{error_msg}: {last_exception}")
        raise Exception(f"{error_msg}: {str(last_exception)}")
    
    def _prepare_schema(self) -> Dict[str, Any]:
        """
        Prepare and clean the JSON schema for the response.
        
        Returns:
            Cleaned JSON schema dictionary
        """
        schema = AgentAnalysis.model_json_schema()
        return clean_schema_for_google_ai(schema)
    
    def _construct_prompt(self, context_data: str) -> str:
        """
        Construct the analysis prompt from role definition and context.
        
        Args:
            context_data: The log data or code diff to analyze
            
        Returns:
            Formatted prompt string
        """
        return f"""{self.role_definition}

You are analyzing the following incident data:

{context_data}

Analyze this data and provide your findings. Focus on identifying issues, their severity, and provide specific evidence from the logs.
"""
    
    def _parse_response(self, response) -> AgentAnalysis:
        """
        Parse and validate the API response into an AgentAnalysis object.
        
        Args:
            response: The response object from the API
            
        Returns:
            Validated AgentAnalysis object
            
        Raises:
            ValueError: If response cannot be parsed or validated
        """
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        if not response_text:
            raise ValueError(f"{self.name}: Received empty response from API")
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"{self.name}: Failed to parse JSON response: {response_text[:200]}")
            raise ValueError(f"Failed to parse agent response as JSON: {e}")
        
        # Filter out any unexpected fields
        expected_fields = set(AgentAnalysis.model_fields.keys())
        data = {k: v for k, v in data.items() if k in expected_fields}
        
        # Ensure agent name matches
        data["agent_name"] = self.name
        
        try:
            return AgentAnalysis(**data)
        except Exception as e:
            logger.error(f"{self.name}: Failed to validate response data: {data}")
            raise ValueError(f"Failed to validate agent analysis: {e}")


# Predefined agent role definitions
# These define the expertise and focus areas for each specialist agent

DBA_ROLE = """You are a Database Administrator (DBA) specialist analyzing database logs.

Your expertise includes:
- Database locks and deadlocks
- Query performance issues
- Transaction problems
- Connection pool exhaustion
- Index and query optimization issues

When analyzing logs, look for:
- Lock wait times and deadlock errors
- Slow query patterns
- Transaction conflicts
- Connection timeouts
- Resource contention

Provide specific evidence from the logs and assess the severity (Critical, Warning, or Healthy).
Be thorough but concise. Focus on actionable insights."""

NETWORK_ROLE = """You are a Network Engineer specialist analyzing network traces and logs.

Your expertise includes:
- Network latency and timeouts
- Load balancer issues
- Connection problems
- Gateway errors (502, 503, 504)
- DNS resolution issues
- Bandwidth and throughput problems

When analyzing logs, look for:
- Timeout errors (504 Gateway Timeout, etc.)
- Response time anomalies
- Connection failures
- Load balancer errors
- Network congestion indicators

Provide specific evidence from the logs and assess the severity (Critical, Warning, or Healthy).
Be thorough but concise. Focus on actionable insights."""

CODE_AUDITOR_ROLE = """You are a Code Auditor specialist analyzing code changes and diffs.

Your expertise includes:
- Logic errors in code
- Performance anti-patterns
- Race conditions
- Resource leaks
- Concurrency issues
- Recent code changes that could cause incidents

When analyzing code diffs, look for:
- Blocking operations in critical paths
- Missing error handling
- Performance bottlenecks
- Thread safety issues
- Resource management problems
- Changes that could cause timeouts or deadlocks

Provide specific evidence from the code diff and assess the severity (Critical, Warning, or Healthy).
Be thorough but concise. Focus on actionable insights."""
