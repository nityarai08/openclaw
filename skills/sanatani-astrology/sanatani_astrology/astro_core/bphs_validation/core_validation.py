"""
Core BPHS Validation Module

This module consolidates all core validation functionality for the Enhanced BPHS Rule System,
including rule validation, performance testing, and compatibility checking.
"""

import json
import yaml
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for rule evaluation."""
    total_evaluation_time: float = 0.0
    rules_evaluated: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_evaluation_time_ms': self.total_evaluation_time * 1000,
            'rules_evaluated': self.rules_evaluated,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'avg_time_per_rule_ms': (self.total_evaluation_time * 1000 / self.rules_evaluated) if self.rules_evaluated > 0 else 0,
            'cache_hit_ratio': (self.cache_hits / (self.cache_hits + self.cache_misses)) if (self.cache_hits + self.cache_misses) > 0 else 0
        }


@dataclass
class RuleValidationReport:
    """Comprehensive rule validation report."""
    total_rules: int
    valid_rules: int
    invalid_rules: int
    validation_errors: Dict[str, List[str]]
    coverage_gaps: List[str]
    recommendations: List[str]
    
    @property
    def success_rate(self) -> float:
        return self.valid_rules / self.total_rules if self.total_rules > 0 else 0
    
    @property
    def all_rules_valid(self) -> bool:
        return self.invalid_rules == 0


# ============================================================================
# Core Validation Classes
# ============================================================================

class RuleValidator:
    """Core rule validation functionality."""
    
    def __init__(self):
        self.validation_rules = {
            'required_fields': ['id', 'section', 'priority', 'conditions', 'summary', 'impact', 'action'],
            'valid_priorities': ['High', 'Medium', 'Low'],
            'min_summary_length': 10,
            'max_summary_length': 500,
            'min_action_length': 5
        }
    
    def validate_rule(self, rule: Dict[str, Any], rule_index: int = 0) -> ValidationResult:
        """Validate a single rule."""
        errors = []
        warnings = []
        
        rule_id = rule.get('id', f'rule_{rule_index}')
        
        # Check required fields
        for field in self.validation_rules['required_fields']:
            if field not in rule or not rule[field]:
                errors.append(f"Missing or empty required field: {field}")
        
        # Validate rule ID
        if 'id' in rule:
            if not isinstance(rule['id'], str) or not rule['id'].strip():
                errors.append("Rule ID must be a non-empty string")
            elif not rule['id'].replace('_', '').replace('-', '').isalnum():
                warnings.append("Rule ID should contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate priority
        if 'priority' in rule:
            if rule['priority'] not in self.validation_rules['valid_priorities']:
                errors.append(f"Invalid priority: {rule['priority']}. Must be one of {self.validation_rules['valid_priorities']}")
        
        # Validate conditions
        if 'conditions' in rule:
            if not isinstance(rule['conditions'], dict):
                errors.append("Conditions must be a dictionary")
            elif not rule['conditions']:
                warnings.append("Empty conditions dictionary")
        
        # Validate summary
        if 'summary' in rule and rule['summary']:
            summary_len = len(rule['summary'])
            if summary_len < self.validation_rules['min_summary_length']:
                errors.append(f"Summary too short (minimum {self.validation_rules['min_summary_length']} characters)")
            elif summary_len > self.validation_rules['max_summary_length']:
                warnings.append(f"Summary very long ({summary_len} characters)")
        
        # Validate action
        if 'action' in rule and rule['action']:
            if isinstance(rule['action'], str):
                if len(rule['action']) < self.validation_rules['min_action_length']:
                    errors.append(f"Action too short (minimum {self.validation_rules['min_action_length']} characters)")
            elif isinstance(rule['action'], dict):
                # Enhanced action format
                if 'primary_actions' not in rule['action'] or not rule['action']['primary_actions']:
                    errors.append("Enhanced action format requires primary_actions")
        
        return ValidationResult(
            success=len(errors) == 0,
            message=f"Rule {rule_id} validation {'passed' if len(errors) == 0 else 'failed'}",
            errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def validate_rules(self, rules: List[Dict[str, Any]]) -> RuleValidationReport:
        """Validate a list of rules."""
        validation_errors = {}
        valid_count = 0
        
        for i, rule in enumerate(rules):
            result = self.validate_rule(rule, i)
            
            if result.success:
                valid_count += 1
            else:
                rule_id = rule.get('id', f'rule_{i}')
                validation_errors[rule_id] = result.errors or []
        
        # Analyze coverage gaps
        coverage_gaps = self._analyze_coverage_gaps(rules)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(rules, validation_errors)
        
        return RuleValidationReport(
            total_rules=len(rules),
            valid_rules=valid_count,
            invalid_rules=len(rules) - valid_count,
            validation_errors=validation_errors,
            coverage_gaps=coverage_gaps,
            recommendations=recommendations
        )
    
    def _analyze_coverage_gaps(self, rules: List[Dict[str, Any]]) -> List[str]:
        """Analyze coverage gaps in the rule set."""
        gaps = []
        
        # Check for basic coverage
        sections = set()
        priorities = set()
        
        for rule in rules:
            if 'section' in rule:
                sections.add(rule['section'])
            if 'priority' in rule:
                priorities.add(rule['priority'])
        
        # Check for missing priorities
        expected_priorities = set(self.validation_rules['valid_priorities'])
        missing_priorities = expected_priorities - priorities
        if missing_priorities:
            gaps.append(f"Missing priority levels: {', '.join(missing_priorities)}")
        
        # Check for minimal section coverage
        if len(sections) < 3:
            gaps.append("Limited section coverage - consider adding more diverse rule categories")
        
        return gaps
    
    def _generate_recommendations(self, rules: List[Dict[str, Any]], validation_errors: Dict[str, List[str]]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if validation_errors:
            recommendations.append("Fix validation errors before deploying rules")
        
        # Check for source references
        rules_with_sources = sum(1 for rule in rules if 'source_reference' in rule)
        if rules_with_sources < len(rules) * 0.5:
            recommendations.append("Consider adding source references to more rules for better traceability")
        
        # Check for enhanced features
        enhanced_rules = sum(1 for rule in rules if isinstance(rule.get('action'), dict))
        if enhanced_rules < len(rules) * 0.3:
            recommendations.append("Consider upgrading more rules to enhanced format with detailed actions")
        
        return recommendations


class PerformanceValidator:
    """Performance validation and testing."""
    
    def __init__(self):
        self.target_time_ms = 100.0
        self.metrics = PerformanceMetrics()
    
    def validate_performance(self, engine, test_charts: List[Dict[str, Any]], iterations: int = 5) -> ValidationResult:
        """Validate performance of rule engine."""
        try:
            all_times = []
            successful_evaluations = 0
            
            for chart in test_charts:
                for _ in range(iterations):
                    start_time = time.perf_counter()
                    result = engine.evaluate_rules(chart)
                    end_time = time.perf_counter()
                    
                    evaluation_time = (end_time - start_time) * 1000
                    
                    # evaluate_rules returns a list, so success means no exception
                    if isinstance(result, list):
                        all_times.append(evaluation_time)
                        successful_evaluations += 1
            
            if not all_times:
                return ValidationResult(
                    success=False,
                    message="No successful evaluations",
                    errors=["All evaluations failed"]
                )
            
            avg_time = sum(all_times) / len(all_times)
            max_time = max(all_times)
            min_time = min(all_times)
            
            performance_target_met = max_time < self.target_time_ms
            
            details = {
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'min_time_ms': min_time,
                'target_time_ms': self.target_time_ms,
                'performance_target_met': performance_target_met,
                'successful_evaluations': successful_evaluations,
                'total_attempts': len(test_charts) * iterations
            }
            
            message = f"Performance validation: {avg_time:.2f}ms avg, {max_time:.2f}ms max"
            if performance_target_met:
                message += f" (✓ Target <{self.target_time_ms}ms met)"
            else:
                message += f" (✗ Target <{self.target_time_ms}ms not met)"
            
            return ValidationResult(
                success=performance_target_met,
                message=message,
                details=details
            )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Performance validation failed: {e}",
                errors=[str(e)]
            )
    
    def validate_memory_usage(self, engine) -> ValidationResult:
        """Validate memory usage of rule engine."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Load rules and run some evaluations
            sample_chart = {
                "planets": {
                    "sun": {"house_number": 1, "sign_key": "aries", "dignity": "exalted"},
                    "moon": {"house_number": 4, "sign_key": "cancer", "dignity": "own"}
                }
            }
            
            # Run multiple evaluations
            for _ in range(10):
                try:
                    engine.evaluate_rules(sample_chart)
                except Exception:
                    pass  # Continue with memory test even if evaluation fails
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory usage should be reasonable (< 50MB increase)
            memory_acceptable = memory_increase < 50
            
            details = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'memory_acceptable': memory_acceptable
            }
            
            message = f"Memory validation: {memory_increase:.1f}MB increase"
            if memory_acceptable:
                message += " (✓ Acceptable)"
            else:
                message += " (⚠ High memory usage)"
            
            return ValidationResult(
                success=memory_acceptable,
                message=message,
                details=details
            )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Memory validation failed: {e}",
                errors=[str(e)]
            )


