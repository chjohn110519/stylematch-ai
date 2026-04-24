"""하이브리드 매칭 엔진 — SSF 상품 DB에서 쿼리 속성과 유사한 상품 Top-K 반환."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.color_map import best_color_similarity
from src.db_init import DB_PATH
from src.schema import (
    QueryAttributes,
    query_color_to_ssf,
    query_pattern_to_ssf,
    query_silhouette_to_ssf_fit,
    query_style_to_ssf_tpo,
    query_texture_to_ssf,
)

MIN_SCORE = 0.40
TOP_K = 5

# class 매핑: TOP_L도 TOP으로 매칭 허용
_CLASS_ALIAS: dict[str, set[str]] = {
    "TOP":    {"TOP", "TOP_L"},
    "BOTTOM": {"BOTTOM"},
    "OUTER":  {"OUTER"},
}

# gender 호환 규칙
_GENDER_COMPAT: dict[str, set[str]] = {
    "WOMEN": {"WOMEN", "ALL"},
    "MEN":   {"MEN",   "ALL"},
    "ALL":   {"WOMEN", "MEN", "ALL"},
}


@dataclass
class MatchResult:
    god_no:     str
    sku_name:   str
    brand_name: str
    tag_price:  int
    image_url:  str
    score:      float
    matched_colors:   list[str]
    matched_fits:     list[str]
    matched_patterns: list[str]
    matched_textures: list[str]


def _load_candidate_attrs(con: sqlite3.Connection, god_nos: list[str]) -> dict[str, dict[str, set[str]]]:
    """상품별 {att01: {att_val, ...}} 딕셔너리 일괄 로딩."""
    if not god_nos:
        return {}
    placeholders = ",".join("?" * len(god_nos))
    rows = con.execute(
        f"SELECT god_no, att01, att_val FROM product_attrs WHERE god_no IN ({placeholders})",
        god_nos,
    ).fetchall()
    result: dict[str, dict[str, set[str]]] = {}
    for god_no, att01, att_val in rows:
        result.setdefault(god_no, {}).setdefault(att01, set()).add(att_val)
    return result


def _score(
    query: QueryAttributes,
    db_attrs: dict[str, set[str]],
    ssf_colors: list[str],
    ssf_fits: list[str],
    ssf_patterns: list[str],
    ssf_textures: list[str],
    ssf_styles: list[str],
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    prod_colors   = list(db_attrs.get("COLOR", set()))
    prod_fits     = db_attrs.get("FIT", set())
    prod_patterns = db_attrs.get("PATTERN", set())
    prod_textures = db_attrs.get("TEXTURE", set())
    prod_styles   = db_attrs.get("STYLE_TPO", set())

    # 색상 유사도
    color_score = best_color_similarity(ssf_colors, prod_colors)

    # 핏 (oversized ↔ 오버핏 등) 일치 여부
    fit_matches = prod_fits & set(ssf_fits)
    fit_score   = 1.0 if fit_matches else 0.0

    # 패턴
    pat_matches = prod_patterns & set(ssf_patterns)
    pat_score   = 1.0 if pat_matches else 0.0

    # 소재 (매핑 없는 소재[cotton 등]는 중립 0.5, 매핑 있으면 1.0/0.0)
    tex_matches = prod_textures & set(ssf_textures)
    if not ssf_textures:
        tex_score = 0.5
    else:
        tex_score = 1.0 if tex_matches else 0.0

    # 스타일
    sty_matches = prod_styles & set(ssf_styles)
    sty_score   = 1.0 if sty_matches else 0.0

    total = (
        0.30 * color_score
        + 0.25 * fit_score
        + 0.20 * pat_score
        + 0.15 * tex_score
        + 0.10 * sty_score
    )

    return (
        total,
        sorted(set(ssf_colors) & set(prod_colors)),
        sorted(fit_matches),
        sorted(pat_matches),
        sorted(tex_matches),
    )


def find_matches(
    query: QueryAttributes,
    db_path: Path = DB_PATH,
    top_k: int = TOP_K,
    min_score: float = MIN_SCORE,
) -> list[MatchResult]:
    ssf_colors   = query_color_to_ssf(query.primary_color)
    ssf_fits     = query_silhouette_to_ssf_fit(query.silhouette, query.cls)
    ssf_patterns = query_pattern_to_ssf(query.pattern)
    ssf_textures = query_texture_to_ssf(query.texture)
    ssf_styles   = query_style_to_ssf_tpo(query.style)

    allowed_classes  = _CLASS_ALIAS.get(query.cls, {query.cls})
    allowed_genders  = _GENDER_COMPAT.get(query.gender, {"ALL"})

    class_ph  = ",".join("?" * len(allowed_classes))
    gender_ph = ",".join("?" * len(allowed_genders))

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    candidates = con.execute(
        f"""
        SELECT god_no, sku_name, brand_name, tag_price, image_url
        FROM products
        WHERE class IN ({class_ph})
          AND gender IN ({gender_ph})
        """,
        [*allowed_classes, *allowed_genders],
    ).fetchall()

    if not candidates:
        con.close()
        return []

    god_nos = [r["god_no"] for r in candidates]
    all_attrs = _load_candidate_attrs(con, god_nos)
    con.close()

    scored: list[MatchResult] = []
    for row in candidates:
        gn = row["god_no"]
        attrs = all_attrs.get(gn, {})
        total, mc, mf, mp, mt = _score(
            query, attrs, ssf_colors, ssf_fits, ssf_patterns, ssf_textures, ssf_styles
        )
        if total >= min_score:
            scored.append(
                MatchResult(
                    god_no=gn,
                    sku_name=row["sku_name"] or "",
                    brand_name=row["brand_name"] or "",
                    tag_price=row["tag_price"] or 0,
                    image_url=row["image_url"] or "",
                    score=total,
                    matched_colors=mc,
                    matched_fits=mf,
                    matched_patterns=mp,
                    matched_textures=mt,
                )
            )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]
