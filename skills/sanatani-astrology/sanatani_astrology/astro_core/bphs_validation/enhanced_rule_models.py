"""
Enhanced BPHS Rule Data Models

This module defines the enhanced data structures for BPHS rules that include
source references, strength modifiers, timing considerations, and improved
validation capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json


class Priority(Enum):
    """Rule priority levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ValidationStatus(Enum):
    """Rule validation status."""
    VALIDATED = "validated"
    PENDING = "pending"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class StrengthLevel(Enum):
    """Planetary strength levels."""
    EXALTED = "exalted"
    OWN = "own"
    MULATRIKONA = "mulatrikona"
    FRIEND = "friend"
    NEUTRAL = "neutral"
    ENEMY = "enemy"
    DEBILITATED = "debilitated"
    COMBUST = "combust"


class TimingPhase(Enum):
    """Timing phases for rule application."""
    WAXING_MOON = "waxing"
    WANING_MOON = "waning"
    NEW_MOON = "new_moon"
    FULL_MOON = "full_moon"
    SPRING = "spring"
    SUMMER = "summer"
    MONSOON = "monsoon"
    AUTUMN = "autumn"
    WINTER = "winter"


@dataclass
class SourceReference:
    """BPHS source reference with chapter, verse, and page information."""
    chapter: str
    verse: Optional[str] = None
    page: Optional[int] = None
    volume: int = 1  # 1 or 2 for BPHS volumes
    exact_quote: Optional[str] = None
    interpretation_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chapter': self.chapter,
            'verse': self.verse,
            'page': self.page,
            'volume': self.volume,
            'exact_quote': self.exact_quote,
            'interpretation_notes': self.interpretation_notes
        }
    
    def validate(self) -> List[str]:
        """Validate source reference completeness."""
        errors = []
        if not self.chapter:
            errors.append("Chapter reference is required")
        if self.volume not in [1, 2]:
            errors.append("Volume must be 1 or 2")
        return errors


@dataclass
class EnhancedCondition:
    """Enhanced condition structure supporting dignity variations and combinations."""
    primary_condition: Dict[str, Any]
    dignity_modifiers: Optional[Dict[str, List[StrengthLevel]]] = None
    aspect_conditions: Optional[Dict[str, Any]] = None
    dasha_relevance: Optional[Dict[str, Any]] = None
    lunar_context: Optional[Dict[str, Any]] = None
    seasonal_context: Optional[List[TimingPhase]] = None
    combination_requirements: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'primary_condition': self.primary_condition,
            'dignity_modifiers': {k: [s.value for s in v] for k, v in self.dignity_modifiers.items()} if self.dignity_modifiers else None,
            'aspect_conditions': self.aspect_conditions,
            'dasha_relevance': self.dasha_relevance,
            'lunar_context': self.lunar_context,
            'seasonal_context': [p.value for p in self.seasonal_context] if self.seasonal_context else None,
            'combination_requirements': self.combination_requirements
        }
    
    def validate(self) -> List[str]:
        """Validate condition structure."""
        errors = []
        if not self.primary_condition:
            errors.append("Primary condition is required")
        return errors


@dataclass
class ImpactDescription:
    """Detailed impact description with strength and timing variations."""
    positive_manifestation: str
    negative_manifestation: str
    neutral_manifestation: Optional[str] = None
    strength_variations: Optional[Dict[str, str]] = None  # dignity -> impact
    timing_variations: Optional[Dict[str, str]] = None    # period -> impact
    duration_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'positive_manifestation': self.positive_manifestation,
            'negative_manifestation': self.negative_manifestation,
            'neutral_manifestation': self.neutral_manifestation,
            'strength_variations': self.strength_variations,
            'timing_variations': self.timing_variations,
            'duration_notes': self.duration_notes
        }
    
    def validate(self) -> List[str]:
        """Validate impact description completeness."""
        errors = []
        if not self.positive_manifestation:
            errors.append("Positive manifestation description is required")
        if not self.negative_manifestation:
            errors.append("Negative manifestation description is required")
        return errors


