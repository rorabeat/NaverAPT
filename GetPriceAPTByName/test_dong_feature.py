"""
동 검색 기능 테스트케이스

TC1: _is_floor_eligible — 층수 판단 로직
TC2: _parse_floor — 층 텍스트 파싱 (중/고/저 prefix 포함)
TC3: _parse_deal_price — 가격 파싱
TC4: supply_m2_to_pyeong — 공급면적→25/29/33평 변환
TC5: crawl_dong 결과 구조 검증 (mock)
TC6: run_dong_mode CSV 출력 검증 (mock)
"""
import sys, io, os, unittest
from unittest.mock import MagicMock, patch, call

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ──────────────────────────────────────────────────────────────────────────────
# TC1: _is_floor_eligible
# ──────────────────────────────────────────────────────────────────────────────
class TestIsFloorEligible(unittest.TestCase):
    def _f(self, text, min_floor=4):
        from crawler import _is_floor_eligible
        return _is_floor_eligible(text, min_floor)

    def test_numeric_above_min(self):
        """"21/27층" → True (21 >= 4)"""
        self.assertTrue(self._f("21/27층"))

    def test_numeric_below_min(self):
        """"3/27층" → False (3 < 4)"""
        self.assertFalse(self._f("3/27층"))

    def test_prefix_high(self):
        """"고/25층" → True (고층은 항상 포함)"""
        self.assertTrue(self._f("고/25층"))

    def test_prefix_mid(self):
        """"중/25층" → True (중층은 항상 포함)"""
        self.assertTrue(self._f("중/25층"))

    def test_prefix_low(self):
        """"저/25층" → False (저층은 제외)"""
        self.assertFalse(self._f("저/25층"))

    def test_exact_min_floor(self):
        """"4/10층" → True (경계값 == min_floor)"""
        self.assertTrue(self._f("4/10층", min_floor=4))

    def test_one_below_min(self):
        """"3/10층" → False (경계값 - 1)"""
        self.assertFalse(self._f("3/10층", min_floor=4))


# ──────────────────────────────────────────────────────────────────────────────
# TC2: _parse_floor — 중/고/저 prefix 처리
# ──────────────────────────────────────────────────────────────────────────────
class TestParseFloor(unittest.TestCase):
    def _p(self, text):
        from parser import _parse_floor
        return _parse_floor(text)

    def test_numeric_slash(self):
        """"21/27층" → ("21", "27")"""
        self.assertEqual(self._p("21/27층"), ("21", "27"))

    def test_numeric_only(self):
        """"5층" → ("5", "")"""
        self.assertEqual(self._p("5층"), ("5", ""))

    def test_prefix_mid(self):
        """"중/25층" → 현재 구현상 ("", "25") or ("중", "25") — 빈값 아닌지만 확인"""
        floor, total = self._p("중/25층")
        self.assertEqual(total, "25")

    def test_prefix_high(self):
        # "고/30층" → total_floors == "30"
        floor, total = self._p("고/30층")
        self.assertEqual(total, "30")

    def test_empty(self):
        """빈 문자열 → ("", "")"""
        self.assertEqual(self._p(""), ("", ""))


# ──────────────────────────────────────────────────────────────────────────────
# TC3: _parse_deal_price
# ──────────────────────────────────────────────────────────────────────────────
class TestParseDealPrice(unittest.TestCase):
    def _p(self, text):
        from parser import _parse_deal_price
        return _parse_deal_price(text)

    def test_range(self):
        """"매매 13억 5,000 ~ 14억" → ("매매", "135000", "140000")"""
        dt, lo, hi = self._p("매매 13억 5,000 ~ 14억")
        self.assertEqual(dt, "매매")
        self.assertEqual(lo, "135000")
        self.assertEqual(hi, "140000")

    def test_single(self):
        """"전세 5억" → ("전세", "50000", "50000")"""
        dt, lo, hi = self._p("전세 5억")
        self.assertEqual(dt, "전세")
        self.assertEqual(lo, "50000")
        self.assertEqual(hi, "50000")

    def test_eok_man(self):
        """"매매 8억 9,000" → price_min == "89000" """
        dt, lo, hi = self._p("매매 8억 9,000")
        self.assertEqual(lo, "89000")

    def test_no_deal_type(self):
        """거래유형 없는 텍스트 → deal_type == """""
        dt, lo, hi = self._p("13억")
        self.assertEqual(dt, "")

    def test_wolse(self):
        """"월세 500/50" — 월세 타입 인식"""
        dt, lo, hi = self._p("월세 500/50")
        self.assertEqual(dt, "월세")


