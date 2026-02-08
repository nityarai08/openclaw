"""
Enhanced BPHS System Module

This module consolidates all enhanced system functionality including performance optimization,
rule management, and integration capabilities for the Enhanced BPHS Rule System.
"""

import json
import yaml
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)


# ============================================================================
# Enhanced Rule Models
# ============================================================================

@dataclass
class SourceReference:
    """BPHS source reference with chapter, verse, and page information."""
    chapter: str
    verse: Optional[str] = None
    page: Optional[int] = None
    volume: int = 1
    exact_quote: Optional[str] = None
    interpretation_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chapter': self.chapter,
            'verse': self.verse,
            'page': self.page,
            'volume': self.volume,
            'exact_quote': self.exact_quote,
            'interpretation_notes': self.interpretation_notes
        }


@dataclass
class EnhancedRule:
    """Enhanced BPHS rule with comprehensive metadata."""
    serial: int
    id: str
    section: str
    priority: str
    conditions: Dict[str, Any]
    summary: str
    impact: Union[str, Dict[str, Any]]
    action: Union[str, Dict[str, Any]]
    source_reference: Optional[SourceReference] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'serial': self.serial,
            'id': self.id,
            'section': self.section,
            'priority': self.priority,
            'conditions': self.conditions,
            'summary': self.summary,
            'impact': self.impact,
            'action': self.action,
            'source_reference': self.source_reference.to_dict() if self.source_reference else None
        }
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy YAML rule format."""
        legacy_rule = {
            'serial': self.serial,
            'id': self.id,
            'section': self.section,
            'priority': self.priority,
            'conditions': self.conditions,
            'summary': self.summary,
            'impact': self.impact if isinstance(self.impact, str) else str(self.impact),
            'action': self.action if isinstance(self.action, str) else str(self.action)
        }
        
        if self.source_reference:
            legacy_rule['_source'] = f"BPHS Ch. {self.source_reference.chapter}"
            if self.source_reference.verse:
                legacy_rule['_source'] += f", v. {self.source_reference.verse}"
        
        return legacy_rule


# ============================================================================
# Performance Optimization
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for rule evaluation."""
    total_time_ms: float = 0.0
    rules_evaluated: int = 0
    rules_triggered: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_time_ms': self.total_time_ms,
            'rules_evaluated': self.rules_evaluated,
            'rules_triggered': self.rules_triggered,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'avg_time_per_rule_ms': self.total_time_ms / self.rules_evaluated if self.rules_evaluated > 0 else 0,
            'cache_hit_ratio': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }


class RuleIndex:
    """Efficient indexing structure for rules."""
    
    def __init__(self):
        self.planet_rules: Dict[str, Set[int]] = defaultdict(set)
        self.house_rules: Dict[int, Set[int]] = defaultdict(set)
        self.priority_rules: Dict[str, Set[int]] = defaultdict(set)
        self.section_rules: Dict[str, Set[int]] = defaultdict(set)
    
    def add_rule(self, rule_serial: int, conditions: Dict[str, Any], priority: str, section: str) -> None:
        """Add a rule to the index."""
        self.priority_rules[priority.lower()].add(rule_serial)
        self.section_rules[section.lower()].add(rule_serial)
        self._index_conditions(rule_serial, conditions)
    
    def _index_conditions(self, rule_serial: int, conditions: Dict[str, Any]) -> None:
        """Index rule by its conditions for fast lookup."""
        if not isinstance(conditions, dict):
            return
        
        # Handle logical operators recursively
        if 'all' in conditions:
            for sub_condition in conditions.get('all', []):
                self._index_conditions(rule_serial, sub_condition)
            return
        
        if 'any' in conditions or 'any_of' in conditions:
            key = 'any' if 'any' in conditions else 'any_of'
            for sub_condition in conditions.get(key, []):
                self._index_conditions(rule_serial, sub_condition)
            return
        
        # Index leaf conditions
        for condition_type, params in conditions.items():
            condition_type = condition_type.lower()
            
            if condition_type == 'planet_position' and isinstance(params, dict):
                planet = params.get('planet', '').lower()
                if planet:
                    self.planet_rules[planet].add(rule_serial)
                
                house = params.get('house')
                if isinstance(house, int):
                    self.house_rules[house].add(rule_serial)
                elif isinstance(house, dict) and 'in' in house:
                    houses = house['in']
                    if not isinstance(houses, list):
                        houses = [houses]
                    for h in houses:
                        try:
                            self.house_rules[int(h)].add(rule_serial)
                        except (ValueError, TypeError):
                            pass
            
            elif condition_type == 'planet_dignity' and isinstance(params, dict):
                planet = params.get('planet', '').lower()
                if planet:
                    self.planet_rules[planet].add(rule_serial)
    
    def get_candidate_rules(self, chart_context: Dict[str, Any]) -> Set[int]:
        """Get candidate rules based on chart context."""
        candidates = set()
        
        # Add rules for planets present in chart
        planets = chart_context.get('planets', {})
        for planet_key in planets.keys():
            candidates.update(self.planet_rules.get(planet_key, set()))
        
        # Add high priority rules
        candidates.update(self.priority_rules.get('high', set()))
        
        # If no candidates, return all indexed rules
        if not candidates:
            for rule_set in self.planet_rules.values():
                candidates.update(rule_set)
        
        return candidates


