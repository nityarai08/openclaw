"""
Kundali error handling framework for the Favorability Heatmap System.

This module provides a hierarchical exception system, logging configuration,
error recovery mechanisms, and user-friendly error reporting.
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "VALIDATION"
    CALCULATION = "CALCULATION"
    DATA_PROCESSING = "DATA_PROCESSING"
    VISUALIZATION = "VISUALIZATION"
    CONFIGURATION = "CONFIGURATION"
    PLUGIN = "PLUGIN"
    SYSTEM = "SYSTEM"
    NETWORK = "NETWORK"
    FILE_IO = "FILE_IO"


@dataclass
class ErrorContext:
    """Context information for errors."""
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_data: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'component': self.component,
            'operation': self.operation,
            'timestamp': self.timestamp.isoformat(),
            'user_data': self.user_data,
            'system_info': self.system_info,
            'stack_trace': self.stack_trace
        }


@dataclass
class ErrorReport:
    """Comprehensive error report."""
    error_id: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    user_message: str
    context: ErrorContext
    suggested_actions: List[str] = field(default_factory=list)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'error_id': self.error_id,
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'user_message': self.user_message,
            'context': self.context.to_dict(),
            'suggested_actions': self.suggested_actions,
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful
        }


# Base Exception Classes
class FavorabilitySystemError(Exception):
    """Base exception for the favorability system."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 context: Optional[ErrorContext] = None, user_message: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.context = context or ErrorContext(component="unknown", operation="unknown")
        self.user_message = user_message or self._generate_user_message()
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.category.value}_{timestamp}_{hash(self.message) % 10000:04d}"
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        return f"An error occurred in the {self.context.component} component. Please check your input and try again."


class ValidationError(FavorabilitySystemError):
    """Errors related to data validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 context: Optional[ErrorContext] = None):
        self.field = field
        super().__init__(message, ErrorCategory.VALIDATION, context)
    
    def _generate_user_message(self) -> str:
        if self.field:
            return f"Invalid data in field '{self.field}': {self.message}"
        return f"Data validation failed: {self.message}"


class CalculationError(FavorabilitySystemError):
    """Errors in astrological calculations."""
    
    def __init__(self, message: str, layer_id: Optional[int] = None,
                 calculation_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        self.layer_id = layer_id
        self.calculation_type = calculation_type
        super().__init__(message, ErrorCategory.CALCULATION, context)
    
    def _generate_user_message(self) -> str:
        if self.layer_id:
            return f"Calculation error in Layer {self.layer_id}: Unable to compute favorability score. Using fallback value."
        return f"Calculation error: {self.message}"


class KundaliGenerationError(FavorabilitySystemError):
    """Errors specific to Kundali generation process."""
    
    def __init__(self, message: str, component: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.component = component
        super().__init__(message, ErrorCategory.CALCULATION, context)
    
    def _generate_user_message(self) -> str:
        if self.component:
            return f"Kundali generation failed in {self.component}: {self.message}"
        return f"Kundali generation error: {self.message}"


class DataProcessingError(FavorabilitySystemError):
    """Errors in data processing operations."""
    
    def __init__(self, message: str, data_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.data_type = data_type
        super().__init__(message, ErrorCategory.DATA_PROCESSING, context)
    
    def _generate_user_message(self) -> str:
        if self.data_type:
            return f"Error processing {self.data_type} data: {self.message}"
        return f"Data processing error: {self.message}"


class VisualizationError(FavorabilitySystemError):
    """Errors in visualization generation."""
    
    def __init__(self, message: str, visualization_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.visualization_type = visualization_type
        super().__init__(message, ErrorCategory.VISUALIZATION, context)
    
    def _generate_user_message(self) -> str:
        if self.visualization_type:
            return f"Failed to generate {self.visualization_type}: {self.message}"
        return f"Visualization error: {self.message}"


class ConfigurationError(FavorabilitySystemError):
    """Errors in configuration management."""
    
    def __init__(self, message: str, config_key: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.config_key = config_key
        super().__init__(message, ErrorCategory.CONFIGURATION, context)
    
    def _generate_user_message(self) -> str:
        if self.config_key:
            return f"Configuration error for '{self.config_key}': {self.message}"
        return f"Configuration error: {self.message}"


class PluginError(FavorabilitySystemError):
    """Errors in plugin system."""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.plugin_name = plugin_name
        super().__init__(message, ErrorCategory.PLUGIN, context)
    
    def _generate_user_message(self) -> str:
        if self.plugin_name:
            return f"Plugin error in '{self.plugin_name}': {self.message}"
        return f"Plugin error: {self.message}"


class NetworkError(FavorabilitySystemError):
    """Errors in network operations."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.endpoint = endpoint
        super().__init__(message, ErrorCategory.NETWORK, context)
    
    def _generate_user_message(self) -> str:
        if self.endpoint:
            return f"Network error accessing '{self.endpoint}': Please check your internet connection."
        return f"Network error: Please check your internet connection and try again."


