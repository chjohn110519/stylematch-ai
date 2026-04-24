"""SQLite DB 초기화 — 테이블 및 인덱스 생성."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ssf_products.db"

DDL = """
CREATE TABLE IF NOT EXISTS products (
    god_no        TEXT PRIMARY KEY,
    sku_name      TEXT,
    brand_code    TEXT,
    brand_name    TEXT,
    tag_price     INTEGER,
    image_url     TEXT,
    class         TEXT,
    category      TEXT,
    subcategory   TEXT,
    gender        TEXT,
    price_range   TEXT,
    season        TEXT,
    release_year  INTEGER
);

CREATE TABLE IF NOT EXISTS product_attrs (
    god_no   TEXT  NOT NULL,
    att01    TEXT  NOT NULL,
    att02    TEXT,
    att_val  TEXT  NOT NULL,
    PRIMARY KEY (god_no, att01, att_val)
);

CREATE INDEX IF NOT EXISTS idx_class  ON products(class);
CREATE INDEX IF NOT EXISTS idx_gender ON products(gender);
CREATE INDEX IF NOT EXISTS idx_att01  ON product_attrs(att01, att_val);
"""


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(DDL)
    con.commit()
    con.close()
    print(f"DB 초기화 완료: {db_path}")


if __name__ == "__main__":
    init_db()
