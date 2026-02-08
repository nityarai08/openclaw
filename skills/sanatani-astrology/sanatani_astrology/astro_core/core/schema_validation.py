"""
JSON schema validation for component interfaces.

This module provides schema validation for data exchange between components
to ensure data integrity and compatibility.
"""

import json
from typing import Dict, Any, List
from jsonschema import validate, ValidationError, Draft7Validator
from .data_models import ValidationResult


class SchemaValidator:
    """JSON schema validator for component interfaces."""
    
    def __init__(self):
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load all JSON schemas for validation."""
        return {
            'kundali_data': self._get_kundali_schema(),
            'layer_data': self._get_layer_data_schema(),
            'birth_details': self._get_birth_details_schema(),
            'configuration': self._get_configuration_schema()
        }
    
    def validate_kundali_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate kundali data against schema."""
        return self._validate_against_schema(data, 'kundali_data')
    
    def validate_layer_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate layer data against schema."""
        return self._validate_against_schema(data, 'layer_data')
    
    def validate_birth_details(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate birth details against schema."""
        return self._validate_against_schema(data, 'birth_details')
    
    def validate_configuration(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema."""
        return self._validate_against_schema(data, 'configuration')
    
    def _validate_against_schema(self, data: Dict[str, Any], schema_name: str) -> ValidationResult:
        """Validate data against specified schema."""
        result = ValidationResult(is_valid=True)
        
        if schema_name not in self.schemas:
            result.add_error(f"Unknown schema: {schema_name}")
            return result
        
        try:
            validate(instance=data, schema=self.schemas[schema_name])
        except ValidationError as e:
            result.add_error(f"Schema validation failed: {e.message}")
            if e.path:
                result.add_error(f"Error path: {' -> '.join(str(p) for p in e.path)}")
        except Exception as e:
            result.add_error(f"Validation error: {str(e)}")
        
        return result
    
    def _get_kundali_schema(self) -> Dict[str, Any]:
        """Get JSON schema for kundali data."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "schema_version": {"type": "string"},
                "generation_timestamp": {"type": ["string", "null"]},
                "birth_details": {
                    "type": ["object", "null"],
                    "properties": {
                        "date": {"type": "string", "format": "date"},
                        "time": {"type": "string"},
                        "place": {"type": "string"},
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                        "timezone_offset": {"type": "number", "minimum": -12, "maximum": 14}
                    },
                    "required": ["date", "time", "place", "latitude", "longitude", "timezone_offset"]
                },
                "astronomical_data": {"type": "object"},
                "planetary_positions": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-z_]+$": {
                            "type": "object",
                            "properties": {
                                "longitude": {"type": "number", "minimum": 0, "maximum": 360},
                                "rasi": {"type": "integer", "minimum": 0, "maximum": 11},
                                "nakshatra": {"type": "integer", "minimum": 0, "maximum": 26},
                                "degree_in_sign": {"type": "number", "minimum": 0, "maximum": 30},
                                "retrograde": {"type": "boolean"}
                            },
                            "required": ["longitude", "rasi", "nakshatra", "degree_in_sign"]
                        }
                    }
                },
                "divisional_charts": {"type": "object"},
                "panchanga": {"type": "object"},
                "yogas_and_doshas": {"type": "object"},
                "dasha_periods": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["schema_version"]
        }
    
    def _get_layer_data_schema(self) -> Dict[str, Any]:
        """Get JSON schema for layer data."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "layer_info": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "minimum": 1, "maximum": 10},
                        "name": {"type": "string"},
                        "accuracy_rating": {"type": "number", "minimum": 0, "maximum": 1},
                        "methodology": {"type": "string"},
                        "description": {"type": "string"},
                        "calculation_factors": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["id", "name", "accuracy_rating", "methodology", "description"]
                },
                "annual_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "format": "date"},
                            "day_of_year": {"type": "integer", "minimum": 1, "maximum": 366},
                            "score": {"type": "number", "minimum": 0, "maximum": 1},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "contributing_factors": {"type": "object"}
                        },
                        "required": ["date", "day_of_year", "score", "confidence"]
                    },
                    "minItems": 365,
                    "maxItems": 366
                },
                "summary_statistics": {"type": "object"},
                "calculation_metadata": {"type": "object"}
            },
            "required": ["layer_info", "annual_data"]
        }
    
    def _get_birth_details_schema(self) -> Dict[str, Any]:
        """Get JSON schema for birth details."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "time": {"type": "string"},
                "place": {"type": "string", "minLength": 1},
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                "timezone_offset": {"type": "number", "minimum": -12, "maximum": 14}
            },
            "required": ["date", "time", "place", "latitude", "longitude", "timezone_offset"]
        }
    
    def _get_configuration_schema(self) -> Dict[str, Any]:
        """Get JSON schema for configuration."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "layer_weights": {
                    "type": "object",
                    "patternProperties": {
                        "^[1-9]|10$": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "additionalProperties": False
                },
                "calculation_parameters": {
                    "type": "object",
                    "properties": {
                        "ayanamsa": {"type": "string"},
                        "calculation_method": {"type": "string"},
                        "ephemeris_path": {"type": "string"},
                        "precision_level": {"type": "string", "enum": ["high", "medium", "low"]}
                    }
                },
                "visualization_settings": {
                    "type": "object",
                    "properties": {
                        "color_scheme": {"type": "string"},
                        "figure_size": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "export_format": {"type": "string", "enum": ["png", "svg", "pdf"]},
                        "dpi": {"type": "integer", "minimum": 72, "maximum": 600}
                    }
                }
            },
            "required": ["layer_weights", "calculation_parameters"]
        }