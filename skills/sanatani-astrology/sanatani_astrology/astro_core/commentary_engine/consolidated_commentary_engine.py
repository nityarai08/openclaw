"""
Consolidated Commentary Engine - Literature-Based Vedic Astrology Analysis

This module provides a single, comprehensive commentary engine that generates
natural language analysis based purely on established Vedic astrological principles.
All rules are grounded in classical texts and no randomization is used.

Key Features:
- 100% grounded in kundali data
- Based on established astrological literature
- Natural language flow
- Single JSON output for rendering
- No randomization or speculation
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging


@dataclass
class PlanetaryAnalysis:
    """Analysis of a single planet's position and effects."""
    planet: str
    house: int
    sign: str
    dignity: str
    strength: float
    effects: List[str]
    remedies: List[str]


@dataclass
class CommentarySection:
    """A section of the commentary with title and content."""
    title: str
    content: str
    confidence: float
    supporting_factors: List[str]


class ConsolidatedCommentaryEngine:
    """
    Consolidated commentary engine based on classical Vedic astrology.
    
    This engine generates comprehensive commentary using only established
    astrological principles from classical texts like:
    - Brihat Parashara Hora Shastra
    - Jataka Parijata
    - Phaladeepika
    - Saravali
    - Hora Sara
    """
    
    def __init__(self):
        """Initialize the consolidated commentary engine."""
        self.logger = logging.getLogger(__name__)
        
        # Classical sign names
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        # Classical house significations (from Parashara)
        self.house_significations = {
            1: "physical body, personality, general health, appearance, vitality",
            2: "wealth, family, speech, food, accumulated resources, values",
            3: "courage, siblings, short journeys, communication, efforts, skills",
            4: "mother, home, property, vehicles, education, emotional foundations",
            5: "children, intelligence, creativity, past-life merit, speculation",
            6: "enemies, diseases, debts, service, daily work, obstacles",
            7: "spouse, partnerships, business, public relations, marriage",
            8: "longevity, transformation, occult, research, inheritance, mysteries",
            9: "father, dharma, higher learning, spirituality, fortune, pilgrimage",
            10: "career, reputation, authority, government, public recognition",
            11: "gains, income, elder siblings, friends, fulfillment of desires",
            12: "losses, expenses, foreign lands, spirituality, liberation, isolation"
        }
        
        # Planetary dignities and their effects (classical)
        self.dignity_effects = {
            "Exalted": "exceptional strength, maximum positive results, natural leadership",
            "Own Sign": "comfortable position, natural expression, good results",
            "Moolatrikona": "strong position, favorable outcomes, stable results",
            "Great Friend": "supportive environment, helpful influences, positive growth",
            "Friend": "favorable conditions, moderate support, steady progress",
            "Neutral": "balanced effects, results depend on other factors, average outcomes",
            "Enemy": "challenging conditions, obstacles, requires extra effort",
            "Great Enemy": "difficult circumstances, significant challenges, needs remedies",
            "Debilitated": "weakened state, struggles, requires specific remedial measures",
            "Combust": "overshadowed by Sun, hidden potential, needs careful handling"
        }
        
        # Load classical astrological rules
        self._load_classical_rules()
    
    def generate_comprehensive_commentary(
        self, 
        kundali_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive commentary based on kundali data.
        
        Args:
            kundali_data: Complete kundali JSON data following the schema
            
        Returns:
            Dictionary with structured commentary for JSON rendering
        """
        self.logger.info("Generating comprehensive commentary from kundali data")
        
        # Extract key data
        birth_details = kundali_data.get('birth_details', {})
        d1_chart = kundali_data.get('divisional_charts', {}).get('D1', {})
        positions = d1_chart.get('planetary_positions', {})
        yogas = d1_chart.get('yogas', [])
        dasha_data = kundali_data.get('dasha_analysis', {})
        
        # Generate commentary sections
        sections = {
            "chart_overview": self._generate_chart_overview(birth_details, positions),
            "planetary_analysis": self._generate_planetary_analysis(positions),
            "house_analysis": self._generate_house_analysis(positions),
            "yoga_analysis": self._generate_yoga_analysis(yogas, positions),
            "dasha_analysis": self._generate_dasha_analysis(dasha_data, positions),
            "life_themes": self._generate_life_themes(positions),
            "remedial_measures": self._generate_remedial_measures(positions)
        }
        
        # Calculate overall metrics
        word_count = sum(len(section.content.split()) for section in sections.values())
        confidence = self._calculate_overall_confidence(positions)
        
        # Structure for JSON output
        commentary_json = {
            "comprehensive_commentary": {
                section_key: {
                    "title": section.title,
                    "content": section.content,
                    "confidence": section.confidence,
                    "supporting_factors": section.supporting_factors
                }
                for section_key, section in sections.items()
            },
            "metadata": {
                "word_count": word_count,
                "confidence_score": confidence,
                "analysis_type": "Classical Vedic Astrology Commentary",
                "generated_at": datetime.now().isoformat(),
                "methodology": "Based on Brihat Parashara Hora Shastra and classical texts",
                "grounding": "100% based on provided kundali data"
            },
            "birth_details": birth_details
        }
        
        return commentary_json  
  
    def _load_classical_rules(self):
        """Load classical astrological rules from established literature."""
        
        # Planetary significations (from Parashara Hora Shastra)
        self.planetary_significations = {
            "sun": {
                "natural_significations": ["soul", "father", "authority", "government", "leadership", "vitality", "ego", "bones", "heart"],
                "positive_houses": [1, 4, 5, 9, 10, 11],
                "exaltation_sign": 0,  # Aries
                "debilitation_sign": 6,  # Libra
                "own_signs": [4],  # Leo
                "moolatrikona": 4  # Leo
            },
            "moon": {
                "natural_significations": ["mind", "mother", "emotions", "public", "water", "nurturing", "intuition", "blood", "stomach"],
                "positive_houses": [1, 2, 4, 5, 9, 10, 11],
                "exaltation_sign": 1,  # Taurus
                "debilitation_sign": 7,  # Scorpio
                "own_signs": [3],  # Cancer
                "moolatrikona": 3  # Cancer
            },
            "mars": {
                "natural_significations": ["energy", "courage", "property", "siblings", "surgery", "competition", "anger", "muscles", "blood"],
                "positive_houses": [1, 3, 6, 10, 11],
                "exaltation_sign": 9,  # Capricorn
                "debilitation_sign": 3,  # Cancer
                "own_signs": [0, 7],  # Aries, Scorpio
                "moolatrikona": 0  # Aries
            },
            "mercury": {
                "natural_significations": ["intelligence", "communication", "business", "education", "analysis", "wit", "skin", "nervous system"],
                "positive_houses": [1, 2, 4, 5, 6, 9, 10, 11],
                "exaltation_sign": 5,  # Virgo
                "debilitation_sign": 11,  # Pisces
                "own_signs": [2, 5],  # Gemini, Virgo
                "moolatrikona": 5  # Virgo
            },
            "jupiter": {
                "natural_significations": ["wisdom", "spirituality", "children", "teaching", "wealth", "dharma", "guru", "liver", "fat"],
                "positive_houses": [1, 2, 4, 5, 7, 9, 10, 11],
                "exaltation_sign": 3,  # Cancer
                "debilitation_sign": 9,  # Capricorn
                "own_signs": [8, 11],  # Sagittarius, Pisces
                "moolatrikona": 8  # Sagittarius
            },
            "venus": {
                "natural_significations": ["relationships", "luxury", "arts", "beauty", "vehicles", "comfort", "spouse", "reproductive organs"],
                "positive_houses": [1, 2, 4, 5, 7, 9, 10, 11, 12],
                "exaltation_sign": 11,  # Pisces
                "debilitation_sign": 5,  # Virgo
                "own_signs": [1, 6],  # Taurus, Libra
                "moolatrikona": 6  # Libra
            },
            "saturn": {
                "natural_significations": ["discipline", "delays", "hard work", "service", "longevity", "karma", "lessons", "bones", "teeth"],
                "positive_houses": [3, 6, 10, 11],
                "exaltation_sign": 6,  # Libra
                "debilitation_sign": 0,  # Aries
                "own_signs": [9, 10],  # Capricorn, Aquarius
                "moolatrikona": 10  # Aquarius
            },
            "rahu": {
                "natural_significations": ["material desires", "foreign connections", "technology", "illusion", "ambition", "unconventional"],
                "positive_houses": [3, 6, 10, 11],
                "exaltation_sign": 2,  # Gemini
                "debilitation_sign": 8  # Sagittarius
            },
            "ketu": {
                "natural_significations": ["spirituality", "detachment", "past-life karma", "mysticism", "liberation", "research"],
                "positive_houses": [3, 6, 8, 12],
                "exaltation_sign": 8,  # Sagittarius
                "debilitation_sign": 2  # Gemini
            }
        }
        
        # Classical yoga definitions (from Jataka Parijata and other texts)
        self.classical_yogas = {
            "Budh Aditya Yoga": {
                "definition": "Sun and Mercury conjunction",
                "effects": "Intelligence, eloquence, scholarly nature, good communication skills",
                "conditions": "Mercury not combust, preferably in good houses"
            },
            "Gaja Kesari Yoga": {
                "definition": "Jupiter in kendra from Moon",
                "effects": "Wisdom, prosperity, good reputation, leadership qualities",
                "conditions": "Jupiter should be strong and not afflicted"
            },
            "Raj Yoga": {
                "definition": "Lords of kendra and trikona houses in conjunction or mutual aspect",
                "effects": "Royal status, authority, wealth, recognition",
                "conditions": "Planets should be strong and well-placed"
            },
            "Dhana Yoga": {
                "definition": "Lords of 2nd and 11th houses in conjunction or mutual aspect",
                "effects": "Wealth accumulation, financial prosperity",
                "conditions": "Houses should be strong and unafflicted"
            },
            "Neecha Bhanga Raj Yoga": {
                "definition": "Debilitated planet's debilitation gets cancelled",
                "effects": "Converts weakness into strength, unexpected success",
                "conditions": "Specific cancellation conditions must be met"
            }
        }
        
        # House-based interpretations (classical)
        self.house_interpretations = {
            1: {
                "strong_planets": ["sun", "mars", "jupiter"],
                "weak_planets": ["saturn", "rahu", "ketu"],
                "general_effects": "Personality, physical appearance, general health, life direction"
            },
            2: {
                "strong_planets": ["jupiter", "venus", "mercury"],
                "weak_planets": ["mars", "saturn", "rahu"],
                "general_effects": "Wealth, family harmony, speech quality, food habits"
            },
            3: {
                "strong_planets": ["mars", "mercury"],
                "weak_planets": ["jupiter", "venus"],
                "general_effects": "Courage, communication, siblings, short travels"
            },
            4: {
                "strong_planets": ["moon", "venus", "jupiter"],
                "weak_planets": ["mars", "saturn"],
                "general_effects": "Mother, home, property, education, emotional stability"
            },
            5: {
                "strong_planets": ["jupiter", "sun", "mercury"],
                "weak_planets": ["saturn", "rahu", "ketu"],
                "general_effects": "Children, intelligence, creativity, past-life merit"
            },
            6: {
                "strong_planets": ["mars", "saturn", "rahu"],
                "weak_planets": ["jupiter", "venus", "moon"],
                "general_effects": "Health challenges, enemies, service, daily work"
            },
            7: {
                "strong_planets": ["venus", "jupiter", "mercury"],
                "weak_planets": ["mars", "saturn", "sun"],
                "general_effects": "Marriage, partnerships, business relationships"
            },
            8: {
                "strong_planets": ["saturn", "rahu", "ketu"],
                "weak_planets": ["sun", "moon", "jupiter"],
                "general_effects": "Longevity, transformation, occult knowledge, inheritance"
            },
            9: {
                "strong_planets": ["jupiter", "sun", "mars"],
                "weak_planets": ["rahu", "ketu"],
                "general_effects": "Father, dharma, higher learning, spirituality, fortune"
            },
            10: {
                "strong_planets": ["sun", "mars", "jupiter", "saturn"],
                "weak_planets": ["moon"],
                "general_effects": "Career, reputation, authority, public recognition"
            },
            11: {
                "strong_planets": ["jupiter", "venus", "mercury"],
                "weak_planets": ["sun", "moon"],
                "general_effects": "Gains, income, friends, fulfillment of desires"
            },
            12: {
                "strong_planets": ["saturn", "ketu", "venus"],
                "weak_planets": ["sun", "mars", "jupiter"],
                "general_effects": "Expenses, foreign connections, spirituality, liberation"
            }
        }
    
    def _generate_chart_overview(
        self, 
        birth_details: Dict[str, Any], 
        positions: Dict[str, Any]
    ) -> CommentarySection:
        """Generate chart overview based on ascendant and key planetary positions."""
        
        content_parts = []
        supporting_factors = []
        
        # Birth details
        place = birth_details.get('place', 'birth location')
        date = birth_details.get('date', 'birth date')
        time = birth_details.get('time', 'birth time')
        
        content_parts.append(f"This analysis is based on the birth chart cast for {place} on {date} at {time}.")
        
        # Ascendant analysis
        lagna_data = positions.get('lagna', {})
        lagna_rasi = lagna_data.get('rasi', 0)
        lagna_sign = self.sign_names[lagna_rasi] if lagna_rasi < len(self.sign_names) else "Unknown"
        
        content_parts.append(f"The {lagna_sign} ascendant establishes the fundamental life approach and personality framework.")
        supporting_factors.append(f"Ascendant in {lagna_sign}")
        
        # Key planetary strengths and challenges
        strong_planets = []
        weak_planets = []
        
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
                
            dignity = data.get('dignity', 'Neutral')
            house = data.get('house', 1)
            
            if dignity in ['Exalted', 'Own Sign', 'Moolatrikona']:
                strong_planets.append(f"{planet.title()} ({dignity} in {house}th house)")
            elif dignity in ['Debilitated', 'Great Enemy']:
                weak_planets.append(f"{planet.title()} ({dignity} in {house}th house)")
        
        if strong_planets:
            content_parts.append(f"Key planetary strengths include {', '.join(strong_planets[:3])}, providing natural advantages in their respective significations.")
            supporting_factors.extend(strong_planets[:3])
        
        if weak_planets:
            content_parts.append(f"Areas requiring attention include {', '.join(weak_planets[:3])}, which need remedial support for optimal functioning.")
            supporting_factors.extend(weak_planets[:3])
        
        # Overall chart emphasis
        house_emphasis = self._identify_chart_emphasis(positions)
        if house_emphasis:
            content_parts.append(f"The chart shows emphasis on {house_emphasis}, indicating primary life focus areas.")
            supporting_factors.append(f"Chart emphasis: {house_emphasis}")
        
        return CommentarySection(
            title="Chart Overview",
            content=" ".join(content_parts),
            confidence=0.95,
            supporting_factors=supporting_factors
        )  
  
    def _generate_planetary_analysis(self, positions: Dict[str, Any]) -> CommentarySection:
        """Generate detailed planetary analysis based on classical principles."""
        
        content_parts = []
        supporting_factors = []
        
        content_parts.append("Planetary Analysis based on classical Vedic principles:")
        
        # Analyze each planet systematically
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
                
            house = data.get('house', 1)
            rasi = data.get('rasi', 0)
            dignity = data.get('dignity', 'Neutral')
            strength = data.get('strength_points', 50.0)
            
            sign_name = self.sign_names[rasi] if rasi < len(self.sign_names) else "Unknown"
            planet_info = self.planetary_significations.get(planet, {})
            significations = planet_info.get('natural_significations', [])
            
            # Classical interpretation
            planet_analysis = []
            planet_analysis.append(f"{planet.title()} in {house}th house ({sign_name}, {dignity}):")
            
            # Dignity effects
            dignity_effect = self.dignity_effects.get(dignity, "balanced influence")
            planet_analysis.append(f"This placement indicates {dignity_effect} regarding {', '.join(significations[:3])}.")
            
            # House-specific effects
            house_signification = self.house_significations.get(house, f"{house}th house themes")
            planet_analysis.append(f"The influence extends to {house_signification}.")
            
            # Strength assessment
            if strength > 70:
                planet_analysis.append("The planet shows good strength and can deliver positive results.")
            elif strength < 30:
                planet_analysis.append("The planet is weak and requires remedial support.")
            else:
                planet_analysis.append("The planet has moderate strength with mixed results.")
            
            content_parts.append(" ".join(planet_analysis))
            supporting_factors.append(f"{planet.title()}: {dignity} in {house}th house")
        
        return CommentarySection(
            title="Planetary Analysis",
            content="\n\n".join(content_parts),
            confidence=0.90,
            supporting_factors=supporting_factors
        )
    
    def _generate_house_analysis(self, positions: Dict[str, Any]) -> CommentarySection:
        """Generate house-wise analysis based on planetary occupations."""
        
        content_parts = []
        supporting_factors = []
        
        content_parts.append("House Analysis based on planetary occupations:")
        
        # Group planets by house
        house_occupations = {}
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
            house = data.get('house', 1)
            if house not in house_occupations:
                house_occupations[house] = []
            house_occupations[house].append(planet)
        
        # Analyze occupied houses
        for house in sorted(house_occupations.keys()):
            planets = house_occupations[house]
            house_signification = self.house_significations.get(house, f"{house}th house themes")
            
            house_analysis = []
            house_analysis.append(f"{house}th House ({house_signification}):")
            
            if len(planets) == 1:
                planet = planets[0]
                planet_data = positions[planet]
                dignity = planet_data.get('dignity', 'Neutral')
                house_analysis.append(f"Occupied by {planet.title()} ({dignity}), influencing {house_signification}.")
            else:
                planet_list = [f"{p.title()}" for p in planets]
                house_analysis.append(f"Occupied by {', '.join(planet_list)}, creating combined influence on {house_signification}.")
            
            # House-specific interpretation
            house_info = self.house_interpretations.get(house, {})
            strong_planets_for_house = house_info.get('strong_planets', [])
            weak_planets_for_house = house_info.get('weak_planets', [])
            
            favorable_planets = [p for p in planets if p in strong_planets_for_house]
            challenging_planets = [p for p in planets if p in weak_planets_for_house]
            
            if favorable_planets:
                house_analysis.append(f"The presence of {', '.join(favorable_planets)} is favorable for this house.")
            if challenging_planets:
                house_analysis.append(f"The presence of {', '.join(challenging_planets)} may create challenges that require careful handling.")
            
            content_parts.append(" ".join(house_analysis))
            supporting_factors.append(f"House {house}: {', '.join(planets)}")
        
        return CommentarySection(
            title="House Analysis",
            content="\n\n".join(content_parts),
            confidence=0.85,
            supporting_factors=supporting_factors
        )
    
    def _generate_yoga_analysis(
        self, 
        yogas: List[str], 
        positions: Dict[str, Any]
    ) -> CommentarySection:
        """Generate analysis of yogas present in the chart."""
        
        content_parts = []
        supporting_factors = []
        
        if not yogas:
            content_parts.append("No major yogas are prominently formed in this chart.")
            return CommentarySection(
                title="Yoga Analysis",
                content=" ".join(content_parts),
                confidence=0.70,
                supporting_factors=["No major yogas identified"]
            )
        
        content_parts.append("Yoga Analysis based on classical combinations:")
        
        for yoga in yogas:
            if yoga in self.classical_yogas:
                yoga_info = self.classical_yogas[yoga]
                
                yoga_analysis = []
                yoga_analysis.append(f"{yoga}:")
                yoga_analysis.append(f"Definition: {yoga_info['definition']}")
                yoga_analysis.append(f"Effects: {yoga_info['effects']}")
                
                # Check conditions if possible
                conditions = yoga_info.get('conditions', '')
                if conditions:
                    yoga_analysis.append(f"For optimal results: {conditions}")
                
                content_parts.append(" ".join(yoga_analysis))
                supporting_factors.append(yoga)
            else:
                # Generic yoga analysis
                content_parts.append(f"{yoga}: This yoga creates specific planetary combinations that influence life outcomes.")
                supporting_factors.append(yoga)
        
        return CommentarySection(
            title="Yoga Analysis",
            content="\n\n".join(content_parts),
            confidence=0.80,
            supporting_factors=supporting_factors
        )
    
    def _generate_dasha_analysis(
        self, 
        dasha_data: Dict[str, Any], 
        positions: Dict[str, Any]
    ) -> CommentarySection:
        """Generate analysis of current dasha periods."""
        
        content_parts = []
        supporting_factors = []
        
        current_mahadasha = dasha_data.get('current_mahadasha', {})
        current_antardasha = dasha_data.get('current_antardasha', {})
        
        if not current_mahadasha:
            content_parts.append("Dasha information is not available for detailed timing analysis.")
            return CommentarySection(
                title="Dasha Analysis",
                content=" ".join(content_parts),
                confidence=0.50,
                supporting_factors=["No dasha data available"]
            )
        
        content_parts.append("Dasha Analysis based on Vimshottari system:")
        
        # Mahadasha analysis
        maha_planet = current_mahadasha.get('planet', 'Unknown')
        maha_end = current_mahadasha.get('end_date', 'Unknown')
        
        if maha_planet.lower() in positions:
            planet_data = positions[maha_planet.lower()]
            house = planet_data.get('house', 1)
            dignity = planet_data.get('dignity', 'Neutral')
            
            maha_analysis = []
            maha_analysis.append(f"Current {maha_planet} Mahadasha (until {maha_end}):")
            maha_analysis.append(f"The dasha lord is placed in {house}th house with {dignity} dignity.")
            
            # Dasha effects based on planet's condition
            planet_info = self.planetary_significations.get(maha_planet.lower(), {})
            significations = planet_info.get('natural_significations', [])
            
            dignity_effect = self.dignity_effects.get(dignity, "balanced influence")
            maha_analysis.append(f"This period emphasizes {', '.join(significations[:3])} with {dignity_effect}.")
            
            house_signification = self.house_significations.get(house, f"{house}th house themes")
            maha_analysis.append(f"Focus areas include {house_signification}.")
            
            content_parts.append(" ".join(maha_analysis))
            supporting_factors.append(f"{maha_planet} Mahadasha: {dignity} in {house}th house")
        
        # Antardasha analysis
        if current_antardasha:
            antar_planet = current_antardasha.get('planet', 'Unknown')
            antar_end = current_antardasha.get('end_date', 'Unknown')
            
            if antar_planet.lower() in positions:
                antar_data = positions[antar_planet.lower()]
                antar_house = antar_data.get('house', 1)
                antar_dignity = antar_data.get('dignity', 'Neutral')
                
                antar_analysis = []
                antar_analysis.append(f"Current {antar_planet} Antardasha (until {antar_end}):")
                antar_analysis.append(f"The sub-period lord is in {antar_house}th house with {antar_dignity} dignity.")
                antar_analysis.append(f"This adds specific influences to the main dasha period.")
                
                content_parts.append(" ".join(antar_analysis))
                supporting_factors.append(f"{antar_planet} Antardasha: {antar_dignity} in {antar_house}th house")
        
        return CommentarySection(
            title="Dasha Analysis",
            content="\n\n".join(content_parts),
            confidence=0.85,
            supporting_factors=supporting_factors
        )
    
    def _generate_life_themes(self, positions: Dict[str, Any]) -> CommentarySection:
        """Generate major life themes based on planetary positions."""
        
        content_parts = []
        supporting_factors = []
        
        content_parts.append("Major Life Themes derived from planetary analysis:")
        
        # Analyze key life areas based on house lords and occupations
        life_areas = {
            "Personality & Self-Expression": [1, 5],
            "Wealth & Resources": [2, 11],
            "Communication & Learning": [3, 9],
            "Home & Family": [4, 7],
            "Career & Reputation": [6, 10],
            "Health & Service": [6, 8],
            "Spirituality & Higher Purpose": [9, 12]
        }
        
        for theme, houses in life_areas.items():
            theme_analysis = []
            theme_planets = []
            
            # Find planets in relevant houses
            for house in houses:
                for planet, data in positions.items():
                    if planet == 'lagna':
                        continue
                    if data.get('house') == house:
                        dignity = data.get('dignity', 'Neutral')
                        theme_planets.append(f"{planet.title()} ({dignity})")
            
            if theme_planets:
                theme_analysis.append(f"{theme}:")
                theme_analysis.append(f"Influenced by {', '.join(theme_planets)}.")
                
                # Assess overall strength for this theme
                strong_count = sum(1 for p in theme_planets if any(d in p for d in ['Exalted', 'Own Sign', 'Moolatrikona']))
                weak_count = sum(1 for p in theme_planets if any(d in p for d in ['Debilitated', 'Great Enemy']))
                
                if strong_count > weak_count:
                    theme_analysis.append("This area shows natural strength and positive potential.")
                elif weak_count > strong_count:
                    theme_analysis.append("This area requires conscious development and remedial support.")
                else:
                    theme_analysis.append("This area shows balanced potential with mixed influences.")
                
                content_parts.append(" ".join(theme_analysis))
                supporting_factors.append(f"{theme}: {', '.join(theme_planets)}")
        
        return CommentarySection(
            title="Life Themes",
            content="\n\n".join(content_parts),
            confidence=0.80,
            supporting_factors=supporting_factors
        )
    
    def _generate_remedial_measures(self, positions: Dict[str, Any]) -> CommentarySection:
        """Generate remedial measures based on planetary weaknesses."""
        
        content_parts = []
        supporting_factors = []
        
        content_parts.append("Remedial Measures based on classical Vedic principles:")
        
        # Identify weak planets needing remedies
        weak_planets = []
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
                
            dignity = data.get('dignity', 'Neutral')
            strength = data.get('strength_points', 50.0)
            
            if dignity in ['Debilitated', 'Great Enemy'] or strength < 25:
                weak_planets.append({
                    'planet': planet,
                    'dignity': dignity,
                    'strength': strength,
                    'house': data.get('house', 1)
                })
        
        if not weak_planets:
            content_parts.append("The chart shows generally balanced planetary strengths. General spiritual practices and charity are recommended for overall enhancement.")
            return CommentarySection(
                title="Remedial Measures",
                content=" ".join(content_parts),
                confidence=0.70,
                supporting_factors=["No major planetary weaknesses identified"]
            )
        
        # Classical remedies for weak planets
        classical_remedies = {
            "sun": {
                "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namaha",
                "gemstone": "Ruby (Manik)",
                "charity": "Donate wheat, jaggery, or copper on Sundays",
                "fasting": "Fast on Sundays",
                "deity": "Worship Lord Surya"
            },
            "moon": {
                "mantra": "Om Shraam Shreem Shraum Sah Chandraya Namaha",
                "gemstone": "Pearl (Moti)",
                "charity": "Donate rice, milk, or silver on Mondays",
                "fasting": "Fast on Mondays",
                "deity": "Worship Lord Shiva or Divine Mother"
            },
            "mars": {
                "mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namaha",
                "gemstone": "Red Coral (Moonga)",
                "charity": "Donate red lentils, jaggery, or copper on Tuesdays",
                "fasting": "Fast on Tuesdays",
                "deity": "Worship Lord Hanuman"
            },
            "mercury": {
                "mantra": "Om Braam Breem Braum Sah Budhaya Namaha",
                "gemstone": "Emerald (Panna)",
                "charity": "Donate green vegetables, books, or brass on Wednesdays",
                "fasting": "Fast on Wednesdays",
                "deity": "Worship Lord Vishnu"
            },
            "jupiter": {
                "mantra": "Om Graam Greem Graum Sah Gurave Namaha",
                "gemstone": "Yellow Sapphire (Pukhraj)",
                "charity": "Donate turmeric, yellow clothes, or gold on Thursdays",
                "fasting": "Fast on Thursdays",
                "deity": "Worship Lord Brihaspati or Guru"
            },
            "venus": {
                "mantra": "Om Draam Dreem Draum Sah Shukraya Namaha",
                "gemstone": "Diamond (Heera)",
                "charity": "Donate white clothes, rice, or silver on Fridays",
                "fasting": "Fast on Fridays",
                "deity": "Worship Goddess Lakshmi"
            },
            "saturn": {
                "mantra": "Om Praam Preem Praum Sah Shanaye Namaha",
                "gemstone": "Blue Sapphire (Neelam)",
                "charity": "Donate black sesame, iron, or oil on Saturdays",
                "fasting": "Fast on Saturdays",
                "deity": "Worship Lord Shani or Hanuman"
            },
            "rahu": {
                "mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namaha",
                "gemstone": "Hessonite (Gomed)",
                "charity": "Donate mustard oil, black clothes on Saturdays",
                "fasting": "Fast on Saturdays",
                "deity": "Worship Goddess Durga"
            },
            "ketu": {
                "mantra": "Om Sraam Sreem Sraum Sah Ketave Namaha",
                "gemstone": "Cat's Eye (Lehsunia)",
                "charity": "Donate sesame, blankets on Tuesdays",
                "fasting": "Fast on Tuesdays",
                "deity": "Worship Lord Ganesha"
            }
        }
        
        for weak_planet in weak_planets[:3]:  # Top 3 weak planets
            planet = weak_planet['planet']
            dignity = weak_planet['dignity']
            house = weak_planet['house']
            
            if planet in classical_remedies:
                remedies = classical_remedies[planet]
                
                remedy_analysis = []
                remedy_analysis.append(f"{planet.title()} Remedies ({dignity} in {house}th house):")
                remedy_analysis.append(f"Primary Mantra: {remedies['mantra']} (108 times daily)")
                remedy_analysis.append(f"Gemstone: {remedies['gemstone']} (consult qualified astrologer)")
                remedy_analysis.append(f"Charity: {remedies['charity']}")
                remedy_analysis.append(f"Spiritual Practice: {remedies['deity']}")
                
                content_parts.append(" ".join(remedy_analysis))
                supporting_factors.append(f"{planet.title()} remedies for {dignity} condition")
        
        # General recommendations
        content_parts.append("\nGeneral Recommendations:")
        content_parts.append("• Daily meditation and yoga for overall planetary harmony")
        content_parts.append("• Regular charity and service to strengthen benefic influences")
        content_parts.append("• Consistent spiritual practices based on your tradition")
        content_parts.append("• Consult qualified astrologer before wearing gemstones")
        
        return CommentarySection(
            title="Remedial Measures",
            content="\n\n".join(content_parts),
            confidence=0.90,
            supporting_factors=supporting_factors
        )
    
    def _identify_chart_emphasis(self, positions: Dict[str, Any]) -> str:
        """Identify the main emphasis of the chart based on planetary distributions."""
        
        house_counts = {}
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
            house = data.get('house', 1)
            house_counts[house] = house_counts.get(house, 0) + 1
        
        # Find houses with multiple planets (stelliums)
        emphasized_houses = [house for house, count in house_counts.items() if count >= 2]
        
        if emphasized_houses:
            house_themes = []
            for house in emphasized_houses[:2]:  # Top 2 emphasized houses
                signification = self.house_significations.get(house, f"{house}th house themes")
                house_themes.append(f"{house}th house ({signification})")
            return ", ".join(house_themes)
        
        return "balanced distribution across life areas"
    
    def _calculate_overall_confidence(self, positions: Dict[str, Any]) -> float:
        """Calculate overall confidence based on data completeness."""
        
        confidence = 0.85  # Base confidence for classical analysis
        
        # Check data completeness
        complete_planets = 0
        total_planets = 0
        
        for planet, data in positions.items():
            if planet == 'lagna':
                continue
            total_planets += 1
            if all(key in data for key in ['house', 'dignity', 'strength_points']):
                complete_planets += 1
        
        if total_planets > 0:
            completeness_factor = complete_planets / total_planets
            confidence += (completeness_factor - 0.5) * 0.3  # Adjust based on completeness
        
        return min(max(confidence, 0.5), 1.0)  # Keep between 0.5 and 1.0