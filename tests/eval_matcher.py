"""
매칭 엔진 품질 평가.

사용법:
  # API 없이 매칭 엔진만 빠르게 테스트 (하드코딩 쿼리)
  python -m tests.eval_matcher --smoke

  # 실제 이미지 디렉토리로 평가 (ANTHROPIC_API_KEY 필요)
  python -m tests.eval_matcher --dir data/demo_samples
"""

import argparse
import json
from pathlib import Path

from src.matcher import find_matches
from src.schema import QueryAttributes


# ─────────────── smoke test용 하드코딩 쿼리 ──────────────────────────

SMOKE_QUERIES: list[QueryAttributes] = [
    QueryAttributes(
        cls="OUTER", subcategory="blazer",
        primary_color="black", silhouette="oversized",
        pattern="solid", texture="wool", style="formal", gender="WOMEN",
    ),
    QueryAttributes(
        cls="TOP", subcategory="hoodie",
        primary_color="beige", silhouette="oversized",
        pattern="solid", texture="cotton", style="casual", gender="ALL",
    ),
    QueryAttributes(
        cls="BOTTOM", subcategory="wide pants",
        primary_color="navy", silhouette="wide",
        pattern="solid", texture="cotton", style="casual", gender="WOMEN",
    ),
    QueryAttributes(
        cls="TOP", subcategory="knit sweater",
        primary_color="ivory", silhouette="regular",
        pattern="solid", texture="knit", style="minimal", gender="WOMEN",
    ),
    QueryAttributes(
        cls="OUTER", subcategory="trench coat",
        primary_color="beige", silhouette="regular",
        pattern="solid", texture="linen", style="elegant", gender="WOMEN",
    ),
]


def smoke_test() -> None:
    print("=" * 60)
    print("매칭 엔진 Smoke Test")
    print("=" * 60)

    total_with_results = 0
    for i, query in enumerate(SMOKE_QUERIES):
        matches = find_matches(query)
        has_result = len(matches) > 0
        if has_result:
            total_with_results += 1

        print(f"\n[{i+1}] {query.cls} / {query.subcategory} / {query.primary_color} / {query.silhouette}")
        if matches:
            for j, m in enumerate(matches):
                print(f"  {j+1}. [{m.score:.2f}] {m.brand_name} — {m.sku_name[:40]}")
                print(f"       색상:{m.matched_colors} 핏:{m.matched_fits} 패턴:{m.matched_patterns}")
        else:
            print("  → 결과 없음 (스코어 0.4 미만)")

    print(f"\n결과 있음: {total_with_results}/{len(SMOKE_QUERIES)}")


def eval_from_dir(image_dir: str) -> None:
    """실제 이미지로 평가 (API 호출)."""
    from src.vision_analyzer import analyze_image

    dir_path = Path(image_dir)
    images = list(dir_path.glob("*.jpg")) + list(dir_path.glob("*.png"))
    if not images:
        print(f"이미지 없음: {dir_path}")
        return

    print(f"평가 대상: {len(images)}장")
    golden_cases = []

    for img_path in images:
        print(f"\n처리: {img_path.name}")
        try:
            results = analyze_image(img_path)
        except Exception as e:
            print(f"  오류: {e}")
            continue

        for item, attrs in results:
            matches = find_matches(attrs)
            print(f"  [{item.cls}] {item.subcategory} → {len(matches)}개 매칭")
            for m in matches:
                print(f"    [{m.score:.2f}] {m.brand_name} {m.sku_name[:35]}")

            if matches and matches[0].score >= 0.55:
                golden_cases.append({
                    "image": img_path.name,
                    "item": {"cls": item.cls, "subcategory": item.subcategory},
                    "top_match": {
                        "god_no": matches[0].god_no,
                        "sku_name": matches[0].sku_name,
                        "score": round(matches[0].score, 3),
                    },
                })

    if golden_cases:
        out = Path("data/golden_samples.json")
        out.write_text(json.dumps(golden_cases, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n골든 케이스 {len(golden_cases)}개 저장: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="API 없이 스모크 테스트")
    parser.add_argument("--dir", type=str, help="이미지 디렉토리 경로")
    args = parser.parse_args()

    if args.smoke or (not args.dir):
        smoke_test()
    if args.dir:
        eval_from_dir(args.dir)
