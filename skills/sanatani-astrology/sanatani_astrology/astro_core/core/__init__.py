"""
Core module for the Kundali Favorability Heatmap System.

This module provides the foundational data structures, interfaces, and utilities
that are shared across all three components of the system.
"""

from .data_models import (
    BirthDetails,
    PlanetaryPosition,
    KundaliData,
    LayerInfo,
    DailyScore,
    LayerData,
    ValidationResult,
    LocationData
)

from .interfaces import (
    KundaliGeneratorInterface,
    LayerProcessorInterface,
    VisualizerInterface,
    ConfigurationManagerInterface,
    DataValidatorInterface
)

from .schema_validation import SchemaValidator
from .configuration import ConfigurationManager, get_config_manager
from .plugin_system import (
    PluginManager, PluginInterface, PluginMetadata,
    get_plugin_manager, reset_plugin_manager
)

from .error_handling import (
    ErrorHandler, ErrorSeverity, ErrorCategory, ErrorContext, ErrorReport,
    FavorabilitySystemError, ValidationError, CalculationError,
    DataProcessingError, VisualizationError, ConfigurationError,
    PluginError, NetworkError, FileIOError,
    ErrorRecoveryStrategy, FallbackValueStrategy, RetryStrategy,
    get_error_handler, reset_error_handler, handle_error,
    error_handler_decorator
)

from .data_validation import (
    ValidationRule, ValidationRuleSet, DataQualityAssessment, DataValidator,
    get_data_validator, reset_data_validator,
    validate_birth_details, validate_kundali_data, validate_layer_data,
    assess_data_quality
)

__version__ = "1.0.0"

__all__ = [
    # Data Models
    'BirthDetails',
    'PlanetaryPosition',
    'KundaliData',
    'LayerInfo',
    'DailyScore',
    'LayerData',
    'ValidationResult',
    'LocationData',

    # Interfaces
    'KundaliGeneratorInterface',
    'LayerProcessorInterface',
    'VisualizerInterface',
    'ConfigurationManagerInterface',
    'DataValidatorInterface',

    # Utilities
    'SchemaValidator',
    'ConfigurationManager',
    'get_config_manager',

    # Plugin System
    'PluginManager',
    'PluginInterface',
    'PluginMetadata',
    'get_plugin_manager',
    'reset_plugin_manager',

    # Error Handling
    'ErrorHandler',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'ErrorReport',
    'FavorabilitySystemError',
    'ValidationError',
    'CalculationError',
    'DataProcessingError',
    'VisualizationError',
    'ConfigurationError',
    'PluginError',
    'NetworkError',
    'FileIOError',
    'ErrorRecoveryStrategy',
    'FallbackValueStrategy',
    'RetryStrategy',
    'get_error_handler',
    'reset_error_handler',
    'handle_error',
    'error_handler_decorator',

    # Data Validation
    'ValidationRule',
    'ValidationRuleSet',
    'DataQualityAssessment',
    'DataValidator',
    'get_data_validator',
    'reset_data_validator',
    'validate_birth_details',
    'validate_kundali_data',
    'validate_layer_data',
    'assess_data_quality'
]
