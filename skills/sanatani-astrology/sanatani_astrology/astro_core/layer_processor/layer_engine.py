"""
Layer processing engine for orchestrating all 10 calculation layers.

This module provides the main engine for coordinating layer calculations,
managing dependencies, and handling parallel processing with comprehensive
error handling and progress tracking.
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

from ..core.data_models import KundaliData, LayerData
from .base_layer import LayerProcessor, LayerProcessingError
from .layers import LAYER_REGISTRY, get_available_layers
from .data_aggregator import LayerDataAggregator, AggregatedLayerData
from .rule_scorer import LayerRuleScorer


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LayerProgress:
    """Progress tracking for individual layers."""
    layer_id: int
    status: ProcessingStatus = ProcessingStatus.NOT_STARTED
    progress_percent: float = 0.0
    current_step: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed processing time."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class ProcessingMetrics:
    """Overall processing metrics."""
    total_layers: int = 0
    completed_layers: int = 0
    failed_layers: int = 0
    cancelled_layers: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    parallel_workers: int = 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_layers == 0:
            return 0.0
        return (self.completed_layers / self.total_layers) * 100
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get total elapsed processing time."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time


class LayerProcessingEngine:
    """
    Main engine for coordinating all layer calculations.
    
    Handles parallel processing, error isolation, progress tracking,
    and result aggregation for all 10 layers with comprehensive
    monitoring and dependency management.
    """
    
    def __init__(self, kundali_data: KundaliData, max_workers: int = 4, rule_path: Optional[str | Path] = None):
        """
        Initialize the layer processing engine.
        
        Args:
            kundali_data: Complete kundali data for calculations
            max_workers: Maximum number of parallel workers
        """
        self.kundali_data = kundali_data
        self.max_workers = max_workers
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Accuracy and timeout overrides via rules
        self._accuracy_overrides: Dict[int, float] = {}
        self._layer_timeouts: Dict[int, int] = {}

        # Use the global layer registry (possibly filtered by rules)
        self._layer_registry: Dict[int, type] = LAYER_REGISTRY.copy()
        self._layer_instances: Dict[int, LayerProcessor] = {}
        
        # Enhanced progress tracking
        self._progress_callback: Optional[Callable[[LayerProgress], None]] = None
        self._status_callback: Optional[Callable[[ProcessingMetrics], None]] = None
        self._layer_progress: Dict[int, LayerProgress] = {}
        self._processing_metrics = ProcessingMetrics()
        
        # Thread safety
        self._progress_lock = threading.Lock()
        self._cancellation_event = threading.Event()
        
        # Dependency management (though layers should be independent)
        self._layer_dependencies: Dict[int, List[int]] = {}
        
        # Rule-driven per-layer scoring specs (must exist before rule load)
        self._layer_scoring_specs: Dict[int, Dict[str, Any]] = {}

        # Load and apply rules (if provided)
        self._load_and_apply_rules(rule_path)

        # Initialize progress tracking for all available layers (after rules)
        self._initialize_progress_tracking()
        
        # Initialize data aggregator
        self._data_aggregator = LayerDataAggregator(kundali_data)

    def _load_and_apply_rules(self, rule_path: Optional[str | Path]) -> None:
        """Load YAML rules to drive engine behavior (layers, accuracy, dependencies, timeouts)."""
        # Default rules location for layer engine
        default_path = Path("config/layers/default.yaml")
        path = Path(rule_path) if rule_path else default_path

        if not path.exists():
            # If no rule file present, keep defaults
            self.logger.info(f"Layer rules not found at {path}, using built-in defaults")
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                content = f.read().replace('\t', '  ')
            spec = yaml.safe_load(content) or {}
        except Exception as e:
            self.logger.error(f"Failed to parse layer rules file {path}: {e}")
            return

        # Settings
        settings = spec.get("settings", {})
        if isinstance(settings.get("max_workers"), int):
            self.max_workers = int(settings["max_workers"]) or self.max_workers
        default_timeout = int(settings.get("default_timeout_secs", 300))

        # Layers: filter, set accuracy, per-layer timeouts, dependencies
        layers_spec = spec.get("layers", []) or []
        enabled_layers: Dict[int, type] = {}
        accuracy_overrides: Dict[int, float] = {}
        timeouts_map: Dict[int, int] = {}
        dependencies: Dict[int, List[int]] = {}

        # Build enabled set; fall back to all if none specified
        specified_ids = set()
        for item in layers_spec:
            try:
                lid = int(item.get("id"))
            except Exception:
                continue
            specified_ids.add(lid)
            if not item.get("enabled", True):
                continue
            if lid in LAYER_REGISTRY:
                enabled_layers[lid] = LAYER_REGISTRY[lid]
            if "accuracy" in item:
                try:
                    accuracy_overrides[lid] = float(item["accuracy"])
                except Exception:
                    pass
            # Per-layer timeout
            if "timeout_secs" in item:
                try:
                    timeouts_map[lid] = int(item["timeout_secs"]) or default_timeout
                except Exception:
                    timeouts_map[lid] = default_timeout
            # Dependencies
            deps = item.get("depends_on") or item.get("dependencies") or []
            if isinstance(deps, list):
                try:
                    dependencies[lid] = [int(d) for d in deps]
                except Exception:
                    dependencies[lid] = []

            # Capture optional scoring spec
            if 'scoring' in item and isinstance(item['scoring'], dict):
                self._layer_scoring_specs[lid] = item['scoring']

        # If layers section present and at least one enabled, replace registry
        if layers_spec:
            # If nothing enabled explicitly, keep existing registry; else filter
            if enabled_layers:
                self._layer_registry = enabled_layers

        # Apply overrides and dependencies
        self._accuracy_overrides = accuracy_overrides
        self._layer_timeouts = timeouts_map
        if dependencies:
            self.set_layer_dependencies(dependencies)
        # Remember default timeout for fallback
        self._default_layer_timeout = default_timeout

    def _initialize_progress_tracking(self) -> None:
        """Initialize progress tracking for all available layers."""
        for layer_id in self._layer_registry.keys():
            self._layer_progress[layer_id] = LayerProgress(layer_id=layer_id)
    
    def register_layer_processor(self, layer_id: int, processor_class: type) -> None:
        """
        Register a layer processor class.
        
        Args:
            layer_id: Layer identifier (1-10)
            processor_class: LayerProcessor subclass
        """
        if not issubclass(processor_class, LayerProcessor):
            raise ValueError(f"Processor class must inherit from LayerProcessor")
        
        if not (1 <= layer_id <= 10):
            raise ValueError(f"Layer ID must be between 1 and 10")
        
        self._layer_registry[layer_id] = processor_class
        self._layer_progress[layer_id] = LayerProgress(layer_id=layer_id)
        self.logger.info(f"Registered layer processor {layer_id}: {processor_class.__name__}")
    
    def set_progress_callback(self, callback: Callable[[LayerProgress], None]) -> None:
        """
        Set callback function for detailed progress updates.
        
        Args:
            callback: Function that receives LayerProgress object
        """
        self._progress_callback = callback
    
    def set_status_callback(self, callback: Callable[[ProcessingMetrics], None]) -> None:
        """
        Set callback function for overall processing status updates.
        
        Args:
            callback: Function that receives ProcessingMetrics object
        """
        self._status_callback = callback
    
    def set_layer_dependencies(self, dependencies: Dict[int, List[int]]) -> None:
        """
        Set layer dependencies (though layers should be independent).
        
        Args:
            dependencies: Dict mapping layer_id to list of prerequisite layer_ids
        """
        self._layer_dependencies = dependencies.copy()
        self.logger.info(f"Set layer dependencies: {dependencies}")
    
    def cancel_processing(self) -> None:
        """Cancel ongoing processing operations."""
        self._cancellation_event.set()
        self.logger.info("Processing cancellation requested")
    
    def get_available_layers(self) -> List[int]:
        """Get list of available layer IDs."""
        return sorted(self._layer_registry.keys())
    
    def get_layer_info(self, layer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific layer.
        
        Args:
            layer_id: Layer identifier
            
        Returns:
            Layer information dictionary or None if not found
        """
        if layer_id not in self._layer_registry:
            return None
        
        processor_class = self._layer_registry[layer_id]
        
        # Create temporary instance to get info
        try:
            temp_instance = processor_class(layer_id, self._get_default_accuracy(layer_id), self.kundali_data)
            layer_info = temp_instance.get_layer_info()
            return layer_info.to_dict()
        except Exception as e:
            self.logger.error(f"Failed to get info for layer {layer_id}: {e}")
            return None
    
    def _get_default_accuracy(self, layer_id: int) -> float:
        """Get default accuracy rating for layer ID (Enhanced)."""
        # Rule override first
        if layer_id in self._accuracy_overrides:
            return self._accuracy_overrides[layer_id]

        accuracy_map = {
            1: 1.0,   # 100% - Astronomical Facts (unchanged)
            2: 0.92,  # 92% - Enhanced Planetary Positions with Divisional Charts
            3: 0.8,   # 80% - Vedic Cycles (unchanged)
            4: 0.75,  # 75% - Enhanced Dasha Periods with Comprehensive Analysis
            5: 0.65,  # 65% - Enhanced Major Transits with Ashtakavarga
            6: 0.55,  # 55% - Enhanced Secondary Transits with Traditional Rules
            7: 0.50,  # 50% - Enhanced Yoga Combinations with Advanced Detection
            8: 0.3,   # 30% - Divisional Charts (unchanged)
            9: 0.2,   # 20% - Micro Periods (unchanged)
            10: 0.1   # 10% - Speculative Factors (unchanged)
        }
        return accuracy_map.get(layer_id, 0.5)

    def _get_timeout_for_layer(self, layer_id: int) -> int:
        """Get processing timeout (seconds) for a layer, honoring rule overrides."""
        if hasattr(self, "_layer_timeouts") and layer_id in self._layer_timeouts:
            return self._layer_timeouts[layer_id]
        return getattr(self, "_default_layer_timeout", 300)
    
    def process_layer(self, layer_id: int, year: int) -> LayerData:
        """
        Process a single layer for the specified year.
        
        Args:
            layer_id: Layer identifier
            year: Year for calculation
            
        Returns:
            Layer data with annual calculations
            
        Raises:
            LayerProcessingError: If layer processing fails
        """
        return self.process_single_layer(layer_id, year)
    
    def process_single_layer(self, layer_id: int, year: int) -> LayerData:
        """
        Process a single layer for the specified year with comprehensive tracking.
        
        Args:
            layer_id: Layer identifier
            year: Year for calculation
            
        Returns:
            Layer data with annual calculations
            
        Raises:
            LayerProcessingError: If layer processing fails
        """
        if layer_id not in self._layer_registry:
            raise LayerProcessingError(layer_id, f"Layer {layer_id} not registered")
        
        # Check for cancellation
        if self._cancellation_event.is_set():
            self._update_layer_progress(layer_id, ProcessingStatus.CANCELLED, "Processing cancelled")
            raise LayerProcessingError(layer_id, "Processing was cancelled")
        
        # Check dependencies
        if not self._check_layer_dependencies(layer_id):
            raise LayerProcessingError(layer_id, "Layer dependencies not satisfied")
        
        self._update_layer_progress(layer_id, ProcessingStatus.INITIALIZING, "Initializing layer processor")
        
        try:
            # Create layer instance
            processor_class = self._layer_registry[layer_id]
            accuracy = self._get_default_accuracy(layer_id)
            processor = processor_class(layer_id, accuracy, self.kundali_data)
            
            self._update_layer_progress(layer_id, ProcessingStatus.INITIALIZING, "Validating kundali data", 10.0)
            
            # Validate kundali data for this layer
            if not processor.validate_kundali_data():
                raise LayerProcessingError(layer_id, "Kundali data validation failed")
            
            self._update_layer_progress(layer_id, ProcessingStatus.PROCESSING, "Processing annual data", 20.0)
            
            # Generate annual data: rule-driven if scoring spec provided
            # Strict rule-driven processing: require a scoring spec
            if layer_id not in self._layer_scoring_specs:
                raise LayerProcessingError(layer_id, "Missing scoring rules for layer in YAML")
            self._update_layer_progress(layer_id, ProcessingStatus.PROCESSING, "Processing (rule-driven)", 25.0)
            layer_data = self._process_layer_rule_driven(processor, year, layer_id)
            
            self._update_layer_progress(layer_id, ProcessingStatus.COMPLETED, "Processing completed", 100.0)
            self.logger.info(f"Successfully processed layer {layer_id} for year {year}")
            
            return layer_data
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            self._update_layer_progress(layer_id, ProcessingStatus.FAILED, error_msg, error_message=str(e))
            self.logger.error(f"Failed to process layer {layer_id}: {e}")
            raise LayerProcessingError(layer_id, error_msg, e)

    def _process_layer_rule_driven(self, processor: LayerProcessor, year: int, layer_id: int) -> LayerData:
        """Generate layer data using rule-driven scoring based on YAML spec."""
        scoring_spec = self._layer_scoring_specs.get(layer_id)
        if not scoring_spec:
            raise LayerProcessingError(layer_id, "Missing scoring rules for layer in YAML")
        scorer = LayerRuleScorer(scoring_spec)

        from ..core.data_models import DailyScore, LayerData
        start_date = datetime(year, 1, 1)
        days_in_year = 366 if processor._is_leap_year(year) else 365
        daily_scores: List[DailyScore] = []
        failed_days = 0

        for i in range(days_in_year):
            current_date = start_date.replace() + timedelta(days=i)
            try:
                # Build feature context using layer-provided contributing factors
                features = {}
                try:
                    features = processor._get_contributing_factors(current_date) or {}
                except Exception:
                    features = {}
                # Build evaluation environment
                try:
                    kundali_dict = processor.kundali.to_dict() if hasattr(processor.kundali, 'to_dict') else {}
                except Exception:
                    kundali_dict = {}
                env = {
                    'kundali': kundali_dict,
                    'date': current_date,
                    'day_of_year': i + 1,
                }
                score = scorer.score(features, env)
                score = max(0.0, min(1.0, float(score)))
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=i + 1,
                    score=round(score, 4),
                    confidence=processor.get_confidence_score(current_date),
                    contributing_factors=features
                ))
            except Exception as e:
                failed_days += 1
                fallback = processor._get_fallback_score(current_date)
                daily_scores.append(DailyScore(
                    date=current_date.isoformat(),
                    day_of_year=i + 1,
                    score=fallback,
                    confidence=0.0,
                    contributing_factors={'error': str(e), 'fallback_used': True}
                ))

        # Build LayerData with same structure as default path
        summary = processor._calculate_summary_statistics(daily_scores)
        metadata = processor._generate_metadata(year, 0.0)
        info = processor.get_layer_info()

        return LayerData(
            layer_info=info,
            annual_data=daily_scores,
            summary_statistics=summary,
            calculation_metadata=metadata
        )
    
    def _process_layer_with_progress(self, processor: LayerProcessor, year: int, layer_id: int) -> LayerData:
        """Process layer with detailed progress tracking."""
        # This is a simplified progress simulation - in a real implementation,
        # you might modify the LayerProcessor to provide progress callbacks
        
        progress_steps = [
            (30.0, "Calculating daily scores"),
            (60.0, "Processing statistics"),
            (80.0, "Generating metadata"),
            (95.0, "Finalizing layer data")
        ]
        
        for progress, step in progress_steps:
            if self._cancellation_event.is_set():
                raise LayerProcessingError(layer_id, "Processing was cancelled")
            
            self._update_layer_progress(layer_id, ProcessingStatus.PROCESSING, step, progress)
            time.sleep(0.1)  # Small delay to simulate processing
        
        # Actually generate the data
        layer_data = processor.generate_annual_data(year)
        
        return layer_data
    
    def _check_layer_dependencies(self, layer_id: int) -> bool:
        """Check if layer dependencies are satisfied."""
        if layer_id not in self._layer_dependencies:
            return True  # No dependencies
        
        required_layers = self._layer_dependencies[layer_id]
        for required_layer in required_layers:
            if required_layer not in self._layer_progress:
                return False
            
            progress = self._layer_progress[required_layer]
            if progress.status != ProcessingStatus.COMPLETED:
                self.logger.warning(f"Layer {layer_id} dependency {required_layer} not completed")
                return False
        
        return True
    
    def process_multiple_layers(self, layer_ids: List[int], year: int, 
                              parallel: bool = True) -> Dict[int, LayerData]:
        """
        Process multiple layers for the specified year with comprehensive tracking.
        
        Args:
            layer_ids: List of layer identifiers to process
            year: Year for calculation
            parallel: Whether to process layers in parallel
            
        Returns:
            Dictionary mapping layer_id to LayerData
        """
        self.logger.info(f"Processing {len(layer_ids)} layers for year {year} (parallel={parallel})")
        
        # Initialize processing metrics
        self._processing_metrics = ProcessingMetrics(
            total_layers=len(layer_ids),
            start_time=time.time(),
            parallel_workers=self.max_workers if parallel else 1
        )
        
        # Reset cancellation event
        self._cancellation_event.clear()
        
        # Validate layer IDs
        invalid_layers = [lid for lid in layer_ids if lid not in self._layer_registry]
        if invalid_layers:
            self.logger.error(f"Invalid layer IDs: {invalid_layers}")
            raise ValueError(f"Invalid layer IDs: {invalid_layers}")
        
        results = {}
        failed_layers = []
        
        try:
            if parallel and len(layer_ids) > 1:
                results, failed_layers = self._process_parallel_enhanced(layer_ids, year)
            else:
                results, failed_layers = self._process_sequential_enhanced(layer_ids, year)
        
        finally:
            # Finalize metrics
            self._processing_metrics.end_time = time.time()
            self._processing_metrics.completed_layers = len(results)
            self._processing_metrics.failed_layers = len(failed_layers)
            self._processing_metrics.cancelled_layers = len([
                lid for lid in layer_ids 
                if self._layer_progress.get(lid, LayerProgress(lid)).status == ProcessingStatus.CANCELLED
            ])
            
            # Final status callback
            if self._status_callback:
                self._status_callback(self._processing_metrics)
        
        # Log summary
        successful_layers = len(results)
        self.logger.info(f"Processing complete: {successful_layers} successful, {len(failed_layers)} failed")
        
        if failed_layers:
            self.logger.warning(f"Failed layers: {failed_layers}")
        
        return results
    
    def _process_parallel_enhanced(self, layer_ids: List[int], year: int) -> Tuple[Dict[int, LayerData], List[int]]:
        """Process layers in parallel with enhanced monitoring and error isolation."""
        results = {}
        failed_layers = []
        
        # Sort layers by dependencies if any exist
        sorted_layer_ids = self._sort_layers_by_dependencies(layer_ids)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks in dependency order
            future_to_layer: Dict[Future, int] = {}
            
            for layer_id in sorted_layer_ids:
                if self._cancellation_event.is_set():
                    break
                
                # Wait for dependencies if any
                if not self._wait_for_dependencies(layer_id, future_to_layer, results):
                    failed_layers.append(layer_id)
                    continue
                
                future = executor.submit(self.process_single_layer, layer_id, year)
                future_to_layer[future] = layer_id
            
            # Collect results as they complete
            for future in as_completed(future_to_layer):
                layer_id = future_to_layer[future]
                
                try:
                    layer_data = future.result(timeout=self._get_timeout_for_layer(layer_id))
                    results[layer_id] = layer_data
                    self.logger.debug(f"Layer {layer_id} completed successfully")
                    
                except Exception as e:
                    failed_layers.append(layer_id)
                    self.logger.error(f"Layer {layer_id} failed in parallel processing: {e}")
                    
                    # Update metrics
                    with self._progress_lock:
                        if self._status_callback:
                            self._status_callback(self._processing_metrics)
        
        return results, failed_layers
    
    def _process_sequential_enhanced(self, layer_ids: List[int], year: int) -> Tuple[Dict[int, LayerData], List[int]]:
        """Process layers sequentially with enhanced error handling."""
        results = {}
        failed_layers = []
        
        # Sort layers by dependencies
        sorted_layer_ids = self._sort_layers_by_dependencies(layer_ids)
        
        for i, layer_id in enumerate(sorted_layer_ids):
            if self._cancellation_event.is_set():
                # Mark remaining layers as cancelled
                for remaining_id in sorted_layer_ids[i:]:
                    self._update_layer_progress(remaining_id, ProcessingStatus.CANCELLED, "Processing cancelled")
                break
            
            try:
                layer_data = self.process_single_layer(layer_id, year)
                results[layer_id] = layer_data
                
                # Update overall progress
                progress_percent = ((i + 1) / len(sorted_layer_ids)) * 100
                self.logger.debug(f"Overall progress: {progress_percent:.1f}% ({i + 1}/{len(sorted_layer_ids)})")
                
            except Exception as e:
                failed_layers.append(layer_id)
                self.logger.error(f"Layer {layer_id} failed in sequential processing: {e}")
                
                # Continue with other layers (error isolation)
                continue
        
        return results, failed_layers
    
    def _sort_layers_by_dependencies(self, layer_ids: List[int]) -> List[int]:
        """Sort layers by their dependencies using topological sort."""
        if not self._layer_dependencies:
            return sorted(layer_ids)  # Simple numeric sort if no dependencies
        
        # Simple topological sort implementation
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(layer_id: int):
            if layer_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving layer {layer_id}")
            if layer_id in visited:
                return
            
            temp_visited.add(layer_id)
            
            # Visit dependencies first
            for dep in self._layer_dependencies.get(layer_id, []):
                if dep in layer_ids:  # Only consider dependencies that are being processed
                    visit(dep)
            
            temp_visited.remove(layer_id)
            visited.add(layer_id)
            result.append(layer_id)
        
        for layer_id in layer_ids:
            if layer_id not in visited:
                visit(layer_id)
        
        return result
    
    def _wait_for_dependencies(self, layer_id: int, future_to_layer: Dict[Future, int], 
                             results: Dict[int, LayerData]) -> bool:
        """Wait for layer dependencies to complete."""
        if layer_id not in self._layer_dependencies:
            return True
        
        required_layers = self._layer_dependencies[layer_id]
        
        # Check if all dependencies are already completed
        for dep_id in required_layers:
            if dep_id not in results:
                # Find the future for this dependency and wait for it
                dep_future = None
                for future, fid in future_to_layer.items():
                    if fid == dep_id:
                        dep_future = future
                        break
                
                if dep_future:
                    try:
                        dep_future.result(timeout=self._get_timeout_for_layer(dep_id))
                    except Exception as e:
                        self.logger.error(f"Dependency layer {dep_id} failed: {e}")
                        return False
                else:
                    self.logger.error(f"Dependency layer {dep_id} not found in processing queue")
                    return False
        
        return True
    
    def process_all_layers(self, year: int, parallel: bool = True) -> Dict[int, LayerData]:
        """
        Process all registered layers for the specified year.
        
        Args:
            year: Year for calculation
            parallel: Whether to process layers in parallel
            
        Returns:
            Dictionary mapping layer_id to LayerData
        """
        available_layers = self.get_available_layers()
        
        if not available_layers:
            self.logger.warning("No layers registered for processing")
            return {}
        
        return self.process_multiple_layers(available_layers, year, parallel)
    
    def _update_layer_progress(self, layer_id: int, status: ProcessingStatus, 
                             current_step: str, progress_percent: float = None, 
                             error_message: str = None) -> None:
        """Update detailed progress for a specific layer."""
        with self._progress_lock:
            if layer_id not in self._layer_progress:
                self._layer_progress[layer_id] = LayerProgress(layer_id=layer_id)
            
            progress = self._layer_progress[layer_id]
            progress.status = status
            progress.current_step = current_step
            
            if progress_percent is not None:
                progress.progress_percent = progress_percent
            
            if error_message is not None:
                progress.error_message = error_message
            
            # Set timing
            if status == ProcessingStatus.INITIALIZING and progress.start_time is None:
                progress.start_time = time.time()
            elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
                progress.end_time = time.time()
            
            # Call progress callback
            if self._progress_callback:
                try:
                    self._progress_callback(progress)
                except Exception as e:
                    self.logger.warning(f"Progress callback failed: {e}")
    
    def get_processing_status(self) -> Dict[int, LayerProgress]:
        """Get current detailed processing status for all layers."""
        with self._progress_lock:
            return {lid: LayerProgress(
                layer_id=progress.layer_id,
                status=progress.status,
                progress_percent=progress.progress_percent,
                current_step=progress.current_step,
                start_time=progress.start_time,
                end_time=progress.end_time,
                error_message=progress.error_message
            ) for lid, progress in self._layer_progress.items()}
    
    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get overall processing metrics."""
        return ProcessingMetrics(
            total_layers=self._processing_metrics.total_layers,
            completed_layers=self._processing_metrics.completed_layers,
            failed_layers=self._processing_metrics.failed_layers,
            cancelled_layers=self._processing_metrics.cancelled_layers,
            start_time=self._processing_metrics.start_time,
            end_time=self._processing_metrics.end_time,
            parallel_workers=self._processing_metrics.parallel_workers
        )
    
    def validate_all_layers(self) -> Dict[int, bool]:
        """
        Validate that all registered layers can process the current kundali data.
        
        Returns:
            Dictionary mapping layer_id to validation result
        """
        validation_results = {}
        
        for layer_id, processor_class in self._layer_registry.items():
            try:
                accuracy = self._get_default_accuracy(layer_id)
                processor = processor_class(layer_id, accuracy, self.kundali_data)
                validation_results[layer_id] = processor.validate_kundali_data()
            except Exception as e:
                self.logger.error(f"Validation failed for layer {layer_id}: {e}")
                validation_results[layer_id] = False
        
        return validation_results
    
    def export_layer_data(self, layer_data_dict: Dict[int, LayerData], 
                         output_dir: str = "layer_output") -> Dict[int, str]:
        """
        Export layer data to JSON files.
        
        Args:
            layer_data_dict: Dictionary of layer data to export
            output_dir: Output directory for JSON files
            
        Returns:
            Dictionary mapping layer_id to output filename
        """
        import os
        import json
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {}
        
        for layer_id, layer_data in layer_data_dict.items():
            try:
                filename = f"layer_{layer_id:02d}_data.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w') as f:
                    json.dump(layer_data.to_dict(), f, indent=2, default=str)
                
                exported_files[layer_id] = filepath
                self.logger.info(f"Exported layer {layer_id} data to {filepath}")
                
            except Exception as e:
                self.logger.error(f"Failed to export layer {layer_id}: {e}")
        
        return exported_files
    
    def get_detailed_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for the processing engine.
        
        Returns:
            Dictionary with detailed performance statistics
        """
        processing_status = self.get_processing_status()
        metrics = self.get_processing_metrics()
        
        # Calculate layer-specific metrics
        layer_metrics = {}
        for layer_id, progress in processing_status.items():
            layer_metrics[layer_id] = {
                'status': progress.status.value,
                'progress_percent': progress.progress_percent,
                'elapsed_time': progress.elapsed_time,
                'current_step': progress.current_step,
                'has_error': progress.error_message is not None
            }
        
        return {
            'engine_info': {
                'registered_layers': len(self._layer_registry),
                'available_layers': self.get_available_layers(),
                'max_workers': self.max_workers,
                'kundali_data_size': len(str(self.kundali_data.to_dict())) if self.kundali_data else 0,
                'has_dependencies': bool(self._layer_dependencies)
            },
            'processing_metrics': {
                'total_layers': metrics.total_layers,
                'completed_layers': metrics.completed_layers,
                'failed_layers': metrics.failed_layers,
                'cancelled_layers': metrics.cancelled_layers,
                'success_rate': metrics.success_rate,
                'elapsed_time': metrics.elapsed_time,
                'parallel_workers': metrics.parallel_workers
            },
            'layer_metrics': layer_metrics,
            'system_status': {
                'is_processing': any(p.status == ProcessingStatus.PROCESSING for p in processing_status.values()),
                'cancellation_requested': self._cancellation_event.is_set(),
                'has_failures': any(p.status == ProcessingStatus.FAILED for p in processing_status.values())
            }
        }
    
    def reset_processing_state(self) -> None:
        """Reset all processing state for a fresh start."""
        with self._progress_lock:
            self._layer_progress.clear()
            self._initialize_progress_tracking()
            self._processing_metrics = ProcessingMetrics()
            self._cancellation_event.clear()
        
        self.logger.info("Processing state reset")
    
    def get_layer_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of layer processing capabilities and status."""
        return {
            'available_layers': {
                layer_id: {
                    'class_name': processor_class.__name__,
                    'accuracy': self._get_default_accuracy(layer_id),
                    'info': self.get_layer_info(layer_id)
                }
                for layer_id, processor_class in self._layer_registry.items()
            },
            'dependencies': self._layer_dependencies,
            'current_status': {
                layer_id: {
                    'status': progress.status.value,
                    'progress': progress.progress_percent,
                    'step': progress.current_step
                }
                for layer_id, progress in self._layer_progress.items()
            }
        }
    
    def process_and_aggregate_layers(self, layer_ids: List[int], year: int, 
                                   parallel: bool = True, 
                                   export_config: Optional[Dict[str, Any]] = None) -> AggregatedLayerData:
        """
        Process multiple layers and aggregate results with optional export.
        
        Args:
            layer_ids: List of layer identifiers to process
            year: Year for calculation
            parallel: Whether to process layers in parallel
            export_config: Optional export configuration
                {
                    'output_path': str,
                    'format': str,
                    'compression': bool,
                    'optimization_level': str
                }
            
        Returns:
            Aggregated layer data with comprehensive analysis
        """
        start_time = time.time()
        
        # Process layers
        layer_results = self.process_multiple_layers(layer_ids, year, parallel)
        
        if not layer_results:
            raise LayerProcessingError(0, "No layers were successfully processed")
        
        processing_duration = time.time() - start_time
        
        # Aggregate results
        self.logger.info("Aggregating layer results...")
        aggregated_data = self._data_aggregator.aggregate_layer_data(
            layer_results, year, processing_duration
        )
        
        # Export if requested
        if export_config:
            self.logger.info("Exporting aggregated data...")
            export_result = self.export_aggregated_data(aggregated_data, export_config)
            
            # Add export info to metadata
            aggregated_data.metadata.export_info = export_result
        
        return aggregated_data
    
    def export_aggregated_data(self, aggregated_data: AggregatedLayerData, 
                             export_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Export aggregated data with specified configuration.
        
        Args:
            aggregated_data: Aggregated layer data to export
            export_config: Export configuration dictionary
            
        Returns:
            Export result information
        """
        # Extract export parameters
        output_path = export_config.get('output_path', 'layer_output')
        export_format = export_config.get('format', 'json')
        compression = export_config.get('compression', False)
        optimization_level = export_config.get('optimization_level', 'standard')
        
        # Optimize data if requested
        if optimization_level != 'none':
            self.logger.info(f"Optimizing data with level: {optimization_level}")
            aggregated_data = self._data_aggregator.optimize_data_for_export(
                aggregated_data, optimization_level
            )
        
        # Export data
        export_result = self._data_aggregator.export_aggregated_data(
            aggregated_data, output_path, export_format, compression
        )
        
        # Verify export if critical
        if export_config.get('verify_export', True):
            self.logger.info("Verifying exported data...")
            verification_result = self._data_aggregator.verify_exported_data(
                export_result, aggregated_data
            )
            
            if not verification_result['is_valid']:
                self.logger.error(f"Export verification failed: {verification_result['errors']}")
                raise LayerProcessingError(0, f"Export verification failed: {verification_result['errors']}")
            
            export_result['verification'] = verification_result
        
        return export_result
    
    def validate_layer_data_collection(self, layer_data_dict: Dict[int, LayerData], 
                                     year: int) -> Dict[str, Any]:
        """
        Validate a collection of layer data for integrity and consistency.
        
        Args:
            layer_data_dict: Dictionary of layer data to validate
            year: Expected year for validation
            
        Returns:
            Comprehensive validation results
        """
        return self._data_aggregator.validate_layer_data_collection(layer_data_dict, year)
    
    def generate_processing_report(self, aggregated_data: AggregatedLayerData, 
                                 include_detailed_analysis: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive processing report.
        
        Args:
            aggregated_data: Aggregated layer data
            include_detailed_analysis: Whether to include detailed cross-layer analysis
            
        Returns:
            Comprehensive processing report
        """
        report = {
            'processing_summary': {
                'total_layers_processed': aggregated_data.metadata.total_layers,
                'successful_layers': aggregated_data.metadata.successful_layers,
                'failed_layers': aggregated_data.metadata.failed_layers,
                'success_rate': (aggregated_data.metadata.successful_layers / 
                               aggregated_data.metadata.total_layers * 100) if aggregated_data.metadata.total_layers > 0 else 0,
                'processing_duration': aggregated_data.metadata.processing_duration,
                'year': aggregated_data.metadata.year
            },
            'layer_details': {},
            'data_quality': aggregated_data.summary_statistics.get('data_quality_metrics', {}),
            'validation_results': aggregated_data.validation_results
        }
        
        # Add layer-specific details
        for layer_id, layer_data in aggregated_data.layer_data.items():
            report['layer_details'][layer_id] = {
                'name': layer_data.layer_info.name,
                'accuracy_rating': layer_data.layer_info.accuracy_rating,
                'methodology': layer_data.layer_info.methodology,
                'statistics': layer_data.summary_statistics,
                'processing_metadata': layer_data.calculation_metadata
            }
        
        # Add detailed analysis if requested
        if include_detailed_analysis:
            report['cross_layer_analysis'] = aggregated_data.cross_layer_analysis
            report['performance_metrics'] = self.get_detailed_performance_metrics()
        
        return report
    
    def create_data_export_batch(self, layer_ids: List[int], year: int,
                               export_configs: List[Dict[str, Any]],
                               parallel_processing: bool = True) -> Dict[str, Any]:
        """
        Process layers and create multiple exports in batch.
        
        Args:
            layer_ids: List of layer identifiers to process
            year: Year for calculation
            export_configs: List of export configurations
            parallel_processing: Whether to use parallel processing
            
        Returns:
            Batch processing results with all export information
        """
        batch_start_time = time.time()
        
        # Process and aggregate layers
        aggregated_data = self.process_and_aggregate_layers(
            layer_ids, year, parallel_processing
        )
        
        # Create multiple exports
        export_results = {}
        for i, export_config in enumerate(export_configs):
            export_name = export_config.get('name', f'export_{i+1}')
            
            try:
                self.logger.info(f"Creating export: {export_name}")
                export_result = self.export_aggregated_data(aggregated_data, export_config)
                export_results[export_name] = {
                    'status': 'success',
                    'result': export_result
                }
            except Exception as e:
                self.logger.error(f"Export {export_name} failed: {e}")
                export_results[export_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        batch_duration = time.time() - batch_start_time
        
        return {
            'batch_summary': {
                'total_exports': len(export_configs),
                'successful_exports': len([r for r in export_results.values() if r['status'] == 'success']),
                'failed_exports': len([r for r in export_results.values() if r['status'] == 'failed']),
                'batch_duration': batch_duration,
                'processing_duration': aggregated_data.metadata.processing_duration
            },
            'aggregated_data': aggregated_data,
            'export_results': export_results,
            'processing_report': self.generate_processing_report(aggregated_data)
        }