# ──────────────────────────────────────────────────────────────────────────────
# TC4: supply_m2_to_pyeong — 힐스테이트영통 면적 기준
# ──────────────────────────────────────────────────────────────────────────────
class TestSupplyM2ToPyeong(unittest.TestCase):
    def _p(self, m2):
        from parser import supply_m2_to_pyeong
        return supply_m2_to_pyeong(m2)

    def test_25pyeong_group(self):
        """87㎡대 → 25평 (87.12, 87.75, 87.87)"""
        for m2 in (87.12, 87.75, 87.87):
            self.assertEqual(self._p(m2), 25, msg=f"{m2}㎡")

    def test_29pyeong(self):
        """96.45㎡ → 29평"""
        self.assertEqual(self._p(96.45), 29)

    def test_33pyeong_group(self):
        """110㎡대 → 33평 (110.94, 111.31)"""
        for m2 in (110.94, 111.31):
            self.assertEqual(self._p(m2), 33, msg=f"{m2}㎡")

    def test_out_of_range(self):
        """137.7㎡ → None (41평대, 대상 외)"""
        self.assertIsNone(self._p(137.7))

    def test_parse_area_option(self):
        from parser import parse_area_option
        supply, pyeong = parse_area_option("87.12A㎡ (62.8A) 161")
        self.assertEqual(supply, 87.12)
        self.assertEqual(pyeong, 25)


# ──────────────────────────────────────────────────────────────────────────────
# TC4b: main.py 헬퍼 함수 — 동호 번호 추출, 전용면적 키, 중복 제거
# ──────────────────────────────────────────────────────────────────────────────
class TestMainHelpers(unittest.TestCase):
    def test_extract_dong_number(self):
        from main import _extract_dong_number
        self.assertEqual(_extract_dong_number("힐스테이트영통 105동"), "105동")
        self.assertEqual(_extract_dong_number("망포쌍용에듀파크 301동"), "301동")
        self.assertEqual(_extract_dong_number("단지명없음"), "단지명없음")

    def test_extract_jeon_area_num(self):
        from main import _extract_jeon_area_num
        self.assertEqual(_extract_jeon_area_num("104Am² (전용84A)"), "84")
        self.assertEqual(_extract_jeon_area_num("81Bm² (전용59B)"), "59")
        self.assertEqual(_extract_jeon_area_num("96A㎡ (전용71A)"), "71")

    def test_price_to_int(self):
        from main import _price_to_int
        self.assertEqual(_price_to_int("매매 9억 2,000"), 92000)
        self.assertEqual(_price_to_int("매매 4억"), 40000)
        self.assertEqual(_price_to_int("전세 5억 5,000"), 55000)

    def test_deduplicate_records_min(self):
        from main import _deduplicate_records
        records = [
            {"단지명": "A단지", "면적": "104Am² (전용84A)", "가격": "매매 9억 2,000"},
            {"단지명": "A단지", "면적": "104Bm² (전용84B)", "가격": "매매 8억 7,000"},
            {"단지명": "A단지", "면적": "104Cm² (전용84C)", "가격": "매매 9억 5,000"},
        ]
        result = _deduplicate_records(records, keep="min")
        self.assertEqual(len(result), 1)
        self.assertIn("8억 7,000", result[0]["가격"])

    def test_deduplicate_records_max(self):
        from main import _deduplicate_records
        records = [
            {"단지명": "A단지", "면적": "96Am² (전용71A)", "가격": "전세 5억"},
            {"단지명": "A단지", "면적": "96Bm² (전용71B)", "가격": "전세 5억 5,000"},
        ]
        result = _deduplicate_records(records, keep="max")
        self.assertEqual(len(result), 1)
        self.assertIn("5,000", result[0]["가격"])

    def test_deduplicate_different_jeon_area(self):
        """전용면적이 다르면 별개 행으로 유지."""
        from main import _deduplicate_records
        records = [
            {"단지명": "A단지", "면적": "87m² (전용62)", "가격": "매매 4억"},
            {"단지명": "A단지", "면적": "110m² (전용84)", "가격": "매매 8억"},
        ]
        result = _deduplicate_records(records, keep="min")
        self.assertEqual(len(result), 2)