@dataclass
class ActionableGuidance:
    """Specific, implementable action recommendations."""
    primary_actions: List[str]
    conditional_actions: Optional[Dict[str, List[str]]] = None  # condition -> actions
    timing_guidance: Optional[Dict[str, str]] = None  # when -> what
    priority_sequence: Optional[List[int]] = None  # order of action indices
    measurable_outcomes: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'primary_actions': self.primary_actions,
            'conditional_actions': self.conditional_actions,
            'timing_guidance': self.timing_guidance,
            'priority_sequence': self.priority_sequence,
            'measurable_outcomes': self.measurable_outcomes
        }
    
    def validate(self) -> List[str]:
        """Validate actionable guidance completeness."""
        errors = []
        if not self.primary_actions:
            errors.append("At least one primary action is required")
        for action in self.primary_actions:
            if len(action.strip()) < 10:
                errors.append(f"Action too vague: '{action}'")
        return errors


@dataclass
class StrengthModifiers:
    """Planetary strength modifiers affecting rule outcomes."""
    dignity_effects: Dict[StrengthLevel, float]  # strength -> multiplier
    aspect_modifiers: Optional[Dict[str, float]] = None  # aspect type -> modifier
    house_strength_factors: Optional[Dict[int, float]] = None  # house -> factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'dignity_effects': {k.value: v for k, v in self.dignity_effects.items()},
            'aspect_modifiers': self.aspect_modifiers,
            'house_strength_factors': self.house_strength_factors
        }


@dataclass
class TimingConsiderations:
    """Timing considerations for rule application."""
    optimal_periods: List[TimingPhase]
    avoid_periods: Optional[List[TimingPhase]] = None
    lunar_dependencies: Optional[Dict[str, Any]] = None
    dasha_sensitivity: Optional[Dict[str, float]] = None  # dasha -> sensitivity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'optimal_periods': [p.value for p in self.optimal_periods],
            'avoid_periods': [p.value for p in self.avoid_periods] if self.avoid_periods else None,
            'lunar_dependencies': self.lunar_dependencies,
            'dasha_sensitivity': self.dasha_sensitivity
        }


@dataclass
class CombinationEffects:
    """Effects when this rule combines with other rules."""
    synergistic_rules: Optional[List[str]] = None  # rule IDs that enhance this rule
    conflicting_rules: Optional[List[str]] = None  # rule IDs that conflict
    precedence_rules: Optional[Dict[str, int]] = None  # rule ID -> precedence level
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'synergistic_rules': self.synergistic_rules,
            'conflicting_rules': self.conflicting_rules,
            'precedence_rules': self.precedence_rules
        }


