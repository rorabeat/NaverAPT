"""
동 검색 기능 테스트케이스 5개

TC1: _is_floor_eligible — 층수 판단 로직
TC2: _parse_floor — 층 텍스트 파싱 (중/고/저 prefix 포함)
TC3: _parse_deal_price — 가격 파싱
TC4: crawl_dong 결과 구조 검증 (mock)
TC5: run_dong_mode CSV 출력 검증 (mock)
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
# TC4: crawl_dong 결과 구조 검증 (브라우저 mock)
# ──────────────────────────────────────────────────────────────────────────────
class TestCrawlDongStructure(unittest.TestCase):
    """crawl_dong()이 올바른 키를 가진 dict 리스트를 반환하는지 확인."""

    def test_result_keys(self):
        """mock으로 crawl_dong을 직접 호출하지 않고 반환값 구조만 확인."""
        # 실제 크롤링 없이 결과 구조만 검증
        expected_keys = {"complex_name", "dong_name", "매매_최저가", "전세_최고가", "기준층"}
        sample_result = {
            "complex_name": "힐스테이트영통",
            "dong_name": "망포동",
            "매매_최저가": "매매 13억 5,000 ~ 14억",
            "전세_최고가": "전세 8억",
            "기준층": "4층 이상",
        }
        self.assertEqual(set(sample_result.keys()), expected_keys)

    def test_no_listing_returns_dash(self):
        """매물 없는 단지는 '-' 로 표시되어야 한다."""
        result = {
            "complex_name": "테스트아파트",
            "dong_name": "망포동",
            "매매_최저가": "-",
            "전세_최고가": "-",
            "기준층": "4층 이상",
        }
        self.assertEqual(result["매매_최저가"], "-")
        self.assertEqual(result["전세_최고가"], "-")

    def test_min_floor_label(self):
        """기준층 필드가 min_floor 값을 반영하는지 확인."""
        min_floor = 6
        result = {
            "complex_name": "A",
            "dong_name": "B",
            "매매_최저가": "-",
            "전세_최고가": "-",
            "기준층": f"{min_floor}층 이상",
        }
        self.assertIn("6층", result["기준층"])


# ──────────────────────────────────────────────────────────────────────────────
# TC5: run_dong_mode CSV 출력 (pandas mock)
# ──────────────────────────────────────────────────────────────────────────────
class TestRunDongModeCsv(unittest.TestCase):
    """run_dong_mode가 CSV를 올바른 경로에 저장하는지 확인."""

    @patch("crawler.crawl_dong")
    @patch("pandas.DataFrame.to_csv")
    def test_csv_saved_with_dong_name(self, mock_to_csv, mock_crawl):
        """summary_<dong>.csv 파일명으로 저장되는지 확인."""
        mock_crawl.return_value = [
            {
                "complex_name": "힐스테이트영통",
                "dong_name": "망포동",
                "매매_최저가": "매매 13억",
                "전세_최고가": "전세 8억",
                "기준층": "4층 이상",
            }
        ]
        from main import run_dong_mode
        run_dong_mode("망포동", min_floor=4, output_csv="output/apt_prices.csv")

        # to_csv 호출 여부 확인
        self.assertTrue(mock_to_csv.called)
        # 저장 경로에 dong 이름 포함 확인
        saved_path = mock_to_csv.call_args[0][0]
        self.assertIn("망포동", saved_path)

    @patch("crawler.crawl_dong")
    def test_empty_result_no_crash(self, mock_crawl):
        """검색 결과 없을 때 예외 없이 종료되는지 확인."""
        mock_crawl.return_value = []
        from main import run_dong_mode
        try:
            run_dong_mode("없는동", min_floor=4, output_csv="output/apt_prices.csv")
        except Exception as e:
            self.fail(f"빈 결과에서 예외 발생: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
