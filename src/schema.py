"""
SSF 속성 코드 정의 및 Claude 쿼리 어휘 ↔ SSF 코드 매핑.
"""

from pydantic import BaseModel


# ─────────────────────────── SSF 원본 코드 ───────────────────────────

SSF_CLASS = ["TOP", "BOTTOM", "OUTER", "TOP_L"]

SSF_COLORS = [
    "0_IVORY", "1_WHITE", "2_LIGHT_GREY", "3_GREY", "4_ASH", "5_BLACK",
    "6_RED", "7_CORAL", "8_ORANGE", "9_SALMON_PINK", "A_BEIGE",
    "B_YELLOWISH_BROWN", "C_BRICK", "D_BROWN", "E_YELLOW", "F_LEMON",
    "G_MUSTAR", "H_KHAKI", "J_OLIVE", "K_APPLE_GREEN", "L_GREEN",
    "M_MINT", "N_EMERALD", "O_SKY_BLUE", "P_BLUE", "Q_SKY_BLUE",
    "R_NAVY", "S_PURPLE", "T_PINK", "U_LAVENDER", "V_WINE",
    "W_GOLD", "X_SILVER", "Y_MULTI",
]

SSF_FIT = [
    "BAGGY", "BOOTSCUT", "BOXY", "CASUAL_SLIM", "CASUAL_TOP_FIT_ETC",
    "CASUAL_TOP_FIT_REGULAR", "CASUAL_TOP_OVER_FIT", "DRESS_A-LINE",
    "DRESS_FIT_ETC", "DRESS_H-LINE", "EMPIRE-HIGHT_WAIST", "JOGGER",
    "LOOSE-WIDE", "MERMAID", "OUTER_FIT_REGULAR", "OUTER_OVER_FIT",
    "OUTER_SLIM", "PANTS_FIT_ETC", "PANTS_SLIM", "REGULAR-STRAIGHT",
    "SHEATH", "SKINNY", "SKIRT_A-LINE", "SKIRT_FIT_ETC", "SKIRT_H-LINE",
    "SKIRT_MERMAID", "SUIT-JACKET_FIT_ETC", "TAPERED(BOY_FRIEND)", "TENT",
    "TIGHT", "WIGGLE",
]

SSF_PATTERN = [
    "ANIMAL", "CAMOUFLAGE", "COLORED", "COLOR_BLOCK", "COLOR_CONTRAST",
    "DENIM_TYPE_ETC", "DOT", "FAIR_ISLE", "FLORAL", "GARMENT_WASHING",
    "GLEN", "GRADATION", "GRAPHIC", "HERRINGBONE", "JACQUARD", "MELANGE",
    "METALIC", "MONOGRAM", "MULTI_CHECK", "PAISLEY", "PATCHWORK",
    "PRINTING_PAINTING", "RAW-SELVEDGE", "RHOMBUS_CHECK", "SHEPHERD_CHECK ",
    "SIMPLE_CHECK", "SOLID", "SQUARE_CHECK", "STRIPE(DIAG)", "STRIPE(HOR)",
    "STRIPE(VER)", "TIE-DYE", "TROPICAL", "TWEED", "TYPOGRAPHY",
    "WASHING", "ZIGZAG",
]

SSF_TEXTURE = [
    "BOA-BOUCLE-FLEECE", "CHIFFON", "CORDUROY", "DENIM", "FUR",
    "KNITTING", "LACE", "LEATHER", "LINEN", "NYLON", "SEERSUCKER",
    "SEE_THROUGH-MESH", "SEQUINS", "SILK", "SUEDE", "TERRY", "VELVET", "WOOL",
]

SSF_STYLE_TPO = [
    "CASUAL-ACTIVE", "CASUAL-BASIC-CASUAL", "CASUAL-CASUAL", "CASUAL-FUNK",
    "CASUAL-KITSCH", "CASUAL-MILITARY", "CASUAL-ROMANTIC-CASUAL",
    "CASUAL-STREET", "CLASSIC-FORMAL", "CLASSIC-SEMI-FORMAL", "ELEGANCE",
    "ETHNIC", "MANNISH", "MODERN", "NATURAL", "ORIENTAL",
    "PARTY-EVENT-FANCY", "PARTY-EVENT-ROMANTIC", "SEXY", "SPORTS", "VACANCE",
]

SSF_LENGTH = [
    "CROP", "HALF", "LONG-MAXI", "MAXI", "MICRO_MINI", "MIDI", "MIDI-LONG",
    "MINI", "PANTS_7-8", "PANTS_9-10", "PANTS_HALF", "PANTS_LONG",
    "PANTS_MINI(HOT)", "PANTS_SHORT", "SHORT", "SLEEVESS",
    "SLEEVE_7", "SLEEVE_HALF", "SLEEVE_LONG",
]


# ─────────────────────── Claude 쿼리 추출 어휘 ───────────────────────

QUERY_CLASS = ["TOP", "BOTTOM", "OUTER"]

