"""
Layer implementations for the 10-layer favorability calculation system.

This module contains all the specific layer implementations, each with
decreasing accuracy from 100% (Layer 1) to 10% (Layer 10).
"""

from .layer_1_astronomical_facts import Layer1_AstronomicalFacts
from .layer_2_planetary_positions import Layer2_PlanetaryPositions
from .layer_3_vedic_cycles import Layer3_VedicCycles
from .layer_4_dasha_periods import Layer4_DashaPeriods
from .layer_5_major_transits import Layer5_MajorTransits
from .layer_6_secondary_transits import Layer6_SecondaryTransits
from .layer_7_yoga_combinations import Layer7_YogaCombinations
from .layer_8_divisional_charts import Layer8_DivisionalCharts
from .layer_9_micro_periods import Layer9_MicroPeriods
from .layer_10_speculative_factors import Layer10_SpeculativeFactors

__all__ = [
    'Layer1_AstronomicalFacts',
    'Layer2_PlanetaryPositions',
    'Layer3_VedicCycles',
    'Layer4_DashaPeriods',
    'Layer5_MajorTransits',
    'Layer6_SecondaryTransits',
    'Layer7_YogaCombinations',
    'Layer8_DivisionalCharts',
    'Layer9_MicroPeriods',
    'Layer10_SpeculativeFactors'
]

# Layer registry for easy access
LAYER_REGISTRY = {
    1: Layer1_AstronomicalFacts,
    2: Layer2_PlanetaryPositions,
    3: Layer3_VedicCycles,
    4: Layer4_DashaPeriods,
    5: Layer5_MajorTransits,
    6: Layer6_SecondaryTransits,
    7: Layer7_YogaCombinations,
    8: Layer8_DivisionalCharts,
    9: Layer9_MicroPeriods,
    10: Layer10_SpeculativeFactors
}

def get_layer_class(layer_id: int):
    """Get layer class by ID."""
    return LAYER_REGISTRY.get(layer_id)

def get_available_layers():
    """Get list of available layer IDs."""
    return sorted(LAYER_REGISTRY.keys())