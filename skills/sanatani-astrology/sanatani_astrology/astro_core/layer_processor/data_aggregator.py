"""
Layer data aggregation and export system for the kundali favorability heatmap.

This module provides comprehensive data collection, validation, aggregation,
and export capabilities for all layer processing results.
"""

import json
import gzip
import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ..core.data_models import LayerData, LayerInfo, DailyScore, KundaliData
from .master_integration_engine import MasterIntegrationEngine


@dataclass
class AggregationMetadata:
    """Metadata for aggregated layer data."""
    aggregation_timestamp: str
    total_layers: int
    successful_layers: int
    failed_layers: int
    year: int
    kundali_reference: str
    schema_version: str = "2.0"
    compression_used: bool = False
    data_integrity_hash: Optional[str] = None
    processing_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'aggregation_timestamp': self.aggregation_timestamp,
            'total_layers': self.total_layers,
            'successful_layers': self.successful_layers,
            'failed_layers': self.failed_layers,
            'year': self.year,
            'kundali_reference': self.kundali_reference,
            'schema_version': self.schema_version,
            'compression_used': self.compression_used,
            'data_integrity_hash': self.data_integrity_hash,
            'processing_duration': self.processing_duration
        }


@dataclass
class AggregatedLayerData:
    """Complete aggregated data from all layers."""
    metadata: AggregationMetadata
    layer_data: Dict[int, LayerData]
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    cross_layer_analysis: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'metadata': self.metadata.to_dict(),
            'layer_data': {str(k): v.to_dict() for k, v in self.layer_data.items()},
            'summary_statistics': self.summary_statistics,
            'cross_layer_analysis': self.cross_layer_analysis,
            'validation_results': self.validation_results
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class DataValidationError(Exception):
    """Exception raised when data validation fails."""
    pass


