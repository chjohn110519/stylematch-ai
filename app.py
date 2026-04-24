"""StyleMatch AI — Streamlit 데모 UI."""

import io
import os
import textwrap
from pathlib import Path

import streamlit as st

# Streamlit Cloud secrets → 환경 변수 브릿지 (로컬 .env는 vision_analyzer에서 load_dotenv로 처리)
if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

from PIL import Image, ImageDraw, ImageFont

from src.explainer import fallback_explanation, generate_explanation
from src.matcher import MatchResult, find_matches
from src.schema import QueryAttributes
from src.vision_analyzer import analyze_image

# ─────────────────────── DB 자동 초기화 (최초 실행 시) ───────────────
from src.db_init import DB_PATH
from src.data_loader import JSON_PATH, load as _load_data

if not DB_PATH.exists():
    with st.spinner("데이터베이스 초기화 중... (최초 실행 시 약 10초)"):
        _load_data()

# ─────────────────────── 페이지 설정 ─────────────────────────────────
st.set_page_config(
    page_title="StyleMatch AI",
    page_icon="👗",
    layout="wide",
)

st.markdown(
    """
    <style>
    .score-badge { background: #ff4b4b; color: white; border-radius: 12px;
                   padding: 2px 8px; font-size: 12px; }
    .attr-chip { background: #f0f0f0; border-radius: 8px; padding: 2px 8px;
                 font-size: 12px; margin: 2px; display: inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────── 헬퍼 함수 ───────────────────────────────────

def render_product_card(m: MatchResult, attrs: QueryAttributes, use_claude: bool) -> None:
    if m.image_url:
        st.image(m.image_url, use_container_width=True)
    else:
        st.markdown("*(이미지 없음)*")

    score_pct = int(m.score * 100)
    st.markdown(
        f'<span class="score-badge">{score_pct}%</span> **{m.brand_name}**',
        unsafe_allow_html=True,
    )
    name = textwrap.shorten(m.sku_name, width=30, placeholder="…")
    st.markdown(f"**{name}**")
    st.markdown(f"₩{m.tag_price:,}")

    if use_claude:
        try:
            explanation = generate_explanation(attrs, m)
        except Exception:
            explanation = fallback_explanation(attrs, m)
    else:
        explanation = fallback_explanation(attrs, m)
    st.caption(explanation)


# ─────────────────────── 메인 UI ─────────────────────────────────────

st.title("👗 StyleMatch AI")
st.caption("연예인 착장 → SSF SHOP 유사 상품 매칭 엔진")

uploaded = st.file_uploader(
    "연예인 사진을 업로드하세요 (jpg / png, 10MB 이하)",
    type=["jpg", "jpeg", "png"],
    label_visibility="visible",
)

use_claude_explain = st.checkbox("Claude 매칭 근거 생성 (API 호출)", value=False)

if uploaded is None:
    st.info("사진을 업로드하면 SSF SHOP 유사 상품을 자동으로 찾아드립니다.")
    st.stop()

if st.button("🔍 분석 시작", type="primary"):
    tmp_path = Path("/tmp/stylematch_query.jpg")
    img_bytes = uploaded.read()
    tmp_path.write_bytes(img_bytes)

    with st.spinner("이미지 분석 중... (약 10~15초)"):
        try:
            results = analyze_image(tmp_path)
        except Exception as e:
            st.error(f"이미지 분석 오류: {e}")
            st.stop()

    if not results:
        st.warning("이미지에서 의류 아이템을 찾지 못했습니다. 다른 사진을 시도해보세요.")
        st.stop()

    # 원본 이미지에 아이템 레이블 주석
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    label_colors = ["#FF4B4B", "#4B9EFF", "#4BFF9E"]
    try:
        font = ImageFont.truetype("arial.ttf", max(14, img.width // 30))
    except Exception:
        font = ImageFont.load_default()
    for i, (item, _) in enumerate(results):
        label = f"[{i+1}] {item.cls}: {item.subcategory}"
        draw.text((10, 10 + i * 32), label, fill=label_colors[i % 3], font=font)

    col_img, col_info = st.columns([1, 2])
    with col_img:
        st.image(img, caption="감지된 아이템", use_container_width=True)

    with col_info:
        for i, (item, attrs) in enumerate(results):
            st.markdown(f"### 아이템 {i+1}: **{item.cls}** — {item.subcategory}")

            attr_html = "".join([
                f'<span class="attr-chip">색상: {attrs.primary_color}</span>',
                f'<span class="attr-chip">핏: {attrs.silhouette}</span>',
                f'<span class="attr-chip">패턴: {attrs.pattern}</span>',
                f'<span class="attr-chip">소재: {attrs.texture}</span>',
                f'<span class="attr-chip">스타일: {attrs.style}</span>',
            ])
            st.markdown(attr_html, unsafe_allow_html=True)
            st.caption(f"설명: {item.description}")

            with st.spinner(f"아이템 {i+1} 유사 상품 검색 중..."):
                matches = find_matches(attrs)

            if not matches:
                st.warning("유사한 상품을 찾지 못했습니다. (매칭 스코어 0.4 미만)")
                st.divider()
                continue

            st.markdown(f"**SSF 유사 상품 Top {len(matches)}**")
            cols = st.columns(min(len(matches), 5))
            for j, m in enumerate(matches):
                with cols[j]:
                    render_product_card(m, attrs, use_claude_explain)

            st.divider()
