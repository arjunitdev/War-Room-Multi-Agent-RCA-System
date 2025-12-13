"""Utility functions for cleaning JSON schemas for Google AI SDK."""

from typing import Any, Dict


def clean_schema_for_google_ai(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a JSON schema to remove fields that Google AI SDK doesn't support.
    
    Removes validation keywords like minLength, maxLength, minItems, ge, le, etc.
    that are not supported by Google AI SDK's response_schema.
    
    Args:
        schema: The JSON schema dictionary from Pydantic
    
    Returns:
        Cleaned schema dictionary compatible with Google AI SDK
    """
    # Create a copy to avoid modifying the original
    cleaned = schema.copy()
    
    # Fields to remove at root level
    root_fields_to_remove = ["title", "description", "additionalProperties"]
    for field in root_fields_to_remove:
        cleaned.pop(field, None)
    
    # Recursively clean properties
    if "properties" in cleaned:
        for prop_name, prop_value in cleaned["properties"].items():
            cleaned["properties"][prop_name] = _clean_property(prop_value)
    
    # Clean items if it's an array type
    if "items" in cleaned:
        cleaned["items"] = _clean_property(cleaned["items"])
    
    return cleaned


def _clean_property(prop: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a single property definition, removing unsupported validation keywords.
    
    Args:
        prop: Property definition dictionary
    
    Returns:
        Cleaned property definition
    """
    if not isinstance(prop, dict):
        return prop
    
    # Create a copy to avoid modifying the original
    cleaned = prop.copy()
    
    # Special handling for Dict types (objects with additionalProperties)
    # Google AI SDK requires OBJECT types to have non-empty properties
    # For Dict[str, str], we'll add example properties that the AI can use
    if cleaned.get("type") == "object":
        if "additionalProperties" in cleaned:
            # This is a Dict type - remove additionalProperties
            cleaned.pop("additionalProperties", None)
            if not cleaned.get("properties"):
                # Add example properties for common agent names
                # The AI can use these or add more as needed
                cleaned["properties"] = {
                    "DBA": {
                        "type": "string",
                        "description": "Assessment for DBA agent"
                    },
                    "Network": {
                        "type": "string", 
                        "description": "Assessment for Network Engineer agent"
                    },
                    "Auditor": {
                        "type": "string",
                        "description": "Assessment for Code Auditor agent"
                    }
                }
        elif not cleaned.get("properties"):
            # Empty object without properties - add placeholder
            cleaned["properties"] = {
                "placeholder": {
                    "type": "string",
                    "description": "Placeholder property"
                }
            }
    
    # Remove validation keywords that Google AI SDK doesn't support
    validation_keywords = [
        "title",
        "description",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "ge",  # greater or equal (Pydantic)
        "le",  # less or equal (Pydantic)
        "gt",  # greater than (Pydantic)
        "lt",  # less than (Pydantic)
        "pattern",
        "format",
        # Note: "additionalProperties" is handled specially above for Dict types
        # Note: "enum" is kept as Google AI SDK supports it (needed for Literal types)
    ]
    
    for keyword in validation_keywords:
        cleaned.pop(keyword, None)
    
    # Recursively clean nested properties
    if "properties" in cleaned:
        for nested_prop_name, nested_prop_value in cleaned["properties"].items():
            cleaned["properties"][nested_prop_name] = _clean_property(nested_prop_value)
    
    # Clean items if it's an array type
    if "items" in cleaned:
        cleaned["items"] = _clean_property(cleaned["items"])
    
    # Clean anyOf, oneOf, allOf if present
    for keyword in ["anyOf", "oneOf", "allOf"]:
        if keyword in cleaned:
            cleaned[keyword] = [
                _clean_property(item) if isinstance(item, dict) else item
                for item in cleaned[keyword]
            ]
    
    return cleaned

