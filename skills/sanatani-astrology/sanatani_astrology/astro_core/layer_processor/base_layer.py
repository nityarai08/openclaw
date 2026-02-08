"""
Base layer processor framework for the 10-layer favorability calculation system.

This module provides the abstract base class and common functionality for all
calculation layers, ensuring consistent interfaces and error handling.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import time
from dataclasses import dataclass

from ..core.data_models import KundaliData, LayerData, LayerInfo, DailyScore
from ..core.interfaces import LayerProcessorInterface


class LayerProcessingError(Exception):
    """Custom exception for layer processing errors."""
    
    def __init__(self, layer_id: int, message: str, original_error: Optional[Exception] = None):
        self.layer_id = layer_id
        self.original_error = original_error
        super().__init__(f"Layer {layer_id}: {message}")


class LayerProcessor(LayerProcessorInterface):
    """
    Abstract base class for all calculation layers.
    
    Provides common functionality for annual data generation, error handling,
    metadata generation, and standardized output formatting.
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """
        Initialize layer processor.
        
        Args:
            layer_id: Unique identifier for the layer (1-10)
            accuracy: Accuracy rating (1.0 = 100%, 0.1 = 10%)
            kundali_data: Complete kundali data for calculations
        """
        super().__init__(layer_id, accuracy, kundali_data)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._calculation_engine = self._initialize_calculation_engine()
        
        # Validate inputs
        if not isinstance(kundali_data, KundaliData):
            raise LayerProcessingError(layer_id, "Invalid kundali data provided")
        
        if not (1 <= layer_id <= 10):
            raise LayerProcessingError(layer_id, "Layer ID must be between 1 and 10")
        
        if not (0.0 <= accuracy <= 1.0):
            raise LayerProcessingError(layer_id, "Accuracy must be between 0.0 and 1.0")
    
    def _initialize_calculation_engine(self) -> Any:
        """
        Initialize calculation engine specific to the layer.
        Override in subclasses to set up layer-specific calculations.
        """
        return None
    
    @abstractmethod
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
            
        Raises:
            LayerProcessingError: If calculation fails
        """
        pass
    
    @abstractmethod
    def get_calculation_methodology(self) -> str:
        """
        Describe calculation approach and methodology.
        
        Returns:
            Detailed description of calculation methods used
        """
        pass
    
    @abstractmethod
    def get_layer_name(self) -> str:
        """
        Get the display name for this layer.
        
        Returns:
            Human-readable layer name
        """
        pass
    
    @abstractmethod
    def get_layer_description(self) -> str:
        """
        Get detailed description of what this layer calculates.
        
        Returns:
            Detailed layer description
        """
        pass
    
    @abstractmethod
    def get_calculation_factors(self) -> List[str]:
        """
        Get list of factors used in calculations.
        
        Returns:
            List of calculation factor names
        """
        pass
    
    def get_layer_info(self) -> LayerInfo:
        """Get layer information and metadata."""
        return LayerInfo(
            id=self.layer_id,
            name=self.get_layer_name(),
            accuracy_rating=self.accuracy,
            methodology=self.get_calculation_methodology(),
            description=self.get_layer_description(),
            calculation_factors=self.get_calculation_factors()
        )
    
    def generate_annual_data(self, year: int) -> LayerData:
        """
        Generate 365-day data with comprehensive error handling and metadata.
        
        Args:
            year: Year for calculation
            
        Returns:
            Complete layer data with daily scores and metadata
        """
        start_time = time.time()
        self.logger.info(f"Starting annual data generation for Layer {self.layer_id}, year {year}")
        
        try:
            daily_scores = self._generate_daily_scores(year)
            processing_time = time.time() - start_time
            
            layer_data = LayerData(
                layer_info=self.get_layer_info(),
                annual_data=daily_scores,
                summary_statistics=self._calculate_summary_statistics(daily_scores),
                calculation_metadata=self._generate_metadata(year, processing_time)
            )
            
            self.logger.info(f"Successfully generated {len(daily_scores)} daily scores for Layer {self.layer_id}")
            return layer_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate annual data for Layer {self.layer_id}: {e}")
            return self._generate_fallback_layer_data(year, str(e))
    
    def _generate_daily_scores(self, year: int) -> List[DailyScore]:
        """Generate daily scores with error handling for individual days."""
        daily_scores = []
        start_date = datetime(year, 1, 1)
        
        # Handle leap years
        days_in_year = 366 if self._is_leap_year(year) else 365
        
        failed_days = 0
        for day in range(days_in_year):
            current_date = start_date + timedelta(days=day)
            
            try:
                score = self.calculate_daily_score(current_date)
                
                # Validate score range
                if not (0.0 <= score <= 1.0):
                    self.logger.warning(f"Score {score} out of range for {current_date}, clamping to [0,1]")
                    score = max(0.0, min(1.0, score))
                
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=day + 1,
                    score=round(score, 4),
                    confidence=self.accuracy,
                    contributing_factors=self._get_contributing_factors(current_date)
                ))
                
            except Exception as e:
                failed_days += 1
                self.logger.warning(f"Failed to calculate score for {current_date}: {e}")
                
                # Use fallback score
                fallback_score = self._get_fallback_score(current_date)
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=day + 1,
                    score=fallback_score,
                    confidence=0.0,  # Zero confidence for failed calculations
                    contributing_factors={'error': str(e), 'fallback_used': True}
                ))
        
        if failed_days > 0:
            self.logger.warning(f"Layer {self.layer_id}: {failed_days} days failed calculation, using fallback scores")
        
        return daily_scores
    
    def _get_fallback_score(self, date: datetime) -> float:
        """
        Get fallback score when calculation fails.
        
        Default implementation returns neutral score (0.5).
        Override in subclasses for more sophisticated fallback logic.
        """
        return 0.5
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """
        Get contributing factors for the calculation.
        
        Override in subclasses to provide detailed factor breakdown.
        Default implementation returns empty dict.
        """
        return {}
    
    def _is_leap_year(self, year: int) -> bool:
        """Check if year is a leap year."""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    def _calculate_summary_statistics(self, daily_scores: List[DailyScore]) -> Dict[str, float]:
        """Calculate comprehensive summary statistics."""
        if not daily_scores:
            return {}
        
        scores = [score.score for score in daily_scores]
        valid_scores = [s for s in scores if s is not None]
        
        if not valid_scores:
            return {'total_days': len(scores), 'valid_days': 0}
        
        # Basic statistics
        stats = {
            'total_days': len(scores),
            'valid_days': len(valid_scores),
            'failed_days': len(scores) - len(valid_scores),
            'average_score': sum(valid_scores) / len(valid_scores),
            'highest_score': max(valid_scores),
            'lowest_score': min(valid_scores),
            'standard_deviation': self._calculate_std_dev(valid_scores)
        }
        
        # Additional statistics
        stats.update({
            'median_score': self._calculate_median(valid_scores),
            'favorable_days': len([s for s in valid_scores if s > 0.6]),
            'unfavorable_days': len([s for s in valid_scores if s < 0.4]),
            'neutral_days': len([s for s in valid_scores if 0.4 <= s <= 0.6])
        })
        
        return stats
    
    def _calculate_std_dev(self, scores: List[float]) -> float:
        """Calculate standard deviation of scores."""
        if len(scores) < 2:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5
    
    def _calculate_median(self, scores: List[float]) -> float:
        """Calculate median of scores."""
        if not scores:
            return 0.0
        
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        if n % 2 == 0:
            return (sorted_scores[n//2 - 1] + sorted_scores[n//2]) / 2
        else:
            return sorted_scores[n//2]
    
    def _generate_metadata(self, year: int, processing_time: float) -> Dict[str, Any]:
        """Generate comprehensive calculation metadata."""
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'year': year,
            'layer_id': self.layer_id,
            'layer_name': self.get_layer_name(),
            'accuracy_rating': self.accuracy,
            'processing_time_seconds': round(processing_time, 3),
            'kundali_reference': self._get_kundali_reference(),
            'calculation_engine': str(type(self._calculation_engine).__name__) if self._calculation_engine else 'None',
            'schema_version': '2.0'
        }
    
    def _get_kundali_reference(self) -> str:
        """Get reference identifier for the kundali data."""
        if hasattr(self.kundali, 'metadata') and self.kundali.metadata:
            return self.kundali.metadata.get('hash', 'unknown')
        return f"kundali_{hash(str(self.kundali.birth_details.to_dict() if self.kundali.birth_details else 'unknown'))}"
    
    def _generate_fallback_layer_data(self, year: int, error_message: str) -> LayerData:
        """Generate fallback layer data when processing completely fails."""
        self.logger.error(f"Generating fallback data for Layer {self.layer_id}: {error_message}")
        
        # Generate neutral scores for all days
        start_date = datetime(year, 1, 1)
        days_in_year = 366 if self._is_leap_year(year) else 365
        
        daily_scores = []
        for day in range(days_in_year):
            current_date = start_date + timedelta(days=day)
            daily_scores.append(DailyScore(
                date=current_date.isoformat(),
                day_of_year=day + 1,
                score=0.5,  # Neutral fallback score
                confidence=0.0,  # Zero confidence for fallback
                contributing_factors={'fallback_reason': error_message}
            ))
        
        return LayerData(
            layer_info=LayerInfo(
                id=self.layer_id,
                name=f"Layer {self.layer_id} (Fallback)",
                accuracy_rating=0.0,
                methodology="Fallback neutral scoring due to processing failure",
                description=f"Fallback data generated due to error: {error_message}",
                calculation_factors=['fallback_neutral_score']
            ),
            annual_data=daily_scores,
            summary_statistics={
                'total_days': len(daily_scores),
                'average_score': 0.5,
                'highest_score': 0.5,
                'lowest_score': 0.5,
                'standard_deviation': 0.0,
                'fallback_used': True
            },
            calculation_metadata={
                'generation_timestamp': datetime.now().isoformat(),
                'year': year,
                'layer_id': self.layer_id,
                'fallback_used': True,
                'error_message': error_message,
                'schema_version': '2.0'
            }
        )
    
    def validate_kundali_data(self) -> bool:
        """
        Validate that kundali data contains required information for this layer.
        
        Returns:
            True if kundali data is valid for this layer
        """
        if not self.kundali:
            return False
        
        # Basic validation - override in subclasses for specific requirements
        required_fields = ['birth_details', 'planetary_positions']
        
        for field in required_fields:
            if not hasattr(self.kundali, field) or not getattr(self.kundali, field):
                self.logger.error(f"Missing required field: {field}")
                return False
        
        return True
    
    def get_confidence_score(self, date: datetime) -> float:
        """
        Get confidence score for a specific date calculation.
        
        Default implementation returns the layer's base accuracy.
        Override in subclasses for date-specific confidence adjustments.
        """
        return self.accuracy