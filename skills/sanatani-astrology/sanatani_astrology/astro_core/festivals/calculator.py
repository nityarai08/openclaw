"""
Festival Calculator

Calculates festival dates based on YAML configuration and panchang data.
"""

from dataclasses import dataclass, field
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from .constants import MONTH_TO_LUNAR
from ..panchang import get_panchang_calculator
from ..panchang.constants import LUNAR_MONTH_NAMES


@dataclass
class FestivalDate:
    """A festival occurrence on a specific date."""
    id: str
    name: str
    category: str
    date: date
    end_date: Optional[date] = None
    duration_days: int = 1
    ruling_deities: List[str] = field(default_factory=list)
    ruling_planets: List[str] = field(default_factory=list)
    tithi: Optional[str] = None
    nakshatra: Optional[str] = None
    significance: Optional[str] = None
    puja_elements: List[str] = field(default_factory=list)
    fasting: Dict[str, Any] = field(default_factory=dict)
    sub_festivals: List[Dict[str, Any]] = field(default_factory=list)
    regional_names: Optional[Dict[str, str]] = None


@dataclass
class PanchangDayInfo:
    """Panchang snapshot for matching festival rules."""
    date: date
    tithi_number: int
    paksha: str
    lunar_month: Optional[str]
    nakshatra: str
    sun_rasi: int
    tithi_number_sunset: Optional[int] = None
    tithi_number_midnight: Optional[int] = None
    nakshatra_sunset: Optional[str] = None
    nakshatra_midnight: Optional[str] = None


