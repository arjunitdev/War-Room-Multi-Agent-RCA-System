"""Utility functions for Google AI SDK client initialization and configuration."""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def get_google_ai_client(api_key: Optional[str] = None) -> bool:
    """
    Initialize the Google AI SDK client with API key.
    
    Args:
        api_key: Optional API key. If not provided, reads from GOOGLE_API_KEY env var.
    
    Returns:
        True if initialization was successful
    
    Raises:
        ValueError: If API key is not provided and not found in environment
    """
    try:
        if api_key:
            genai.configure(api_key=api_key)
            logger.info("Google AI client configured with provided API key")
        else:
            env_api_key = os.getenv("GOOGLE_API_KEY")
            if not env_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY not found. Please provide it via .env file or function parameter."
                )
            genai.configure(api_key=env_api_key)
            logger.info("Google AI client configured with environment API key")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Google AI client: {e}")
        raise ValueError(f"Failed to initialize Google AI client: {str(e)}")


def list_available_models() -> List[str]:
    """
    List all available models from the Google AI API.
    
    Returns:
        List of available model names
    """
    try:
        models = genai.list_models()
        model_names = [model.name for model in models if 'generateContent' in model.supported_generation_methods]
        logger.info(f"Found {len(model_names)} available models: {model_names}")
        return model_names
    except Exception as e:
        logger.warning(f"Failed to list models: {e}")
        return []


def get_available_model(preferred: str, fallbacks: List[str]) -> str:
    """
    Get the first available model from a list of preferred and fallback options.
    
    Args:
        preferred: Preferred model name
        fallbacks: List of fallback model names
        
    Returns:
        First available model name, or preferred if listing fails
    """
    try:
        available = list_available_models()
        if not available:
            logger.warning("Could not list models, using gemini-pro as safe default")
            return "gemini-pro"  # Safe default
        
        # Normalize model names - remove "models/" prefix if present
        available_normalized = [m.split("/")[-1] if "/" in m else m for m in available]
        logger.info(f"Available models: {available_normalized}")
        
        # Check preferred first, then fallbacks
        for model in [preferred] + fallbacks:
            # Try exact match first
            if model in available_normalized:
                logger.info(f"Selected available model: {model}")
                return model
            # Try partial match (e.g., "gemini-pro" matches "models/gemini-pro")
            for avail in available_normalized:
                if model in avail or avail in model:
                    logger.info(f"Selected available model (matched): {avail}")
                    return avail
        
        # If none match, use the first available model
        if available_normalized:
            selected = available_normalized[0]
            logger.info(f"No preferred model available, using first available: {selected}")
            return selected
        
    except Exception as e:
        logger.warning(f"Error checking available models: {e}, using gemini-pro as safe default")
    
    # Ultimate fallback - gemini-pro is most widely available
    return "gemini-pro"