QUERY_COLOR = [
    "black", "white", "grey", "ivory", "beige", "brown", "navy", "blue",
    "sky_blue", "green", "khaki", "olive", "red", "pink", "coral",
    "yellow", "purple", "orange", "gold", "silver", "multi",
]

QUERY_SILHOUETTE = ["slim", "regular", "oversized", "boxy", "wide"]

QUERY_PATTERN = [
    "solid", "stripe", "check", "floral", "logo", "graphic",
    "color_block", "animal", "denim_wash",
]

QUERY_TEXTURE = [
    "denim", "knit", "wool", "leather", "linen", "chiffon",
    "cotton", "nylon", "velvet", "fur",
]

QUERY_STYLE = [
    "casual", "formal", "street", "romantic", "sporty",
    "mannish", "elegant", "minimal",
]


# ──────────────────────── 데이터 모델 ────────────────────────────────

class ItemDetection(BaseModel):
    item_id: int
    cls: str           # TOP / BOTTOM / OUTER
    subcategory: str   # blazer, hoodie 등 자유 텍스트
    description: str   # 위치/색상 요약 (bbox 대체)


class QueryAttributes(BaseModel):
    cls: str
    subcategory: str
    primary_color: str
    secondary_colors: list[str] = []
    silhouette: str
    pattern: str
    texture: str
    style: str
    gender: str = "WOMEN"   # WOMEN / MEN / ALL


# ──────────────────────── 매핑 함수 ─────────────────────────────────

def query_color_to_ssf(color: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "black":   ["5_BLACK"],
        "white":   ["1_WHITE"],
        "grey":    ["2_LIGHT_GREY", "3_GREY", "4_ASH"],
        "ivory":   ["0_IVORY"],
        "beige":   ["A_BEIGE"],
        "brown":   ["D_BROWN", "B_YELLOWISH_BROWN", "C_BRICK"],
        "navy":    ["R_NAVY"],
        "blue":    ["P_BLUE"],
        "sky_blue":["O_SKY_BLUE", "Q_SKY_BLUE"],
        "green":   ["L_GREEN", "K_APPLE_GREEN", "N_EMERALD"],
        "khaki":   ["H_KHAKI"],
        "olive":   ["J_OLIVE"],
        "red":     ["6_RED", "C_BRICK"],
        "pink":    ["T_PINK", "9_SALMON_PINK", "7_CORAL"],
        "coral":   ["7_CORAL", "9_SALMON_PINK"],
        "yellow":  ["E_YELLOW", "F_LEMON", "G_MUSTAR"],
        "purple":  ["S_PURPLE", "U_LAVENDER", "V_WINE"],
        "orange":  ["8_ORANGE"],
        "gold":    ["W_GOLD"],
        "silver":  ["X_SILVER"],
        "multi":   ["Y_MULTI"],
    }
    return mapping.get(color, [])


def query_silhouette_to_ssf_fit(silhouette: str, cls: str = "") -> list[str]:
    cls = cls.upper()
    mapping: dict[str, list[str]] = {
        "oversized": [
            "CASUAL_TOP_OVER_FIT", "OUTER_OVER_FIT", "BAGGY", "BOXY",
            "TENT", "LOOSE-WIDE",
        ],
        "slim": ["CASUAL_SLIM", "OUTER_SLIM", "PANTS_SLIM", "SKINNY", "TIGHT"],
        "regular": [
            "CASUAL_TOP_FIT_REGULAR", "OUTER_FIT_REGULAR", "REGULAR-STRAIGHT",
            "CASUAL_TOP_FIT_ETC",
        ],
        "boxy":  ["BOXY", "CASUAL_TOP_OVER_FIT"],
        "wide":  ["LOOSE-WIDE", "BAGGY", "JOGGER"],
    }
    return mapping.get(silhouette, [])


def query_pattern_to_ssf(pattern: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "solid":       ["SOLID", "COLORED"],
        "stripe":      ["STRIPE(HOR)", "STRIPE(VER)", "STRIPE(DIAG)"],
        "check":       ["SIMPLE_CHECK", "MULTI_CHECK", "GLEN", "RHOMBUS_CHECK",
                        "SQUARE_CHECK", "SHEPHERD_CHECK "],
        "floral":      ["FLORAL", "TROPICAL"],
        "logo":        ["MONOGRAM", "TYPOGRAPHY"],
        "graphic":     ["GRAPHIC", "PRINTING_PAINTING"],
        "color_block": ["COLOR_BLOCK", "COLOR_CONTRAST"],
        "animal":      ["ANIMAL", "CAMOUFLAGE"],
        "denim_wash":  ["GARMENT_WASHING", "WASHING", "DENIM_TYPE_ETC", "RAW-SELVEDGE"],
    }
    return mapping.get(pattern, [])


