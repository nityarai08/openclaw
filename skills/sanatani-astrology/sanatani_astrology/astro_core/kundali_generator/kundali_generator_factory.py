"""
Kundali Generator Factory.

This module provides a factory for creating the two main kundali generator implementations:
1. PyJHora-based generator
2. Ephemeris-based generator
"""

from enum import Enum
from typing import Optional, Dict, Any

from .base_kundali_generator import BaseKundaliGenerator
from .pyjhora_kundali_generator import PyJHoraKundaliGenerator, PYJHORA_AVAILABLE
from .ephemeris_kundali_generator import EphemerisKundaliGenerator

try:
    import swisseph as swe
    SWISS_EPHEMERIS_AVAILABLE = True
except ImportError:
    SWISS_EPHEMERIS_AVAILABLE = False


class GeneratorType(Enum):
    """Available kundali generator types."""
    PYJHORA = "pyjhora"
    EPHEMERIS = "ephemeris"
    AUTO = "auto"


class KundaliGeneratorFactory:
    """
    Factory class for creating kundali generator instances.
    
    This factory supports two main implementations:
    1. PyJHora-based generator (traditional Vedic calculations)
    2. Ephemeris-based generator (Swiss Ephemeris with fallback)
    """
    
    @staticmethod
    def create_generator(
        generator_type: GeneratorType = GeneratorType.AUTO,
        ephemeris_path: Optional[str] = None,
        **kwargs
    ) -> BaseKundaliGenerator:
        """
        Create a kundali generator instance.
        
        Args:
            generator_type: Type of generator to create
            ephemeris_path: Path to Swiss Ephemeris data files (for ephemeris generator)
            **kwargs: Additional arguments for specific generators
            
        Returns:
            Kundali generator instance
            
        Raises:
            ValueError: If requested generator type is not available
            ImportError: If required libraries are not available
        """
        if generator_type == GeneratorType.AUTO:
            return KundaliGeneratorFactory._create_auto_generator(ephemeris_path, **kwargs)
        elif generator_type == GeneratorType.PYJHORA:
            return KundaliGeneratorFactory._create_pyjhora_generator(**kwargs)
        elif generator_type == GeneratorType.EPHEMERIS:
            return KundaliGeneratorFactory._create_ephemeris_generator(ephemeris_path, **kwargs)
        else:
            raise ValueError(f"Unknown generator type: {generator_type}")
    
    @staticmethod
    def _create_auto_generator(
        ephemeris_path: Optional[str] = None,
        **kwargs
    ) -> BaseKundaliGenerator:
        """
        Create the best available generator automatically.
        
        Priority order:
        1. PyJHora (if available - most accurate for Vedic calculations)
        2. Ephemeris (Swiss Ephemeris or fallback methods)
        
        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
            **kwargs: Additional arguments
            
        Returns:
            Best available kundali generator instance
        """
        # Try PyJHora first if available (most accurate for Vedic calculations)
        if PYJHORA_AVAILABLE:
            try:
                return PyJHoraKundaliGenerator()
            except Exception as e:
                print(f"Warning: Could not create PyJHora generator: {e}")
        
        # Fallback to ephemeris generator (always available with fallback methods)
        try:
            return EphemerisKundaliGenerator(ephemeris_path)
        except Exception as e:
            raise ImportError(
                f"No suitable kundali generator implementation available. Error: {e}"
            )
    
    @staticmethod
    def _create_pyjhora_generator(**kwargs) -> PyJHoraKundaliGenerator:
        """
        Create PyJHora-based generator.
        
        Args:
            **kwargs: Additional arguments
            
        Returns:
            PyJHora kundali generator instance
            
        Raises:
            ImportError: If PyJHora is not available
        """
        if not PYJHORA_AVAILABLE:
            raise ImportError(
                "PyJHora library is not available. "
                "Please install PyJHora to use this generator type."
            )
        
        return PyJHoraKundaliGenerator()
    
    @staticmethod
    def _create_ephemeris_generator(
        ephemeris_path: Optional[str] = None,
        **kwargs
    ) -> EphemerisKundaliGenerator:
        """
        Create ephemeris-based generator.
        
        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
            **kwargs: Additional arguments
            
        Returns:
            Ephemeris kundali generator instance
        """
        return EphemerisKundaliGenerator(ephemeris_path)
    
    @staticmethod
    def get_available_generators() -> Dict[str, Dict[str, Any]]:
        """
        Get information about available generator implementations.
        
        Returns:
            Dictionary with generator availability and info
        """
        generators = {}
        
        # Check PyJHora availability
        generators['pyjhora'] = {
            'available': PYJHORA_AVAILABLE,
            'name': 'PyJHora Generator',
            'description': 'Traditional Vedic calculations using PyJHora library',
            'accuracy': 'high',
            'dependencies': ['pyjhora'],
            'features': [
                'Traditional Vedic methods',
                'Precise planetary positions',
                'Accurate ascendant calculation',
                'Consistent output schema'
            ]
        }
        
        # Check ephemeris availability
        generators['ephemeris'] = {
            'available': True,  # Always available with fallbacks
            'name': 'Ephemeris Generator',
            'description': 'Swiss Ephemeris with simplified fallback methods',
            'accuracy': 'high' if SWISS_EPHEMERIS_AVAILABLE else 'medium',
            'dependencies': ['swisseph (optional)'],
            'primary_engine': 'Swiss Ephemeris' if SWISS_EPHEMERIS_AVAILABLE else 'Simplified',
            'features': [
                'Swiss Ephemeris calculations' if SWISS_EPHEMERIS_AVAILABLE else 'Simplified calculations',
                'Comprehensive error handling',
                'Consistent output schema',
                'Always available fallback'
            ]
        }
        
        return generators
    
    @staticmethod
    def get_recommended_generator() -> GeneratorType:
        """
        Get the recommended generator type based on system capabilities.
        
        Returns:
            Recommended generator type
        """
        if PYJHORA_AVAILABLE:
            return GeneratorType.PYJHORA  # Most accurate for Vedic calculations
        else:
            return GeneratorType.EPHEMERIS  # Always available with fallback methods
    
    @staticmethod
    def validate_generator_requirements(generator_type: GeneratorType) -> Dict[str, Any]:
        """
        Validate requirements for a specific generator type.
        
        Args:
            generator_type: Generator type to validate
            
        Returns:
            Validation result with requirements status
        """
        result = {
            'valid': True,
            'missing_dependencies': [],
            'warnings': [],
            'recommendations': []
        }
        
        if generator_type == GeneratorType.PYJHORA:
            if not PYJHORA_AVAILABLE:
                result['valid'] = False
                result['missing_dependencies'].append('pyjhora')
                result['recommendations'].append('Install PyJHora library for traditional Vedic calculations')
        
        elif generator_type == GeneratorType.EPHEMERIS:
            if not SWISS_EPHEMERIS_AVAILABLE:
                result['warnings'].append('Swiss Ephemeris not available, will use simplified calculations')
                result['recommendations'].append('Install Swiss Ephemeris for highest accuracy')
        
        elif generator_type == GeneratorType.AUTO:
            # Auto will always work with some implementation
            if not PYJHORA_AVAILABLE and not SWISS_EPHEMERIS_AVAILABLE:
                result['warnings'].append('No high-accuracy libraries available, using simplified calculations')
                result['recommendations'].extend([
                    'Install PyJHora for traditional Vedic calculations',
                    'Install Swiss Ephemeris for highest accuracy'
                ])
            elif not PYJHORA_AVAILABLE:
                result['warnings'].append('PyJHora not available, using ephemeris generator')
                result['recommendations'].append('Install PyJHora for traditional Vedic calculations')
        
        return result


# Convenience functions for backward compatibility

def create_kundali_generator(
    generator_type: str = "auto",
    ephemeris_path: Optional[str] = None
) -> BaseKundaliGenerator:
    """
    Convenience function to create a kundali generator.
    
    Args:
        generator_type: Type of generator ("auto", "pyjhora", "ephemeris")
        ephemeris_path: Path to Swiss Ephemeris data files
        
    Returns:
        Kundali generator instance
    """
    try:
        gen_type = GeneratorType(generator_type.lower())
    except ValueError:
        gen_type = GeneratorType.AUTO
    
    return KundaliGeneratorFactory.create_generator(gen_type, ephemeris_path)


def get_default_generator(ephemeris_path: Optional[str] = None) -> BaseKundaliGenerator:
    """
    Get the default (recommended) kundali generator.
    
    Args:
        ephemeris_path: Path to Swiss Ephemeris data files
        
    Returns:
        Default kundali generator instance
    """
    recommended_type = KundaliGeneratorFactory.get_recommended_generator()
    return KundaliGeneratorFactory.create_generator(recommended_type, ephemeris_path)