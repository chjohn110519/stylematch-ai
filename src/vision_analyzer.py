"""OpenAI Vision API를 이용한 의류 아이템 감지 및 속성 추출."""

import base64
import json
import re
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from src.schema import (
    QUERY_COLOR, QUERY_SILHOUETTE, QUERY_PATTERN, QUERY_TEXTURE, QUERY_STYLE,
    ItemDetection, QueryAttributes,
)

load_dotenv()

_PROMPTS = Path(__file__).parent.parent / "prompts"
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1024
IMAGE_MAX_PX = 512  # 장변 제한 (비용 절감)


def _resize_and_encode(image_path: str | Path) -> str:
    """이미지를 리사이즈하고 base64 data URL로 인코딩."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    if max(w, h) > IMAGE_MAX_PX:
        scale = IMAGE_MAX_PX / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.standard_b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _extract_json(text: str) -> dict | list:
    """응답 텍스트에서 JSON 파싱. 마크다운 코드블록 처리 포함."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def detect_items(image_path: str | Path) -> list[ItemDetection]:
    """연예인 사진에서 의류 아이템 감지 (최대 3개)."""
    client = OpenAI()
    prompt_text = (_PROMPTS / "item_detection.txt").read_text(encoding="utf-8")
    image_url = _resize_and_encode(image_path)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ],
    )

    raw = response.choices[0].message.content
    data = _extract_json(raw)
    items_raw = data.get("items", []) if isinstance(data, dict) else []

    results = []
    for it in items_raw[:3]:
        results.append(
            ItemDetection(
                item_id=it.get("item_id", len(results) + 1),
                cls=it.get("cls", "TOP"),
                subcategory=it.get("subcategory", ""),
                description=it.get("description", ""),
            )
        )
    return results


def extract_attributes(
    image_path: str | Path,
    item: ItemDetection,
) -> QueryAttributes:
    """감지된 아이템의 속성을 추출."""
    client = OpenAI()
    prompt_template = (_PROMPTS / "attribute_extraction.txt").read_text(encoding="utf-8")

    prompt_text = prompt_template.format(
        cls=item.cls,
        subcategory=item.subcategory,
        description=item.description,
        color_list=str(QUERY_COLOR),
        silhouette_list=str(QUERY_SILHOUETTE),
        pattern_list=str(QUERY_PATTERN),
        texture_list=str(QUERY_TEXTURE),
        style_list=str(QUERY_STYLE),
    )

    image_url = _resize_and_encode(image_path)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ],
    )

    raw = response.choices[0].message.content
    data = _extract_json(raw)

    def _pick(val: str, allowed: list[str], default: str) -> str:
        return val if val in allowed else default

    return QueryAttributes(
        cls=item.cls,
        subcategory=item.subcategory,
        primary_color=_pick(data.get("primary_color", ""), QUERY_COLOR, "black"),
        secondary_colors=[c for c in data.get("secondary_colors", []) if c in QUERY_COLOR],
        silhouette=_pick(data.get("silhouette", ""), QUERY_SILHOUETTE, "regular"),
        pattern=_pick(data.get("pattern", ""), QUERY_PATTERN, "solid"),
        texture=_pick(data.get("texture", ""), QUERY_TEXTURE, "cotton"),
        style=_pick(data.get("style", ""), QUERY_STYLE, "casual"),
        gender=data.get("gender", "ALL") if data.get("gender") in ("WOMEN", "MEN", "ALL") else "ALL",
    )


def analyze_image(image_path: str | Path) -> list[tuple[ItemDetection, QueryAttributes]]:
    """이미지에서 아이템 감지 + 속성 추출을 한 번에 실행."""
    items = detect_items(image_path)
    results = []
    for item in items:
        attrs = extract_attributes(image_path, item)
        results.append((item, attrs))
    return results
