"""
Configuration management system for the Kundali Favorability Heatmap System.

This module provides comprehensive configuration management including layer weights,
astrological parameters, user preferences, and profile management with import/export
capabilities.
"""

import json
import os
import copy
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from .interfaces import ConfigurationManagerInterface
from .data_models import ValidationResult


class ConfigurationManager(ConfigurationManagerInterface):
    """
    Comprehensive configuration management system for system-wide settings.
    
    Handles layer weights, astrological parameters, user preferences, and provides
    configuration persistence, validation, and import/export capabilities.
    """
    
    # Default configuration values
    DEFAULT_LAYER_WEIGHTS = {
        1: 0.25,  # Astronomical Facts - highest weight
        2: 0.20,  # Planetary Positions
        3: 0.15,  # Vedic Cycles
        4: 0.12,  # Dasha Periods
        5: 0.10,  # Major Transits
        6: 0.08,  # Secondary Transits
        7: 0.05,  # Yoga Combinations
        8: 0.03,  # Divisional Charts
        9: 0.02,  # Micro-Periods
        10: 0.00  # Speculative - minimal weight
    }
    
    DEFAULT_CALCULATION_PARAMETERS = {
        'ayanamsa': 'TRUE_CITRA',
        'calculation_method': 'SWISS_EPHEMERIS',
        'ephemeris_path': '/usr/share/ephe',
        'precision_level': 'high',
        'fallback_methods': ['PYJHORA', 'SIMPLIFIED'],
        'coordinate_lookup_service': 'geopy',
        'timezone_service': 'timezonefinder'
    }
    
    DEFAULT_VISUALIZATION_SETTINGS = {
        'color_scheme': 'RdYlGn',
        'figure_size': [16, 10],
        'export_format': 'png',
        'dpi': 300,
        'calendar_layout': 'monthly',
        'show_weekends': True,
        'show_month_labels': True,
        'show_legend': True,
        'transparency_level': 0.8
    }
    
    DEFAULT_USER_PREFERENCES = {
        'default_profile': 'default',
        'auto_save': True,
        'backup_configurations': True,
        'max_backup_files': 5,
        'validation_level': 'strict',
        'logging_level': 'INFO'
    }
    
    def __init__(self, config_dir: str = 'config', profile_name: str = 'default'):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files
            profile_name: Name of the configuration profile to use
        """
        self.config_dir = Path(config_dir)
        self.profile_name = profile_name
        self.config_file = self.config_dir / f'{profile_name}_config.json'
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize configuration
        self._config = self._load_configuration()
        
        # Track changes for auto-save
        self._modified = False
        self._last_save = datetime.now()
    
    def get_layer_weights(self) -> Dict[int, float]:
        """Get layer weights for combination calculations."""
        weights = self._config.get('layer_weights', self.DEFAULT_LAYER_WEIGHTS.copy())
        # Ensure keys are integers
        return {int(k): float(v) for k, v in weights.items()}
    
    def set_layer_weights(self, weights: Dict[int, float]) -> None:
        """
        Set layer weights for combination calculations.
        
        Args:
            weights: Dictionary mapping layer IDs to weight values
            
        Raises:
            ValueError: If weights are invalid
        """
        # Validate weights
        validation = self._validate_layer_weights(weights)
        if not validation.is_valid:
            raise ValueError(f"Invalid layer weights: {', '.join(validation.errors)}")
        
        # Convert keys to strings for JSON compatibility
        self._config['layer_weights'] = {str(k): float(v) for k, v in weights.items()}
        self._mark_modified()
    
    def get_calculation_parameters(self) -> Dict[str, Any]:
        """Get calculation parameters (ayanamsa, methods, etc.)."""
        return copy.deepcopy(self._config.get('calculation_parameters', 
                                            self.DEFAULT_CALCULATION_PARAMETERS.copy()))
    
    def set_calculation_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Set calculation parameters.
        
        Args:
            parameters: Dictionary of calculation parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        validation = self._validate_calculation_parameters(parameters)
        if not validation.is_valid:
            raise ValueError(f"Invalid calculation parameters: {', '.join(validation.errors)}")
        
        self._config['calculation_parameters'] = copy.deepcopy(parameters)
        self._mark_modified()
    
    def get_visualization_settings(self) -> Dict[str, Any]:
        """Get visualization settings."""
        return copy.deepcopy(self._config.get('visualization_settings',
                                            self.DEFAULT_VISUALIZATION_SETTINGS.copy()))
    
    def set_visualization_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set visualization settings.
        
        Args:
            settings: Dictionary of visualization settings
            
        Raises:
            ValueError: If settings are invalid
        """
        # Validate settings
        validation = self._validate_visualization_settings(settings)
        if not validation.is_valid:
            raise ValueError(f"Invalid visualization settings: {', '.join(validation.errors)}")
        
        self._config['visualization_settings'] = copy.deepcopy(settings)
        self._mark_modified()
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences."""
        return copy.deepcopy(self._config.get('user_preferences',
                                            self.DEFAULT_USER_PREFERENCES.copy()))
    
    def set_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Set user preferences.
        
        Args:
            preferences: Dictionary of user preferences
        """
        self._config['user_preferences'] = copy.deepcopy(preferences)
        self._mark_modified()
    
    def get_profile_name(self) -> str:
        """Get current profile name."""
        return self.profile_name
    
    def switch_profile(self, profile_name: str) -> None:
        """
        Switch to a different configuration profile.
        
        Args:
            profile_name: Name of the profile to switch to
        """
        # Save current configuration if modified
        if self._modified:
            self.save_configuration()
        
        # Switch to new profile
        self.profile_name = profile_name
        self.config_file = self.config_dir / f'{profile_name}_config.json'
        self._config = self._load_configuration()
        self._modified = False
    
    def create_profile(self, profile_name: str, copy_from: Optional[str] = None) -> None:
        """
        Create a new configuration profile.
        
        Args:
            profile_name: Name of the new profile
            copy_from: Optional profile name to copy settings from
        """
        new_config_file = self.config_dir / f'{profile_name}_config.json'
        
        if new_config_file.exists():
            raise ValueError(f"Profile '{profile_name}' already exists")
        
        if copy_from:
            source_file = self.config_dir / f'{copy_from}_config.json'
            if source_file.exists():
                # Copy from existing profile
                with open(source_file, 'r') as f:
                    config_data = json.load(f)
            else:
                raise ValueError(f"Source profile '{copy_from}' does not exist")
        else:
            # Create with default settings
            config_data = self._get_default_configuration()
        
        # Add profile metadata
        config_data['profile_metadata'] = {
            'name': profile_name,
            'created_at': datetime.now().isoformat(),
            'created_from': copy_from or 'default',
            'version': '1.0'
        }
        
        # Save new profile
        with open(new_config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def list_profiles(self) -> List[str]:
        """List all available configuration profiles."""
        profiles = []
        for config_file in self.config_dir.glob('*_config.json'):
            profile_name = config_file.stem.replace('_config', '')
            profiles.append(profile_name)
        return sorted(profiles)
    
    def delete_profile(self, profile_name: str) -> None:
        """
        Delete a configuration profile.
        
        Args:
            profile_name: Name of the profile to delete
            
        Raises:
            ValueError: If trying to delete the current profile or default profile
        """
        if profile_name == self.profile_name:
            raise ValueError("Cannot delete the currently active profile")
        
        if profile_name == 'default':
            raise ValueError("Cannot delete the default profile")
        
        config_file = self.config_dir / f'{profile_name}_config.json'
        if config_file.exists():
            config_file.unlink()
        else:
            raise ValueError(f"Profile '{profile_name}' does not exist")
    
    def validate_configuration(self) -> ValidationResult:
        """Validate current configuration."""
        result = ValidationResult(is_valid=True)
        
        # Validate layer weights
        layer_weights = self.get_layer_weights()
        weight_validation = self._validate_layer_weights(layer_weights)
        result.errors.extend(weight_validation.errors)
        result.warnings.extend(weight_validation.warnings)
        
        # Validate calculation parameters
        calc_params = self.get_calculation_parameters()
        param_validation = self._validate_calculation_parameters(calc_params)
        result.errors.extend(param_validation.errors)
        result.warnings.extend(param_validation.warnings)
        
        # Validate visualization settings
        viz_settings = self.get_visualization_settings()
        viz_validation = self._validate_visualization_settings(viz_settings)
        result.errors.extend(viz_validation.errors)
        result.warnings.extend(viz_validation.warnings)
        
        # Update overall validity
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def export_configuration(self, filename: str) -> None:
        """
        Export configuration to file.
        
        Args:
            filename: Path to export file
        """
        export_data = {
            'export_metadata': {
                'profile_name': self.profile_name,
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'configuration': copy.deepcopy(self._config)
        }
        
        export_path = Path(filename)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_configuration(self, filename: str) -> None:
        """
        Import configuration from file.
        
        Args:
            filename: Path to import file
            
        Raises:
            FileNotFoundError: If import file doesn't exist
            ValueError: If import data is invalid
        """
        import_path = Path(filename)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {filename}")
        
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        # Validate import data structure
        if 'configuration' not in import_data:
            raise ValueError("Invalid import file: missing 'configuration' section")
        
        imported_config = import_data['configuration']
        
        # Validate imported configuration
        temp_config = self._config
        self._config = imported_config
        validation = self.validate_configuration()
        self._config = temp_config
        
        if not validation.is_valid:
            raise ValueError(f"Invalid configuration in import file: {', '.join(validation.errors)}")
        
        # Create backup before importing
        if self.get_user_preferences().get('backup_configurations', True):
            self._create_backup()
        
        # Import configuration
        self._config = copy.deepcopy(imported_config)
        self._mark_modified()
        self.save_configuration()
    
    def save_configuration(self) -> None:
        """Save current configuration to file."""
        # Add save metadata
        self._config['save_metadata'] = {
            'last_saved': datetime.now().isoformat(),
            'profile_name': self.profile_name,
            'version': '1.0'
        }
        
        # Create backup if enabled
        if (self.config_file.exists() and 
            self.get_user_preferences().get('backup_configurations', True)):
            self._create_backup()
        
        # Save configuration
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
        
        self._modified = False
        self._last_save = datetime.now()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._get_default_configuration()
        self._mark_modified()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                default_config = self._get_default_configuration()
                merged_config = self._merge_configurations(default_config, config)
                return merged_config
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load configuration file {self.config_file}: {e}")
                print("Using default configuration.")
                return self._get_default_configuration()
        else:
            # Create default configuration file
            default_config = self._get_default_configuration()
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            'layer_weights': {str(k): v for k, v in self.DEFAULT_LAYER_WEIGHTS.items()},
            'calculation_parameters': copy.deepcopy(self.DEFAULT_CALCULATION_PARAMETERS),
            'visualization_settings': copy.deepcopy(self.DEFAULT_VISUALIZATION_SETTINGS),
            'user_preferences': copy.deepcopy(self.DEFAULT_USER_PREFERENCES)
        }
    
    def _merge_configurations(self, default: Dict[str, Any], 
                            loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded configuration with defaults."""
        merged = copy.deepcopy(default)
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = copy.deepcopy(value)
        
        return merged
    
    def _validate_layer_weights(self, weights: Dict[int, float]) -> ValidationResult:
        """Validate layer weights."""
        result = ValidationResult(is_valid=True)
        
        # Check if all required layers are present
        required_layers = set(range(1, 11))
        provided_layers = set(weights.keys())
        
        missing_layers = required_layers - provided_layers
        if missing_layers:
            result.add_error(f"Missing weights for layers: {sorted(missing_layers)}")
        
        extra_layers = provided_layers - required_layers
        if extra_layers:
            result.add_warning(f"Unexpected layer weights: {sorted(extra_layers)}")
        
        # Check weight values
        for layer_id, weight in weights.items():
            if not isinstance(weight, (int, float)):
                result.add_error(f"Layer {layer_id} weight must be numeric, got {type(weight)}")
            elif weight < 0:
                result.add_error(f"Layer {layer_id} weight cannot be negative: {weight}")
            elif weight > 1:
                result.add_warning(f"Layer {layer_id} weight is greater than 1: {weight}")
        
        # Check if weights sum to reasonable value
        total_weight = sum(weights.values())
        if total_weight == 0:
            result.add_error("Total weight cannot be zero")
        elif total_weight > 2:
            result.add_warning(f"Total weight is unusually high: {total_weight}")
        
        return result
    
    def _validate_calculation_parameters(self, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate calculation parameters."""
        result = ValidationResult(is_valid=True)
        
        # Valid ayanamsa options
        valid_ayanamsas = [
            'TRUE_CITRA', 'LAHIRI', 'KRISHNAMURTI', 'RAMAN', 'YUKTESHWAR',
            'JN_BHASIN', 'BABYL_KUGLER1', 'BABYL_KUGLER2', 'BABYL_KUGLER3',
            'BABYL_HUBER', 'BABYL_ETPSC', 'ALDEBARAN_15TAU', 'HIPPARCHOS',
            'SASSANIAN', 'GALCENT_0SAG', 'J2000', 'J1900', 'B1950'
        ]
        
        ayanamsa = parameters.get('ayanamsa')
        if ayanamsa and ayanamsa not in valid_ayanamsas:
            result.add_error(f"Invalid ayanamsa: {ayanamsa}")
        
        # Valid calculation methods
        valid_methods = ['SWISS_EPHEMERIS', 'PYJHORA', 'SIMPLIFIED']
        method = parameters.get('calculation_method')
        if method and method not in valid_methods:
            result.add_error(f"Invalid calculation method: {method}")
        
        # Valid precision levels
        valid_precision = ['low', 'medium', 'high', 'ultra']
        precision = parameters.get('precision_level')
        if precision and precision not in valid_precision:
            result.add_error(f"Invalid precision level: {precision}")
        
        # Validate fallback methods
        fallback_methods = parameters.get('fallback_methods', [])
        if not isinstance(fallback_methods, list):
            result.add_error("fallback_methods must be a list")
        else:
            for method in fallback_methods:
                if method not in valid_methods:
                    result.add_error(f"Invalid fallback method: {method}")
        
        return result
    
    def _validate_visualization_settings(self, settings: Dict[str, Any]) -> ValidationResult:
        """Validate visualization settings."""
        result = ValidationResult(is_valid=True)
        
        # Valid color schemes
        valid_color_schemes = [
            'RdYlGn', 'RdYlBu', 'RdGy', 'RdBu', 'PuOr', 'PRGn', 'PiYG',
            'BrBG', 'RdYlGn_r', 'RdYlBu_r', 'RdGy_r', 'RdBu_r', 'PuOr_r',
            'PRGn_r', 'PiYG_r', 'BrBG_r', 'viridis', 'plasma', 'inferno',
            'magma', 'cividis'
        ]
        
        color_scheme = settings.get('color_scheme')
        if color_scheme and color_scheme not in valid_color_schemes:
            result.add_warning(f"Unknown color scheme: {color_scheme}")
        
        # Validate figure size
        figure_size = settings.get('figure_size')
        if figure_size:
            if not isinstance(figure_size, list) or len(figure_size) != 2:
                result.add_error("figure_size must be a list of two numbers [width, height]")
            elif not all(isinstance(x, (int, float)) and x > 0 for x in figure_size):
                result.add_error("figure_size values must be positive numbers")
        
        # Validate DPI
        dpi = settings.get('dpi')
        if dpi and (not isinstance(dpi, int) or dpi < 50 or dpi > 1200):
            result.add_error("dpi must be an integer between 50 and 1200")
        
        # Validate transparency level
        transparency = settings.get('transparency_level')
        if transparency and (not isinstance(transparency, (int, float)) or 
                           transparency < 0 or transparency > 1):
            result.add_error("transparency_level must be a number between 0 and 1")
        
        return result
    
    def _mark_modified(self) -> None:
        """Mark configuration as modified."""
        self._modified = True
        
        # Auto-save if enabled
        if self.get_user_preferences().get('auto_save', True):
            self.save_configuration()
    
    def _create_backup(self) -> None:
        """Create backup of current configuration."""
        if not self.config_file.exists():
            return
        
        backup_dir = self.config_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'{self.profile_name}_config_{timestamp}.json'
        
        # Copy current config to backup
        import shutil
        shutil.copy2(self.config_file, backup_file)
        
        # Clean up old backups
        self._cleanup_old_backups(backup_dir)
    
    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Clean up old backup files."""
        max_backups = self.get_user_preferences().get('max_backup_files', 5)
        
        # Get all backup files for this profile
        pattern = f'{self.profile_name}_config_*.json'
        backup_files = list(backup_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess backups
        for backup_file in backup_files[max_backups:]:
            backup_file.unlink()


class ConfigurationValidator:
    """Utility class for configuration validation."""
    
    @staticmethod
    def validate_layer_weights_sum(weights: Dict[int, float], 
                                 expected_sum: float = 1.0,
                                 tolerance: float = 0.01) -> ValidationResult:
        """
        Validate that layer weights sum to expected value.
        
        Args:
            weights: Layer weights dictionary
            expected_sum: Expected sum of weights
            tolerance: Tolerance for sum validation
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)
        
        total = sum(weights.values())
        if abs(total - expected_sum) > tolerance:
            result.add_warning(
                f"Layer weights sum to {total:.3f}, expected {expected_sum:.3f}"
            )
        
        return result
    
    @staticmethod
    def validate_accuracy_weight_correlation(weights: Dict[int, float]) -> ValidationResult:
        """
        Validate that higher accuracy layers have higher weights.
        
        Args:
            weights: Layer weights dictionary
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)
        
        # Check if weights generally decrease with layer number (lower accuracy)
        for i in range(1, 10):
            if i in weights and (i + 1) in weights:
                if weights[i] < weights[i + 1]:
                    result.add_warning(
                        f"Layer {i} (higher accuracy) has lower weight than Layer {i+1}"
                    )
        
        return result


# Global configuration manager instance
_global_config_manager = None


def get_config_manager(config_dir: str = 'config', profile_name: str = 'default') -> ConfigurationManager:
    """
    Get or create global configuration manager instance.
    
    Args:
        config_dir: Directory for configuration files
        profile_name: Name of the configuration profile to use
        
    Returns:
        ConfigurationManager instance
    """
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigurationManager(config_dir, profile_name)
    
    return _global_config_manager


def reset_config_manager():
    """Reset global configuration manager (mainly for testing)."""
    global _global_config_manager
    _global_config_manager = None