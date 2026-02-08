#!/usr/bin/env python3
"""
Unified Weighting Engine for Layer Combination

This module provides a single, consistent algorithm for combining multiple
astrological layers with proper confidence-based weighting.
"""

import csv
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import logging

from .data_models import LayerData, DailyScore


class WeightingEngine:
    """
    Unified engine for combining multiple layers using confidence-based weighting.
    
    This engine supports two input formats:
    1. LayerData objects (from layer processing)
    2. CSV files with layer scores and confidence values
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def combine_layer_data_objects(self, layer_data: Dict[int, LayerData]) -> Dict[str, float]:
        """
        Combine LayerData objects using confidence-based weighting.
        
        Args:
            layer_data: Dictionary mapping layer_id -> LayerData objects
            
        Returns:
            Dictionary mapping date_string -> combined_score
        """
        if not layer_data:
            self.logger.warning("No layer data provided for combination")
            return {}
        
        # Index all data by date
        indexed_scores = {}
        all_dates = set()
        
        for layer_id, data in layer_data.items():
            by_date = {}
            for daily_score in data.annual_data:
                # Handle both string and datetime objects
                if isinstance(daily_score.date, str):
                    date_str = daily_score.date[:10]  # Take YYYY-MM-DD part
                else:
                    date_str = daily_score.date.strftime('%Y-%m-%d')
                
                by_date[date_str] = {
                    'score': daily_score.score,
                    'confidence': daily_score.confidence
                }
                all_dates.add(date_str)
            
            indexed_scores[layer_id] = by_date
        
        # Calculate weighted combinations for each date
        combined_data = {}
        dates = sorted(all_dates)
        
        for date_str in dates:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for layer_id, date_data in indexed_scores.items():
                if date_str in date_data:
                    score = date_data[date_str]['score']
                    confidence = date_data[date_str]['confidence']
                    
                    if score is not None and confidence is not None and confidence > 0:
                        weighted_sum += score * confidence
                        total_weight += confidence
            
            # Calculate final weighted average
            if total_weight > 0:
                combined_data[date_str] = weighted_sum / total_weight
            else:
                combined_data[date_str] = 0.5  # Default neutral score
                self.logger.warning(f"No valid data for date {date_str}, using default score")
        
        self.logger.info(f"Combined {len(layer_data)} layers for {len(combined_data)} dates")
        return combined_data
    
    def combine_from_csv(self, csv_file_path: Union[str, Path]) -> Dict[str, float]:
        """
        Combine layer data from CSV file using confidence-based weighting.
        
        Expected CSV format:
        date,day_of_year,layer_1_score,layer_1_confidence,layer_2_score,layer_2_confidence,...
        
        Args:
            csv_file_path: Path to CSV file containing layer scores and confidence values
            
        Returns:
            Dictionary mapping date_string -> combined_score
        """
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return {}
        
        combined_data = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
                if not lines:
                    self.logger.warning("CSV file is empty")
                    return {}
                
                header = lines[0].split(',')
                
                # Build column mapping for layer scores and confidence values
                col_map = self._build_column_mapping(header)
                
                if not col_map:
                    self.logger.warning("No valid layer columns found in CSV")
                    return {}
                
                # Process each data row
                for line in lines[1:]:
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    # Extract date (first column)
                    date_str = parts[0][:10]  # Take YYYY-MM-DD part
                    
                    # Calculate weighted average for this date
                    weighted_sum = 0.0
                    total_weight = 0.0
                    
                    for layer_key, (score_idx, conf_idx) in col_map.items():
                        try:
                            score = float(parts[score_idx])
                            confidence = float(parts[conf_idx])
                            
                            if confidence > 0:  # Only include layers with positive confidence
                                weighted_sum += score * confidence
                                total_weight += confidence
                                
                        except (ValueError, IndexError) as e:
                            self.logger.debug(f"Skipping {layer_key} for {date_str}: {e}")
                            continue
                    
                    # Store the weighted average
                    if total_weight > 0:
                        combined_data[date_str] = weighted_sum / total_weight
                    else:
                        combined_data[date_str] = 0.5  # Default neutral score
                        
        except Exception as e:
            self.logger.error(f"Error processing CSV file {csv_path}: {e}")
            return {}
        
        self.logger.info(f"Combined data from CSV for {len(combined_data)} dates")
        return combined_data
    
    def _build_column_mapping(self, header: List[str]) -> Dict[str, Tuple[int, int]]:
        """
        Build mapping from layer names to (score_index, confidence_index).
        
        Args:
            header: List of column names from CSV
            
        Returns:
            Dictionary mapping layer_key -> (score_idx, confidence_idx)
        """
        # Find score columns
        score_cols = []
        conf_cols = []
        
        for idx, col in enumerate(header):
            col_lower = col.lower().strip()
            if col_lower.startswith('layer_') and col_lower.endswith('_score'):
                score_cols.append((col_lower, idx))
            elif col_lower.startswith('layer_') and col_lower.endswith('_confidence'):
                conf_cols.append((col_lower.replace('_confidence', ''), idx))
        
        # Match score columns with confidence columns
        col_map = {}
        for score_col, score_idx in score_cols:
            layer_key = score_col.replace('_score', '')
            
            # Find corresponding confidence column
            conf_idx = None
            for conf_key, conf_index in conf_cols:
                if conf_key == layer_key:
                    conf_idx = conf_index
                    break
            
            if conf_idx is not None:
                col_map[layer_key] = (score_idx, conf_idx)
            else:
                self.logger.warning(f"No confidence column found for {score_col}")
        
        return col_map
    
    def export_combined_csv(self, combined_data: Dict[str, float], 
                           output_path: Union[str, Path], 
                           year: int) -> Path:
        """
        Export combined data to CSV file in the format expected by visualizers.
        
        Args:
            combined_data: Dictionary mapping date_string -> combined_score
            output_path: Output file path
            year: Year for filename generation
            
        Returns:
            Path to the created CSV file
        """
        output_file = Path(output_path)
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'Combined_Score'])
                
                for date_str in sorted(combined_data.keys()):
                    score = combined_data[date_str]
                    writer.writerow([f"{date_str} 12:00:00", "12:00:00", f"{score:.6f}"])
            
            self.logger.info(f"Exported combined data to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to export combined data: {e}")
            raise
    
    def get_statistics(self, combined_data: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate statistics for combined data.
        
        Args:
            combined_data: Dictionary mapping date_string -> combined_score
            
        Returns:
            Dictionary with avg, min, max, days statistics
        """
        if not combined_data:
            return {'avg': 0.5, 'min': 0.0, 'max': 1.0, 'days': 0}
        
        values = list(combined_data.values())
        return {
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'days': len(values)
        }