@dataclass
class EnhancedBPHSRule:
    """Enhanced BPHS rule with comprehensive metadata and validation."""
    serial: int
    id: str
    section: str
    priority: Priority
    source_reference: SourceReference
    conditions: EnhancedCondition
    summary: str
    impact: ImpactDescription
    action: ActionableGuidance
    
    # Optional enhanced features
    timing_considerations: Optional[TimingConsiderations] = None
    strength_modifiers: Optional[StrengthModifiers] = None
    combination_effects: Optional[CombinationEffects] = None
    
    # Validation and metadata
    validation_status: ValidationStatus = ValidationStatus.PENDING
    last_validated: Optional[datetime] = None
    validation_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'serial': self.serial,
            'id': self.id,
            'section': self.section,
            'priority': self.priority.value,
            'source_reference': self.source_reference.to_dict(),
            'conditions': self.conditions.to_dict(),
            'summary': self.summary,
            'impact': self.impact.to_dict(),
            'action': self.action.to_dict(),
            'timing_considerations': self.timing_considerations.to_dict() if self.timing_considerations else None,
            'strength_modifiers': self.strength_modifiers.to_dict() if self.strength_modifiers else None,
            'combination_effects': self.combination_effects.to_dict() if self.combination_effects else None,
            'validation_status': self.validation_status.value,
            'last_validated': self.last_validated.isoformat() if self.last_validated else None,
            'validation_notes': self.validation_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def validate(self) -> List[str]:
        """Comprehensive validation of the rule."""
        import re
        errors = []
        
        # Basic field validation
        if not self.id:
            errors.append("Rule ID is required")
        elif not re.match(r'^[a-z_][a-z0-9_]*$', self.id):
            errors.append("Rule ID must be lowercase with underscores only")
            
        if not self.summary:
            errors.append("Summary is required")
        if len(self.summary) < 20:
            errors.append("Summary too brief - should be at least 20 characters")
        
        # Component validation
        errors.extend(self.source_reference.validate())
        errors.extend(self.conditions.validate())
        errors.extend(self.impact.validate())
        errors.extend(self.action.validate())
        
        return errors
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy YAML rule format for backward compatibility."""
        legacy_rule = {
            'serial': self.serial,
            'id': self.id,
            'section': self.section,
            'priority': self.priority.value,
            'conditions': self.conditions.primary_condition,
            'summary': self.summary,
            'impact': self.impact.positive_manifestation,
            'action': self.action.primary_actions[0] if self.action.primary_actions else ""
        }
        
        # Add source reference as comment if available
        if self.source_reference.chapter:
            legacy_rule['_source'] = f"BPHS Ch. {self.source_reference.chapter}"
            if self.source_reference.verse:
                legacy_rule['_source'] += f", v. {self.source_reference.verse}"
        
        return legacy_rule


@dataclass
class RuleValidationReport:
    """Comprehensive validation report for a set of rules."""
    total_rules: int
    validated_rules: int
    failed_rules: int
    pending_rules: int
    validation_errors: Dict[str, List[str]]  # rule_id -> errors
    coverage_gaps: List[str]
    duplicate_serials: List[int]
    missing_citations: List[str]  # rule_ids without proper citations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_rules': self.total_rules,
            'validated_rules': self.validated_rules,
            'failed_rules': self.failed_rules,
            'pending_rules': self.pending_rules,
            'validation_errors': self.validation_errors,
            'coverage_gaps': self.coverage_gaps,
            'duplicate_serials': self.duplicate_serials,
            'missing_citations': self.missing_citations
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class EnhancedRuleSet:
    """Collection of enhanced BPHS rules with metadata."""
    meta: Dict[str, Any]
    rules: List[EnhancedBPHSRule]
    validation_report: Optional[RuleValidationReport] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'meta': self.meta,
            'rules': [rule.to_dict() for rule in self.rules],
            'validation_report': self.validation_report.to_dict() if self.validation_report else None
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def to_legacy_yaml_format(self) -> Dict[str, Any]:
        """Convert to legacy YAML format for backward compatibility."""
        return {
            'meta': self.meta,
            'rules': [rule.to_legacy_format() for rule in self.rules]
        }
    
    def validate_all(self) -> RuleValidationReport:
        """Validate all rules and generate comprehensive report."""
        validation_errors = {}
        validated_count = 0
        failed_count = 0
        pending_count = 0
        duplicate_serials = []
        missing_citations = []
        
        # Check for duplicate serials
        serials = [rule.serial for rule in self.rules]
        seen_serials = set()
        for serial in serials:
            if serial in seen_serials:
                duplicate_serials.append(serial)
            seen_serials.add(serial)
        
        # Validate each rule
        for rule in self.rules:
            errors = rule.validate()
            if errors:
                validation_errors[rule.id] = errors
                failed_count += 1
                rule.validation_status = ValidationStatus.FAILED
            else:
                validated_count += 1
                rule.validation_status = ValidationStatus.VALIDATED
            
            # Check for missing citations
            if not rule.source_reference.chapter:
                missing_citations.append(rule.id)
        
        self.validation_report = RuleValidationReport(
            total_rules=len(self.rules),
            validated_rules=validated_count,
            failed_rules=failed_count,
            pending_rules=pending_count,
            validation_errors=validation_errors,
            coverage_gaps=[],  # To be filled by coverage analysis
            duplicate_serials=duplicate_serials,
            missing_citations=missing_citations
        )
        
        return self.validation_report