class CompatibilityValidator:
    """Backward compatibility validation."""
    
    def validate_api_compatibility(self, enhanced_engine) -> ValidationResult:
        """Validate API compatibility."""
        try:
            # Test basic API structure
            sample_chart = {
                "planets": {
                    "sun": {"house_number": 1, "sign_key": "aries", "dignity": "exalted"}
                }
            }
            
            result = enhanced_engine.evaluate_rules(sample_chart)
            
            # evaluate_rules returns a list of triggered rules
            if not isinstance(result, list):
                return ValidationResult(
                    success=False,
                    message="API compatibility validation failed",
                    errors=["Expected list return type from evaluate_rules"]
                )
            
            # Check triggered rules structure if any rules were triggered
            if result:
                rule_sample = result[0]
                expected_rule_fields = ['id', 'section', 'priority', 'summary']
                missing_rule_fields = [field for field in expected_rule_fields if field not in rule_sample]
                
                if missing_rule_fields:
                    return ValidationResult(
                        success=False,
                        message="Rule structure compatibility validation failed",
                        errors=[f"Missing rule fields: {missing_rule_fields}"]
                    )
            
            return ValidationResult(
                success=True,
                message="API compatibility validation passed",
                details={'api_structure_valid': True, 'rule_structure_valid': True}
            )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"API compatibility validation failed: {e}",
                errors=[str(e)]
            )
    
    def validate_data_compatibility(self, enhanced_engine, test_charts: List[Dict[str, Any]]) -> ValidationResult:
        """Validate data format compatibility."""
        try:
            compatible_charts = 0
            total_charts = len(test_charts)
            
            for chart in test_charts:
                try:
                    result = enhanced_engine.evaluate_rules(chart)
                    # evaluate_rules returns a list, success means no exception
                    if isinstance(result, list):
                        compatible_charts += 1
                except Exception:
                    pass  # Chart not compatible
            
            compatibility_rate = compatible_charts / total_charts if total_charts > 0 else 0
            compatibility_acceptable = compatibility_rate >= 0.8  # 80% compatibility required
            
            details = {
                'compatible_charts': compatible_charts,
                'total_charts': total_charts,
                'compatibility_rate': compatibility_rate
            }
            
            message = f"Data compatibility: {compatibility_rate:.1%} ({compatible_charts}/{total_charts})"
            
            return ValidationResult(
                success=compatibility_acceptable,
                message=message,
                details=details
            )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Data compatibility validation failed: {e}",
                errors=[str(e)]
            )


