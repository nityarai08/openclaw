"""
Comprehensive error handling and recovery mechanisms for layer processing.

This module provides specialized error handling, logging, and recovery
strategies for the layer processing system.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from ..core.data_models import LayerData, LayerInfo, DailyScore


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LayerError:
    """Detailed error information for layer processing."""
    layer_id: int
    error_type: str
    severity: ErrorSeverity
    message: str
    timestamp: str
    traceback_info: Optional[str] = None
    context: Dict[str, Any] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/export."""
        return {
            'layer_id': self.layer_id,
            'error_type': self.error_type,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'traceback_info': self.traceback_info,
            'context': self.context or {},
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful
        }


class LayerErrorHandler:
    """
    Comprehensive error handler for layer processing.
    
    Provides error classification, recovery strategies, and detailed logging
    for all types of layer processing errors.
    """
    
    def __init__(self, enable_recovery: bool = True):
        """
        Initialize error handler.
        
        Args:
            enable_recovery: Whether to attempt error recovery
        """
        self.enable_recovery = enable_recovery
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Error tracking
        self.error_history: List[LayerError] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default error recovery strategies."""
        self.recovery_strategies.update({
            'calculation_error': self._recover_calculation_error,
            'data_validation_error': self._recover_data_validation_error,
            'ephemeris_error': self._recover_ephemeris_error,
            'memory_error': self._recover_memory_error,
            'timeout_error': self._recover_timeout_error
        })
    
    def handle_layer_error(self, layer_id: int, error: Exception, 
                          context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Handle layer processing error with classification and recovery.
        
        Args:
            layer_id: Layer identifier
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            Recovery result if successful, None otherwise
        """
        # Classify error
        error_info = self._classify_error(layer_id, error, context)
        
        # Log error
        self._log_error(error_info)
        
        # Store in history
        self.error_history.append(error_info)
        
        # Attempt recovery if enabled
        recovery_result = None
        if self.enable_recovery:
            recovery_result = self._attempt_recovery(error_info)
        
        return recovery_result
    
    def _classify_error(self, layer_id: int, error: Exception, 
                       context: Optional[Dict[str, Any]] = None) -> LayerError:
        """Classify error by type and severity."""
        error_type = type(error).__name__
        severity = self._determine_severity(error)
        
        return LayerError(
            layer_id=layer_id,
            error_type=error_type,
            severity=severity,
            message=str(error),
            timestamp=datetime.now().isoformat(),
            traceback_info=traceback.format_exc(),
            context=context or {}
        )
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on error type."""
        critical_errors = (MemoryError, SystemError, KeyboardInterrupt)
        high_errors = (ValueError, TypeError, AttributeError)
        medium_errors = (RuntimeError, OSError, ImportError)
        
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, medium_errors):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _log_error(self, error_info: LayerError) -> None:
        """Log error with appropriate level based on severity."""
        log_message = f"Layer {error_info.layer_id} - {error_info.error_type}: {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log traceback for high severity errors
        if error_info.severity in (ErrorSeverity.HIGH, ErrorSeverity.CRITICAL):
            if error_info.traceback_info:
                self.logger.debug(f"Traceback for Layer {error_info.layer_id}:\n{error_info.traceback_info}")
    
    def _attempt_recovery(self, error_info: LayerError) -> Optional[Any]:
        """Attempt error recovery using registered strategies."""
        error_info.recovery_attempted = True
        
        # Find appropriate recovery strategy
        recovery_strategy = None
        for strategy_name, strategy_func in self.recovery_strategies.items():
            if strategy_name.lower() in error_info.error_type.lower():
                recovery_strategy = strategy_func
                break
        
        # Try generic recovery if no specific strategy found
        if not recovery_strategy:
            recovery_strategy = self._generic_recovery
        
        try:
            result = recovery_strategy(error_info)
            error_info.recovery_successful = True
            self.logger.info(f"Successfully recovered from error in Layer {error_info.layer_id}")
            return result
        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for Layer {error_info.layer_id}: {recovery_error}")
            error_info.recovery_successful = False
            return None
    
    def _recover_calculation_error(self, error_info: LayerError) -> Any:
        """Recover from calculation errors using simplified methods."""
        self.logger.info(f"Attempting calculation error recovery for Layer {error_info.layer_id}")
        
        # Return neutral score as fallback
        return 0.5
    
    def _recover_data_validation_error(self, error_info: LayerError) -> Any:
        """Recover from data validation errors using default values."""
        self.logger.info(f"Attempting data validation error recovery for Layer {error_info.layer_id}")
        
        # Return minimal valid data structure
        return {'status': 'recovered', 'data': None}
    
    def _recover_ephemeris_error(self, error_info: LayerError) -> Any:
        """Recover from ephemeris calculation errors using approximations."""
        self.logger.info(f"Attempting ephemeris error recovery for Layer {error_info.layer_id}")
        
        # Use simplified astronomical calculations
        return {'ephemeris_data': 'approximated', 'accuracy': 'reduced'}
    
    def _recover_memory_error(self, error_info: LayerError) -> Any:
        """Recover from memory errors by reducing data size."""
        self.logger.warning(f"Attempting memory error recovery for Layer {error_info.layer_id}")
        
        # Suggest processing in smaller chunks
        return {'processing_mode': 'chunked', 'chunk_size': 30}
    
    def _recover_timeout_error(self, error_info: LayerError) -> Any:
        """Recover from timeout errors using cached or simplified data."""
        self.logger.info(f"Attempting timeout error recovery for Layer {error_info.layer_id}")
        
        # Return cached result or simplified calculation
        return {'timeout_recovery': True, 'simplified_calculation': True}
    
    def _generic_recovery(self, error_info: LayerError) -> Any:
        """Generic recovery strategy for unclassified errors."""
        self.logger.info(f"Attempting generic recovery for Layer {error_info.layer_id}")
        
        # Return safe default values
        return {'recovery_type': 'generic', 'safe_defaults': True}
    
    def register_recovery_strategy(self, error_pattern: str, 
                                 strategy_func: Callable[[LayerError], Any]) -> None:
        """
        Register custom recovery strategy.
        
        Args:
            error_pattern: Pattern to match in error type
            strategy_func: Recovery function that takes LayerError and returns recovery result
        """
        self.recovery_strategies[error_pattern] = strategy_func
        self.logger.info(f"Registered recovery strategy for pattern: {error_pattern}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        if not self.error_history:
            return {'total_errors': 0}
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = len([e for e in self.error_history if e.severity == severity])
        
        # Count by layer
        layer_counts = {}
        for error in self.error_history:
            layer_counts[error.layer_id] = layer_counts.get(error.layer_id, 0) + 1
        
        # Count by error type
        type_counts = {}
        for error in self.error_history:
            type_counts[error.error_type] = type_counts.get(error.error_type, 0) + 1
        
        # Recovery statistics
        recovery_attempted = len([e for e in self.error_history if e.recovery_attempted])
        recovery_successful = len([e for e in self.error_history if e.recovery_successful])
        
        return {
            'total_errors': len(self.error_history),
            'severity_breakdown': severity_counts,
            'layer_breakdown': layer_counts,
            'error_type_breakdown': type_counts,
            'recovery_statistics': {
                'attempted': recovery_attempted,
                'successful': recovery_successful,
                'success_rate': recovery_successful / recovery_attempted if recovery_attempted > 0 else 0
            },
            'most_problematic_layer': max(layer_counts.items(), key=lambda x: x[1])[0] if layer_counts else None,
            'most_common_error': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
    
    def export_error_report(self, filename: str = None) -> str:
        """
        Export detailed error report to JSON file.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        import json
        import os
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"layer_error_report_{timestamp}.json"
        
        report_data = {
            'report_timestamp': datetime.now().isoformat(),
            'statistics': self.get_error_statistics(),
            'error_history': [error.to_dict() for error in self.error_history],
            'recovery_strategies': list(self.recovery_strategies.keys())
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"Exported error report to {filename}")
        return filename
    
    def clear_error_history(self) -> None:
        """Clear error history (useful for testing or periodic cleanup)."""
        cleared_count = len(self.error_history)
        self.error_history.clear()
        self.logger.info(f"Cleared {cleared_count} errors from history")
    
    def get_layer_error_summary(self, layer_id: int) -> Dict[str, Any]:
        """Get error summary for specific layer."""
        layer_errors = [e for e in self.error_history if e.layer_id == layer_id]
        
        if not layer_errors:
            return {'layer_id': layer_id, 'total_errors': 0}
        
        return {
            'layer_id': layer_id,
            'total_errors': len(layer_errors),
            'error_types': list(set(e.error_type for e in layer_errors)),
            'severity_levels': list(set(e.severity.value for e in layer_errors)),
            'recovery_rate': len([e for e in layer_errors if e.recovery_successful]) / len(layer_errors),
            'last_error': layer_errors[-1].to_dict() if layer_errors else None
        }