"""
Astro Core - Comprehensive Vedic Astrology Library

A Python library providing core astrological calculation capabilities including
kundali generation, layer processing, and commentary generation.
"""

# Core data models and interfaces
from .core import (
    BirthDetails,
    PlanetaryPosition,
    KundaliData,
    LayerInfo,
    DailyScore,
    LayerData,
    ValidationResult,
    LocationData,
    KundaliGeneratorInterface,
    LayerProcessorInterface,
    ConfigurationManager,
    get_config_manager,
    SchemaValidator,
    ErrorHandler,
    get_error_handler,
    DataValidator,
    get_data_validator,
)

# Kundali generation
from .kundali_generator import (
    KundaliGeneratorFactory,
    GeneratorType,
    create_kundali_generator,
    get_default_generator,
    BaseKundaliGenerator,
)

# Layer processing
from .layer_processor import (
    LayerProcessor,
    LayerProcessingEngine,
    LayerProcessingError,
)

# Commentary generation
from .commentary_engine import (
    ConsolidatedCommentaryEngine,
)

__version__ = "1.0.0"
__author__ = "Astro Core Development Team"

__all__ = [
    # Core data models
    'BirthDetails',
    'PlanetaryPosition', 
    'KundaliData',
    'LayerInfo',
    'DailyScore',
    'LayerData',
    'ValidationResult',
    'LocationData',
    
    # Core interfaces
    'KundaliGeneratorInterface',
    'LayerProcessorInterface',
    
    # Core utilities
    'ConfigurationManager',
    'get_config_manager',
    'SchemaValidator',
    'ErrorHandler',
    'get_error_handler',
    'DataValidator',
    'get_data_validator',
    
    # Kundali generation
    'KundaliGeneratorFactory',
    'GeneratorType',
    'create_kundali_generator',
    'get_default_generator',
    'BaseKundaliGenerator',
    
    # Layer processing
    'LayerProcessor',
    'LayerProcessingEngine',
    'LayerProcessingError',
    
    # Commentary generation
    'ConsolidatedCommentaryEngine',
]