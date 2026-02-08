"""
Enhanced Kundali Generator Component (v2.0)

This component generates comprehensive, structured horoscope data from birth details
with high accuracy using two distinct calculation approaches:

1. PyJHora Generator: Traditional Vedic calculations using PyJHora library
2. Ephemeris Generator: Swiss Ephemeris with simplified fallback methods

Features:
- Dual generator architecture with consistent output schema
- Auto-selection of best available generator
- Enhanced divisional charts with house cusps, aspects, and strength analysis
- Detailed yoga/dosha analysis with strength points and remedies
- Complete dasha sequences with mahadasha/antardasha periods
- Enhanced panchanga with paksha, weekday, and astronomical details
- Full JSON serialization with comprehensive error handling
"""

from .kundali_generator_factory import (
    KundaliGeneratorFactory,
    GeneratorType,
    create_kundali_generator,
    get_default_generator
)
from .base_kundali_generator import BaseKundaliGenerator
from .pyjhora_kundali_generator import PyJHoraKundaliGenerator
from .ephemeris_kundali_generator import EphemerisKundaliGenerator

__version__ = "2.0.0"

# Default factory instance for convenience
factory = KundaliGeneratorFactory()

__all__ = [
    'KundaliGeneratorFactory',
    'GeneratorType',
    'BaseKundaliGenerator',
    'PyJHoraKundaliGenerator', 
    'EphemerisKundaliGenerator',
    'create_kundali_generator',
    'get_default_generator',
    'factory'
]