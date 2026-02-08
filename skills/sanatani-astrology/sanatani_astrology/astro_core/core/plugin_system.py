"""
Plugin architecture system for the Kundali Favorability Heatmap System.

This module provides a comprehensive plugin system for extending the layer calculation
capabilities with custom layers, validation, compatibility checking, and dynamic loading.
"""

import os
import sys
import json
import importlib
import importlib.util
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from pathlib import Path
from datetime import datetime
import logging

from .interfaces import LayerProcessorInterface
from .data_models import ValidationResult, LayerInfo, KundaliData


class PluginMetadata:
    """Metadata for a plugin."""
    
    def __init__(self, name: str, version: str, author: str, description: str,
                 layer_id: int, accuracy: float, dependencies: List[str] = None,
                 min_system_version: str = "1.0.0", max_system_version: str = None,
                 configuration_schema: Dict[str, Any] = None):
        """
        Initialize plugin metadata.
        
        Args:
            name: Plugin name
            version: Plugin version
            author: Plugin author
            description: Plugin description
            layer_id: Layer ID for this plugin
            accuracy: Accuracy rating (0.0 to 1.0)
            dependencies: List of required dependencies
            min_system_version: Minimum system version required
            max_system_version: Maximum system version supported
            configuration_schema: JSON schema for plugin configuration
        """
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.layer_id = layer_id
        self.accuracy = accuracy
        self.dependencies = dependencies or []
        self.min_system_version = min_system_version
        self.max_system_version = max_system_version
        self.configuration_schema = configuration_schema or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'layer_id': self.layer_id,
            'accuracy': self.accuracy,
            'dependencies': self.dependencies,
            'min_system_version': self.min_system_version,
            'max_system_version': self.max_system_version,
            'configuration_schema': self.configuration_schema,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            version=data['version'],
            author=data['author'],
            description=data['description'],
            layer_id=data['layer_id'],
            accuracy=data['accuracy'],
            dependencies=data.get('dependencies', []),
            min_system_version=data.get('min_system_version', '1.0.0'),
            max_system_version=data.get('max_system_version'),
            configuration_schema=data.get('configuration_schema', {})
        )


class PluginInterface(ABC):
    """Abstract interface that all plugins must implement."""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def get_layer_processor_class(self) -> Type[LayerProcessorInterface]:
        """Get the layer processor class for this plugin."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate plugin configuration."""
        pass
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize plugin with configuration (optional override)."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup plugin resources (optional override)."""
        pass


