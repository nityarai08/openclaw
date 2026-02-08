"""
Comprehensive data validation and integrity checking system.

This module provides validation for all data types used in the favorability system,
including input validation, data integrity checking, quality assessment, and
automated correction suggestions.
"""

import re
import json
from datetime import datetime, time, date
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import math

from .data_models import (
    BirthDetails, PlanetaryPosition, KundaliData, LayerInfo,
    DailyScore, LayerData, ValidationResult, LocationData
)
from .error_handling import (
    ValidationError, ErrorContext, get_error_handler
)


@dataclass
class ValidationRule:
    """Represents a validation rule."""
    name: str
    description: str
    validator: Callable[[Any], bool]
    error_message: str
    severity: str = "error"  # "error", "warning", "info"
    auto_fix: Optional[Callable[[Any], Any]] = None
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a value against this rule."""
        try:
            is_valid = self.validator(value)
            return is_valid, None if is_valid else self.error_message
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def attempt_fix(self, value: Any) -> Tuple[bool, Any]:
        """Attempt to automatically fix the value."""
        if self.auto_fix:
            try:
                fixed_value = self.auto_fix(value)
                return True, fixed_value
            except Exception:
                return False, value
        return False, value


@dataclass
class ValidationRuleSet:
    """Collection of validation rules for a specific data type."""
    name: str
    rules: List[ValidationRule] = field(default_factory=list)
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate value against all rules."""
        result = ValidationResult(is_valid=True)
        
        for rule in self.rules:
            is_valid, error_msg = rule.validate(value)
            if not is_valid:
                if rule.severity == "error":
                    result.add_error(f"{rule.name}: {error_msg}")
                elif rule.severity == "warning":
                    result.add_warning(f"{rule.name}: {error_msg}")
        
        return result


class DataQualityAssessment:
    """Assess data quality and provide quality metrics."""
    
    def __init__(self):
        self.quality_metrics = {}
    
    def assess_birth_details_quality(self, birth_details: BirthDetails) -> Dict[str, float]:
        """Assess quality of birth details data."""
        quality_scores = {}
        
        # Date precision (1.0 for exact date, lower for estimated)
        quality_scores['date_precision'] = 1.0  # Assume exact unless indicated
        
        # Time precision (1.0 for exact time, lower for estimated)
        if birth_details.time.second == 0 and birth_details.time.microsecond == 0:
            if birth_details.time.minute == 0:
                quality_scores['time_precision'] = 0.7  # Hour precision
            else:
                quality_scores['time_precision'] = 0.9  # Minute precision
        else:
            quality_scores['time_precision'] = 1.0  # Second precision
        
        # Location precision (based on coordinate precision)
        lat_precision = len(str(birth_details.latitude).split('.')[-1]) if '.' in str(birth_details.latitude) else 0
        lon_precision = len(str(birth_details.longitude).split('.')[-1]) if '.' in str(birth_details.longitude) else 0
        avg_precision = (lat_precision + lon_precision) / 2
        quality_scores['location_precision'] = min(1.0, avg_precision / 6)  # 6 decimal places = high precision
        
        # Overall quality score
        quality_scores['overall'] = sum(quality_scores.values()) / len(quality_scores)
        
        return quality_scores
    
    def assess_kundali_data_quality(self, kundali_data: KundaliData) -> Dict[str, float]:
        """Assess quality of kundali data."""
        quality_scores = {}
        
        # Completeness score
        expected_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        present_planets = len([p for p in expected_planets if p in kundali_data.planetary_positions])
        quality_scores['planetary_completeness'] = present_planets / len(expected_planets)
        
        # Divisional chart completeness
        expected_charts = ['D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12']
        present_charts = len([c for c in expected_charts if c in kundali_data.divisional_charts])
        quality_scores['chart_completeness'] = present_charts / len(expected_charts)
        
        # Data consistency (check for reasonable planetary positions)
        consistency_score = 1.0
        for planet, position in kundali_data.planetary_positions.items():
            if not (0 <= position.longitude <= 360):
                consistency_score -= 0.1
            if not (0 <= position.rasi <= 11):
                consistency_score -= 0.1
            if not (0 <= position.nakshatra <= 26):
                consistency_score -= 0.1
        
        quality_scores['data_consistency'] = max(0.0, consistency_score)
        
        # Overall quality
        quality_scores['overall'] = sum(quality_scores.values()) / len(quality_scores)
        
        return quality_scores
    
    def assess_layer_data_quality(self, layer_data: LayerData) -> Dict[str, float]:
        """Assess quality of layer data."""
        quality_scores = {}
        
        # Data completeness (should have 365/366 days)
        expected_days = 366 if any(score.date.endswith('-02-29') for score in layer_data.annual_data) else 365
        actual_days = len(layer_data.annual_data)
        quality_scores['completeness'] = min(1.0, actual_days / expected_days)
        
        # Score validity (all scores should be between 0 and 1)
        valid_scores = sum(1 for score in layer_data.annual_data if 0 <= score.score <= 1)
        quality_scores['score_validity'] = valid_scores / len(layer_data.annual_data) if layer_data.annual_data else 0
        
        # Confidence consistency
        expected_confidence = layer_data.layer_info.accuracy_rating
        confidence_consistency = sum(1 for score in layer_data.annual_data 
                                   if abs(score.confidence - expected_confidence) < 0.01)
        quality_scores['confidence_consistency'] = confidence_consistency / len(layer_data.annual_data) if layer_data.annual_data else 0
        
        # Date sequence integrity
        if layer_data.annual_data:
            sorted_data = sorted(layer_data.annual_data, key=lambda x: x.date)
            sequence_correct = all(
                sorted_data[i].day_of_year == i + 1 
                for i in range(len(sorted_data))
            )
            quality_scores['date_sequence'] = 1.0 if sequence_correct else 0.0
        else:
            quality_scores['date_sequence'] = 0.0
        
        # Overall quality
        quality_scores['overall'] = sum(quality_scores.values()) / len(quality_scores)
        
        return quality_scores