class FileIOError(FavorabilitySystemError):
    """Errors in file I/O operations."""
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        self.file_path = file_path
        super().__init__(message, ErrorCategory.FILE_IO, context)
    
    def _generate_user_message(self) -> str:
        if self.file_path:
            return f"File error with '{self.file_path}': {self.message}"
        return f"File I/O error: {self.message}"


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def can_recover(self, error: FavorabilitySystemError) -> bool:
        """Check if this strategy can recover from the error."""
        return False
    
    def attempt_recovery(self, error: FavorabilitySystemError, **kwargs) -> bool:
        """Attempt to recover from the error."""
        return False


class FallbackValueStrategy(ErrorRecoveryStrategy):
    """Recovery strategy using fallback values."""
    
    def __init__(self):
        super().__init__("fallback_value", "Use fallback values when calculations fail")
    
    def can_recover(self, error: FavorabilitySystemError) -> bool:
        return isinstance(error, (CalculationError, DataProcessingError))
    
    def attempt_recovery(self, error: FavorabilitySystemError, **kwargs) -> bool:
        """Use fallback values for failed calculations."""
        fallback_value = kwargs.get('fallback_value', 0.5)  # Neutral score
        return True


class RetryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy using retry logic."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__("retry", f"Retry operation up to {max_retries} times")
        self.max_retries = max_retries
    
    def can_recover(self, error: FavorabilitySystemError) -> bool:
        return isinstance(error, (NetworkError, FileIOError))
    
    def attempt_recovery(self, error: FavorabilitySystemError, **kwargs) -> bool:
        """Retry the failed operation."""
        retry_function = kwargs.get('retry_function')
        if not retry_function:
            return False
        
        for attempt in range(self.max_retries):
            try:
                retry_function()
                return True
            except Exception:
                if attempt == self.max_retries - 1:
                    return False
                continue
        return False


