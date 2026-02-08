"""
Constants for festival calculations.
"""

# Lunar months in order
LUNAR_MONTHS = [
    "Magha", "Phalguna", "Chaitra", "Vaishakha",
    "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwin", "Kartik", "Margashirsha", "Pausha"
]

# Month number to lunar name mapping
MONTH_TO_LUNAR = {
    1: "Magha", 2: "Phalguna", 3: "Chaitra", 4: "Vaishakha",
    5: "Jyeshtha", 6: "Ashadha", 7: "Shravana", 8: "Bhadrapada",
    9: "Ashwin", 10: "Kartik", 11: "Margashirsha", 12: "Pausha",
}

# 27 Nakshatras
NAKSHATRA_LIST = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Planet to deity mapping (for Ishta Devata)
PLANET_DEITY_MAP = {
    "Sun": ["Surya", "Vishnu", "Rama"],
    "Moon": ["Chandra", "Shiva", "Parvati"],
    "Mars": ["Hanuman", "Kartikeya"],
    "Mercury": ["Vishnu", "Krishna"],
    "Jupiter": ["Brihaspati", "Vishnu", "Dattatreya"],
    "Venus": ["Lakshmi", "Durga"],
    "Saturn": ["Shani", "Hanuman", "Vishnu"],
    "Rahu": ["Durga", "Kali"],
    "Ketu": ["Ganesha", "Vishnu"],
}

# Deity to festivals mapping
DEITY_FESTIVALS = {
    "Shiva": ["maha_shivaratri", "pradosh", "shravan_somvar"],
    "Vishnu": ["ekadashi", "ram_navami", "janmashtami", "vaikuntha_ekadashi"],
    "Krishna": ["janmashtami", "holi", "govardhan_puja"],
    "Rama": ["ram_navami", "dussehra", "diwali"],
    "Ganesha": ["ganesh_chaturthi", "sankashti_chaturthi"],
    "Durga": ["navratri", "durga_puja", "dussehra"],
    "Lakshmi": ["diwali", "sharad_purnima"],
    "Hanuman": ["hanuman_jayanti"],
    "Surya": ["makar_sankranti", "chhath_puja", "ratha_saptami"],
}
