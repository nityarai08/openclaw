"""
Layer processor module for the Kundali Favorability Heatmap System.

This module provides the framework for implementing and orchestrating
the 10-layer favorability calculation system with decreasing accuracy
from 100% (Layer 1) to 10% (Layer 10).
"""

from .base_layer import LayerProcessor, LayerProcessingError
from .layer_engine import LayerProcessingEngine
from .error_handling import LayerErrorHandler, LayerError, ErrorSeverity

__all__ = [
    'LayerProcessor',
    'LayerProcessingError', 
    'LayerProcessingEngine',
    'LayerErrorHandler',
    'LayerError',
    'ErrorSeverity'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Kundali Favorability Heatmap System'