class ErrorHandler:
    """Comprehensive error handling system."""
    
    def __init__(self, log_file: Optional[str] = None, log_level: str = "INFO"):
        self.logger = self._setup_logging(log_file, log_level)
        self.error_reports: List[ErrorReport] = []
        self.recovery_strategies: List[ErrorRecoveryStrategy] = [
            FallbackValueStrategy(),
            RetryStrategy()
        ]
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
    
    def _setup_logging(self, log_file: Optional[str], log_level: str) -> logging.Logger:
        """Set up comprehensive logging system."""
        logger = logging.getLogger('favorability_system')
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def handle_error(self, error: Union[Exception, FavorabilitySystemError], 
                    context: Optional[ErrorContext] = None,
                    attempt_recovery: bool = True) -> ErrorReport:
        """Handle an error with comprehensive reporting and recovery."""
        
        # Convert regular exceptions to FavorabilitySystemError
        if not isinstance(error, FavorabilitySystemError):
            context = context or ErrorContext(
                component="unknown",
                operation="unknown",
                stack_trace=traceback.format_exc()
            )
            error = FavorabilitySystemError(str(error), context=context)
        
        # Determine severity
        severity = self._determine_severity(error)
        
        # Create error report
        report = ErrorReport(
            error_id=error.error_id,
            severity=severity,
            category=error.category,
            message=error.message,
            user_message=error.user_message,
            context=error.context,
            suggested_actions=self._generate_suggested_actions(error)
        )
        
        # Log the error
        self._log_error(report)
        
        # Attempt recovery if requested
        if attempt_recovery:
            report.recovery_attempted = True
            report.recovery_successful = self._attempt_recovery(error)
        
        # Store error report
        self.error_reports.append(report)
        
        # Trigger callbacks
        self._trigger_callbacks(error)
        
        return report
    
    def _determine_severity(self, error: FavorabilitySystemError) -> ErrorSeverity:
        """Determine error severity based on error type and context."""
        if isinstance(error, (ValidationError, ConfigurationError)):
            return ErrorSeverity.ERROR
        elif isinstance(error, (CalculationError, DataProcessingError)):
            return ErrorSeverity.WARNING
        elif isinstance(error, (VisualizationError, PluginError)):
            return ErrorSeverity.WARNING
        elif isinstance(error, (NetworkError, FileIOError)):
            return ErrorSeverity.ERROR
        else:
            return ErrorSeverity.CRITICAL
    
    def _generate_suggested_actions(self, error: FavorabilitySystemError) -> List[str]:
        """Generate suggested actions based on error type."""
        actions = []
        
        if isinstance(error, ValidationError):
            actions.extend([
                "Check input data format and completeness",
                "Verify date and time values are valid",
                "Ensure coordinates are within valid ranges"
            ])
        elif isinstance(error, CalculationError):
            actions.extend([
                "Verify birth details are accurate",
                "Check if ephemeris data is available",
                "Try using fallback calculation methods"
            ])
        elif isinstance(error, NetworkError):
            actions.extend([
                "Check internet connection",
                "Verify firewall settings",
                "Try again in a few minutes"
            ])
        elif isinstance(error, FileIOError):
            actions.extend([
                "Check file permissions",
                "Verify file path exists",
                "Ensure sufficient disk space"
            ])
        elif isinstance(error, ConfigurationError):
            actions.extend([
                "Check configuration file format",
                "Verify all required settings are present",
                "Reset to default configuration if needed"
            ])
        
        return actions
    
    def _log_error(self, report: ErrorReport) -> None:
        """Log error with appropriate level."""
        log_message = f"[{report.error_id}] {report.message}"
        
        if report.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif report.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif report.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log context if available
        if report.context.stack_trace:
            self.logger.debug(f"Stack trace for {report.error_id}:\n{report.context.stack_trace}")
    
    def _attempt_recovery(self, error: FavorabilitySystemError) -> bool:
        """Attempt to recover from error using available strategies."""
        for strategy in self.recovery_strategies:
            if strategy.can_recover(error):
                try:
                    if strategy.attempt_recovery(error):
                        self.logger.info(f"Successfully recovered from error using {strategy.name}")
                        return True
                except Exception as recovery_error:
                    self.logger.warning(f"Recovery strategy {strategy.name} failed: {recovery_error}")
        
        return False
    
    def _trigger_callbacks(self, error: FavorabilitySystemError) -> None:
        """Trigger registered callbacks for error category."""
        callbacks = self.error_callbacks.get(error.category, [])
        for callback in callbacks:
            try:
                callback(error)
            except Exception as callback_error:
                self.logger.warning(f"Error callback failed: {callback_error}")
    
    def register_callback(self, category: ErrorCategory, callback: Callable) -> None:
        """Register callback for specific error category."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def add_recovery_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """Add custom recovery strategy."""
        self.recovery_strategies.append(strategy)
    
    def get_error_reports(self, category: Optional[ErrorCategory] = None,
                         severity: Optional[ErrorSeverity] = None) -> List[ErrorReport]:
        """Get error reports filtered by category and/or severity."""
        reports = self.error_reports
        
        if category:
            reports = [r for r in reports if r.category == category]
        
        if severity:
            reports = [r for r in reports if r.severity == severity]
        
        return reports
    
    def export_error_reports(self, filename: str) -> None:
        """Export error reports to JSON file."""
        try:
            reports_data = [report.to_dict() for report in self.error_reports]
            with open(filename, 'w') as f:
                json.dump(reports_data, f, indent=2, default=str)
            self.logger.info(f"Exported {len(self.error_reports)} error reports to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to export error reports: {e}")
    
    def clear_error_reports(self) -> None:
        """Clear all stored error reports."""
        self.error_reports.clear()
        self.logger.info("Cleared all error reports")


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(log_file: Optional[str] = None, log_level: str = "INFO") -> ErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(log_file, log_level)
    return _global_error_handler


def reset_error_handler() -> None:
    """Reset global error handler (mainly for testing)."""
    global _global_error_handler
    _global_error_handler = None


def handle_error(error: Union[Exception, FavorabilitySystemError],
                context: Optional[ErrorContext] = None,
                attempt_recovery: bool = True) -> ErrorReport:
    """Convenience function to handle errors using global handler."""
    handler = get_error_handler()
    return handler.handle_error(error, context, attempt_recovery)


# Decorator for automatic error handling
def error_handler_decorator(component: str, operation: str, 
                          fallback_value: Any = None,
                          suppress_errors: bool = False):
    """Decorator for automatic error handling in functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    component=component,
                    operation=operation,
                    user_data={'args': str(args), 'kwargs': str(kwargs)},
                    stack_trace=traceback.format_exc()
                )
                
                report = handle_error(e, context, attempt_recovery=True)
                
                if suppress_errors:
                    return fallback_value
                else:
                    raise
        
        return wrapper
    return decorator