class DataValidator:
    """Comprehensive data validator with rule management."""
    
    def __init__(self):
        self.rule_sets: Dict[str, ValidationRuleSet] = {}
        self.quality_assessor = DataQualityAssessment()
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default validation rules for all data types."""
        self._create_birth_details_rules()
        self._create_planetary_position_rules()
        self._create_kundali_data_rules()
        self._create_layer_data_rules()
        self._create_location_data_rules()
    
    def _create_birth_details_rules(self) -> None:
        """Create validation rules for birth details."""
        rule_set = ValidationRuleSet("birth_details")
        
        # Date validation
        rule_set.add_rule(ValidationRule(
            name="valid_date",
            description="Birth date must be a valid date",
            validator=lambda bd: isinstance(bd.date, datetime) and bd.date.year >= 1900,
            error_message="Birth date must be a valid date after 1900",
            auto_fix=lambda bd: BirthDetails(
                date=datetime(2000, 1, 1) if not isinstance(bd.date, datetime) else bd.date,
                time=bd.time, place=bd.place, latitude=bd.latitude, 
                longitude=bd.longitude, timezone_offset=bd.timezone_offset
            )
        ))
        
        # Time validation
        rule_set.add_rule(ValidationRule(
            name="valid_time",
            description="Birth time must be valid",
            validator=lambda bd: isinstance(bd.time, time),
            error_message="Birth time must be a valid time object"
        ))
        
        # Place validation
        rule_set.add_rule(ValidationRule(
            name="valid_place",
            description="Birth place must be provided",
            validator=lambda bd: isinstance(bd.place, str) and len(bd.place.strip()) > 0,
            error_message="Birth place must be a non-empty string",
            auto_fix=lambda bd: BirthDetails(
                date=bd.date, time=bd.time, place="Unknown",
                latitude=bd.latitude, longitude=bd.longitude, timezone_offset=bd.timezone_offset
            )
        ))
        
        # Latitude validation
        rule_set.add_rule(ValidationRule(
            name="valid_latitude",
            description="Latitude must be between -90 and 90 degrees",
            validator=lambda bd: -90 <= bd.latitude <= 90,
            error_message="Latitude must be between -90 and 90 degrees",
            auto_fix=lambda bd: BirthDetails(
                date=bd.date, time=bd.time, place=bd.place,
                latitude=max(-90, min(90, bd.latitude)),
                longitude=bd.longitude, timezone_offset=bd.timezone_offset
            )
        ))
        
        # Longitude validation
        rule_set.add_rule(ValidationRule(
            name="valid_longitude",
            description="Longitude must be between -180 and 180 degrees",
            validator=lambda bd: -180 <= bd.longitude <= 180,
            error_message="Longitude must be between -180 and 180 degrees",
            auto_fix=lambda bd: BirthDetails(
                date=bd.date, time=bd.time, place=bd.place, latitude=bd.latitude,
                longitude=max(-180, min(180, bd.longitude)),
                timezone_offset=bd.timezone_offset
            )
        ))
        
        # Timezone validation
        rule_set.add_rule(ValidationRule(
            name="valid_timezone",
            description="Timezone offset must be between -12 and 14 hours",
            validator=lambda bd: -12 <= bd.timezone_offset <= 14,
            error_message="Timezone offset must be between -12 and 14 hours",
            auto_fix=lambda bd: BirthDetails(
                date=bd.date, time=bd.time, place=bd.place,
                latitude=bd.latitude, longitude=bd.longitude,
                timezone_offset=max(-12, min(14, bd.timezone_offset))
            )
        ))
        
        self.rule_sets["birth_details"] = rule_set
    
    def _create_planetary_position_rules(self) -> None:
        """Create validation rules for planetary positions."""
        rule_set = ValidationRuleSet("planetary_position")
        
        # Longitude validation
        rule_set.add_rule(ValidationRule(
            name="valid_longitude",
            description="Planetary longitude must be between 0 and 360 degrees",
            validator=lambda pp: 0 <= pp.longitude <= 360,
            error_message="Planetary longitude must be between 0 and 360 degrees",
            auto_fix=lambda pp: PlanetaryPosition(
                longitude=pp.longitude % 360,
                rasi=pp.rasi, nakshatra=pp.nakshatra,
                degree_in_sign=pp.degree_in_sign, retrograde=pp.retrograde
            )
        ))
        
        # Rasi validation
        rule_set.add_rule(ValidationRule(
            name="valid_rasi",
            description="Rasi must be between 0 and 11",
            validator=lambda pp: 0 <= pp.rasi <= 11,
            error_message="Rasi must be between 0 and 11",
            auto_fix=lambda pp: PlanetaryPosition(
                longitude=pp.longitude, rasi=int(pp.longitude // 30),
                nakshatra=pp.nakshatra, degree_in_sign=pp.degree_in_sign,
                retrograde=pp.retrograde
            )
        ))
        
        # Nakshatra validation
        rule_set.add_rule(ValidationRule(
            name="valid_nakshatra",
            description="Nakshatra must be between 0 and 26",
            validator=lambda pp: 0 <= pp.nakshatra <= 26,
            error_message="Nakshatra must be between 0 and 26",
            auto_fix=lambda pp: PlanetaryPosition(
                longitude=pp.longitude, rasi=pp.rasi,
                nakshatra=int(pp.longitude // 13.333333),
                degree_in_sign=pp.degree_in_sign, retrograde=pp.retrograde
            )
        ))
        
        # Degree in sign validation
        rule_set.add_rule(ValidationRule(
            name="valid_degree_in_sign",
            description="Degree in sign must be between 0 and 30",
            validator=lambda pp: 0 <= pp.degree_in_sign <= 30,
            error_message="Degree in sign must be between 0 and 30",
            auto_fix=lambda pp: PlanetaryPosition(
                longitude=pp.longitude, rasi=pp.rasi, nakshatra=pp.nakshatra,
                degree_in_sign=pp.longitude % 30, retrograde=pp.retrograde
            )
        ))
        
        self.rule_sets["planetary_position"] = rule_set
    
    def _create_kundali_data_rules(self) -> None:
        """Create validation rules for kundali data."""
        rule_set = ValidationRuleSet("kundali_data")
        
        # Schema version validation
        rule_set.add_rule(ValidationRule(
            name="valid_schema_version",
            description="Schema version must be provided",
            validator=lambda kd: isinstance(kd.schema_version, str) and len(kd.schema_version) > 0,
            error_message="Schema version must be a non-empty string"
        ))
        
        # Birth details validation
        rule_set.add_rule(ValidationRule(
            name="birth_details_present",
            description="Birth details must be provided",
            validator=lambda kd: kd.birth_details is not None,
            error_message="Birth details must be provided"
        ))
        
        # Planetary positions validation
        rule_set.add_rule(ValidationRule(
            name="planetary_positions_present",
            description="Planetary positions must be provided",
            validator=lambda kd: len(kd.planetary_positions) > 0,
            error_message="At least one planetary position must be provided"
        ))
        
        # Essential planets validation
        rule_set.add_rule(ValidationRule(
            name="essential_planets_present",
            description="Essential planets (Sun, Moon, Lagna) must be present",
            validator=lambda kd: all(planet in kd.planetary_positions 
                                   for planet in ['sun', 'moon']),
            error_message="Essential planets (Sun, Moon) must be present",
            severity="warning"
        ))
        
        self.rule_sets["kundali_data"] = rule_set
    
    def _create_layer_data_rules(self) -> None:
        """Create validation rules for layer data."""
        rule_set = ValidationRuleSet("layer_data")
        
        # Layer info validation
        rule_set.add_rule(ValidationRule(
            name="layer_info_present",
            description="Layer info must be provided",
            validator=lambda ld: ld.layer_info is not None,
            error_message="Layer info must be provided"
        ))
        
        # Annual data validation
        rule_set.add_rule(ValidationRule(
            name="annual_data_present",
            description="Annual data must be provided",
            validator=lambda ld: len(ld.annual_data) > 0,
            error_message="Annual data must contain at least one day"
        ))
        
        # Data completeness validation
        rule_set.add_rule(ValidationRule(
            name="data_completeness",
            description="Annual data should contain 365 or 366 days",
            validator=lambda ld: 365 <= len(ld.annual_data) <= 366,
            error_message="Annual data should contain 365 or 366 days",
            severity="warning"
        ))
        
        # Score validity validation
        rule_set.add_rule(ValidationRule(
            name="valid_scores",
            description="All scores must be between 0 and 1",
            validator=lambda ld: all(0 <= score.score <= 1 for score in ld.annual_data),
            error_message="All scores must be between 0 and 1"
        ))
        
        # Confidence validity validation
        rule_set.add_rule(ValidationRule(
            name="valid_confidence",
            description="All confidence values must be between 0 and 1",
            validator=lambda ld: all(0 <= score.confidence <= 1 for score in ld.annual_data),
            error_message="All confidence values must be between 0 and 1"
        ))
        
        self.rule_sets["layer_data"] = rule_set
    
    def _create_location_data_rules(self) -> None:
        """Create validation rules for location data."""
        rule_set = ValidationRuleSet("location_data")
        
        # Place name validation
        rule_set.add_rule(ValidationRule(
            name="valid_place_name",
            description="Place name must be provided",
            validator=lambda ld: isinstance(ld.place_name, str) and len(ld.place_name.strip()) > 0,
            error_message="Place name must be a non-empty string"
        ))
        
        # Coordinate validation (same as birth details)
        rule_set.add_rule(ValidationRule(
            name="valid_coordinates",
            description="Coordinates must be valid",
            validator=lambda ld: (-90 <= ld.latitude <= 90) and (-180 <= ld.longitude <= 180),
            error_message="Coordinates must be valid (lat: -90 to 90, lon: -180 to 180)"
        ))
        
        self.rule_sets["location_data"] = rule_set
    
    def validate_birth_details(self, birth_details: BirthDetails) -> ValidationResult:
        """Validate birth details."""
        try:
            return self.rule_sets["birth_details"].validate(birth_details)
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="validate_birth_details")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation failed: {str(e)}")
            return result
    
    def validate_planetary_position(self, position: PlanetaryPosition) -> ValidationResult:
        """Validate planetary position."""
        try:
            return self.rule_sets["planetary_position"].validate(position)
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="validate_planetary_position")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation failed: {str(e)}")
            return result
    
    def validate_kundali_data(self, kundali_data: KundaliData) -> ValidationResult:
        """Validate complete kundali data."""
        try:
            # Validate main structure
            result = self.rule_sets["kundali_data"].validate(kundali_data)
            
            # Validate birth details if present
            if kundali_data.birth_details:
                birth_result = self.validate_birth_details(kundali_data.birth_details)
                result.errors.extend(birth_result.errors)
                result.warnings.extend(birth_result.warnings)
                if not birth_result.is_valid:
                    result.is_valid = False
            
            # Validate planetary positions
            for planet, position in kundali_data.planetary_positions.items():
                pos_result = self.validate_planetary_position(position)
                if not pos_result.is_valid:
                    result.errors.extend([f"{planet}: {error}" for error in pos_result.errors])
                    result.warnings.extend([f"{planet}: {warning}" for warning in pos_result.warnings])
                    result.is_valid = False
            
            return result
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="validate_kundali_data")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation failed: {str(e)}")
            return result
    
    def validate_layer_data(self, layer_data: LayerData) -> ValidationResult:
        """Validate layer data."""
        try:
            return self.rule_sets["layer_data"].validate(layer_data)
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="validate_layer_data")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation failed: {str(e)}")
            return result
    
    def validate_location_data(self, location_data: LocationData) -> ValidationResult:
        """Validate location data."""
        try:
            return self.rule_sets["location_data"].validate(location_data)
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="validate_location_data")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation failed: {str(e)}")
            return result
    
    def assess_data_quality(self, data: Any, data_type: str) -> Dict[str, float]:
        """Assess data quality for given data type."""
        try:
            if data_type == "birth_details":
                return self.quality_assessor.assess_birth_details_quality(data)
            elif data_type == "kundali_data":
                return self.quality_assessor.assess_kundali_data_quality(data)
            elif data_type == "layer_data":
                return self.quality_assessor.assess_layer_data_quality(data)
            else:
                return {"overall": 0.0, "error": "Unknown data type"}
        except Exception as e:
            context = ErrorContext(component="data_validator", operation="assess_data_quality")
            get_error_handler().handle_error(ValidationError(str(e), context=context))
            return {"overall": 0.0, "error": str(e)}
    
    def suggest_corrections(self, data: Any, validation_result: ValidationResult) -> Dict[str, Any]:
        """Suggest corrections for validation errors."""
        suggestions = {
            "auto_fixable": [],
            "manual_fixes": [],
            "warnings": []
        }
        
        # For each error, check if we have an auto-fix available
        for error in validation_result.errors:
            if "latitude" in error.lower():
                suggestions["manual_fixes"].append({
                    "field": "latitude",
                    "issue": error,
                    "suggestion": "Ensure latitude is between -90 and 90 degrees"
                })
            elif "longitude" in error.lower():
                suggestions["manual_fixes"].append({
                    "field": "longitude", 
                    "issue": error,
                    "suggestion": "Ensure longitude is between -180 and 180 degrees"
                })
            elif "date" in error.lower():
                suggestions["manual_fixes"].append({
                    "field": "date",
                    "issue": error,
                    "suggestion": "Provide a valid date in YYYY-MM-DD format"
                })
            elif "time" in error.lower():
                suggestions["manual_fixes"].append({
                    "field": "time",
                    "issue": error,
                    "suggestion": "Provide a valid time in HH:MM:SS format"
                })
        
        for warning in validation_result.warnings:
            suggestions["warnings"].append({
                "issue": warning,
                "suggestion": "This may affect calculation accuracy but is not critical"
            })
        
        return suggestions
    
    def add_custom_rule(self, data_type: str, rule: ValidationRule) -> None:
        """Add custom validation rule for a data type."""
        if data_type not in self.rule_sets:
            self.rule_sets[data_type] = ValidationRuleSet(data_type)
        self.rule_sets[data_type].add_rule(rule)
    
    def get_validation_report(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Get comprehensive validation report."""
        # Perform validation
        if data_type == "birth_details":
            validation_result = self.validate_birth_details(data)
        elif data_type == "kundali_data":
            validation_result = self.validate_kundali_data(data)
        elif data_type == "layer_data":
            validation_result = self.validate_layer_data(data)
        elif data_type == "location_data":
            validation_result = self.validate_location_data(data)
        else:
            validation_result = ValidationResult(is_valid=False)
            validation_result.add_error(f"Unknown data type: {data_type}")
        
        # Assess quality
        quality_assessment = self.assess_data_quality(data, data_type)
        
        # Generate suggestions
        suggestions = self.suggest_corrections(data, validation_result)
        
        return {
            "validation_result": {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            },
            "quality_assessment": quality_assessment,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }


# Global validator instance
_global_validator: Optional[DataValidator] = None


def get_data_validator() -> DataValidator:
    """Get global data validator instance."""
    global _global_validator
    if _global_validator is None:
        _global_validator = DataValidator()
    return _global_validator


def reset_data_validator() -> None:
    """Reset global data validator (mainly for testing)."""
    global _global_validator
    _global_validator = None


# Convenience functions
def validate_birth_details(birth_details: BirthDetails) -> ValidationResult:
    """Convenience function to validate birth details."""
    return get_data_validator().validate_birth_details(birth_details)


def validate_kundali_data(kundali_data: KundaliData) -> ValidationResult:
    """Convenience function to validate kundali data."""
    return get_data_validator().validate_kundali_data(kundali_data)


def validate_layer_data(layer_data: LayerData) -> ValidationResult:
    """Convenience function to validate layer data."""
    return get_data_validator().validate_layer_data(layer_data)


def assess_data_quality(data: Any, data_type: str) -> Dict[str, float]:
    """Convenience function to assess data quality."""
    return get_data_validator().assess_data_quality(data, data_type)