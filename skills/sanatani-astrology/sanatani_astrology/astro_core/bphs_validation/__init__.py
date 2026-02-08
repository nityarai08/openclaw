"""
Enhanced BPHS Validation System

This package provides comprehensive validation and enhanced rule management
for the BPHS (Brihat Parasara Hora Sastra) astrological system.
"""

from .core_validation import (
    ValidationResult,
    PerformanceMetrics,
    RuleValidationReport,
    RuleValidator,
    PerformanceValidator,
    CompatibilityValidator,
    ComprehensiveValidator,
    load_rules_from_file,
    create_sample_test_charts,
    save_validation_results
)

from .enhanced_system import (
    SourceReference,
    EnhancedRule,
    RuleIndex,
    OptimizedRuleEngine,
    EnhancedRuleSystem,
    benchmark_system_performance,
    create_sample_enhanced_rule
)

__version__ = "2.0.0"
__all__ = [
    # Core validation
    'ValidationResult',
    'PerformanceMetrics', 
    'RuleValidationReport',
    'RuleValidator',
    'PerformanceValidator',
    'CompatibilityValidator',
    'ComprehensiveValidator',
    'load_rules_from_file',
    'create_sample_test_charts',
    'save_validation_results',
    
    # Enhanced system
    'SourceReference',
    'EnhancedRule',
    'RuleIndex',
    'OptimizedRuleEngine',
    'EnhancedRuleSystem',
    'benchmark_system_performance',
    'create_sample_enhanced_rule'
]
