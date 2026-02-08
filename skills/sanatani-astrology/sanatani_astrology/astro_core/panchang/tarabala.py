"""
Tarabala Calculator - Star Compatibility

Tarabala determines the favorability of a nakshatra based on
the person's birth nakshatra. The 27 nakshatras are divided
into 9 groups of 3, cycling from the birth star.

The 9 Tara positions repeat 3 times through the 27 nakshatras.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from .constants import (
    TARABALA_NAMES,
    TARABALA_FAVORABILITY,
    NAKSHATRA_NAMES,
)

logger = logging.getLogger(__name__)


@dataclass
class TarabalaInfo:
    """Information about tarabala for a given day."""
    tara_index: int          # 0-8 (which of the 9 taras)
    tara_name: str           # Name of the tara
    cycle: int               # Which cycle (1, 2, or 3)
    birth_nakshatra: int     # Birth nakshatra index (0-26)
    birth_nakshatra_name: str
    current_nakshatra: int   # Current nakshatra index (0-26)
    current_nakshatra_name: str
    is_favorable: bool       # Generally good or bad
    is_critical_avoid: bool  # Naidhana (4th tara) - death star
    favorability: float      # 0.0-1.0
    description: str         # What this tara means


# Detailed descriptions for each tara
# Aligned with classical Vedic texts - 5th tara (index 4) is Naidhana (death star)
TARA_DESCRIPTIONS = {
    0: "Janma (Birth Star) - Neutral to mixed results. The Moon returns to your birth "
       "nakshatra. Can be introspective. Avoid major new beginnings, but personal "
       "matters and routine activities are fine.",
    1: "Sampat (Wealth) - Highly auspicious. Excellent for financial matters, "
       "new ventures, investments, business deals, and material gains.",
    2: "Vipat (Danger) - Inauspicious. Avoid important activities, long travel, "
       "and new beginnings. Risk of obstacles, losses, and setbacks.",
    3: "Kshema (Well-being) - Auspicious. Good for health matters, peace, "
       "stability, family activities, and maintaining existing ventures.",
    4: "Naidhana (Death Star) - CRITICAL AVOID. The most inauspicious tara. "
       "Strongly avoid all important activities, surgeries, travel, contracts, "
       "and major decisions. Associated with severe obstacles and danger.",
    5: "Sadhaka (Achievement) - Highly auspicious. Excellent for accomplishing goals, "
       "learning, skill development, examinations, and spiritual practices.",
    6: "Vadha (Destruction) - Inauspicious. Avoid conflicts, legal matters, "
       "confrontations, and activities requiring precision. Risk of harm and losses.",
    7: "Mitra (Friend) - Auspicious. Good for social activities, partnerships, "
       "friendships, networking, and collaborative ventures.",
    8: "Parama Mitra (Best Friend) - Most auspicious tara. Excellent for all "
       "activities, especially relationships, major decisions, ceremonies, and ventures.",
}


class TarabalaCalculator:
    """
    Calculator for Tarabala (Star Compatibility).

    Tarabala creates a personalized overlay on the daily nakshatra,
    showing how favorable a day is based on the person's birth star.

    The 9 Taras (0-indexed):
    0. Janma (Birth) - Neutral/Mixed
    1. Sampat (Wealth) - Excellent
    2. Vipat (Danger) - Bad (avoid)
    3. Kshema (Well-being) - Good
    4. Naidhana (Death Star) - CRITICAL AVOID
    5. Sadhaka (Achievement) - Excellent
    6. Vadha (Destruction) - Bad (avoid)
    7. Mitra (Friend) - Good
    8. Parama Mitra (Best Friend) - Excellent

    Reference: Muhurta Chintamani, Brihat Samhita
    """

    def calculate(
        self,
        birth_nakshatra: int,
        current_nakshatra: int
    ) -> TarabalaInfo:
        """
        Calculate tarabala from birth and current nakshatras.

        Args:
            birth_nakshatra: Birth nakshatra index (0-26)
            current_nakshatra: Current nakshatra index (0-26)

        Returns:
            TarabalaInfo with complete tarabala details
        """
        # Validate inputs
        birth_nakshatra = birth_nakshatra % 27
        current_nakshatra = current_nakshatra % 27

        # Calculate position from birth nakshatra (0-26)
        # The birth nakshatra itself is position 0 (Janma tara)
        position_from_birth = (current_nakshatra - birth_nakshatra) % 27

        # Calculate tara index (0-8) and cycle (1-3)
        tara_index = position_from_birth % 9
        cycle = (position_from_birth // 9) + 1

        # Get tara details
        tara_name = TARABALA_NAMES[tara_index]
        favorability = TARABALA_FAVORABILITY.get(tara_index, 0.5)

        # Determine favorability
        is_favorable = favorability >= 0.6
        is_critical_avoid = tara_index == 4  # Naidhana (Death Star) - 5th tara position

        # Get description
        description = TARA_DESCRIPTIONS.get(tara_index, "")

        return TarabalaInfo(
            tara_index=tara_index,
            tara_name=tara_name,
            cycle=cycle,
            birth_nakshatra=birth_nakshatra,
            birth_nakshatra_name=NAKSHATRA_NAMES[birth_nakshatra],
            current_nakshatra=current_nakshatra,
            current_nakshatra_name=NAKSHATRA_NAMES[current_nakshatra],
            is_favorable=is_favorable,
            is_critical_avoid=is_critical_avoid,
            favorability=favorability,
            description=description
        )

    def get_favorable_days(
        self,
        birth_nakshatra: int,
        start_nakshatra: int,
        num_nakshatras: int = 27
    ) -> list:
        """
        Get list of favorable nakshatra positions from birth star.

        Args:
            birth_nakshatra: Birth nakshatra index (0-26)
            start_nakshatra: Starting nakshatra to check from
            num_nakshatras: Number of nakshatras to check

        Returns:
            List of TarabalaInfo for favorable days
        """
        favorable = []

        for i in range(num_nakshatras):
            current = (start_nakshatra + i) % 27
            tara_info = self.calculate(birth_nakshatra, current)

            if tara_info.is_favorable:
                favorable.append(tara_info)

        return favorable

    def get_avoid_days(
        self,
        birth_nakshatra: int,
        start_nakshatra: int,
        num_nakshatras: int = 27
    ) -> list:
        """
        Get list of nakshatras to avoid based on birth star.

        Args:
            birth_nakshatra: Birth nakshatra index (0-26)
            start_nakshatra: Starting nakshatra to check from
            num_nakshatras: Number of nakshatras to check

        Returns:
            List of TarabalaInfo for days to avoid
        """
        avoid = []

        for i in range(num_nakshatras):
            current = (start_nakshatra + i) % 27
            tara_info = self.calculate(birth_nakshatra, current)

            if not tara_info.is_favorable:
                avoid.append(tara_info)

        return avoid

    def get_naidhana_nakshatras(self, birth_nakshatra: int) -> list:
        """
        Get the Naidhana (most inauspicious) nakshatras for a birth star.

        Naidhana (5th tara) occurs at positions 4, 13, and 22 from birth.

        Args:
            birth_nakshatra: Birth nakshatra index (0-26)

        Returns:
            List of nakshatra indices that are Naidhana
        """
        naidhana = []
        for offset in [4, 13, 22]:  # 5th position in each cycle
            naidhana_nak = (birth_nakshatra + offset) % 27
            naidhana.append(naidhana_nak)
        return naidhana

    def get_best_nakshatras(self, birth_nakshatra: int) -> list:
        """
        Get the most auspicious nakshatras for a birth star.

        Returns Sampat (2nd), Kshema (4th), Sadhaka (6th),
        Mitra (8th), and Parama Mitra (9th) positions.

        Args:
            birth_nakshatra: Birth nakshatra index (0-26)

        Returns:
            List of (nakshatra_index, tara_name) tuples
        """
        best = []
        favorable_taras = [1, 3, 5, 7, 8]  # Sampat, Kshema, Sadhaka, Mitra, Parama Mitra

        for cycle in range(3):
            for tara in favorable_taras:
                offset = (cycle * 9) + tara
                if offset < 27:
                    nak = (birth_nakshatra + offset) % 27
                    best.append((nak, TARABALA_NAMES[tara]))

        return best

    def calculate_day_quality(
        self,
        birth_nakshatra: int,
        current_nakshatra: int
    ) -> str:
        """
        Get simple quality rating for the day.

        Args:
            birth_nakshatra: Birth nakshatra index
            current_nakshatra: Current nakshatra index

        Returns:
            Quality string: "excellent", "good", "neutral", "avoid", "critical_avoid"
        """
        tara_info = self.calculate(birth_nakshatra, current_nakshatra)

        if tara_info.is_critical_avoid:
            return "critical_avoid"
        elif tara_info.favorability >= 0.8:
            return "excellent"
        elif tara_info.favorability >= 0.6:
            return "good"
        elif tara_info.favorability >= 0.4:
            return "neutral"
        else:
            return "avoid"


# Singleton instance
_calculator: Optional[TarabalaCalculator] = None


def get_tarabala_calculator() -> TarabalaCalculator:
    """Get singleton TarabalaCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = TarabalaCalculator()
    return _calculator


def calculate_tarabala(
    birth_nakshatra: int,
    current_nakshatra: int
) -> TarabalaInfo:
    """
    Convenience function to calculate tarabala.

    Args:
        birth_nakshatra: Birth nakshatra index (0-26)
        current_nakshatra: Current nakshatra index (0-26)

    Returns:
        TarabalaInfo object
    """
    return get_tarabala_calculator().calculate(
        birth_nakshatra,
        current_nakshatra
    )
