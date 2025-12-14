"""Judge agent for synthesizing multiple agent analyses with production-grade reliability."""

import json
import logging
import time
from typing import List, Dict, Any
import google.generativeai as genai

from .schemas import AgentAnalysis, JudgeVerdict
from .schema_utils import clean_schema_for_google_ai
from .utils import get_available_model

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 90  # Longer timeout for the Judge (more complex reasoning)


class JudgeAgent:
    """
    Judge agent that synthesizes conflicting agent findings to determine root cause.
    
    This agent uses Google's Gemini Pro model (higher reasoning capability) to
    analyze multiple specialist reports, identify causal relationships, and
    provide a definitive root cause analysis with remediation plan.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-pro",
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize the Judge agent.
        
        Args:
            model_name: Gemini model to use (default: gemini-1.5-pro-latest for better reasoning)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.max_retries = max_retries
        self._model = None  # Lazy initialization
        self._model_name = None  # Will be set during initialization
        logger.info("Initialized Judge agent (model will be auto-detected on first use)")
    
    @property
    def model(self):
        """Lazy initialization of the model."""
        if self._model is None:
            self._model = self._initialize_model()
            logger.info(f"Judge agent model initialized: {self.model_name}")
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
            logger.info("Judge: Listing available models...")
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            
            if not model_names:
                raise ValueError("No models found that support generateContent")
            
            logger.info(f"Judge: Found {len(model_names)} available models")
            
            # Extract model IDs (remove "models/" prefix)
            model_ids = [m.split("/")[-1] if "/" in m else m for m in model_names]
            logger.info(f"Judge: Available model IDs: {model_ids}")
            
            # Try models in order of preference (prefer pro for better reasoning)
            # NOTE: Only include models that are known to work reliably
            preferred_order = [
                "gemini-pro",           # Most stable and widely available
                "gemini-1.5-pro",       # Best reasoning (if available)
                "gemini-1.0-pro",       # Older pro (if available)
            ]
            # Removed gemini-1.5-flash as it causes 404 errors for many API keys
            
            model_to_use = None
            
            # First, try preferred models
            for preferred in preferred_order:
                if preferred in model_ids:
                    model_to_use = preferred
                    logger.info(f"Judge: Using preferred model: {model_to_use}")
                    break
            
            # If no preferred model found, use the first available
            if not model_to_use:
                model_to_use = model_ids[0]
                logger.info(f"Judge: Using first available model: {model_to_use}")
            
            # Try to initialize models, starting with preferred, then any available
            models_to_try = [model_to_use] + [m for m in model_ids if m != model_to_use]
            
            last_error = None
            for model_id in models_to_try:
                try:
                    logger.info(f"Judge: Attempting to initialize model: {model_id}")
                    model = genai.GenerativeModel(model_id)
                    self._model_name = model_id
                    logger.info(f"Judge: Successfully initialized model: {model_id}")
                    return model
                except Exception as e:
                    last_error = e
                    logger.warning(f"Judge: Model {model_id} failed: {e}")
                    continue
            
            # If all models failed
            raise ValueError(
                f"Judge: Failed to initialize any model. "
                f"Tried: {models_to_try}. "
                f"Last error: {last_error}. "
                f"Please verify your API key has access to Gemini models."
            )
            
        except Exception as e:
            error_msg = (
                f"Judge: Failed to initialize model. "
                f"Error: {str(e)}. "
                f"Please verify your API key has access to Gemini models."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def synthesize_verdict(self, analyses: List[AgentAnalysis]) -> JudgeVerdict:
        """
        Synthesize multiple agent analyses to determine the true root cause.
        
        This method includes retry logic for transient failures and robust
        error handling. It analyzes all specialist reports to identify
        causal relationships and determine the primary root cause.
        
        Args:
            analyses: List of AgentAnalysis objects from specialist agents
        
        Returns:
            JudgeVerdict object with final decision
        
        Raises:
            ValueError: If analyses list is empty or response parsing fails
            Exception: If API call fails after all retries
        """
        if not analyses:
            raise ValueError("Judge: Cannot adjudicate with empty analyses list")
        
        logger.info(f"Judge: Beginning adjudication of {len(analyses)} agent reports")
        
        # Prepare schema and prompt
        schema = self._prepare_schema()
        prompt = self._construct_prompt(analyses)
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema
        )
        
        # Attempt adjudication with retries
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Judge: Adjudication attempt {attempt}/{self.max_retries}")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": REQUEST_TIMEOUT_SECONDS}
                )
                
                # Parse and validate response
                verdict = self._parse_response(response)
                logger.info("Judge: Adjudication completed successfully")
                return verdict
                
            except json.JSONDecodeError as e:
                last_exception = e
                logger.warning(f"Judge: JSON parsing failed on attempt {attempt}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Judge: Request failed on attempt {attempt}: {e}")
            
            # Wait before retrying (except on last attempt)
            if attempt < self.max_retries:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
        
        # All retries exhausted
        error_msg = f"Judge: Adjudication failed after {self.max_retries} attempts"
        logger.error(f"{error_msg}: {last_exception}")
        raise Exception(f"{error_msg}: {str(last_exception)}")
    
    def _prepare_schema(self) -> Dict[str, Any]:
        """
        Prepare and clean the JSON schema for the response.
        
        Returns:
            Cleaned JSON schema dictionary
        """
        schema = JudgeVerdict.model_json_schema()
        return clean_schema_for_google_ai(schema)
    
    def _construct_prompt(self, analyses: List[AgentAnalysis]) -> str:
        """
        Construct the adjudication prompt from agent analyses.
        
        Args:
            analyses: List of agent analyses to synthesize
            
        Returns:
            Formatted prompt string
        """
        # Format agent analyses for the prompt
        analyses_text = "\n\n".join([
            f"=== {analysis.agent_name} Analysis ===\n"
            f"Status: {analysis.status}\n"
            f"Hypothesis: {analysis.hypothesis}\n"
            f"Confidence: {analysis.confidence_score:.2f}\n"
            f"Evidence: {', '.join(analysis.evidence_cited)}\n"
            f"Reasoning: {analysis.reasoning}"
            for analysis in analyses
        ])
        
        JUDGE_ROLE = """You are a Senior Principal Engineer and Incident Commander.