class OptimizedRuleEngine:
    """Performance-optimized rule evaluation engine."""
    
    def __init__(self, cache_size: int = 1000):
        self.rule_index = RuleIndex()
        self.metrics = PerformanceMetrics()
        self._rules: List[Dict[str, Any]] = []
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_size = cache_size
        self._cache_lock = threading.RLock()
    
    def load_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Load and index rules for optimized evaluation."""
        self._rules = rules
        self.rule_index = RuleIndex()
        
        for rule in rules:
            serial = rule.get('serial', 0)
            conditions = rule.get('conditions', {})
            priority = rule.get('priority', 'Medium')
            section = rule.get('section', '')
            
            self.rule_index.add_rule(serial, conditions, priority, section)
        
        logger.info(f"Loaded and indexed {len(rules)} rules")
    
    def evaluate_rules(self, chart_context: Dict[str, Any], max_time_ms: float = 100.0) -> List[Dict[str, Any]]:
        """Evaluate rules with performance optimization."""
        start_time = time.perf_counter()
        max_time_seconds = max_time_ms / 1000.0
        
        triggered_rules = []
        self.metrics = PerformanceMetrics()
        
        # Generate cache key
        cache_key = self._generate_cache_key(chart_context)
        
        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            self.metrics.cache_hits += 1
            return cached_result
        
        self.metrics.cache_misses += 1
        
        # Get candidate rules
        candidate_serials = self.rule_index.get_candidate_rules(chart_context)
        
        # Filter to candidate rules only
        candidate_rules = [rule for rule in self._rules if rule.get('serial') in candidate_serials]
        
        # Sort by priority
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        candidate_rules.sort(key=lambda r: (priority_order.get(r.get('priority', 'Medium'), 1), r.get('serial', 0)))
        
        # Evaluate rules with time limit
        for rule in candidate_rules:
            current_time = time.perf_counter()
            if current_time - start_time > max_time_seconds:
                logger.warning(f"Rule evaluation timeout after {(current_time - start_time)*1000:.2f}ms")
                break
            
            if self._evaluate_rule_conditions(rule.get('conditions', {}), chart_context):
                triggered_rules.append(rule)
                self.metrics.rules_triggered += 1
            
            self.metrics.rules_evaluated += 1
        
        end_time = time.perf_counter()
        self.metrics.total_time_ms = (end_time - start_time) * 1000
        
        # Cache result
        self._put_in_cache(cache_key, triggered_rules)
        
        logger.debug(f"Evaluated {self.metrics.rules_evaluated} rules in {self.metrics.total_time_ms:.2f}ms, "
                    f"triggered {self.metrics.rules_triggered}")
        
        return triggered_rules
    
    def _generate_cache_key(self, chart_context: Dict[str, Any]) -> str:
        """Generate cache key from chart context."""
        context_str = json.dumps(chart_context, sort_keys=True, default=str)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Get result from cache."""
        with self._cache_lock:
            if key in self._cache:
                result, timestamp = self._cache[key]
                # Simple TTL check (1 hour)
                if time.time() - timestamp < 3600:
                    return result
                else:
                    del self._cache[key]
        return None
    
    def _put_in_cache(self, key: str, result: List[Dict[str, Any]]) -> None:
        """Put result in cache."""
        with self._cache_lock:
            # Simple LRU eviction
            if len(self._cache) >= self._cache_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[key] = (result, time.time())
    
    def _evaluate_rule_conditions(self, conditions: Dict[str, Any], chart_context: Dict[str, Any]) -> bool:
        """Evaluate rule conditions with optimized matchers."""
        if not conditions:
            return True
        
        if isinstance(conditions, list):
            return all(self._evaluate_rule_conditions(cond, chart_context) for cond in conditions)
        
        if not isinstance(conditions, dict):
            return False
        
        # Handle logical operators
        if 'all' in conditions:
            return all(self._evaluate_rule_conditions(cond, chart_context) 
                      for cond in conditions.get('all', []))
        
        if 'any' in conditions or 'any_of' in conditions:
            key = 'any' if 'any' in conditions else 'any_of'
            return any(self._evaluate_rule_conditions(cond, chart_context) 
                      for cond in conditions.get(key, []))
        
        # Evaluate leaf conditions with optimized matchers
        for condition_type, params in conditions.items():
            if condition_type.lower() == 'planet_position':
                return self._check_planet_position(params, chart_context)
            elif condition_type.lower() == 'planet_dignity':
                return self._check_planet_dignity(params, chart_context)
        
        return False
    
    def _check_planet_position(self, params: Dict[str, Any], chart_context: Dict[str, Any]) -> bool:
        """Fast planet position check."""
        if not isinstance(params, dict):
            return False
        
        planet = params.get('planet', '').lower()
        house_spec = params.get('house')
        
        if not planet:
            return False
        
        planets = chart_context.get('planets', {})
        planet_data = planets.get(planet)
        
        if not planet_data:
            return False
        
        planet_house = planet_data.get('house_number')
        if not planet_house:
            return False
        
        try:
            planet_house_int = int(planet_house)
        except (ValueError, TypeError):
            return False
        
        # Check house specification
        if isinstance(house_spec, dict) and 'in' in house_spec:
            target_houses = house_spec['in']
            if not isinstance(target_houses, list):
                target_houses = [target_houses]
            
            for house in target_houses:
                try:
                    if int(house) == planet_house_int:
                        return True
                except (ValueError, TypeError):
                    continue
            return False
        
        elif house_spec is not None:
            try:
                return int(house_spec) == planet_house_int
            except (ValueError, TypeError):
                return False
        
        return True
    
    def _check_planet_dignity(self, params: Dict[str, Any], chart_context: Dict[str, Any]) -> bool:
        """Fast planet dignity check."""
        if not isinstance(params, dict):
            return False
        
        planet = params.get('planet', '').lower()
        dignity_spec = params.get('in', params.get('dignity'))
        
        if not planet:
            return False
        
        planets = chart_context.get('planets', {})
        planet_data = planets.get(planet)
        
        if not planet_data:
            return False
        
        planet_dignity = planet_data.get('dignity', '').lower()
        
        if isinstance(dignity_spec, list):
            return planet_dignity in [str(d).lower() for d in dignity_spec]
        elif dignity_spec is not None:
            return planet_dignity == str(dignity_spec).lower()
        
        return True
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report."""
        return {
            'metrics': self.metrics.to_dict(),
            'cache_size': len(self._cache),
            'optimization_enabled': True
        }
    
    def clear_cache(self) -> None:
        """Clear evaluation cache."""
        with self._cache_lock:
            self._cache.clear()


# ============================================================================
# Integration and Management
# ============================================================================

class EnhancedRuleSystem:
    """Main interface for the Enhanced BPHS Rule System."""
    
    def __init__(self, rule_file_path: Optional[str] = None):
        self.rule_file_path = rule_file_path or "config/narrative/rules/bphs_context_rules.yaml"
        self.engine = OptimizedRuleEngine()
        self.rules = []
        self.enhanced_rules = []
        
    def load_rules(self) -> bool:
        """Load rules from file."""
        rule_file = Path(self.rule_file_path)
        
        if not rule_file.exists():
            logger.error(f"Rule file not found: {rule_file}")
            return False
        
        try:
            with rule_file.open('r', encoding='utf-8') as f:
                content = f.read().replace('\t', '  ')
                spec = yaml.safe_load(content)
            
            self.rules = spec.get('rules', [])
            
            # Convert to enhanced rules if needed
            self.enhanced_rules = []
            for rule in self.rules:
                enhanced_rule = self._convert_to_enhanced_rule(rule)
                self.enhanced_rules.append(enhanced_rule)
            
            # Load into engine
            self.engine.load_rules(self.rules)
            
            logger.info(f"Loaded {len(self.rules)} rules from {rule_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return False
    
    def _convert_to_enhanced_rule(self, rule: Dict[str, Any]) -> EnhancedRule:
        """Convert legacy rule to enhanced format."""
        source_ref = None
        if '_source' in rule:
            source_ref = SourceReference(chapter=rule['_source'])
        
        return EnhancedRule(
            serial=rule.get('serial', 0),
            id=rule.get('id', ''),
            section=rule.get('section', ''),
            priority=rule.get('priority', 'Medium'),
            conditions=rule.get('conditions', {}),
            summary=rule.get('summary', ''),
            impact=rule.get('impact', ''),
            action=rule.get('action', ''),
            source_reference=source_ref
        )
    
    def evaluate_chart(self, chart_data: Dict[str, Any], max_time_ms: float = 100.0) -> Dict[str, Any]:
        """Evaluate chart with enhanced system."""
        start_time = time.perf_counter()
        
        try:
            triggered_rules = self.engine.evaluate_rules(chart_data, max_time_ms)
            
            end_time = time.perf_counter()
            evaluation_time = (end_time - start_time) * 1000
            
            performance_report = self.engine.get_performance_report()
            
            return {
                'success': True,
                'evaluation_time_ms': evaluation_time,
                'triggered_rules': triggered_rules,
                'performance_report': performance_report,
                'performance_target_met': evaluation_time < max_time_ms
            }
        
        except Exception as e:
            end_time = time.perf_counter()
            evaluation_time = (end_time - start_time) * 1000
            
            logger.error(f"Chart evaluation failed: {e}")
            return {
                'success': False,
                'evaluation_time_ms': evaluation_time,
                'error': str(e),
                'performance_target_met': False
            }
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        if not self.rules:
            return {'error': 'No rules loaded'}
        
        stats = {
            'total_rules': len(self.rules),
            'sections': {},
            'priorities': {},
            'enhanced_rules': len(self.enhanced_rules)
        }
        
        for rule in self.rules:
            section = rule.get('section', 'unknown')
            priority = rule.get('priority', 'unknown')
            
            stats['sections'][section] = stats['sections'].get(section, 0) + 1
            stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
        
        return stats
    
    def export_enhanced_rules(self, output_file: str, format: str = 'json') -> bool:
        """Export enhanced rules to file."""
        if not self.enhanced_rules:
            logger.error("No enhanced rules to export")
            return False
        
        try:
            output_path = Path(output_file)
            
            enhanced_data = {
                'meta': {
                    'title': 'Enhanced BPHS Rules',
                    'version': '2.0',
                    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'rules': [rule.to_dict() for rule in self.enhanced_rules]
            }
            
            with output_path.open('w', encoding='utf-8') as f:
                if format.lower() == 'json':
                    json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
                elif format.lower() == 'yaml':
                    yaml.dump(enhanced_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    logger.error(f"Unsupported format: {format}")
                    return False
            
            logger.info(f"Enhanced rules exported to: {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting enhanced rules: {e}")
            return False


# ============================================================================
# Utility Functions
# ============================================================================

def benchmark_system_performance(system: EnhancedRuleSystem, test_charts: List[Dict[str, Any]], iterations: int = 10) -> Dict[str, Any]:
    """Benchmark system performance."""
    results = []
    
    for chart in test_charts:
        chart_times = []
        
        for _ in range(iterations):
            result = system.evaluate_chart(chart)
            if result['success']:
                chart_times.append(result['evaluation_time_ms'])
        
        if chart_times:
            results.append({
                'avg_time_ms': sum(chart_times) / len(chart_times),
                'min_time_ms': min(chart_times),
                'max_time_ms': max(chart_times),
                'successful_evaluations': len(chart_times)
            })
    
    if results:
        all_times = []
        for result in results:
            all_times.extend([result['avg_time_ms']])  # Use average times
        
        return {
            'overall_avg_time_ms': sum(all_times) / len(all_times),
            'overall_max_time_ms': max(result['max_time_ms'] for result in results),
            'overall_min_time_ms': min(result['min_time_ms'] for result in results),
            'performance_target_met': max(result['max_time_ms'] for result in results) < 100.0,
            'chart_results': results
        }
    else:
        return {'error': 'No successful evaluations'}


def create_sample_enhanced_rule() -> EnhancedRule:
    """Create a sample enhanced rule for testing."""
    return EnhancedRule(
        serial=1,
        id="sun_exalted_first_house",
        section="planetary_dignities",
        priority="High",
        conditions={
            "all": [
                {"planet_position": {"planet": "sun", "house": 1}},
                {"planet_dignity": {"planet": "sun", "in": "exalted"}}
            ]
        },
        summary="Sun exalted in 1st house creates exceptional leadership qualities",
        impact={
            "positive_manifestation": "Natural authority, recognition from government, strong constitution",
            "negative_manifestation": "Possible ego conflicts, authoritarian tendencies"
        },
        action={
            "primary_actions": [
                "Develop leadership skills through formal training",
                "Seek positions of responsibility and authority"
            ],
            "timing_guidance": {
                "sun_dasha": "Peak period for career advancement and recognition"
            }
        },
        source_reference=SourceReference(
            chapter="Ch. 11 - Effects of Planets in Houses",
            verse="11.1-2",
            page=156,
            volume=1
        )
    )