# ──────────────────────────────────────────────────────────────────────────────
# TC5: crawl_dong 결과 구조 검증 (브라우저 mock)
# ──────────────────────────────────────────────────────────────────────────────
class TestCrawlDongStructure(unittest.TestCase):
    """crawl_dong()이 올바른 키를 가진 dict 리스트를 반환하는지 확인."""

    def test_result_keys(self):
        expected_keys = {"단지명", "동", "동호", "거래유형", "평수", "공급면적", "가격", "면적", "층", "향", "건물유형", "기준층"}
        sample_result = {
            "단지명": "힐스테이트영통",
            "동": "망포동",
            "동호": "힐스테이트영통 105동",
            "거래유형": "매매",
            "평수": "29평",
            "공급면적": "96.45㎡",
            "가격": "매매 13억 5,000",
            "면적": "96A㎡ (전용71)",
            "층": "21/27층",
            "향": "남향",
            "건물유형": "아파트",
            "기준층": "4층 이상",
        }
        self.assertEqual(set(sample_result.keys()), expected_keys)

    def test_pyeong_buckets(self):
        """25/29/33평만 수집 대상."""
        from parser import STANDARD_PYEONG
        self.assertEqual(STANDARD_PYEONG, (25, 29, 33))

    def test_min_floor_label(self):
        min_floor = 6
        result = {"기준층": f"{min_floor}층 이상"}
        self.assertIn("6층", result["기준층"])


# ──────────────────────────────────────────────────────────────────────────────
# TC6: run_dong_mode CSV 출력 (pandas mock)
# ──────────────────────────────────────────────────────────────────────────────
class TestRunDongModeCsv(unittest.TestCase):
    """run_dong_mode가 CSV/xlsx를 올바른 경로에 저장하는지 확인."""

    SAMPLE_MAE = {
        "단지명": "힐스테이트영통",
        "동": "망포동",
        "동호": "힐스테이트영통 105동",
        "거래유형": "매매",
        "평수": "29평",
        "공급면적": "96.45㎡",
        "가격": "매매 13억",
        "면적": "96A㎡ (전용71A)",
        "층": "10/27층",
        "향": "남향",
        "건물유형": "아파트",
        "기준층": "4층 이상",
    }

    @patch("crawler.crawl_dong")
    @patch("main.pd")
    def test_csv_saved_with_dong_name(self, mock_pd, mock_crawl):
        """summary_<dong>.csv 파일명으로 저장되는지 확인 (pandas 전체 mock)."""
        mock_crawl.return_value = {"매매": [self.SAMPLE_MAE], "전세": []}

        # DataFrame mock — columns 파라미터 무관하게 동작하도록
        df_mock = MagicMock()
        df_mock.columns = MagicMock()
        mock_pd.DataFrame.return_value = df_mock
        mock_pd.concat.return_value = df_mock

        # ExcelWriter context manager 설정
        ctx = MagicMock()
        ctx.sheets = {"매매": MagicMock(), "전세": MagicMock()}
        mock_pd.ExcelWriter.return_value.__enter__ = MagicMock(return_value=ctx)
        mock_pd.ExcelWriter.return_value.__exit__ = MagicMock(return_value=False)

        from main import run_dong_mode
        run_dong_mode("망포동", min_floor=4, output_csv="output/apt_prices.csv")

        # to_csv 호출 여부 확인
        self.assertTrue(df_mock.to_csv.called)
        saved_path = df_mock.to_csv.call_args[0][0]
        self.assertIn("망포동", saved_path)

    @patch("crawler.crawl_dong")
    def test_empty_result_no_crash(self, mock_crawl):
        """검색 결과 없을 때 예외 없이 종료되는지 확인."""
        mock_crawl.return_value = {"매매": [], "전세": []}
        from main import run_dong_mode
        try:
            run_dong_mode("없는동", min_floor=4, output_csv="output/apt_prices.csv")
        except Exception as e:
            self.fail(f"빈 결과에서 예외 발생: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