Your Goal: Synthesize reports from Network, DBA, and Code Agents to find the single **Root Cause**.

### THE HIERARCHY OF CAUSALITY (Use this to find the Root Cause)

1. **CODE LOGIC IS KING (The "Bug" Check):**
   - If the Code Auditor finds a **LOGIC ERROR** (e.g., `JSONDecodeError`, `KeyError`, `ValueError`, `NullPointer`, `DivisionByZero`), **THIS IS THE ROOT CAUSE.**
   - *Reasoning:* These are internal code failures that happen regardless of infrastructure health.

2. **INFRASTRUCTURE EXCEPTIONS ARE NUANCED:**
   - If the Code Auditor *only* finds **CONNECTIVITY ERRORS** (e.g., `ConnectionRefused`, `Timeout`, `503 Service Unavailable`), **DO NOT** automatically blame the code.
   - CHECK THE DBA:
     - If DBA shows "Deadlocks" or "Sleep > 10s" -> **Database is Root Cause.**
     - If DBA is Healthy -> **Network/Infrastructure is Root Cause.**

3. **DATABASE IS SECONDARY:**
   - If Code is totally healthy (no logic errors), look at the DBA.
   - **Deadlocks** (Error 1213) or **Lock Wait Timeouts** are the Root Cause here.
   - *Note:* If the DB is full of "Sleeping" connections, blame the **Code** only if the Code Auditor also shows a missing close/rollback (Logic Error).

### TIMELINE FORENSICS
- **Look at the Timestamps:** The event that happened at **T+0s** is the trigger.
- If a `JSONDecodeError` (Code) happens at T+0, and DB Connections spike at T+2, the Code is guilty.

### OUTPUT FORMAT (JSON)
{
  "root_cause_headline": "The one-sentence summary of the failure.",
  "root_cause_agent": "The agent who found the PRIMARY failure.",
  "scenarios_logic": "Explain the chain: Trigger -> Mechanism -> Symptom.",
  "remediation_plan": "Specific technical steps (e.g., 'Wrap JSON parsing in try/finally')."
}"""
        
        return f"""{JUDGE_ROLE}

Agent Reports:
{analyses_text}

Synthesize these findings and determine the root cause. Follow the hierarchy of causality above and provide your analysis in the specified JSON format."""
    
    def _parse_response(self, response) -> JudgeVerdict:
        """
        Parse and validate the API response into a JudgeVerdict object.
        
        Args:
            response: The response object from the API
            
        Returns:
            Validated JudgeVerdict object
            
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
            raise ValueError("Judge: Received empty response from API")
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Judge: Failed to parse JSON response: {response_text[:200]}")
            raise ValueError(f"Failed to parse judge response as JSON: {e}")
        
        # Filter out any unexpected fields
        expected_fields = set(JudgeVerdict.model_fields.keys())
        data = {k: v for k, v in data.items() if k in expected_fields}
        
        try:
            return JudgeVerdict(**data)
        except Exception as e:
            logger.error(f"Judge: Failed to validate response data: {data}")
            raise ValueError(f"Failed to validate judge verdict: {e}")