class FestivalCalculator:
    """
    Calculates festival dates from YAML configuration.

    Uses panchang data for tithi/nakshatra-based festivals and falls back
    to approximate dates when panchang is unavailable.
    """

    def __init__(
        self,
        config_path: Path,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        timezone_offset: float = 5.5,
        timezone_name: str = "IST",
    ):
        """
        Initialize calculator with config path.

        Args:
            config_path: Path to festival config directory
            latitude: Reference latitude for sunrise/tithi calculations
            longitude: Reference longitude for sunrise/tithi calculations
            timezone_offset: Reference timezone offset
            timezone_name: Timezone name for display
        """
        self.config_path = config_path
        self.latitude = latitude
        self.longitude = longitude
        self.timezone_offset = timezone_offset
        self.timezone_name = timezone_name

        self._config_data = self._load_festival_config()
        self._master_festivals = self._config_data.get("festivals", {})
        self._ekadashi_names = self._config_data.get("ekadashi_names", {})
        self._recurring = self._load_recurring_festivals()

        self._panchang_calculator = None
        self._panchang_cache: Dict[int, List[PanchangDayInfo]] = {}
        self._panchang_available = True

    def _load_festival_config(self) -> Dict[str, Any]:
        """Load full festival config YAML."""
        master_file = self.config_path / "master_festivals.yaml"
        if master_file.exists():
            with open(master_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_recurring_festivals(self) -> Dict[str, Any]:
        """Load recurring festival patterns (fallback mode)."""
        return {
            "ekadashi": {
                "name": "Ekadashi",
                "frequency": "twice_monthly",
                "ruling_deities": ["Vishnu"],
                "category": "recurring",
                "tithi": "Ekadashi",
                "fasting": {"recommended": True, "type": "ekadashi_vrat"},
                "significance": (
                    "Ekadashi is the 11th lunar day, sacred to Lord Vishnu.\n"
                    "Fasting on Ekadashi is said to cleanse sins and grant moksha.\n"
                ),
            },
            "pradosh": {
                "name": "Pradosh Vrat",
                "frequency": "twice_monthly",
                "ruling_deities": ["Shiva"],
                "category": "recurring",
                "tithi": "Trayodashi",
                "fasting": {"recommended": True, "type": "until_sunset"},
            },
            "purnima": {
                "name": "Purnima",
                "frequency": "monthly",
                "ruling_deities": ["Chandra", "Vishnu"],
                "category": "recurring",
                "tithi": "Purnima",
            },
            "amavasya": {
                "name": "Amavasya",
                "frequency": "monthly",
                "ruling_deities": ["Pitru", "Shani"],
                "category": "recurring",
                "tithi": "Amavasya",
            },
            "sankashti_chaturthi": {
                "name": "Sankashti Chaturthi",
                "frequency": "monthly",
                "ruling_deities": ["Ganesha"],
                "category": "recurring",
                "tithi": "Chaturthi",
                "fasting": {"recommended": True, "type": "until_moonrise"},
            },
        }

    def _get_panchang_calculator(self):
        """Lazy-load panchang calculator."""
        if self._panchang_calculator is None:
            self._panchang_calculator = get_panchang_calculator()
        return self._panchang_calculator

    def _get_panchang_days(self, year: int) -> List[PanchangDayInfo]:
        """Compute daily panchang indices for a year (cached)."""
        if year in self._panchang_cache:
            return self._panchang_cache[year]
        if not self._panchang_available:
            return []

        try:
            calc = self._get_panchang_calculator()
            days: List[PanchangDayInfo] = []
            current = date(year, 1, 1)

            while current.year == year:
                sun_times = calc._sun_times.calculate(
                    current, self.latitude, self.longitude, self.timezone_offset
                )
                sunrise_dt = sun_times.sunrise
                sunset_dt = sun_times.sunset
                midnight_dt = datetime.combine(current, datetime.min.time())

                global_panchang = calc.calculate_global(
                    sunrise_dt,
                    self.latitude,
                    self.longitude,
                    timezone_offset=self.timezone_offset,
                    timezone_name=self.timezone_name,
                    include_hora_sequence=False,
                    include_inauspicious=False,
                )
                sunset_panchang = calc.calculate_global(
                    sunset_dt,
                    self.latitude,
                    self.longitude,
                    timezone_offset=self.timezone_offset,
                    timezone_name=self.timezone_name,
                    include_hora_sequence=False,
                    include_inauspicious=False,
                )
                midnight_panchang = calc.calculate_global(
                    midnight_dt,
                    self.latitude,
                    self.longitude,
                    timezone_offset=self.timezone_offset,
                    timezone_name=self.timezone_name,
                    include_hora_sequence=False,
                    include_inauspicious=False,
                )

                sun_longitude, _, _, _ = calc._get_planetary_data(
                    sunrise_dt, self.latitude, self.longitude, self.timezone_offset
                )
                sun_rasi = int(sun_longitude / 30) % 12
                lunar_month = self._normalize_lunar_month_name(global_panchang.lunar_month)
                if not lunar_month:
                    lunar_month = self._normalize_lunar_month_name(LUNAR_MONTH_NAMES[sun_rasi])

                days.append(
                    PanchangDayInfo(
                        date=current,
                        tithi_number=global_panchang.tithi.number,
                        paksha=self._paksha_key_from_tithi(global_panchang.tithi.number),
                        lunar_month=lunar_month,
                        nakshatra=self._normalize_nakshatra_name(global_panchang.nakshatra.name),
                        tithi_number_sunset=sunset_panchang.tithi.number,
                        tithi_number_midnight=midnight_panchang.tithi.number,
                        nakshatra_sunset=self._normalize_nakshatra_name(
                            sunset_panchang.nakshatra.name
                        ),
                        nakshatra_midnight=self._normalize_nakshatra_name(
                            midnight_panchang.nakshatra.name
                        ),
                        sun_rasi=sun_rasi,
                    )
                )

                current += timedelta(days=1)

            self._panchang_cache[year] = days
            return days
        except Exception:
            self._panchang_available = False
            return []

    def _normalize_lunar_month_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize lunar month name to config format."""
        if not name:
            return None
        normalized = name.strip().lower()
        aliases = {
            "ashwina": "ashwin",
            "kartika": "kartik",
            "pausha": "pausha",
            "margashirsha": "margashirsha",
            "vaishakha": "vaishakha",
        }
        return aliases.get(normalized, normalized)

    def _format_lunar_month_name(self, name: str) -> str:
        """Format lunar month name for display."""
        return " ".join(part.capitalize() for part in name.replace("_", " ").split())

    def _normalize_nakshatra_name(self, name: str) -> str:
        """Normalize nakshatra name to config key format."""
        cleaned = name.strip().lower().replace("-", " ").replace("_", " ")
        return "_".join(cleaned.split())

    def _normalize_paksha_key(self, paksha: Optional[str]) -> Optional[str]:
        """Normalize paksha value to 'shukla' or 'krishna'."""
        if not paksha:
            return None
        paksha_lower = paksha.strip().lower()
        if paksha_lower.startswith("shukla"):
            return "shukla"
        if paksha_lower.startswith("krishna"):
            return "krishna"
        return paksha_lower

    def _normalize_tithi_time(self, value: Optional[str]) -> str:
        """Normalize tithi time selector."""
        if not value:
            return "sunrise"
        cleaned = value.strip().lower()
        if cleaned in ("sunset", "dusk", "evening"):
            return "sunset"
        if cleaned in ("midnight", "night"):
            return "midnight"
        return "sunrise"

    def _get_day_tithi_number(self, day: PanchangDayInfo, tithi_time: str) -> int:
        """Pick tithi number based on configured time."""
        if tithi_time == "sunset" and day.tithi_number_sunset:
            return day.tithi_number_sunset
        if tithi_time == "midnight" and day.tithi_number_midnight:
            return day.tithi_number_midnight
        return day.tithi_number

    def _get_day_nakshatra(self, day: PanchangDayInfo, tithi_time: str) -> str:
        """Pick nakshatra based on configured time."""
        if tithi_time == "sunset" and day.nakshatra_sunset:
            return day.nakshatra_sunset
        if tithi_time == "midnight" and day.nakshatra_midnight:
            return day.nakshatra_midnight
        return day.nakshatra

    def _paksha_key_from_tithi(self, tithi_number: int) -> str:
        """Derive paksha key from tithi number."""
        return "shukla" if tithi_number <= 15 else "krishna"

    def _expand_tithi_targets(self, tithi: Any, paksha: Optional[str]) -> List[int]:
        """Expand a tithi into matching tithi numbers."""
        if tithi is None:
            return []
        if isinstance(tithi, str):
            try:
                tithi_num = int(tithi)
            except ValueError:
                return []
        else:
            tithi_num = int(tithi)

        if paksha:
            if paksha == "krishna" and tithi_num <= 15:
                return [tithi_num + 15]
            return [tithi_num]

        if tithi_num in (15, 30):
            return [tithi_num]
        if 1 <= tithi_num <= 15:
            return [tithi_num, tithi_num + 15]
        return [tithi_num]

    def calculate_year(self, year: int) -> List[FestivalDate]:
        """
        Calculate all festivals for a year.

        Args:
            year: Year to calculate

        Returns:
            List of FestivalDate sorted by date
        """
        festivals: List[FestivalDate] = []

        for fest_id, fest_data in self._master_festivals.items():
            festivals.extend(self._calculate_festival_dates(fest_id, fest_data, year))

        if not self._panchang_available:
            for month in range(1, 13):
                festivals.extend(self._generate_recurring(year, month))

        festivals.sort(key=lambda f: f.date)
        return festivals

    def calculate_month(self, year: int, month: int) -> List[FestivalDate]:
        """
        Calculate festivals for a specific month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            List of FestivalDate for that month
        """
        all_festivals = self.calculate_year(year)
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        return [
            f for f in all_festivals
            if f.date <= end_date and (f.end_date or f.date) >= start_date
        ]

    def get_upcoming(self, from_date: date, days: int = 30) -> List[FestivalDate]:
        """
        Get upcoming festivals from a date.

        Args:
            from_date: Start date
            days: Number of days to look ahead

        Returns:
            List of FestivalDate in date range
        """
        end_date = from_date + timedelta(days=days)

        festivals = []
        for year in range(from_date.year, end_date.year + 1):
            festivals.extend(self.calculate_year(year))

        return [f for f in festivals if from_date <= f.date <= end_date]

    def _calculate_festival_dates(
        self, fest_id: str, fest_data: Dict[str, Any], year: int
    ) -> List[FestivalDate]:
        """Calculate one or more dates for a festival in a given year."""
        dates_by_year = fest_data.get("dates", {})
        if year in dates_by_year:
            year_date = dates_by_year[year]
            try:
                fest_date = date(year, year_date.get("month"), year_date.get("day"))
            except (TypeError, ValueError):
                return []
            return [self._build_festival_date(fest_id, fest_data, fest_date)]

        calc = fest_data.get("calculation", {})
        calc_type = calc.get("type", "tithi")

        if self._panchang_available:
            if calc_type == "solar":
                matches = self._calculate_solar_festival_dates(fest_id, fest_data, year)
            elif calc_type == "nakshatra":
                matches = self._calculate_nakshatra_festival_dates(fest_id, fest_data, year)
            else:
                matches = self._calculate_tithi_festival_dates(fest_id, fest_data, year)

            if matches:
                return matches

        fallback = self._calculate_festival_date_approx(fest_id, fest_data, year)
        return [fallback] if fallback else []

    def _calculate_tithi_festival_dates(
        self, fest_id: str, fest_data: Dict[str, Any], year: int
    ) -> List[FestivalDate]:
        """Calculate tithi-based festival dates using panchang."""
        calc = fest_data.get("calculation", {})
        tithi = calc.get("tithi") or fest_data.get("tithi")
        if tithi is None:
            return []

        paksha = self._normalize_paksha_key(calc.get("paksha"))
        month = self._normalize_lunar_month_name(calc.get("month") or fest_data.get("lunar_month"))
        tithi_time = self._normalize_tithi_time(
            calc.get("tithi_time") or fest_data.get("tithi_time")
        )
        nakshatra = calc.get("nakshatra") or fest_data.get("nakshatra")
        if nakshatra:
            nakshatra = self._normalize_nakshatra_name(nakshatra)
        nakshatra_condition_raw = (
            calc.get("nakshatra_condition") or fest_data.get("nakshatra_condition")
        )
        nakshatra_condition = None
        if nakshatra_condition_raw:
            if isinstance(nakshatra_condition_raw, (list, tuple, set)):
                nakshatra_condition = {
                    self._normalize_nakshatra_name(str(item))
                    for item in nakshatra_condition_raw
                }
            else:
                nakshatra_condition = {
                    self._normalize_nakshatra_name(str(nakshatra_condition_raw))
                }

        target_tithis = self._expand_tithi_targets(tithi, paksha)
        days = self._get_panchang_days(year)

        def collect_matches(time_key: str) -> List[PanchangDayInfo]:
            collected: List[PanchangDayInfo] = []
            for day in days:
                if month and day.lunar_month != month:
                    continue
                day_tithi = self._get_day_tithi_number(day, time_key)
                day_paksha = self._paksha_key_from_tithi(day_tithi)
                if paksha and day_paksha != paksha:
                    continue
                if day_tithi not in target_tithis:
                    continue
                day_nakshatra = self._get_day_nakshatra(day, time_key)
                if nakshatra and day_nakshatra != nakshatra:
                    continue
                if nakshatra_condition and day_nakshatra not in nakshatra_condition:
                    continue
                collected.append(day)
            return collected

        matches = collect_matches(tithi_time)
        if not matches and tithi_time == "sunrise":
            for fallback_time in ("midnight", "sunset"):
                matches = collect_matches(fallback_time)
                if matches:
                    break

        if not matches:
            return []

        if month:
            return [
                self._build_festival_date(fest_id, fest_data, day.date)
                for day in matches
            ]

        return [self._build_recurring_festival_date(fest_id, fest_data, day) for day in matches]

    def _calculate_nakshatra_festival_dates(
        self, fest_id: str, fest_data: Dict[str, Any], year: int
    ) -> List[FestivalDate]:
        """Calculate nakshatra-based festival dates using panchang."""
        calc = fest_data.get("calculation", {})
        month = self._normalize_lunar_month_name(calc.get("month") or fest_data.get("lunar_month"))
        nakshatra = calc.get("nakshatra") or fest_data.get("nakshatra")
        if not nakshatra:
            return []

        target_nakshatra = self._normalize_nakshatra_name(nakshatra)
        days = self._get_panchang_days(year)

        matches = [
            day for day in days
            if day.nakshatra == target_nakshatra
            and (not month or day.lunar_month == month)
        ]

        if not matches:
            return []

        return [
            self._build_festival_date(fest_id, fest_data, day.date)
            for day in matches
        ]

    def _calculate_solar_festival_dates(
        self, fest_id: str, fest_data: Dict[str, Any], year: int
    ) -> List[FestivalDate]:
        """Calculate solar festivals (sun ingress events)."""
        fallback = self._calculate_festival_date_approx(fest_id, fest_data, year)
        return [fallback] if fallback else []

    def _build_recurring_festival_date(
        self,
        fest_id: str,
        fest_data: Dict[str, Any],
        day: PanchangDayInfo,
    ) -> FestivalDate:
        """Build festival date for recurring festivals with variants."""
        variant_id = None
        name_override = None
        significance_override = None

        if fest_id == "ekadashi":
            name_override = self._get_ekadashi_name(day.lunar_month, day.paksha)

        variant = self._match_variant(fest_data.get("special_variants", []), day)
        if variant:
            variant_id = variant.get("id")
            name_override = variant.get("name", name_override)
            significance_override = variant.get("significance")

        if fest_id in ("purnima", "amavasya") and day.lunar_month:
            suffix = "Purnima" if fest_id == "purnima" else "Amavasya"
            name_override = f"{self._format_lunar_month_name(day.lunar_month)} {suffix}"

        return self._build_festival_date(
            variant_id or fest_id,
            fest_data,
            day.date,
            name_override=name_override,
            significance_override=significance_override,
        )

    def _get_ekadashi_name(self, lunar_month: Optional[str], paksha: str) -> Optional[str]:
        """Get ekadashi name for a lunar month/paksha."""
        if not lunar_month:
            return None
        month_key = self._normalize_lunar_month_name(lunar_month)
        month_data = self._ekadashi_names.get(month_key, {})
        return month_data.get(paksha)

    def _match_variant(
        self, variants: List[Dict[str, Any]], day: PanchangDayInfo
    ) -> Optional[Dict[str, Any]]:
        """Find special variant matching this day."""
        for variant in variants:
            month = self._normalize_lunar_month_name(variant.get("month"))
            if month and month != day.lunar_month:
                continue

            paksha = self._normalize_paksha_key(variant.get("paksha"))
            if paksha and paksha != day.paksha:
                continue

            weekday = variant.get("weekday")
            if weekday and self._weekday_to_index(weekday) != day.date.weekday():
                continue

            return variant
        return None

    def _weekday_to_index(self, weekday: str) -> int:
        """Convert weekday string to Python weekday index."""
        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return weekday_map.get(weekday.strip().lower(), -1)

    def _build_festival_date(
        self,
        fest_id: str,
        fest_data: Dict[str, Any],
        fest_date: date,
        name_override: Optional[str] = None,
        significance_override: Optional[str] = None,
    ) -> FestivalDate:
        """Build FestivalDate from festival config and computed date."""
        duration = fest_data.get("duration_days", 1)
        end_date = None
        if duration > 1:
            end_date = fest_date + timedelta(days=duration - 1)

        calc = fest_data.get("calculation", {})
        raw_tithi = calc.get("tithi") or fest_data.get("tithi")
        tithi_name = self._tithi_number_to_name(raw_tithi)
        if not tithi_name and isinstance(raw_tithi, str):
            tithi_name = raw_tithi
        raw_nakshatra = (
            calc.get("nakshatra")
            or fest_data.get("nakshatra")
            or calc.get("nakshatra_condition")
            or fest_data.get("nakshatra_condition")
        )
        if isinstance(raw_nakshatra, (list, tuple, set)):
            raw_nakshatra = next(iter(raw_nakshatra), None)

        return FestivalDate(
            id=fest_id,
            name=name_override or fest_data.get("name", fest_id.replace("_", " ").title()),
            category=fest_data.get("category", "major"),
            date=fest_date,
            end_date=end_date,
            duration_days=duration,
            ruling_deities=fest_data.get("ruling_deities", []),
            ruling_planets=fest_data.get("ruling_planets", []),
            tithi=tithi_name,
            nakshatra=raw_nakshatra,
            significance=significance_override or fest_data.get("significance"),
            puja_elements=fest_data.get("puja_elements", []),
            fasting=fest_data.get("fasting", {}),
            sub_festivals=fest_data.get("sub_festivals", []),
            regional_names=fest_data.get("regional_names"),
        )

    def _calculate_festival_date_approx(
        self, fest_id: str, fest_data: Dict[str, Any], year: int
    ) -> Optional[FestivalDate]:
        """
        Calculate the date for a festival in a given year (fallback).

        Priority:
        1. Year-specific dates from 'dates' field
        2. approximate_date field
        3. Calculated from lunar month/tithi (approximate)
        """
        month = None
        day = None

        dates_by_year = fest_data.get("dates", {})
        if year in dates_by_year:
            year_date = dates_by_year[year]
            month = year_date.get("month")
            day = year_date.get("day")

        if not month or not day:
            approx = fest_data.get("approximate_date", {})
            month = approx.get("month")
            day = approx.get("day")

        if not month or not day:
            calc = fest_data.get("calculation", {})
            lunar_month = calc.get("month") or fest_data.get("lunar_month")
            tithi = calc.get("tithi") or fest_data.get("tithi")
            calc_type = calc.get("type", "tithi")

            if calc_type == "solar":
                event = calc.get("event", "")
                if event == "sun_enters_capricorn":
                    month, day = 1, 14
                elif event == "sun_enters_aries":
                    month, day = 4, 14
                else:
                    return None
            elif lunar_month and tithi:
                month = self._lunar_to_solar_month(lunar_month)
                day = self._tithi_to_day(tithi)
            else:
                return None

        try:
            fest_date = date(year, month, day)
        except ValueError:
            return None

        return self._build_festival_date(fest_id, fest_data, fest_date)

    def _tithi_number_to_name(self, tithi_num: Optional[int]) -> Optional[str]:
        """Convert tithi number to name."""
        if not tithi_num:
            return None
        tithi_names = {
            1: "Pratipada", 2: "Dwitiya", 3: "Tritiya", 4: "Chaturthi",
            5: "Panchami", 6: "Shashti", 7: "Saptami", 8: "Ashtami",
            9: "Navami", 10: "Dashami", 11: "Ekadashi", 12: "Dwadashi",
            13: "Trayodashi", 14: "Chaturdashi", 15: "Purnima", 30: "Amavasya",
        }
        return tithi_names.get(tithi_num)

    def _lunar_to_solar_month(self, lunar_month: str) -> int:
        """Map lunar month name to solar month number (approximate)."""
        lunar_months = {
            "magha": 2, "magh": 2,
            "phalguna": 3, "phalgun": 3,
            "chaitra": 3,
            "vaishakha": 4, "vaisakha": 4, "baisakh": 4,
            "jyeshtha": 5, "jyeshta": 5, "jeth": 5,
            "ashadha": 7, "ashadh": 7,
            "shravana": 8, "shravan": 8, "sawan": 8,
            "bhadrapada": 9, "bhadra": 9, "bhadon": 9,
            "ashwin": 10, "ashvin": 10,
            "kartik": 11, "kartika": 11,
            "margashirsha": 12, "aghan": 12,
            "pausha": 1, "paush": 1, "posh": 1,
        }
        return lunar_months.get(lunar_month.lower(), 1)

    def _tithi_to_day(self, tithi: Any) -> int:
        """Map tithi name or number to approximate day of month."""
        if isinstance(tithi, int):
            if tithi == 30:
                return 30
            if tithi == 15:
                return 15
            return min(tithi, 28)

        tithi_days = {
            "pratipada": 1, "dwitiya": 2, "tritiya": 3,
            "chaturthi": 4, "panchami": 5, "shashti": 6,
            "saptami": 7, "ashtami": 8, "navami": 9,
            "dashami": 10, "ekadashi": 11, "dwadashi": 12,
            "trayodashi": 13, "chaturdashi": 14, "purnima": 15,
            "amavasya": 30,
        }
        return tithi_days.get(str(tithi).lower(), 15)

    def _generate_recurring(self, year: int, month: int) -> List[FestivalDate]:
        """Generate recurring festivals for a month (fallback mode)."""
        festivals = []
        lunar_month = MONTH_TO_LUNAR.get(month, "")

        ekadashi_names = {
            1: ("Jaya", "Vijaya"),
            2: ("Amalaki", "Papmochani"),
            3: ("Kamada", "Varuthini"),
            4: ("Mohini", "Apara"),
            5: ("Nirjala", "Yogini"),
            6: ("Devshayani", "Kamika"),
            7: ("Putrada", "Aja"),
            8: ("Parivartini", "Indira"),
            9: ("Papankusha", "Rama"),
            10: ("Devuthani", "Utpanna"),
            11: ("Vaikuntha", "Saphala"),
            12: ("Putrada", "Shattila"),
        }

        pradosh_weekdays = {
            0: "Soma Pradosh",
            5: "Shani Pradosh",
        }

        for i, day in enumerate([11, 26]):
            try:
                fest_date = date(year, month, day)
                name_pair = ekadashi_names.get(month, ("Ekadashi", "Ekadashi"))
                name = name_pair[i] + " Ekadashi"

                fest_id = "ekadashi"
                if "Nirjala" in name:
                    fest_id = "nirjala_ekadashi"
                elif "Devshayani" in name:
                    fest_id = "devshayani_ekadashi"
                elif "Devuthani" in name:
                    fest_id = "devuthani_ekadashi"
                elif "Vaikuntha" in name:
                    fest_id = "vaikuntha_ekadashi"
                elif "Papankusha" in name:
                    fest_id = "papankusha_ekadashi"

                festivals.append(
                    FestivalDate(
                        id=fest_id,
                        name=name,
                        category="recurring",
                        date=fest_date,
                        ruling_deities=["Vishnu"],
                        tithi="Ekadashi",
                        fasting={"recommended": True, "type": "ekadashi_vrat"},
                        significance=self._recurring["ekadashi"].get("significance"),
                    )
                )
            except ValueError:
                pass

        for day in [13, 28]:
            try:
                fest_date = date(year, month, day)
                weekday = fest_date.weekday()
                name = pradosh_weekdays.get(weekday, "Pradosh Vrat")

                festivals.append(
                    FestivalDate(
                        id="pradosh",
                        name=name,
                        category="recurring",
                        date=fest_date,
                        ruling_deities=["Shiva"],
                        tithi="Trayodashi",
                        fasting={"recommended": True, "type": "until_sunset"},
                    )
                )
            except ValueError:
                pass

        try:
            last_day = monthrange(year, month)[1]
            purnima_date = date(year, month, min(15, last_day))
            amavasya_date = date(year, month, min(30, last_day))
            festivals.append(
                FestivalDate(
                    id="purnima",
                    name=f"{lunar_month} Purnima",
                    category="recurring",
                    date=purnima_date,
                    ruling_deities=["Chandra", "Vishnu"],
                    tithi="Purnima",
                )
            )
            festivals.append(
                FestivalDate(
                    id="amavasya",
                    name=f"{lunar_month} Amavasya",
                    category="recurring",
                    date=amavasya_date,
                    ruling_deities=["Pitru", "Shani"],
                    tithi="Amavasya",
                )
            )
        except ValueError:
            pass

        try:
            sankashti_date = date(year, month, 19)
            festivals.append(
                FestivalDate(
                    id="sankashti_chaturthi",
                    name="Sankashti Chaturthi",
                    category="recurring",
                    date=sankashti_date,
                    ruling_deities=["Ganesha"],
                    tithi="Chaturthi",
                    fasting={"recommended": True, "type": "until_moonrise"},
                )
            )
        except ValueError:
            pass

        return festivals
