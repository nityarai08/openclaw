"""
Abstract base classes and interfaces for the Kundali Favorability Heatmap System.

This module defines the interfaces that each component must implement to ensure
proper decoupling and standardized communication between components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .data_models import (
    BirthDetails, KundaliData, LayerData, ValidationResult,
    LocationData, DailyScore, LayerInfo
)


class KundaliGeneratorInterface(ABC):
    """Abstract interface for kundali generation."""
    
    @abstractmethod
    def generate_from_birth_details(
        self,
        birth_data: BirthDetails,
        ayanamsa: str = "LAHIRI",
        house_system: str = "BHAVA_CHALIT",
    ) -> KundaliData:
        """Generate complete kundali from birth details."""
        pass
    
    @abstractmethod
    def validate_birth_details(self, birth_data: BirthDetails) -> ValidationResult:
        """Validate birth details for completeness and accuracy."""
        pass
    
    @abstractmethod
    def export_standardized_json(self, kundali: KundaliData) -> str:
        """Export kundali in standardized JSON format."""
        pass


class LayerProcessorInterface(ABC):
    """Abstract interface for layer processing."""
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        self.layer_id = layer_id
        self.accuracy = accuracy
        self.kundali = kundali_data
    
    @abstractmethod
    def calculate_daily_score(self, date: datetime) -> float:
        """Calculate favorability score for specific date."""
        pass
    
    @abstractmethod
    def get_calculation_methodology(self) -> str:
        """Describe calculation approach and methodology."""
        pass
    
    @abstractmethod
    def get_layer_info(self) -> LayerInfo:
        """Get layer information and metadata."""
        pass
    
    def generate_annual_data(self, year: int) -> LayerData:
        """Generate 365-day data with metadata."""
        from datetime import timedelta
        
        daily_scores = []
        start_date = datetime(year, 1, 1)
        
        # Handle leap years (366 days) vs regular years (365 days)
        days_in_year = 366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365
        
        for day in range(days_in_year):
            current_date = start_date + timedelta(days=day)
            try:
                score = self.calculate_daily_score(current_date)
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=day + 1,
                    score=round(score, 4),
                    confidence=self.accuracy,
                    contributing_factors=self._get_contributing_factors(current_date)
                ))
            except Exception as e:
                # Log error and use neutral score
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=day + 1,
                    score=0.5,  # Neutral score on error
                    confidence=0.0,
                    contributing_factors={'error': str(e)}
                ))
        
        return LayerData(
            layer_info=self.get_layer_info(),
            annual_data=daily_scores,
            summary_statistics=self._calculate_summary_statistics(daily_scores),
            calculation_metadata=self._generate_metadata(year)
        )
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get contributing factors for the calculation (override in subclasses)."""
        return {}
    
    def _calculate_summary_statistics(self, daily_scores: List[DailyScore]) -> Dict[str, float]:
        """Calculate summary statistics for the annual data."""
        if not daily_scores:
            return {}
        
        scores = [score.score for score in daily_scores]
        return {
            'total_days': len(scores),
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'standard_deviation': self._calculate_std_dev(scores)
        }
    
    def _calculate_std_dev(self, scores: List[float]) -> float:
        """Calculate standard deviation of scores."""
        if len(scores) < 2:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5
    
    def _generate_metadata(self, year: int) -> Dict[str, Any]:
        """Generate calculation metadata."""
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'year': year,
            'layer_id': self.layer_id,
            'accuracy_rating': self.accuracy,
            'kundali_reference': getattr(self.kundali, 'metadata', {}).get('hash', 'unknown')
        }


class VisualizerInterface(ABC):
    """Abstract interface for visualization generation."""
    
    @abstractmethod
    def create_individual_layer_heatmap(self, layer_data: LayerData, year: int) -> Any:
        """Create heatmap for single layer."""
        pass
    
    @abstractmethod
    def create_combined_heatmap(self, layer_data_list: List[LayerData], 
                               layer_weights: Dict[int, float], year: int) -> Any:
        """Create weighted combination heatmap."""
        pass
    
    @abstractmethod
    def create_overlay_comparison(self, layer_data_list: List[LayerData], 
                                 layer_ids: List[int], year: int) -> Any:
        """Create side-by-side layer comparison."""
        pass
    
    @abstractmethod
    def export_visualization(self, figure: Any, filename: str, format: str = 'png') -> str:
        """Export visualization to file."""
        pass


class ConfigurationManagerInterface(ABC):
    """Abstract interface for configuration management."""
    
    @abstractmethod
    def get_layer_weights(self) -> Dict[int, float]:
        """Get layer weights for combination calculations."""
        pass
    
    @abstractmethod
    def set_layer_weights(self, weights: Dict[int, float]) -> None:
        """Set layer weights for combination calculations."""
        pass
    
    @abstractmethod
    def get_calculation_parameters(self) -> Dict[str, Any]:
        """Get calculation parameters (ayanamsa, methods, etc.)."""
        pass
    
    @abstractmethod
    def set_calculation_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set calculation parameters."""
        pass
    
    @abstractmethod
    def validate_configuration(self) -> ValidationResult:
        """Validate current configuration."""
        pass
    
    @abstractmethod
    def export_configuration(self, filename: str) -> None:
        """Export configuration to file."""
        pass
    
    @abstractmethod
    def import_configuration(self, filename: str) -> None:
        """Import configuration from file."""
        pass


class DataValidatorInterface(ABC):
    """Abstract interface for data validation."""
    
    @abstractmethod
    def validate_kundali_data(self, kundali: KundaliData) -> ValidationResult:
        """Validate kundali data structure and content."""
        pass
    
    @abstractmethod
    def validate_layer_data(self, layer_data: LayerData) -> ValidationResult:
        """Validate layer data structure and content."""
        pass
    
    @abstractmethod
    def validate_birth_details(self, birth_details: BirthDetails) -> ValidationResult:
        """Validate birth details."""
        pass
    
    @abstractmethod
    def assess_data_quality(self, data: Any, data_type: str) -> Dict[str, float]:
        """Assess data quality for given data type."""
        pass
    
    @abstractmethod
    def get_validation_report(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Get comprehensive validation report."""
        pass
