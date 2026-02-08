"""
Core data models and structures for the Kundali Favorability Heatmap System.

This module defines all the base data classes used across the three components
to ensure consistent data structures and interfaces.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json


@dataclass
class BirthDetails:
    """Birth details for kundali generation."""
    date: datetime
    time: time
    place: str
    latitude: float
    longitude: float
    timezone_offset: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date.isoformat(),
            'time': self.time.isoformat(),
            'place': self.place,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timezone_offset': self.timezone_offset
        }


@dataclass
class PlanetaryPosition:
    """Planetary position data."""
    longitude: float
    rasi: int
    nakshatra: int
    degree_in_sign: float
    retrograde: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'longitude': self.longitude,
            'rasi': self.rasi,
            'nakshatra': self.nakshatra,
            'degree_in_sign': self.degree_in_sign,
            'retrograde': self.retrograde
        }


@dataclass
class KundaliData:
    """Complete kundali data structure."""
    schema_version: str = "2.0"
    generation_timestamp: Optional[str] = None
    birth_details: Optional[BirthDetails] = None
    astronomical_data: Dict[str, Any] = field(default_factory=dict)
    planetary_positions: Dict[str, PlanetaryPosition] = field(default_factory=dict)
    divisional_charts: Dict[str, Dict] = field(default_factory=dict)
    panchanga: Dict[str, Any] = field(default_factory=dict)
    yogas_and_doshas: Dict[str, List] = field(default_factory=dict)
    dasha_periods: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'schema_version': self.schema_version,
            'generation_timestamp': self.generation_timestamp,
            'birth_details': self.birth_details.to_dict() if self.birth_details else None,
            'astronomical_data': self.astronomical_data,
            'planetary_positions': {k: v.to_dict() for k, v in self.planetary_positions.items()},
            'divisional_charts': self.divisional_charts,
            'panchanga': self.panchanga,
            'yogas_and_doshas': self.yogas_and_doshas,
            'dasha_periods': self.dasha_periods,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class LayerInfo:
    """Information about a calculation layer."""
    id: int
    name: str
    accuracy_rating: float
    methodology: str
    description: str
    calculation_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'accuracy_rating': self.accuracy_rating,
            'methodology': self.methodology,
            'description': self.description,
            'calculation_factors': self.calculation_factors
        }


@dataclass
class DailyScore:
    """Daily favorability score data."""
    date: str
    day_of_year: int
    score: float
    confidence: float
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date,
            'day_of_year': self.day_of_year,
            'score': self.score,
            'confidence': self.confidence,
            'contributing_factors': self.contributing_factors
        }


@dataclass
class LayerData:
    """Complete layer calculation data."""
    layer_info: LayerInfo
    annual_data: List[DailyScore]
    summary_statistics: Dict[str, float] = field(default_factory=dict)
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'layer_info': self.layer_info.to_dict(),
            'annual_data': [score.to_dict() for score in self.annual_data],
            'summary_statistics': self.summary_statistics,
            'calculation_metadata': self.calculation_metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning."""
        self.warnings.append(warning)


@dataclass
class LocationData:
    """Location data with coordinates and timezone."""
    place_name: str
    latitude: float
    longitude: float
    timezone_offset: float
    country: Optional[str] = None
    region: Optional[str] = None

# Astrological Constants for Signs and Planets
SIGN_SEQUENCE = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

# Classical sign rulers per BPHS (sidereal)
SIGN_RULERS = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
    "pisces": "jupiter",
}

PLANET_DIGNITY_TABLE = {
    "sun": {
        "exalted": [{"sign": "aries"}], "debilitated": [{"sign": "libra"}],
        "mulatrikona": [{"sign": "leo", "start": 0, "end": 20}], "own": [{"sign": "leo"}],
    },
    "moon": {
        "exalted": [{"sign": "taurus"}], "debilitated": [{"sign": "scorpio"}],
        "mulatrikona": [{"sign": "taurus", "start": 3, "end": 30}], "own": [{"sign": "cancer"}],
    },
    "mars": {
        "exalted": [{"sign": "capricorn"}], "debilitated": [{"sign": "cancer"}],
        "mulatrikona": [{"sign": "aries", "start": 0, "end": 12}],
        "own": [{"sign": "aries"}, {"sign": "scorpio"}],
    },
    "mercury": {
        "exalted": [{"sign": "virgo"}], "debilitated": [{"sign": "pisces"}],
        "mulatrikona": [{"sign": "virgo", "start": 16, "end": 20}],
        "own": [{"sign": "gemini"}, {"sign": "virgo"}],
    },
    "jupiter": {
        "exalted": [{"sign": "cancer"}], "debilitated": [{"sign": "capricorn"}],
        "mulatrikona": [{"sign": "sagittarius", "start": 0, "end": 10}],
        "own": [{"sign": "sagittarius"}, {"sign": "pisces"}],
    },
    "venus": {
        "exalted": [{"sign": "pisces"}], "debilitated": [{"sign": "virgo"}],
        "mulatrikona": [{"sign": "libra", "start": 0, "end": 15}],
        "own": [{"sign": "taurus"}, {"sign": "libra"}],
    },
    "saturn": {
        "exalted": [{"sign": "libra"}], "debilitated": [{"sign": "aries"}],
        "mulatrikona": [{"sign": "aquarius", "start": 0, "end": 20}],
        "own": [{"sign": "capricorn"}, {"sign": "aquarius"}],
    },
    "rahu": {
        "exalted": [{"sign": "taurus"}, {"sign": "gemini"}],
        "debilitated": [{"sign": "scorpio"}, {"sign": "sagittarius"}],
    },
    "ketu": {
        "exalted": [{"sign": "scorpio"}, {"sign": "sagittarius"}],
        "debilitated": [{"sign": "taurus"}, {"sign": "gemini"}],
    },
}