def create_weighting_engine(logger: Optional[logging.Logger] = None) -> WeightingEngine:
    """Factory function to create a WeightingEngine instance."""
    return WeightingEngine(logger)


# Legacy compatibility - maintain the same interface as the old WeightedCombinationEngine
class WeightedCombinationEngine(WeightingEngine):
    """Legacy compatibility class that extends WeightingEngine."""
    
    def calculate_weighted_combination(self, layer_results: Dict[int, LayerData], day_index: int):
        """Legacy method for single day calculation."""
        # Convert to date-based format for single day
        single_day_data = {}
        for layer_id, layer_data in layer_results.items():
            if day_index < len(layer_data.annual_data):
                daily_score = layer_data.annual_data[day_index]
                date_str = daily_score.date[:10] if isinstance(daily_score.date, str) else daily_score.date.strftime('%Y-%m-%d')
                single_day_data[layer_id] = LayerData(
                    layer_info=layer_data.layer_info,
                    annual_data=[daily_score],
                    calculation_metadata=layer_data.calculation_metadata
                )
        
        combined = self.combine_layer_data_objects(single_day_data)
        date_key = list(combined.keys())[0] if combined else None
        
        # Return a simple object with the expected attributes
        class DayResult:
            def __init__(self, score, confidence):
                self.combined_score = score
                self.confidence_score = confidence
        
        if date_key:
            return DayResult(combined[date_key], 1.0)
        else:
            return DayResult(0.5, 0.0)
    
    def calculate_annual_combination(self, layer_results: Dict[int, LayerData]):
        """Legacy method for annual calculation."""
        combined = self.combine_layer_data_objects(layer_results)
        
        # Return list of results with expected attributes
        class AnnualResult:
            def __init__(self, score):
                self.combined_score = score
        
        results = []
        for date_str in sorted(combined.keys()):
            results.append(AnnualResult(combined[date_str]))
        
        return results
    
    def export_weight_configuration(self, config_file: str):
        """Legacy method - creates a simple config file."""
        import json
        config = {
            "algorithm": "confidence_based_weighting",
            "description": "Uses per-day confidence scores for dynamic weighting"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
