"""
Compatibility module for old comprehensive_kundali_generator imports.

This module provides backward compatibility for tests and legacy code
that still imports the old ComprehensiveKundaliGenerator class.
"""

from .kundali_generator_factory import KundaliGeneratorFactory, GeneratorType

# Backward compatibility alias
class ComprehensiveKundaliGenerator:
    """Backward compatibility wrapper for the old ComprehensiveKundaliGenerator."""
    
    def __init__(self):
        """Initialize with auto-selected generator."""
        self.generator = KundaliGeneratorFactory.create_generator(GeneratorType.AUTO)
    
    def generate_from_birth_details(
        self,
        birth_details,
        ayanamsa: str = "LAHIRI",
        house_system: str = "BHAVA_CHALIT",
    ):
        """Generate kundali from birth details with configurable ayanamsa and house system."""
        return self.generator.generate_from_birth_details(
            birth_details,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
    
    def export_standardized_json(self, kundali_data):
        """Export kundali data as JSON."""
        return self.generator.export_standardized_json(kundali_data)
    
    def validate_birth_details(self, birth_details):
        """Validate birth details."""
        return self.generator.validate_birth_details(birth_details)

# For direct import compatibility
def create_comprehensive_generator():
    """Create a comprehensive kundali generator."""
    return ComprehensiveKundaliGenerator()
