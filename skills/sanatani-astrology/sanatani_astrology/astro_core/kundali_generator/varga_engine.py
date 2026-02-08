"""
Varga (Divisional Chart) Calculation Engine.

This module provides logic for calculating specific qualities and details
for higher divisional charts, specifically D16 (Shodasamsa) and D60 (Shashtiamsa).
"""

from typing import Dict, Any, List, Optional

class VargaEngine:
    """
    Engine for detailed Divisional Chart calculations and quality assessment.
    """

    # D16 (Shodasamsa) Deities
    # Benefic: Brahma, Vishnu, Shiva
    # Malefic: Surya (Sun is Krura/Malefic in this context)
    D16_DEITIES = ["Brahma", "Vishnu", "Shiva", "Surya"]
    
    # D60 (Shashtiamsa) Names and Qualities (BPHS Ch. 6)
    # 1=Benefic (Shubha), 0=Malefic (Papa)
    D60_MAPPING = [
        ("Ghora", 0), ("Rakshasa", 0), ("Deva", 1), ("Kubera", 1), ("Yaksha", 0), 
        ("Kinnara", 1), ("Bhrashta", 0), ("Kulaghna", 0), ("Garala", 0), ("Vahni", 0),
        ("Maya", 0), ("Purishaka", 0), ("Apampathi", 1), ("Marutwan", 1), ("Kaala", 0),
        ("Sarpa", 0), ("Amrita", 1), ("Indu", 1), ("Mridu", 1), ("Komala", 1),
        ("Heramba", 1), ("Brahma", 1), ("Vishnu", 1), ("Maheswara", 1), ("Deva", 1),
        ("Ardra", 1), ("Kalinasa", 1), ("Kshitisa", 1), ("Kamalakara", 1), ("Gulika", 0),
        ("Mrityu", 0), ("Kaala", 0), ("Davagni", 0), ("Ghora", 0), ("Yama", 0),
        ("Kantaka", 0), ("Sudha", 1), ("Amrita", 1), ("Purnachandra", 1), ("Vishadagdha", 0),
        ("Kulanasa", 0), ("Vamsakshaya", 0), ("Utpata", 0), ("Kaala", 0), ("Saumya", 1),
        ("Komala", 1), ("Sheetala", 1), ("Karaladamshtra", 0), ("Chandramukha", 1), ("Praveena", 1),
        ("Kaalpavaka", 0), ("Dandayudha", 0), ("Nirmala", 1), ("Saumya", 1), ("Krura", 0),
        ("Atisheetala", 1), ("Amrita", 1), ("Payodhi", 1), ("Bhramana", 0), ("Chandrarekha", 1)
    ]

    @staticmethod
    def calculate_d16_quality(degree_in_sign: float, rasi_index: int) -> Dict[str, Any]:
        """
        Calculate Shodasamsa (D16) quality.
        16 parts of 1° 52' 30" (1.875 degrees).
        
        Odd Signs: Brahma, Vishnu, Shiva, Surya... (Repeating 1,2,3,4)
        Even Signs: Reverse of Odd? No, BPHS says "In even signs these are in the reverse order".
                    The cycle is 4 deities. 
                    Odd: 1=Brahma, 2=Vishnu, 3=Shiva, 4=Surya.
                    Even: 1=Surya, 2=Shiva, 3=Vishnu, 4=Brahma.
        """
        part_span = 1.875
        part_index = int(degree_in_sign / part_span) # 0-15
        if part_index >= 16: part_index = 15 # Cap at 15 for 30.0 deg
        
        # Determine deity index (0-3)
        cycle_index = part_index % 4
        
        # Check if sign is Odd (Aries=0, Gemini=2...) or Even (Taurus=1...)
        # Rasi index 0 is Odd (1st sign). 
        is_odd_sign = (rasi_index % 2) == 0 
        
        if is_odd_sign:
            deity_idx = cycle_index
        else:
            # Reverse order: 0->3 (Surya), 1->2 (Shiva), 2->1 (Vishnu), 3->0 (Brahma)
            deity_idx = 3 - cycle_index
            
        deity_name = VargaEngine.D16_DEITIES[deity_idx]
        
        # Quality: Surya is considered Malefic (Krura), others Benefic (Shubha) in this context
        # usually. Though Surya is Sattvic, in Kalamsa context usually only the Trinity are the pure benefics.
        # Rule says "benefic shodasamsa".
        is_benefic = (deity_name != "Surya")
        
        return {
            "deity": deity_name,
            "quality": "benefic" if is_benefic else "malefic"
        }

    @staticmethod
    def calculate_d60_quality(degree_in_sign: float, rasi_index: int) -> Dict[str, Any]:
        """
        Calculate Shashtiamsa (D60) quality.
        60 parts of 0° 30' (0.5 degrees).
        
        Odd Signs: Direct order 1-60.
        Even Signs: Reverse order 60-1.
        """
        part_span = 0.5
        part_index = int(degree_in_sign / part_span) # 0-59
        if part_index >= 60: part_index = 59
        
        is_odd_sign = (rasi_index % 2) == 0
        
        if is_odd_sign:
            final_index = part_index
        else:
            # Reverse: 0->59 (60th), 59->0 (1st)
            final_index = 59 - part_index
            
        name, status_code = VargaEngine.D60_MAPPING[final_index]
        
        return {
            "name": name,
            "quality": "benefic" if status_code == 1 else "malefic"
        }