def query_texture_to_ssf(texture: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "denim":   ["DENIM"],
        "knit":    ["KNITTING"],
        "wool":    ["WOOL", "BOA-BOUCLE-FLEECE"],
        "leather": ["LEATHER", "SUEDE"],
        "linen":   ["LINEN", "SEERSUCKER"],
        "chiffon": ["CHIFFON", "SEE_THROUGH-MESH"],
        "cotton":  [],  # SSF TEXTURE에 cotton 없음 — 스킵
        "nylon":   ["NYLON"],
        "velvet":  ["VELVET"],
        "fur":     ["FUR"],
    }
    return mapping.get(texture, [])


def query_style_to_ssf_tpo(style: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "casual":   ["CASUAL-CASUAL", "CASUAL-BASIC-CASUAL", "CASUAL-ACTIVE"],
        "formal":   ["CLASSIC-FORMAL", "CLASSIC-SEMI-FORMAL"],
        "street":   ["CASUAL-STREET", "CASUAL-FUNK"],
        "romantic": ["CASUAL-ROMANTIC-CASUAL", "PARTY-EVENT-ROMANTIC"],
        "sporty":   ["SPORTS", "CASUAL-ACTIVE"],
        "mannish":  ["MANNISH"],
        "elegant":  ["ELEGANCE", "CLASSIC-SEMI-FORMAL"],
        "minimal":  ["MODERN", "CLASSIC-SEMI-FORMAL"],
    }
    return mapping.get(style, [])


# SSF 코드 → 한국어 표시 라벨

SSF_COLOR_KO: dict[str, str] = {
    "0_IVORY": "아이보리", "1_WHITE": "화이트", "2_LIGHT_GREY": "라이트그레이",
    "3_GREY": "그레이", "4_ASH": "애쉬", "5_BLACK": "블랙",
    "6_RED": "레드", "7_CORAL": "코럴", "8_ORANGE": "오렌지",
    "9_SALMON_PINK": "살몬핑크", "A_BEIGE": "베이지", "B_YELLOWISH_BROWN": "옐로우브라운",
    "C_BRICK": "브릭", "D_BROWN": "브라운", "E_YELLOW": "옐로우",
    "F_LEMON": "레몬", "G_MUSTAR": "머스타드", "H_KHAKI": "카키",
    "J_OLIVE": "올리브", "K_APPLE_GREEN": "애플그린", "L_GREEN": "그린",
    "M_MINT": "민트", "N_EMERALD": "에메랄드", "O_SKY_BLUE": "스카이블루",
    "P_BLUE": "블루", "Q_SKY_BLUE": "스카이블루", "R_NAVY": "네이비",
    "S_PURPLE": "퍼플", "T_PINK": "핑크", "U_LAVENDER": "라벤더",
    "V_WINE": "와인", "W_GOLD": "골드", "X_SILVER": "실버", "Y_MULTI": "멀티",
}

SSF_FIT_KO: dict[str, str] = {
    "BAGGY": "배기핏", "BOXY": "박시핏", "CASUAL_SLIM": "슬림핏",
    "CASUAL_TOP_OVER_FIT": "오버핏", "CASUAL_TOP_FIT_REGULAR": "레귤러핏",
    "LOOSE-WIDE": "루즈와이드", "OUTER_OVER_FIT": "오버핏", "OUTER_SLIM": "슬림핏",
    "OUTER_FIT_REGULAR": "레귤러핏", "PANTS_SLIM": "슬림핏",
    "REGULAR-STRAIGHT": "레귤러스트레이트", "SKINNY": "스키니",
    "TAPERED(BOY_FRIEND)": "테이퍼드", "JOGGER": "조거", "BOOTSCUT": "부츠컷",
}

SSF_PATTERN_KO: dict[str, str] = {
    "SOLID": "무지", "STRIPE(HOR)": "스트라이프", "STRIPE(VER)": "스트라이프",
    "STRIPE(DIAG)": "대각선스트라이프", "SIMPLE_CHECK": "체크",
    "MULTI_CHECK": "멀티체크", "GLEN": "글렌체크", "FLORAL": "플로럴",
    "GRAPHIC": "그래픽", "COLOR_BLOCK": "컬러블록", "ANIMAL": "애니멀",
    "GARMENT_WASHING": "가먼트워싱", "WASHING": "워싱", "MONOGRAM": "모노그램",
    "DOT": "도트", "HERRINGBONE": "헤링본", "TWEED": "트위드",
    "JACQUARD": "자카드", "CAMOUFLAGE": "카무플라주",
}

SSF_TEXTURE_KO: dict[str, str] = {
    "DENIM": "데님", "KNITTING": "니트", "WOOL": "울",
    "LEATHER": "레더", "LINEN": "린넨", "CHIFFON": "시폰",
    "NYLON": "나일론", "VELVET": "벨벳", "FUR": "퍼",
    "CORDUROY": "코듀로이", "LACE": "레이스", "SUEDE": "스웨이드",
    "SILK": "실크", "TERRY": "테리", "SEQUINS": "시퀀스",
    "BOA-BOUCLE-FLEECE": "플리스/부클",
}