# ============================================================================
# Comprehensive Validation Orchestrator
# ============================================================================

class ComprehensiveValidator:
    """Orchestrates all validation processes."""
    
    def __init__(self):
        self.rule_validator = RuleValidator()
        self.performance_validator = PerformanceValidator()
        self.compatibility_validator = CompatibilityValidator()
        self.results = {}
    
    def validate_all(self, rules: List[Dict[str, Any]], engine, test_charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive validation."""
        logger.info("Starting comprehensive validation...")
        
        start_time = time.time()
        
        # Rule validation
        logger.info("Validating rules...")
        rule_report = self.rule_validator.validate_rules(rules)
        self.results['rule_validation'] = {
            'success': rule_report.all_rules_valid,
            'total_rules': rule_report.total_rules,
            'valid_rules': rule_report.valid_rules,
            'invalid_rules': rule_report.invalid_rules,
            'success_rate': rule_report.success_rate,
            'validation_errors': rule_report.validation_errors,
            'recommendations': rule_report.recommendations
        }
        
        # Performance validation
        logger.info("Validating performance...")
        perf_result = self.performance_validator.validate_performance(engine, test_charts)
        self.results['performance_validation'] = {
            'success': perf_result.success,
            'message': perf_result.message,
            'details': perf_result.details
        }
        
        # Memory validation
        logger.info("Validating memory usage...")
        memory_result = self.performance_validator.validate_memory_usage(engine)
        self.results['memory_validation'] = {
            'success': memory_result.success,
            'message': memory_result.message,
            'details': memory_result.details
        }
        
        # Compatibility validation
        logger.info("Validating compatibility...")
        api_result = self.compatibility_validator.validate_api_compatibility(engine)
        data_result = self.compatibility_validator.validate_data_compatibility(engine, test_charts)
        
        self.results['compatibility_validation'] = {
            'api_compatibility': {
                'success': api_result.success,
                'message': api_result.message
            },
            'data_compatibility': {
                'success': data_result.success,
                'message': data_result.message,
                'details': data_result.details
            }
        }
        
        # Calculate overall results
        all_validations = [
            rule_report.all_rules_valid,
            perf_result.success,
            memory_result.success,
            api_result.success,
            data_result.success
        ]
        
        overall_success = all(all_validations)
        success_rate = sum(all_validations) / len(all_validations)
        
        end_time = time.time()
        
        summary = {
            'overall_success': overall_success,
            'success_rate': success_rate,
            'total_validations': len(all_validations),
            'passed_validations': sum(all_validations),
            'execution_time_seconds': end_time - start_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'detailed_results': self.results
        }
        
        # Log summary
        logger.info(f"Comprehensive validation complete:")
        logger.info(f"  Overall success: {overall_success}")
        logger.info(f"  Success rate: {success_rate:.1%}")
        logger.info(f"  Execution time: {end_time - start_time:.2f}s")
        
        return summary


# ============================================================================
# Utility Functions
# ============================================================================

def load_rules_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load rules from YAML or JSON file."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Rule file not found: {file_path}")
    
    with path.open('r', encoding='utf-8') as f:
        if path.suffix.lower() == '.json':
            data = json.load(f)
        else:
            content = f.read().replace('\t', '  ')
            data = yaml.safe_load(content)
    
    if isinstance(data, dict) and 'rules' in data:
        return data['rules']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid rule file format")


def create_sample_test_charts() -> List[Dict[str, Any]]:
    """Create sample test charts for validation."""
    return [
        {
            "planets": {
                "sun": {"house_number": 1, "sign_key": "aries", "dignity": "exalted"},
                "moon": {"house_number": 4, "sign_key": "cancer", "dignity": "own"},
                "jupiter": {"house_number": 7, "sign_key": "libra", "dignity": "debilitated"}
            }
        },
        {
            "planets": {
                "venus": {"house_number": 2, "sign_key": "taurus", "dignity": "own"},
                "mars": {"house_number": 10, "sign_key": "capricorn", "dignity": "exalted"},
                "saturn": {"house_number": 11, "sign_key": "aquarius", "dignity": "own"}
            }
        }
    ]


def save_validation_results(results: Dict[str, Any], output_file: str) -> None:
    """Save validation results to file."""
    output_path = Path(output_file)
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to: {output_path}")