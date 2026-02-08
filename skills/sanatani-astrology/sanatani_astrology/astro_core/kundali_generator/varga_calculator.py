"""
Varga (Divisional Chart) position calculator.

Implements Parashari-style varga mappings for divisional charts used in the app
(D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D16, D20, D24, D27, D30,
D40, D45, D60).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


MOVABLE_SIGNS = {0, 3, 6, 9}  # Aries, Cancer, Libra, Capricorn
FIXED_SIGNS = {1, 4, 7, 10}   # Taurus, Leo, Scorpio, Aquarius
DUAL_SIGNS = {2, 5, 8, 11}    # Gemini, Virgo, Sagittarius, Pisces
ODD_SIGNS = {0, 2, 4, 6, 8, 10}
EVEN_SIGNS = {1, 3, 5, 7, 9, 11}
FIRE_SIGNS = {0, 4, 8}
EARTH_SIGNS = {1, 5, 9}
AIR_SIGNS = {2, 6, 10}
WATER_SIGNS = {3, 7, 11}


@dataclass(frozen=True)
class VargaPosition:
    rasi: int
    degree_in_sign: float
    longitude: float


def calculate_varga_position(longitude: float, division: int) -> VargaPosition:
    """Calculate divisional chart position for a given longitude."""
    sign_index = int(longitude // 30) % 12
    degree_in_sign = longitude % 30

    if division == 1:
        rasi = sign_index
        degree = degree_in_sign
    elif division == 2:
        rasi, degree = _hora(sign_index, degree_in_sign)
    elif division == 3:
        rasi, degree = _drekkana(sign_index, degree_in_sign)
    elif division == 4:
        rasi, degree = _chaturthamsa(sign_index, degree_in_sign)
    elif division == 5:
        rasi, degree = _panchamsa(sign_index, degree_in_sign)
    elif division == 6:
        rasi, degree = _shashthamsa(sign_index, degree_in_sign)
    elif division == 7:
        rasi, degree = _saptamsa(sign_index, degree_in_sign)
    elif division == 8:
        rasi, degree = _ashtamsa(sign_index, degree_in_sign)
    elif division == 9:
        rasi, degree = _navamsa(sign_index, degree_in_sign)
    elif division == 10:
        rasi, degree = _dasamsa(sign_index, degree_in_sign)
    elif division == 11:
        rasi, degree = _rudramsa(sign_index, degree_in_sign)
    elif division == 12:
        rasi, degree = _dwadasamsa(sign_index, degree_in_sign)
    elif division == 16:
        rasi, degree = _shodasamsa(sign_index, degree_in_sign)
    elif division == 20:
        rasi, degree = _vimsamsa(sign_index, degree_in_sign)
    elif division == 24:
        rasi, degree = _chaturvimsamsa(sign_index, degree_in_sign)
    elif division == 27:
        rasi, degree = _nakshatramsa(sign_index, degree_in_sign)
    elif division == 30:
        rasi, degree = _trimsamsa(sign_index, degree_in_sign)
    elif division == 40:
        rasi, degree = _khavedamsa(sign_index, degree_in_sign)
    elif division == 45:
        rasi, degree = _akshavedamsa(sign_index, degree_in_sign)
    elif division == 60:
        rasi, degree = _shashtiamsa(sign_index, degree_in_sign)
    else:
        rasi, degree = _equal_division(sign_index, degree_in_sign, division)

    longitude_out = (rasi * 30) + degree
    return VargaPosition(rasi=rasi, degree_in_sign=degree, longitude=longitude_out)


def _clamp_degree(value: float) -> float:
    if value >= 30:
        return 30 - 1e-6
    if value < 0:
        return 0.0
    return value


def _equal_division(sign_index: int, degree_in_sign: float, division: int) -> Tuple[int, float]:
    part_size = 30.0 / division
    part_index = int(degree_in_sign / part_size)
    if part_index >= division:
        part_index = division - 1
    degree = (degree_in_sign % part_size) * division
    degree = _clamp_degree(degree)
    rasi = (sign_index + part_index) % 12
    return rasi, degree


def _hora(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    is_odd_sign = (sign_index % 2) == 0  # Aries=0 treated as odd
    in_first_half = degree_in_sign < 15
    if is_odd_sign:
        rasi = 4 if in_first_half else 3  # Leo or Cancer
    else:
        rasi = 3 if in_first_half else 4  # Cancer or Leo
    degree = (degree_in_sign % 15) * 2
    return rasi, _clamp_degree(degree)


def _drekkana(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 10.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 2:
        part_index = 2
    rasi = (sign_index + part_index * 4) % 12
    degree = (degree_in_sign % part_size) * 3
    return rasi, _clamp_degree(degree)


def _chaturthamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 7.5
    part_index = int(degree_in_sign / part_size)
    if part_index > 3:
        part_index = 3
    rasi = (sign_index + part_index * 3) % 12
    degree = (degree_in_sign % part_size) * 4
    return rasi, _clamp_degree(degree)


def _panchamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 6.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 4:
        part_index = 4
    odd = [0, 10, 8, 2, 6]
    even = [1, 5, 11, 9, 7]
    rasi = odd[part_index] if sign_index in ODD_SIGNS else even[part_index]
    degree = (degree_in_sign % part_size) * 5
    return rasi, _clamp_degree(degree)


def _shashthamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 5.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 5:
        part_index = 5
    rasi = part_index
    if sign_index in EVEN_SIGNS:
        rasi = (part_index + 6) % 12
    degree = (degree_in_sign % part_size) * 6
    return rasi, _clamp_degree(degree)


def _saptamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 7.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 6:
        part_index = 6
    is_odd_sign = (sign_index % 2) == 0
    start = 0 if is_odd_sign else 6
    rasi = (sign_index + start + part_index) % 12
    degree = (degree_in_sign % part_size) * 7
    return rasi, _clamp_degree(degree)


def _ashtamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 8.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 7:
        part_index = 7
    rasi = part_index
    if sign_index in FIXED_SIGNS:
        rasi = (part_index + 8) % 12
    elif sign_index in DUAL_SIGNS:
        rasi = (part_index + 4) % 12
    degree = (degree_in_sign % part_size) * 8
    return rasi, _clamp_degree(degree)


def _navamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 9.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 8:
        part_index = 8
    if sign_index in MOVABLE_SIGNS:
        start = 0
    elif sign_index in FIXED_SIGNS:
        start = 8
    else:
        start = 4
    rasi = (sign_index + start + part_index) % 12
    degree = (degree_in_sign % part_size) * 9
    return rasi, _clamp_degree(degree)


def _dasamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 3.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 9:
        part_index = 9
    is_odd_sign = (sign_index % 2) == 0
    start = 0 if is_odd_sign else 8
    rasi = (sign_index + start + part_index) % 12
    degree = (degree_in_sign % part_size) * 10
    return rasi, _clamp_degree(degree)


def _rudramsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 11.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 10:
        part_index = 10
    rasi = (12 - sign_index + part_index) % 12
    degree = (degree_in_sign % part_size) * 11
    return rasi, _clamp_degree(degree)


def _dwadasamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 2.5
    part_index = int(degree_in_sign / part_size)
    if part_index > 11:
        part_index = 11
    rasi = (sign_index + part_index) % 12
    degree = (degree_in_sign % part_size) * 12
    return rasi, _clamp_degree(degree)


def _shodasamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 16.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 15:
        part_index = 15
    if sign_index in MOVABLE_SIGNS:
        start = 0
    elif sign_index in FIXED_SIGNS:
        start = 4
    else:
        start = 8
    # Shodasamsa starts from Aries/Leo/Sagittarius based on sign type.
    rasi = (start + part_index) % 12
    degree = (degree_in_sign % part_size) * 16
    return rasi, _clamp_degree(degree)


def _vimsamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 20.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 19:
        part_index = 19
    rasi = part_index % 12
    if sign_index in DUAL_SIGNS:
        rasi = (part_index + 4) % 12
    elif sign_index in FIXED_SIGNS:
        rasi = (part_index + 8) % 12
    degree = (degree_in_sign % part_size) * 20
    return rasi, _clamp_degree(degree)


def _chaturvimsamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 24.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 23:
        part_index = 23
    odd_base = 4  # Leo
    even_base = 3  # Cancer
    rasi = (odd_base + part_index) % 12
    if sign_index in EVEN_SIGNS:
        rasi = (even_base + part_index) % 12
    degree = (degree_in_sign % part_size) * 24
    return rasi, _clamp_degree(degree)


def _nakshatramsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 27.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 26:
        part_index = 26
    rasi = part_index % 12
    if sign_index in EARTH_SIGNS:
        rasi = (part_index + 3) % 12
    elif sign_index in AIR_SIGNS:
        rasi = (part_index + 6) % 12
    elif sign_index in WATER_SIGNS:
        rasi = (part_index + 9) % 12
    degree = (degree_in_sign % part_size) * 27
    return rasi, _clamp_degree(degree)


def _trimsamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 1.0
    degree = (degree_in_sign % part_size) * 30
    odd_segments = [
        (0, 5, 0),
        (5, 10, 10),
        (10, 18, 8),
        (18, 25, 2),
        (25, 30, 6),
    ]
    even_segments = [
        (0, 5, 1),
        (5, 12, 5),
        (12, 20, 11),
        (20, 25, 9),
        (25, 30, 7),
    ]
    segments = odd_segments if sign_index in ODD_SIGNS else even_segments
    rasi = segments[-1][2]
    for start, end, seg_rasi in segments:
        if degree_in_sign >= start and degree_in_sign <= end:
            rasi = seg_rasi
            break
    return rasi % 12, _clamp_degree(degree)


def _khavedamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 40.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 39:
        part_index = 39
    rasi = part_index % 12
    if sign_index in EVEN_SIGNS:
        rasi = (part_index + 6) % 12
    degree = (degree_in_sign % part_size) * 40
    return rasi, _clamp_degree(degree)


def _akshavedamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 30.0 / 45.0
    part_index = int(degree_in_sign / part_size)
    if part_index > 44:
        part_index = 44
    rasi = part_index % 12
    if sign_index in FIXED_SIGNS:
        rasi = (part_index + 4) % 12
    elif sign_index in DUAL_SIGNS:
        rasi = (part_index + 8) % 12
    degree = (degree_in_sign % part_size) * 45
    return rasi, _clamp_degree(degree)


def _shashtiamsa(sign_index: int, degree_in_sign: float) -> Tuple[int, float]:
    part_size = 0.5
    part_index = int(degree_in_sign / part_size)
    if part_index > 59:
        part_index = 59
    rasi = (sign_index + part_index) % 12
    degree = (degree_in_sign % part_size) * 60
    return rasi, _clamp_degree(degree)
