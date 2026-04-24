"""SSF 34색 코드 → CIE LAB 변환 및 색상 유사도 계산."""

import math

# SSF 색상 코드 → sRGB (0-255)
_SSF_RGB: dict[str, tuple[int, int, int]] = {
    "0_IVORY":           (255, 255, 240),
    "1_WHITE":           (255, 255, 255),
    "2_LIGHT_GREY":      (211, 211, 211),
    "3_GREY":            (169, 169, 169),
    "4_ASH":             (120, 120, 120),
    "5_BLACK":           (30,  30,  30),
    "6_RED":             (200, 30,  30),
    "7_CORAL":           (255, 127, 80),
    "8_ORANGE":          (255, 140, 0),
    "9_SALMON_PINK":     (250, 160, 120),
    "A_BEIGE":           (220, 200, 170),
    "B_YELLOWISH_BROWN": (160, 120, 60),
    "C_BRICK":           (180, 65,  45),
    "D_BROWN":           (101, 67,  33),
    "E_YELLOW":          (255, 220, 50),
    "F_LEMON":           (240, 240, 100),
    "G_MUSTAR":          (210, 175, 45),
    "H_KHAKI":           (150, 140, 90),
    "J_OLIVE":           (107, 120, 55),
    "K_APPLE_GREEN":     (140, 195, 80),
    "L_GREEN":           (60,  160, 80),
    "M_MINT":            (150, 220, 200),
    "N_EMERALD":         (0,   145, 100),
    "O_SKY_BLUE":        (135, 196, 235),
    "P_BLUE":            (30,  100, 200),
    "Q_SKY_BLUE":        (115, 180, 220),
    "R_NAVY":            (25,  40,  100),
    "S_PURPLE":          (130, 60,  180),
    "T_PINK":            (255, 160, 190),
    "U_LAVENDER":        (200, 170, 230),
    "V_WINE":            (100, 30,  50),
    "W_GOLD":            (205, 170, 50),
    "X_SILVER":          (190, 190, 200),
    "Y_MULTI":           (128, 128, 128),
}


def _srgb_to_linear(c: int) -> float:
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _rgb_to_lab(r: int, g: int, b: int) -> tuple[float, float, float]:
    rl, gl, bl = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    xn, yn, zn = 0.95047, 1.00000, 1.08883
    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_ = 200 * (fy - fz)
    return L, a, b_


# 사전 계산된 LAB 값
_SSF_LAB: dict[str, tuple[float, float, float]] = {
    code: _rgb_to_lab(*rgb) for code, rgb in _SSF_RGB.items()
}


def color_distance(code1: str, code2: str) -> float:
    """두 SSF 색상 코드 간 CIE76 거리 (0 = 동일)."""
    if code1 == code2:
        return 0.0
    L1, a1, b1 = _SSF_LAB.get(code1, (50, 0, 0))
    L2, a2, b2 = _SSF_LAB.get(code2, (50, 0, 0))
    return math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def color_similarity(code1: str, code2: str, max_dist: float = 80.0) -> float:
    """색상 유사도 [0, 1]. 거리가 클수록 낮은 점수."""
    dist = color_distance(code1, code2)
    return max(0.0, 1.0 - dist / max_dist)


def best_color_similarity(query_ssf_codes: list[str], product_ssf_codes: list[str]) -> float:
    """쿼리 색상 목록과 상품 색상 목록 간 최대 유사도."""
    if not query_ssf_codes or not product_ssf_codes:
        return 0.0
    best = 0.0
    for qc in query_ssf_codes:
        for pc in product_ssf_codes:
            s = color_similarity(qc, pc)
            if s > best:
                best = s
    return best
