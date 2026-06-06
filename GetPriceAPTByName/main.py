import argparse
import sys
import io
import os

# Windows 콘솔 cp949 → utf-8 강제 (em dash 등 처리)
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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


def run_dong_mode(dong_name: str, min_floor: int, output_csv: str):
    from crawler import crawl_dong
    import pandas as pd

    data = crawl_dong(dong_name, min_floor=min_floor)
    mae_list = data["매매"]
    jeon_list = data["전세"]

    if not mae_list and not jeon_list:
        print(f"[main] '{dong_name}' 결과 없음")
        return

    # 컬럼 순서 정의
    cols = ["단지명", "동", "동호", "거래유형", "가격", "면적", "층", "향", "건물유형", "기준층"]

    df_mae  = pd.DataFrame(mae_list,  columns=cols) if mae_list  else pd.DataFrame(columns=cols)
    df_jeon = pd.DataFrame(jeon_list, columns=cols) if jeon_list else pd.DataFrame(columns=cols)

    # 콘솔 요약 출력
    print(f"\n[결과] {dong_name} — {min_floor}층 이상 기준")
    print(f"  매매: {len(df_mae)}건 / 전세: {len(df_jeon)}건")

    # Excel 저장 (시트: 매매 / 전세)
    os.makedirs("output", exist_ok=True)
    xlsx_path = f"output/summary_{dong_name}.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_mae.to_excel(writer,  sheet_name="매매", index=False)
        df_jeon.to_excel(writer, sheet_name="전세", index=False)

        # 컬럼 너비 자동 조정
        for sheet_name, df in [("매매", df_mae), ("전세", df_jeon)]:
            ws = writer.sheets[sheet_name]
            for col_cells in ws.columns:
                max_len = max((len(str(c.value)) if c.value else 0) for c in col_cells)
                ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 40)

    print(f"[main] 저장 완료: {xlsx_path}")

    # CSV도 함께 저장 (매매+전세 합본)
    all_df = pd.concat([df_mae, df_jeon], ignore_index=True)
    csv_path = f"output/summary_{dong_name}.csv"
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
    args = parse_args()
    if args.dong:
        run_dong_mode(args.dong, args.min_floor, args.output_csv)
    else:
        run_map_mode(args)


if __name__ == "__main__":
    main()
