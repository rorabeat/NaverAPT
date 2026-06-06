import argparse
import re
import sys
import io
import os
from datetime import datetime

import pandas as pd
from openpyxl.styles import PatternFill, Border, Side, Font, Alignment

import config
from config import OUTPUT_CSV, OUTPUT_DB, TARGET_URL


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="네이버 부동산 아파트 매물 크롤러")
    parser.add_argument("--dong", default=None, help="검색할 동 이름 (예: 망포동)")
    parser.add_argument("--min-floor", type=int, default=4, help="최소 층수 (기본값: 4)")
    parser.add_argument("--url", default=TARGET_URL, help="네이버 부동산 지도 URL (--dong 없을 때 사용)")
    parser.add_argument("--output-csv", default=OUTPUT_CSV)
    parser.add_argument("--output-db", default=OUTPUT_DB)
    return parser.parse_args()


def _extract_dong_number(unit_text: str) -> str:
    """'힐스테이트영통 105동' → '105동', '힐스테이트영통' → ''"""
    m = re.search(r'(\d+동)', unit_text)
    return m.group(1) if m else unit_text.strip()


def _extract_jeon_area_num(area_text: str) -> str:
    """'104Am² (전용84A)' → '84', '81Bm² (전용59B)' → '59'"""
    m = re.search(r'전용\s*(\d+)', area_text)
    return m.group(1) if m else area_text.strip()


def _price_to_int(price_text: str) -> int:
    """'매매 9억 2,000' → 92000, 비교용 정수 변환."""
    price_text = re.sub(r'^(매매|전세|월세)\s*', '', price_text.strip())
    price_text = price_text.replace(",", "").replace(" ", "")
    m = re.match(r'(\d+)억(\d+)?', price_text)
    if m:
        return int(m.group(1)) * 10000 + (int(m.group(2)) if m.group(2) else 0)
    m2 = re.match(r'(\d+)', price_text)
    return int(m2.group(1)) if m2 else 0


def _deduplicate_records(records: list[dict], keep: str) -> list[dict]:
    """전용면적 번호 기준 그룹핑 후 keep='min'이면 최저가, 'max'이면 최고가 1건 유지."""
    groups: dict[tuple, tuple[int, dict]] = {}
    for r in records:
        jeon_key = _extract_jeon_area_num(r.get("면적", ""))
        group_key = (r.get("단지명", ""), jeon_key)
        price_val = _price_to_int(r.get("가격", ""))
        if group_key not in groups:
            groups[group_key] = (price_val, r)
        else:
            existing_val, _ = groups[group_key]
            if (keep == "min" and price_val < existing_val) or \
               (keep == "max" and price_val > existing_val):
                groups[group_key] = (price_val, r)
    return [r for _, r in groups.values()]


def _apply_excel_style(ws):
    """헤더 회색 배경, 데이터 영역 외곽선 적용."""
    header_fill = PatternFill(fill_type="solid", fgColor="C0C0C0")
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    max_row = ws.max_row
    max_col = ws.max_column

    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
        for cell in row:
            cell.border = border
            if cell.row == 1:
                cell.fill = header_fill
                cell.font = Font(bold=True)
            cell.alignment = Alignment(vertical="center")


def run_dong_mode(dong_name: str, min_floor: int, output_csv: str):
    from crawler import crawl_dong

    data = crawl_dong(dong_name, min_floor=min_floor)
    mae_list = data["매매"]
    jeon_list = data["전세"]

    if not mae_list and not jeon_list:
        print(f"[main] '{dong_name}' 결과 없음")
        return

    # 동호: 동 번호만 표시
    for r in mae_list + jeon_list:
        r["동호"] = _extract_dong_number(r.get("동호", ""))

    # 전용면적 기준 중복 제거 (매매=최저가, 전세=최고가)
    mae_list  = _deduplicate_records(mae_list,  keep="min")
    jeon_list = _deduplicate_records(jeon_list, keep="max")

    # 컬럼 순서 (건물유형·기준층 제외)
    cols = ["단지명", "동", "동호", "거래유형", "평수", "공급면적", "가격", "면적", "층", "향"]

    df_mae  = pd.DataFrame(mae_list,  columns=cols) if mae_list  else pd.DataFrame(columns=cols)
    df_jeon = pd.DataFrame(jeon_list, columns=cols) if jeon_list else pd.DataFrame(columns=cols)

    print(f"\n[결과] {dong_name} — {min_floor}층 이상 / 전용면적별 최저·최고가")
    print(f"  매매: {len(df_mae)}건 / 전세: {len(df_jeon)}건")

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_path = f"output/{timestamp}_{dong_name}.xlsx"

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_mae.to_excel(writer,  sheet_name="매매", index=False)
        df_jeon.to_excel(writer, sheet_name="전세", index=False)

        for sheet_name, df in [("매매", df_mae), ("전세", df_jeon)]:
            ws = writer.sheets[sheet_name]
            # 컬럼 너비 자동 조정
            for col_cells in ws.columns:
                max_len = max((len(str(c.value)) if c.value else 0) for c in col_cells)
                ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 40)
            # 스타일 적용
            _apply_excel_style(ws)

    print(f"[main] 저장 완료: {xlsx_path}")

    all_df = pd.concat([df_mae, df_jeon], ignore_index=True)
    csv_path = f"output/{timestamp}_{dong_name}.csv"
    try:
        all_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[main] CSV 저장 완료: {csv_path}")
    except PermissionError:
        print(f"[main] CSV 저장 건너뜀 (파일이 열려 있음): {csv_path}")


def run_map_mode(args):
    from crawler import crawl
    from parser import parse_article
    from storage import DedupBuffer

    config.TARGET_URL = args.url
    buffer = DedupBuffer()
    total_raw = total_parsed = total_dup = 0

    print("[main] 크롤링 시작")
    try:
        for raw in crawl():
            total_raw += 1
            record = parse_article(raw)
            if record is None:
                continue
            total_parsed += 1
            if not buffer.add(record):
                total_dup += 1

    except KeyboardInterrupt:
        print("\n[main] 중단 — 수집 데이터를 저장합니다.")
    except Exception as e:
        print(f"[main] 오류: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        print(f"[main] 수집 {total_raw}건 / 파싱 {total_parsed}건 / 중복 {total_dup}건 / 저장 {len(buffer.records)}건")
        buffer.flush(csv_path=args.output_csv, db_path=args.output_db)


def main():
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    args = parse_args()
    if args.dong:
        run_dong_mode(args.dong, args.min_floor, args.output_csv)
    else:
        run_map_mode(args)


if __name__ == "__main__":
    main()