class PluginRegistry:
    """Registry for managing loaded plugins."""
    
    def __init__(self):
        """Initialize plugin registry."""
        self.plugins: Dict[str, PluginInterface] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.layer_mappings: Dict[int, str] = {}  # layer_id -> plugin_name
        self.logger = logging.getLogger(__name__)
    
    def register_plugin(self, plugin: PluginInterface) -> None:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Raises:
            ValueError: If plugin is invalid or conflicts with existing plugin
        """
        metadata = plugin.get_metadata()
        
        # Validate plugin
        validation = self._validate_plugin(plugin, metadata)
        if not validation.is_valid:
            raise ValueError(f"Plugin validation failed: {', '.join(validation.errors)}")
        
        # Check for conflicts
        if metadata.name in self.plugins:
            raise ValueError(f"Plugin '{metadata.name}' is already registered")
        
        if metadata.layer_id in self.layer_mappings:
            existing_plugin = self.layer_mappings[metadata.layer_id]
            raise ValueError(f"Layer ID {metadata.layer_id} is already used by plugin '{existing_plugin}'")
        
        # Register plugin
        self.plugins[metadata.name] = plugin
        self.metadata[metadata.name] = metadata
        self.layer_mappings[metadata.layer_id] = metadata.name
        
        self.logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is not registered")
        
        # Cleanup plugin
        try:
            self.plugins[plugin_name].cleanup()
        except Exception as e:
            self.logger.warning(f"Error during plugin cleanup for '{plugin_name}': {e}")
        
        # Remove from registry
        metadata = self.metadata[plugin_name]
        del self.plugins[plugin_name]
        del self.metadata[plugin_name]
        del self.layer_mappings[metadata.layer_id]
        
        self.logger.info(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get plugin by name."""
        return self.plugins.get(plugin_name)
    
    def get_plugin_by_layer_id(self, layer_id: int) -> Optional[PluginInterface]:
        """Get plugin by layer ID."""
        plugin_name = self.layer_mappings.get(layer_id)
        return self.plugins.get(plugin_name) if plugin_name else None
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.plugins.keys())
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name."""
        return self.metadata.get(plugin_name)
    
    def get_all_metadata(self) -> Dict[str, PluginMetadata]:
        """Get all plugin metadata."""
        return self.metadata.copy()
    
    def get_layer_mappings(self) -> Dict[int, str]:
        """Get layer ID to plugin name mappings."""
        return self.layer_mappings.copy()
    
    def _validate_plugin(self, plugin: PluginInterface, metadata: PluginMetadata) -> ValidationResult:
        """Validate plugin implementation."""
        result = ValidationResult(is_valid=True)
        
        # Check if plugin implements required methods
        required_methods = ['get_metadata', 'get_layer_processor_class', 'validate_configuration']
        for method_name in required_methods:
            if not hasattr(plugin, method_name):
                result.add_error(f"Plugin missing required method: {method_name}")
        
        # Validate metadata
        if not metadata.name:
            result.add_error("Plugin name cannot be empty")
        
        if not metadata.version:
            result.add_error("Plugin version cannot be empty")
        
        if not isinstance(metadata.layer_id, int) or metadata.layer_id < 1:
            result.add_error("Plugin layer_id must be a positive integer")
        
        if not isinstance(metadata.accuracy, (int, float)) or not (0.0 <= metadata.accuracy <= 1.0):
            result.add_error("Plugin accuracy must be a number between 0.0 and 1.0")
        
        # Validate layer processor class
        try:
            processor_class = plugin.get_layer_processor_class()
            if not issubclass(processor_class, LayerProcessorInterface):
                result.add_error("Layer processor class must inherit from LayerProcessorInterface")
        except Exception as e:
            result.add_error(f"Error getting layer processor class: {e}")
        
        return result


class PluginLoader:
    """Loader for dynamically loading plugins from files."""
    
    def __init__(self, plugin_registry: PluginRegistry):
        """
        Initialize plugin loader.
        
        Args:
            plugin_registry: Registry to register loaded plugins
        """
        self.registry = plugin_registry
        self.logger = logging.getLogger(__name__)
    
    def load_plugin_from_file(self, plugin_file: str, config: Dict[str, Any] = None) -> str:
        """
        Load plugin from Python file.
        
        Args:
            plugin_file: Path to plugin Python file
            config: Optional configuration for plugin
            
        Returns:
            Plugin name
            
        Raises:
            ValueError: If plugin loading fails
        """
        plugin_path = Path(plugin_file)
        if not plugin_path.exists():
            raise ValueError(f"Plugin file not found: {plugin_file}")
        
        if not plugin_path.suffix == '.py':
            raise ValueError(f"Plugin file must be a Python file: {plugin_file}")
        
        # Load module
        module_name = f"plugin_{plugin_path.stem}_{id(self)}"
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load plugin module from: {plugin_file}")
        
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ValueError(f"Error executing plugin module: {e}")
        
        # Find plugin class
        plugin_class = self._find_plugin_class(module)
        if plugin_class is None:
            raise ValueError(f"No plugin class found in: {plugin_file}")
        
        # Create plugin instance
        try:
            plugin_instance = plugin_class()
            if config:
                plugin_instance.initialize(config)
        except Exception as e:
            raise ValueError(f"Error creating plugin instance: {e}")
        
        # Register plugin
        self.registry.register_plugin(plugin_instance)
        
        plugin_name = plugin_instance.get_metadata().name
        self.logger.info(f"Loaded plugin from file: {plugin_file} -> {plugin_name}")
        
        return plugin_name
    
    def load_plugins_from_directory(self, plugin_dir: str, 
                                  config_map: Dict[str, Dict[str, Any]] = None) -> List[str]:
        """
        Load all plugins from directory.
        
        Args:
            plugin_dir: Directory containing plugin files
            config_map: Optional mapping of plugin names to configurations
            
        Returns:
            List of loaded plugin names
        """
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            raise ValueError(f"Plugin directory not found: {plugin_dir}")
        
        loaded_plugins = []
        config_map = config_map or {}
        
        # Find all Python files
        for plugin_file in plugin_path.glob('*.py'):
            if plugin_file.name.startswith('__'):
                continue  # Skip __init__.py and similar files
            
            try:
                # Try to determine plugin name from file for config lookup
                temp_plugin_name = plugin_file.stem
                plugin_config = config_map.get(temp_plugin_name, {})
                
                plugin_name = self.load_plugin_from_file(str(plugin_file), plugin_config)
                loaded_plugins.append(plugin_name)
                
            except Exception as e:
                self.logger.error(f"Failed to load plugin from {plugin_file}: {e}")
                continue
        
        return loaded_plugins
    
    def _find_plugin_class(self, module) -> Optional[Type[PluginInterface]]:
        """Find plugin class in module."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (obj != PluginInterface and 
                issubclass(obj, PluginInterface) and 
                obj.__module__ == module.__name__):
                return obj
        return None


