import csv
import os
import sqlite3

import pandas as pd

from config import OUTPUT_CSV, OUTPUT_DB

# 중복 판단 기준 필드
_DEDUP_KEYS = ("complex_name", "dong", "deal_type", "price_min", "area_m2", "floor")

_COLUMNS = [
    "complex_name", "dong", "deal_type", "price_min", "price_max",
    "area_m2", "floor", "total_floors", "direction", "building_type", "listing_date",
]


def _dedup_key(record: dict) -> tuple:
    return tuple(record.get(k) for k in _DEDUP_KEYS)


# ── SQLite ───────────────────────────────────────────────────────────────────

def _init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS apt_prices (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            complex_name TEXT,
            dong         TEXT,
            deal_type    TEXT,
            price_min    TEXT,
            price_max    TEXT,
            area_m2      TEXT,
            floor        TEXT,
            total_floors TEXT,
            direction    TEXT,
            building_type TEXT,
            listing_date TEXT,
            UNIQUE (complex_name, dong, deal_type, price_min, area_m2, floor)
        )
    """)
    conn.commit()


def save_to_db(records: list[dict], db_path: str = OUTPUT_DB):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        _init_db(conn)
        inserted = 0
        for rec in records:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO apt_prices
                        (complex_name, dong, deal_type, price_min, price_max,
                         area_m2, floor, total_floors, direction, building_type, listing_date)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    [rec.get(c) for c in _COLUMNS],
                )
                if conn.execute("SELECT changes()").fetchone()[0]:
                    inserted += 1
            except sqlite3.Error as e:
                print(f"[storage] DB 오류: {e}")
        conn.commit()
    print(f"[storage] DB 저장 — {inserted}/{len(records)}건 신규 ({db_path})")


# ── CSV ──────────────────────────────────────────────────────────────────────

def save_to_csv(records: list[dict], csv_path: str = OUTPUT_CSV):
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    df_new = pd.DataFrame(records, columns=_COLUMNS)

    if os.path.exists(csv_path):
        df_all = pd.concat([pd.read_csv(csv_path, dtype=str), df_new], ignore_index=True)
    else:
        df_all = df_new

    before = len(df_all)
    df_all = df_all.drop_duplicates(subset=list(_DEDUP_KEYS))
    df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[storage] CSV 저장 — 중복 {before - len(df_all)}건 제거, 총 {len(df_all)}건 ({csv_path})")


# ── 실시간 중복 제거 버퍼 ────────────────────────────────────────────────────

class DedupBuffer:
    def __init__(self):
        self._seen: set[tuple] = set()
        self._records: list[dict] = []

    def add(self, record: dict) -> bool:
        key = _dedup_key(record)
        if key in self._seen:
            return False
        self._seen.add(key)
        self._records.append(record)
        return True

    @property
    def records(self) -> list[dict]:
        return list(self._records)

    def flush(self, csv_path: str = OUTPUT_CSV, db_path: str = OUTPUT_DB):
        if not self._records:
            print("[storage] 저장할 데이터 없음")
            return
        save_to_csv(self._records, csv_path)
        save_to_db(self._records, db_path)
