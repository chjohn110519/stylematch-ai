"""OpenAI API를 이용한 매칭 근거 텍스트 생성."""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.matcher import MatchResult
from src.schema import (
    QueryAttributes,
    SSF_COLOR_KO, SSF_FIT_KO, SSF_PATTERN_KO, SSF_TEXTURE_KO,
)

load_dotenv()

_PROMPTS = Path(__file__).parent.parent / "prompts"
MODEL = "gpt-4o-mini"
MAX_TOKENS = 128


def _ko(codes: list[str], mapping: dict[str, str]) -> str:
    labels = [mapping.get(c, c) for c in codes if c]
    return ", ".join(labels) if labels else "없음"


def generate_explanation(
    query: QueryAttributes,
    match: MatchResult,
) -> str:
    """40자 이내 한국어 유사 근거 문장 생성."""
    client = OpenAI()
    template = (_PROMPTS / "match_explanation.txt").read_text(encoding="utf-8")

    prompt = template.format(
        query_color=query.primary_color,
        query_silhouette=query.silhouette,
        query_pattern=query.pattern,
        query_texture=query.texture,
        query_style=query.style,
        product_name=match.sku_name,
        product_colors=_ko(match.matched_colors, SSF_COLOR_KO) or _ko([], SSF_COLOR_KO),
        product_fits=_ko(match.matched_fits, SSF_FIT_KO),
        product_patterns=_ko(match.matched_patterns, SSF_PATTERN_KO),
        product_textures=_ko(match.matched_textures, SSF_TEXTURE_KO),
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.choices[0].message.content or "").strip()
        if len(text) > 40:
            text = text[:38] + "…"
        return text
    except Exception:
        return fallback_explanation(query, match)


def fallback_explanation(query: QueryAttributes, match: MatchResult) -> str:
    """API 호출 없이 규칙 기반으로 빠르게 근거 생성 (데모 백업용)."""
    parts = []
    if match.matched_colors:
        parts.append(_ko(match.matched_colors[:1], SSF_COLOR_KO) + " 컬러")
    if match.matched_fits:
        parts.append(_ko(match.matched_fits[:1], SSF_FIT_KO))
    if match.matched_patterns:
        parts.append(_ko(match.matched_patterns[:1], SSF_PATTERN_KO) + " 패턴")
    if match.matched_textures:
        parts.append(_ko(match.matched_textures[:1], SSF_TEXTURE_KO) + " 소재")

    if not parts:
        parts.append(f"{query.cls.lower()} 카테고리")

    return ", ".join(parts[:3]) + "가 유사합니다"