class PluginManager:
    """Main plugin management system."""
    
    def __init__(self, plugin_dir: str = 'plugins'):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dir: Directory for plugin files
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)
        
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self.logger = logging.getLogger(__name__)
        
        # Plugin configuration storage
        self.config_file = self.plugin_dir / 'plugin_config.json'
        self.plugin_configs = self._load_plugin_configs()
    
    def load_all_plugins(self) -> List[str]:
        """
        Load all plugins from the plugin directory.
        
        Returns:
            List of loaded plugin names
        """
        return self.loader.load_plugins_from_directory(str(self.plugin_dir), self.plugin_configs)
    
    def load_plugin(self, plugin_file: str, config: Dict[str, Any] = None) -> str:
        """
        Load a specific plugin.
        
        Args:
            plugin_file: Path to plugin file
            config: Optional plugin configuration
            
        Returns:
            Plugin name
        """
        return self.loader.load_plugin_from_file(plugin_file, config)
    
    def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
        """
        self.registry.unregister_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get plugin by name."""
        return self.registry.get_plugin(plugin_name)
    
    def get_plugin_by_layer_id(self, layer_id: int) -> Optional[PluginInterface]:
        """Get plugin by layer ID."""
        return self.registry.get_plugin_by_layer_id(layer_id)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugin names."""
        return self.registry.list_plugins()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive plugin information.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Dictionary with plugin information
        """
        metadata = self.registry.get_plugin_metadata(plugin_name)
        if not metadata:
            return None
        
        plugin = self.registry.get_plugin(plugin_name)
        config = self.plugin_configs.get(plugin_name, {})
        
        return {
            'metadata': metadata.to_dict(),
            'configuration': config,
            'is_loaded': plugin is not None,
            'layer_processor_class': plugin.get_layer_processor_class().__name__ if plugin else None
        }
    
    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all plugins."""
        return {name: self.get_plugin_info(name) for name in self.list_plugins()}
    
    def validate_plugin_compatibility(self, plugin_name: str, 
                                    system_version: str = "1.0.0") -> ValidationResult:
        """
        Validate plugin compatibility with system version.
        
        Args:
            plugin_name: Name of plugin to validate
            system_version: Current system version
            
        Returns:
            ValidationResult with compatibility status
        """
        result = ValidationResult(is_valid=True)
        
        metadata = self.registry.get_plugin_metadata(plugin_name)
        if not metadata:
            result.add_error(f"Plugin '{plugin_name}' not found")
            return result
        
        # Check version compatibility
        if not self._is_version_compatible(system_version, metadata.min_system_version, 
                                         metadata.max_system_version):
            result.add_error(
                f"Plugin '{plugin_name}' requires system version "
                f"{metadata.min_system_version} - {metadata.max_system_version or 'latest'}, "
                f"but current version is {system_version}"
            )
        
        # Check dependencies
        for dependency in metadata.dependencies:
            if not self._check_dependency(dependency):
                result.add_error(f"Missing dependency: {dependency}")
        
        return result
    
    def set_plugin_configuration(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        Set configuration for a plugin.
        
        Args:
            plugin_name: Name of plugin
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        # Validate configuration
        validation = plugin.validate_configuration(config)
        if not validation.is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(validation.errors)}")
        
        # Store configuration
        self.plugin_configs[plugin_name] = config.copy()
        self._save_plugin_configs()
        
        # Reinitialize plugin with new configuration
        try:
            plugin.initialize(config)
        except Exception as e:
            self.logger.error(f"Error reinitializing plugin '{plugin_name}': {e}")
    
    def get_plugin_configuration(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a plugin."""
        return self.plugin_configs.get(plugin_name, {}).copy()
    
    def create_layer_processor(self, layer_id: int, kundali_data: KundaliData) -> Optional[LayerProcessorInterface]:
        """
        Create layer processor instance for given layer ID.
        
        Args:
            layer_id: Layer ID
            kundali_data: Kundali data for processing
            
        Returns:
            Layer processor instance or None if not found
        """
        plugin = self.registry.get_plugin_by_layer_id(layer_id)
        if not plugin:
            return None
        
        metadata = plugin.get_metadata()
        processor_class = plugin.get_layer_processor_class()
        
        return processor_class(layer_id, metadata.accuracy, kundali_data)
    
    def export_plugin_documentation(self, output_file: str) -> None:
        """
        Export documentation for all plugins.
        
        Args:
            output_file: Path to output documentation file
        """
        doc_data = {
            'generation_timestamp': datetime.now().isoformat(),
            'total_plugins': len(self.list_plugins()),
            'plugins': {}
        }
        
        for plugin_name in self.list_plugins():
            plugin_info = self.get_plugin_info(plugin_name)
            if plugin_info:
                doc_data['plugins'][plugin_name] = plugin_info
        
        with open(output_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
    
    def _load_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load plugin configurations from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Could not load plugin configs: {e}")
        
        return {}
    
    def _save_plugin_configs(self) -> None:
        """Save plugin configurations to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.plugin_configs, f, indent=2)
        except IOError as e:
            self.logger.error(f"Could not save plugin configs: {e}")
    
    def _is_version_compatible(self, current: str, min_version: str, 
                             max_version: Optional[str]) -> bool:
        """Check if current version is compatible with plugin requirements."""
        # Simple version comparison (can be enhanced with proper semver)
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        current_tuple = version_tuple(current)
        min_tuple = version_tuple(min_version)
        
        if current_tuple < min_tuple:
            return False
        
        if max_version:
            max_tuple = version_tuple(max_version)
            if current_tuple > max_tuple:
                return False
        
        return True
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if dependency is available."""
        try:
            importlib.import_module(dependency)
            return True
        except ImportError:
            return False


# Global plugin manager instance
_global_plugin_manager = None


def get_plugin_manager(plugin_dir: str = 'plugins') -> PluginManager:
    """
    Get or create global plugin manager instance.
    
    Args:
        plugin_dir: Directory for plugin files
        
    Returns:
        PluginManager instance
    """
    global _global_plugin_manager
    
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager(plugin_dir)
    
    return _global_plugin_manager


def reset_plugin_manager():
    """Reset global plugin manager (mainly for testing)."""
    global _global_plugin_manager
    _global_plugin_manager = None