"""scnt.a_items.json → SQLite 임포터."""

import json
import sqlite3
from pathlib import Path

from src.db_init import DB_PATH, init_db

JSON_PATH = Path(__file__).parent.parent / "scnt.a_items.json"
ALLOWED_CLASSES = {"TOP", "BOTTOM", "OUTER", "TOP_L"}


def load(json_path: Path = JSON_PATH, db_path: Path = DB_PATH) -> None:
    init_db(db_path)

    with open(json_path, encoding="utf-8") as f:
        items = json.load(f)

    products = []
    attrs = []

    for item in items:
        cls = item.get("class", "")
        if cls not in ALLOWED_CLASSES:
            continue

        god_no = item["godNo"]

        gal = item.get("galCategory", [{}])
        subcategory = item.get("subcategory") or (gal[0].get("galCate03", "") if gal else "")

        products.append((
            god_no,
            item.get("skuName"),
            item.get("brandCode"),
            item.get("brandName"),
            item.get("tagPrice"),
            item.get("imageUrl"),
            cls,
            item.get("category"),
            subcategory,
            item.get("gender"),
            item.get("priceRange"),
            item.get("season"),
            item.get("releaseYear"),
        ))

        for att in item.get("attribute", []):
            attrs.append((god_no, att.get("att01", ""), att.get("att02", ""), att.get("attVal", "")))

        # color 배열도 COLOR att01으로 저장 (중복 무시)
        for color in item.get("color", []):
            attrs.append((god_no, "COLOR", "", color))

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")

    con.executemany(
        "INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        products,
    )
    con.executemany(
        "INSERT OR IGNORE INTO product_attrs VALUES (?,?,?,?)",
        attrs,
    )

    con.commit()
    prod_count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    attr_count = con.execute("SELECT COUNT(*) FROM product_attrs").fetchone()[0]
    con.close()

    print(f"임포트 완료 — 상품: {prod_count:,}개 / 속성 행: {attr_count:,}개")


if __name__ == "__main__":
    load()