class LayerDataAggregator:
    """
    Comprehensive layer data aggregation and export system.
    
    Handles data collection, validation, integrity checking, cross-layer analysis,
    and multiple export formats with compression and optimization.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize the data aggregator.
        
        Args:
            kundali_data: Source kundali data for reference
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validation rules
        self._validation_rules = self._initialize_validation_rules()
        
        # Export formats
        self._export_handlers = {
            'json': self._export_json,
            'compressed_json': self._export_compressed_json,
            'individual_layers': self._export_individual_layers,
            'summary_only': self._export_summary_only,
            'csv': self._export_csv
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize data validation rules."""
        return {
            'required_fields': ['layer_info', 'annual_data', 'summary_statistics', 'calculation_metadata'],
            'score_range': (0.0, 1.0),
            'confidence_range': (0.0, 1.0),
            'expected_days': {
                'regular_year': 365,
                'leap_year': 366
            },
            'layer_id_range': (1, 10),
            'accuracy_expectations': {
                1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6,
                6: 0.5, 7: 0.4, 8: 0.3, 9: 0.2, 10: 0.1
            }
        }
    
    def aggregate_layer_data(self, layer_data_dict: Dict[int, LayerData], 
                           year: int, processing_duration: float = None) -> AggregatedLayerData:
        """
        Aggregate multiple layer data into a comprehensive structure.
        
        Args:
            layer_data_dict: Dictionary mapping layer_id to LayerData
            year: Year for which data was processed
            processing_duration: Total processing time in seconds
            
        Returns:
            Aggregated layer data with comprehensive analysis
            
        Raises:
            DataValidationError: If data validation fails
        """
        start_time = datetime.now()
        self.logger.info(f"Starting data aggregation for {len(layer_data_dict)} layers")
        
        # Validate input data
        validation_results = self.validate_layer_data_collection(layer_data_dict, year)
        if not validation_results['is_valid']:
            raise DataValidationError(f"Data validation failed: {validation_results['errors']}")
        
        # Create metadata
        metadata = AggregationMetadata(
            aggregation_timestamp=start_time.isoformat(),
            total_layers=len(layer_data_dict),
            successful_layers=len([ld for ld in layer_data_dict.values() if ld is not None]),
            failed_layers=len([ld for ld in layer_data_dict.values() if ld is None]),
            year=year,
            kundali_reference=self._get_kundali_reference(),
            processing_duration=processing_duration
        )
        
        # Generate comprehensive statistics
        summary_stats = self._generate_comprehensive_statistics(layer_data_dict, year)
        
        # Perform cross-layer analysis
        cross_layer_analysis = self._perform_cross_layer_analysis(layer_data_dict)
        
        # Calculate data integrity hash
        data_hash = self._calculate_data_integrity_hash(layer_data_dict)
        metadata.data_integrity_hash = data_hash
        
        aggregated_data = AggregatedLayerData(
            metadata=metadata,
            layer_data=layer_data_dict,
            summary_statistics=summary_stats,
            cross_layer_analysis=cross_layer_analysis,
            validation_results=validation_results
        )
        
        self.logger.info(f"Data aggregation completed in {(datetime.now() - start_time).total_seconds():.2f} seconds")
        return aggregated_data
    
    def validate_layer_data_collection(self, layer_data_dict: Dict[int, LayerData], 
                                     year: int) -> Dict[str, Any]:
        """
        Comprehensive validation of layer data collection.
        
        Args:
            layer_data_dict: Dictionary of layer data to validate
            year: Expected year for validation
            
        Returns:
            Validation results with detailed error and warning information
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'layer_validation': {},
            'cross_layer_validation': {}
        }
        
        # Validate each layer individually
        for layer_id, layer_data in layer_data_dict.items():
            layer_validation = self._validate_single_layer(layer_id, layer_data, year)
            validation_result['layer_validation'][layer_id] = layer_validation
            
            if not layer_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['errors'].extend([
                    f"Layer {layer_id}: {error}" for error in layer_validation['errors']
                ])
            
            validation_result['warnings'].extend([
                f"Layer {layer_id}: {warning}" for warning in layer_validation['warnings']
            ])
        
        # Cross-layer validation
        cross_validation = self._validate_cross_layer_consistency(layer_data_dict, year)
        validation_result['cross_layer_validation'] = cross_validation
        
        if not cross_validation['is_valid']:
            validation_result['is_valid'] = False
            validation_result['errors'].extend(cross_validation['errors'])
        
        validation_result['warnings'].extend(cross_validation['warnings'])
        
        return validation_result
    
    def _validate_single_layer(self, layer_id: int, layer_data: LayerData, year: int) -> Dict[str, Any]:
        """Validate a single layer's data."""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        if layer_data is None:
            result['is_valid'] = False
            result['errors'].append("Layer data is None")
            return result
        
        # Validate layer ID
        if not (1 <= layer_id <= 10):
            result['errors'].append(f"Invalid layer ID: {layer_id}")
            result['is_valid'] = False
        
        # Validate required fields
        for field in self._validation_rules['required_fields']:
            if not hasattr(layer_data, field) or getattr(layer_data, field) is None:
                result['errors'].append(f"Missing required field: {field}")
                result['is_valid'] = False
        
        if not result['is_valid']:
            return result
        
        # Validate layer info
        if layer_data.layer_info.id != layer_id:
            result['errors'].append(f"Layer info ID mismatch: expected {layer_id}, got {layer_data.layer_info.id}")
            result['is_valid'] = False
        
        # Validate accuracy rating
        expected_accuracy = self._validation_rules['accuracy_expectations'].get(layer_id)
        if expected_accuracy and abs(layer_data.layer_info.accuracy_rating - expected_accuracy) > 0.01:
            result['warnings'].append(f"Unexpected accuracy rating: expected {expected_accuracy}, got {layer_data.layer_info.accuracy_rating}")
        
        # Validate annual data
        annual_validation = self._validate_annual_data(layer_data.annual_data, year)
        if not annual_validation['is_valid']:
            result['is_valid'] = False
            result['errors'].extend(annual_validation['errors'])
        result['warnings'].extend(annual_validation['warnings'])
        
        return result
    
    def _validate_annual_data(self, annual_data: List[DailyScore], year: int) -> Dict[str, Any]:
        """Validate annual data for completeness and consistency."""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        # Check expected number of days
        is_leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        expected_days = 366 if is_leap_year else 365
        
        if len(annual_data) != expected_days:
            result['errors'].append(f"Expected {expected_days} days, got {len(annual_data)}")
            result['is_valid'] = False
            return result
        
        # Validate each daily score
        for i, daily_score in enumerate(annual_data):
            day_errors = []
            
            # Validate score range
            if not (0.0 <= daily_score.score <= 1.0):
                day_errors.append(f"Score out of range: {daily_score.score}")
            
            # Validate confidence range
            if not (0.0 <= daily_score.confidence <= 1.0):
                day_errors.append(f"Confidence out of range: {daily_score.confidence}")
            
            # Validate day of year
            if daily_score.day_of_year != i + 1:
                day_errors.append(f"Day of year mismatch: expected {i + 1}, got {daily_score.day_of_year}")
            
            if day_errors:
                result['errors'].extend([f"Day {i + 1}: {error}" for error in day_errors])
                result['is_valid'] = False
        
        return result
    
    def _validate_cross_layer_consistency(self, layer_data_dict: Dict[int, LayerData], 
                                        year: int) -> Dict[str, Any]:
        """Validate consistency across layers."""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        if len(layer_data_dict) < 2:
            return result  # No cross-layer validation needed
        
        # Check that all layers have the same number of days
        day_counts = {layer_id: len(data.annual_data) for layer_id, data in layer_data_dict.items()}
        unique_counts = set(day_counts.values())
        
        if len(unique_counts) > 1:
            result['errors'].append(f"Inconsistent day counts across layers: {day_counts}")
            result['is_valid'] = False
        
        # Check date consistency
        first_layer_data = next(iter(layer_data_dict.values()))
        reference_dates = [score.date for score in first_layer_data.annual_data]
        
        for layer_id, layer_data in layer_data_dict.items():
            layer_dates = [score.date for score in layer_data.annual_data]
            if layer_dates != reference_dates:
                result['errors'].append(f"Layer {layer_id} has inconsistent dates")
                result['is_valid'] = False
        
        return result
    
    def _generate_comprehensive_statistics(self, layer_data_dict: Dict[int, LayerData], 
                                         year: int) -> Dict[str, Any]:
        """Generate comprehensive statistics across all layers."""
        stats = {
            'year': year,
            'total_layers': len(layer_data_dict),
            'layer_statistics': {},
            'cross_layer_statistics': {},
            'data_quality_metrics': {}
        }
        
        # Individual layer statistics
        for layer_id, layer_data in layer_data_dict.items():
            if layer_data and layer_data.summary_statistics:
                stats['layer_statistics'][layer_id] = layer_data.summary_statistics.copy()
        
        # Cross-layer statistics
        if len(layer_data_dict) > 1:
            stats['cross_layer_statistics'] = self._calculate_cross_layer_statistics(layer_data_dict)
        
        # Data quality metrics
        stats['data_quality_metrics'] = self._calculate_data_quality_metrics(layer_data_dict)
        
        return stats
    
    def _calculate_cross_layer_statistics(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Calculate statistics across multiple layers."""
        cross_stats = {}
        
        # Collect all daily scores by date
        daily_scores_by_date = {}
        for layer_id, layer_data in layer_data_dict.items():
            for daily_score in layer_data.annual_data:
                date = daily_score.date
                if date not in daily_scores_by_date:
                    daily_scores_by_date[date] = {}
                daily_scores_by_date[date][layer_id] = daily_score.score
        
        # Calculate correlation matrix
        layer_ids = sorted(layer_data_dict.keys())
        correlations = {}
        
        for i, layer1 in enumerate(layer_ids):
            for j, layer2 in enumerate(layer_ids):
                if i < j:  # Only calculate upper triangle
                    scores1 = []
                    scores2 = []
                    
                    for date_scores in daily_scores_by_date.values():
                        if layer1 in date_scores and layer2 in date_scores:
                            scores1.append(date_scores[layer1])
                            scores2.append(date_scores[layer2])
                    
                    if len(scores1) > 1:
                        correlation = self._calculate_correlation(scores1, scores2)
                        correlations[f"{layer1}_{layer2}"] = correlation
        
        cross_stats['layer_correlations'] = correlations
        
        # Calculate daily averages across layers
        daily_averages = []
        for date_scores in daily_scores_by_date.values():
            if date_scores:
                avg_score = sum(date_scores.values()) / len(date_scores)
                daily_averages.append(avg_score)
        
        if daily_averages:
            cross_stats['overall_statistics'] = {
                'mean_daily_average': sum(daily_averages) / len(daily_averages),
                'max_daily_average': max(daily_averages),
                'min_daily_average': min(daily_averages),
                'std_daily_average': self._calculate_std_dev(daily_averages)
            }
        
        return cross_stats
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _calculate_data_quality_metrics(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        metrics = {
            'completeness': {},
            'consistency': {},
            'accuracy_distribution': {}
        }
        
        # Completeness metrics
        for layer_id, layer_data in layer_data_dict.items():
            if layer_data:
                total_days = len(layer_data.annual_data)
                valid_scores = len([s for s in layer_data.annual_data if s.confidence > 0])
                completeness = (valid_scores / total_days) * 100 if total_days > 0 else 0
                metrics['completeness'][layer_id] = completeness
        
        # Accuracy distribution
        accuracy_counts = {}
        for layer_data in layer_data_dict.values():
            if layer_data:
                accuracy = layer_data.layer_info.accuracy_rating
                accuracy_range = f"{int(accuracy * 100)}%"
                accuracy_counts[accuracy_range] = accuracy_counts.get(accuracy_range, 0) + 1
        
        metrics['accuracy_distribution'] = accuracy_counts
        
        return metrics
    
    def _perform_cross_layer_analysis(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Perform comprehensive cross-layer analysis."""
        analysis = {
            'layer_agreement': {},
            'outlier_detection': {},
            'trend_analysis': {},
            'confidence_analysis': {},
            'master_integration': {}
        }
        
        if len(layer_data_dict) < 2:
            return analysis
        
        # Layer agreement analysis
        analysis['layer_agreement'] = self._analyze_layer_agreement(layer_data_dict)
        
        # Outlier detection
        analysis['outlier_detection'] = self._detect_outliers(layer_data_dict)
        
        # Trend analysis
        analysis['trend_analysis'] = self._analyze_trends(layer_data_dict)
        
        # Confidence analysis
        analysis['confidence_analysis'] = self._analyze_confidence_patterns(layer_data_dict)

        # Master integration daily analysis (world-class synthesis)
        try:
            # Use dates from the first available layer as the driving calendar
            first_layer = next(iter(layer_data_dict.values()))
            dates = [score.date for score in first_layer.annual_data]
            engine = MasterIntegrationEngine(self.kundali_data)
            daily_master = []
            for date_str in dates:
                try:
                    dt = datetime.fromisoformat(date_str)
                except Exception:
                    continue
                result = engine.calculate_master_favorability(dt)
                daily_master.append({
                    'date': date_str,
                    'master_favorability': result.get('master_favorability', 0.5),
                    'confidence': result.get('confidence_level', 0.5)
                })
            if daily_master:
                avg_master = sum(d['master_favorability'] for d in daily_master) / len(daily_master)
                avg_conf = sum(d['confidence'] for d in daily_master) / len(daily_master)
                analysis['master_integration'] = {
                    'daily_scores': daily_master,
                    'summary': {
                        'average_master_favorability': avg_master,
                        'average_confidence': avg_conf
                    }
                }
        except Exception as e:
            self.logger.warning(f"Master integration analysis skipped: {e}")
        
        return analysis
    
    def _analyze_layer_agreement(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Analyze agreement between layers."""
        agreement_analysis = {}
        
        # Find days where layers agree (within threshold)
        agreement_threshold = 0.2  # 20% difference threshold
        
        daily_agreements = []
        for day_idx in range(len(next(iter(layer_data_dict.values())).annual_data)):
            day_scores = []
            for layer_data in layer_data_dict.values():
                if day_idx < len(layer_data.annual_data):
                    day_scores.append(layer_data.annual_data[day_idx].score)
            
            if len(day_scores) > 1:
                score_range = max(day_scores) - min(day_scores)
                agreement = score_range <= agreement_threshold
                daily_agreements.append(agreement)
        
        if daily_agreements:
            agreement_rate = (sum(daily_agreements) / len(daily_agreements)) * 100
            agreement_analysis['overall_agreement_rate'] = agreement_rate
            agreement_analysis['agreement_threshold'] = agreement_threshold
        
        return agreement_analysis
    
    def _detect_outliers(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Detect outlier days across layers."""
        outlier_analysis = {}
        
        # Calculate daily averages and identify outliers
        daily_stats = []
        for day_idx in range(len(next(iter(layer_data_dict.values())).annual_data)):
            day_scores = []
            for layer_data in layer_data_dict.values():
                if day_idx < len(layer_data.annual_data):
                    day_scores.append(layer_data.annual_data[day_idx].score)
            
            if day_scores:
                daily_stats.append({
                    'day': day_idx + 1,
                    'mean': sum(day_scores) / len(day_scores),
                    'std': self._calculate_std_dev(day_scores),
                    'range': max(day_scores) - min(day_scores)
                })
        
        # Identify outlier days (high standard deviation)
        if daily_stats:
            std_values = [stat['std'] for stat in daily_stats]
            mean_std = sum(std_values) / len(std_values)
            std_threshold = mean_std + 2 * self._calculate_std_dev(std_values)
            
            outlier_days = [
                stat['day'] for stat in daily_stats 
                if stat['std'] > std_threshold
            ]
            
            outlier_analysis['outlier_days'] = outlier_days
            outlier_analysis['outlier_threshold'] = std_threshold
            outlier_analysis['outlier_count'] = len(outlier_days)
        
        return outlier_analysis
    
    def _analyze_trends(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Analyze trends across layers and time."""
        trend_analysis = {}
        
        # Calculate monthly averages for each layer
        monthly_averages = {}
        for layer_id, layer_data in layer_data_dict.items():
            monthly_scores = [[] for _ in range(12)]  # 12 months
            
            for daily_score in layer_data.annual_data:
                try:
                    date_obj = datetime.fromisoformat(daily_score.date)
                    month_idx = date_obj.month - 1
                    monthly_scores[month_idx].append(daily_score.score)
                except ValueError:
                    continue
            
            monthly_averages[layer_id] = [
                sum(scores) / len(scores) if scores else 0.0
                for scores in monthly_scores
            ]
        
        trend_analysis['monthly_averages'] = monthly_averages
        
        return trend_analysis
    
    def _analyze_confidence_patterns(self, layer_data_dict: Dict[int, LayerData]) -> Dict[str, Any]:
        """Analyze confidence patterns across layers."""
        confidence_analysis = {}
        
        # Calculate average confidence by layer
        layer_confidences = {}
        for layer_id, layer_data in layer_data_dict.items():
            confidences = [score.confidence for score in layer_data.annual_data]
            if confidences:
                layer_confidences[layer_id] = {
                    'average': sum(confidences) / len(confidences),
                    'min': min(confidences),
                    'max': max(confidences),
                    'zero_confidence_days': len([c for c in confidences if c == 0.0])
                }
        
        confidence_analysis['layer_confidences'] = layer_confidences
        
        return confidence_analysis
    
    def _calculate_data_integrity_hash(self, layer_data_dict: Dict[int, LayerData]) -> str:
        """Calculate SHA-256 hash for data integrity verification."""
        # Create a deterministic string representation of the data
        data_string = ""
        
        for layer_id in sorted(layer_data_dict.keys()):
            layer_data = layer_data_dict[layer_id]
            if layer_data:
                # Include key data points for hash calculation
                data_string += f"layer_{layer_id}:"
                data_string += f"accuracy_{layer_data.layer_info.accuracy_rating}:"
                
                # Include a sample of daily scores for efficiency
                sample_scores = layer_data.annual_data[::10]  # Every 10th score
                for score in sample_scores:
                    data_string += f"{score.date}_{score.score}_{score.confidence}:"
        
        # Calculate SHA-256 hash
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _get_kundali_reference(self) -> str:
        """Get reference identifier for the kundali data."""
        if hasattr(self.kundali_data, 'metadata') and self.kundali_data.metadata:
            return self.kundali_data.metadata.get('hash', 'unknown')
        
        # Generate hash from birth details
        if self.kundali_data.birth_details:
            birth_string = f"{self.kundali_data.birth_details.date}_{self.kundali_data.birth_details.time}_{self.kundali_data.birth_details.latitude}_{self.kundali_data.birth_details.longitude}"
            return hashlib.md5(birth_string.encode()).hexdigest()[:16]
        
        return 'unknown'
    
    def export_aggregated_data(self, aggregated_data: AggregatedLayerData, 
                             output_path: str, export_format: str = 'json',
                             compression: bool = False) -> Dict[str, str]:
        """
        Export aggregated data in specified format.
        
        Args:
            aggregated_data: Aggregated layer data to export
            output_path: Base output path (directory or file)
            export_format: Export format ('json', 'compressed_json', 'individual_layers', 'summary_only', 'csv')
            compression: Whether to use compression (for applicable formats)
            
        Returns:
            Dictionary with export results and file paths
        """
        if export_format not in self._export_handlers:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        self.logger.info(f"Exporting aggregated data in {export_format} format to {output_path}")
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent if Path(output_path).is_file() else Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Call appropriate export handler
        export_handler = self._export_handlers[export_format]
        result = export_handler(aggregated_data, output_path, compression)
        
        self.logger.info(f"Export completed: {result}")
        return result
    
    def _export_json(self, aggregated_data: AggregatedLayerData, 
                    output_path: str, compression: bool = False) -> Dict[str, str]:
        """Export as single JSON file."""
        if Path(output_path).is_dir():
            filename = f"aggregated_layer_data_{aggregated_data.metadata.year}.json"
            filepath = Path(output_path) / filename
        else:
            filepath = Path(output_path)
        
        # Write JSON data
        with open(filepath, 'w') as f:
            json.dump(aggregated_data.to_dict(), f, indent=2, default=str)
        
        # Apply compression if requested
        if compression:
            compressed_path = f"{filepath}.gz"
            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove uncompressed file
            filepath.unlink()
            filepath = Path(compressed_path)
            
            # Update metadata
            aggregated_data.metadata.compression_used = True
        
        return {
            'format': 'json',
            'filepath': str(filepath),
            'size_bytes': filepath.stat().st_size,
            'compressed': compression
        }
    
    def _export_compressed_json(self, aggregated_data: AggregatedLayerData, 
                              output_path: str, compression: bool = True) -> Dict[str, str]:
        """Export as compressed JSON file."""
        return self._export_json(aggregated_data, output_path, compression=True)
    
    def _export_individual_layers(self, aggregated_data: AggregatedLayerData, 
                                output_path: str, compression: bool = False) -> Dict[str, str]:
        """Export each layer as separate JSON file."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export metadata file
        metadata_file = output_dir / f"metadata_{aggregated_data.metadata.year}.json"
        with open(metadata_file, 'w') as f:
            json.dump(aggregated_data.metadata.to_dict(), f, indent=2, default=str)
        
        exported_files['metadata'] = str(metadata_file)
        
        # Export each layer individually
        for layer_id, layer_data in aggregated_data.layer_data.items():
            filename = f"layer_{layer_id:02d}_{aggregated_data.metadata.year}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(layer_data.to_dict(), f, indent=2, default=str)
            
            # Apply compression if requested
            if compression:
                compressed_path = f"{filepath}.gz"
                with open(filepath, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                filepath.unlink()
                filepath = Path(compressed_path)
            
            exported_files[f'layer_{layer_id}'] = str(filepath)
        
        # Export summary statistics
        summary_file = output_dir / f"summary_statistics_{aggregated_data.metadata.year}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'summary_statistics': aggregated_data.summary_statistics,
                'cross_layer_analysis': aggregated_data.cross_layer_analysis,
                'validation_results': aggregated_data.validation_results
            }, f, indent=2, default=str)
        
        exported_files['summary'] = str(summary_file)
        
        return {
            'format': 'individual_layers',
            'output_directory': str(output_dir),
            'files': exported_files,
            'total_files': len(exported_files),
            'compressed': compression
        }
    
    def _export_summary_only(self, aggregated_data: AggregatedLayerData, 
                           output_path: str, compression: bool = False) -> Dict[str, str]:
        """Export only summary data without daily scores."""
        if Path(output_path).is_dir():
            filename = f"layer_summary_{aggregated_data.metadata.year}.json"
            filepath = Path(output_path) / filename
        else:
            filepath = Path(output_path)
        
        # Create summary-only data structure
        summary_data = {
            'metadata': aggregated_data.metadata.to_dict(),
            'layer_info': {
                str(layer_id): layer_data.layer_info.to_dict()
                for layer_id, layer_data in aggregated_data.layer_data.items()
            },
            'summary_statistics': aggregated_data.summary_statistics,
            'cross_layer_analysis': aggregated_data.cross_layer_analysis,
            'validation_results': aggregated_data.validation_results
        }
        
        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        # Apply compression if requested
        if compression:
            compressed_path = f"{filepath}.gz"
            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            filepath.unlink()
            filepath = Path(compressed_path)
        
        return {
            'format': 'summary_only',
            'filepath': str(filepath),
            'size_bytes': filepath.stat().st_size,
            'compressed': compression
        }
    
    def _export_csv(self, aggregated_data: AggregatedLayerData, 
                   output_path: str, compression: bool = False) -> Dict[str, str]:
        """Export daily scores as CSV files."""
        import csv
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export combined CSV with all layers
        combined_file = output_dir / f"combined_daily_scores_{aggregated_data.metadata.year}.csv"
        
        # Prepare data for combined CSV
        if aggregated_data.layer_data:
            # Get all dates from first layer
            first_layer = next(iter(aggregated_data.layer_data.values()))
            dates = [score.date for score in first_layer.annual_data]
            
            with open(combined_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                header = ['date', 'day_of_year'] + [f'layer_{lid}_score' for lid in sorted(aggregated_data.layer_data.keys())] + [f'layer_{lid}_confidence' for lid in sorted(aggregated_data.layer_data.keys())]
                writer.writerow(header)
                
                # Write data rows
                for i, date in enumerate(dates):
                    row = [date, i + 1]
                    
                    # Add scores
                    for layer_id in sorted(aggregated_data.layer_data.keys()):
                        layer_data = aggregated_data.layer_data[layer_id]
                        if i < len(layer_data.annual_data):
                            row.append(layer_data.annual_data[i].score)
                        else:
                            row.append('')
                    
                    # Add confidences
                    for layer_id in sorted(aggregated_data.layer_data.keys()):
                        layer_data = aggregated_data.layer_data[layer_id]
                        if i < len(layer_data.annual_data):
                            row.append(layer_data.annual_data[i].confidence)
                        else:
                            row.append('')
                    
                    writer.writerow(row)
            
            exported_files['combined'] = str(combined_file)
        
        # Export individual layer CSVs
        for layer_id, layer_data in aggregated_data.layer_data.items():
            filename = f"layer_{layer_id:02d}_daily_scores_{aggregated_data.metadata.year}.csv"
            filepath = output_dir / filename
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['date', 'day_of_year', 'score', 'confidence'])
                
                # Write data
                for score in layer_data.annual_data:
                    writer.writerow([score.date, score.day_of_year, score.score, score.confidence])
            
            exported_files[f'layer_{layer_id}'] = str(filepath)
        
        # Apply compression if requested
        if compression:
            compressed_files = {}
            for key, filepath in exported_files.items():
                compressed_path = f"{filepath}.gz"
                with open(filepath, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                Path(filepath).unlink()
                compressed_files[key] = compressed_path
            
            exported_files = compressed_files
        
        return {
            'format': 'csv',
            'output_directory': str(output_dir),
            'files': exported_files,
            'total_files': len(exported_files),
            'compressed': compression
        }
    
    def verify_exported_data(self, export_result: Dict[str, str], 
                           original_data: AggregatedLayerData) -> Dict[str, Any]:
        """
        Verify integrity of exported data.
        
        Args:
            export_result: Result from export operation
            original_data: Original aggregated data for comparison
            
        Returns:
            Verification results
        """
        verification_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_checks': {}
        }
        
        export_format = export_result.get('format')
        
        if export_format == 'json':
            # Verify JSON file
            filepath = export_result.get('filepath')
            if filepath and Path(filepath).exists():
                try:
                    with open(filepath, 'r') as f:
                        loaded_data = json.load(f)
                    
                    # Basic structure verification
                    required_keys = ['metadata', 'layer_data', 'summary_statistics']
                    for key in required_keys:
                        if key not in loaded_data:
                            verification_result['errors'].append(f"Missing key in exported JSON: {key}")
                            verification_result['is_valid'] = False
                    
                    verification_result['file_checks'][filepath] = {
                        'exists': True,
                        'readable': True,
                        'size_bytes': Path(filepath).stat().st_size
                    }
                    
                except Exception as e:
                    verification_result['errors'].append(f"Failed to read exported JSON: {e}")
                    verification_result['is_valid'] = False
            else:
                verification_result['errors'].append(f"Exported file not found: {filepath}")
                verification_result['is_valid'] = False
        
        elif export_format == 'individual_layers':
            # Verify individual layer files
            files = export_result.get('files', {})
            for file_key, filepath in files.items():
                if Path(filepath).exists():
                    verification_result['file_checks'][filepath] = {
                        'exists': True,
                        'size_bytes': Path(filepath).stat().st_size
                    }
                else:
                    verification_result['errors'].append(f"Missing exported file: {filepath}")
                    verification_result['is_valid'] = False
        
        elif export_format == 'csv':
            # Verify CSV files
            files = export_result.get('files', {})
            for file_key, filepath in files.items():
                if Path(filepath).exists():
                    try:
                        import csv
                        with open(filepath, 'r') as f:
                            reader = csv.reader(f)
                            header = next(reader)
                            row_count = sum(1 for _ in reader)
                        
                        verification_result['file_checks'][filepath] = {
                            'exists': True,
                            'readable': True,
                            'header_columns': len(header),
                            'data_rows': row_count,
                            'size_bytes': Path(filepath).stat().st_size
                        }
                    except Exception as e:
                        verification_result['errors'].append(f"Failed to read CSV file {filepath}: {e}")
                        verification_result['is_valid'] = False
                else:
                    verification_result['errors'].append(f"Missing CSV file: {filepath}")
                    verification_result['is_valid'] = False
        
        return verification_result
    
    def optimize_data_for_export(self, aggregated_data: AggregatedLayerData, 
                               optimization_level: str = 'standard') -> AggregatedLayerData:
        """
        Optimize aggregated data for export by reducing size and improving performance.
        
        Args:
            aggregated_data: Original aggregated data
            optimization_level: 'minimal', 'standard', or 'aggressive'
            
        Returns:
            Optimized aggregated data
        """
        if optimization_level == 'minimal':
            # Just round scores to reduce precision
            return self._round_scores(aggregated_data, decimal_places=4)
        
        elif optimization_level == 'standard':
            # Round scores and remove empty contributing factors
            optimized = self._round_scores(aggregated_data, decimal_places=3)
            return self._clean_contributing_factors(optimized)
        
        elif optimization_level == 'aggressive':
            # Round scores, clean factors, and remove detailed metadata
            optimized = self._round_scores(aggregated_data, decimal_places=2)
            optimized = self._clean_contributing_factors(optimized)
            return self._reduce_metadata(optimized)
        
        else:
            raise ValueError(f"Unknown optimization level: {optimization_level}")
    
    def _round_scores(self, aggregated_data: AggregatedLayerData, decimal_places: int) -> AggregatedLayerData:
        """Round all scores to specified decimal places."""
        # Create a deep copy to avoid modifying original data
        import copy
        optimized_data = copy.deepcopy(aggregated_data)
        
        for layer_data in optimized_data.layer_data.values():
            for daily_score in layer_data.annual_data:
                daily_score.score = round(daily_score.score, decimal_places)
                daily_score.confidence = round(daily_score.confidence, decimal_places)
        
        return optimized_data
    
    def _clean_contributing_factors(self, aggregated_data: AggregatedLayerData) -> AggregatedLayerData:
        """Remove empty or minimal contributing factors."""
        for layer_data in aggregated_data.layer_data.values():
            for daily_score in layer_data.annual_data:
                # Remove factors with zero values or empty strings
                if daily_score.contributing_factors:
                    daily_score.contributing_factors = {
                        k: v for k, v in daily_score.contributing_factors.items()
                        if v and v != 0.0 and v != ''
                    }
        
        return aggregated_data
    
    def _reduce_metadata(self, aggregated_data: AggregatedLayerData) -> AggregatedLayerData:
        """Reduce metadata to essential information only."""
        # Keep only essential metadata fields
        essential_fields = [
            'aggregation_timestamp', 'total_layers', 'successful_layers',
            'year', 'kundali_reference', 'schema_version'
        ]
        
        # Filter metadata
        filtered_metadata = {
            k: v for k, v in aggregated_data.metadata.to_dict().items()
            if k in essential_fields
        }
        
        # Update metadata object
        aggregated_data.metadata = AggregationMetadata(**filtered_metadata)
        
        # Reduce layer metadata
        for layer_data in aggregated_data.layer_data.values():
            essential_layer_metadata = [
                'generation_timestamp', 'year', 'layer_id',
                'accuracy_rating', 'schema_version'
            ]
            
            layer_data.calculation_metadata = {
                k: v for k, v in layer_data.calculation_metadata.items()
                if k in essential_layer_metadata
            }
        
        return aggregated_data