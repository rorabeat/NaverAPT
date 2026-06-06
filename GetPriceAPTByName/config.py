import random

# 목표 URL
TARGET_URL = (
    "https://fin.land.naver.com/map"
    "?center=3zkle5-2Ayvzo"
    "&layer=NobwRAlgJmBcYGMD2BbADgGwKYA8D6UWALgIYQZgA0YaJATiSgM5zjLrY4CSM8"
    "AjAAYAnABY%2BAJjABfakyz0EACwAK9Ri1jgITAGrkMJOADMSGOdVIAjO"
    "ABUGhDwE80WBpgAIJ80tR0xACudAB2JJZOsER0UVhSALpAA"
    "&zoom=14.400225253300547"
)

# 실제 DOM 검증 완료된 CSS 셀렉터
SELECTORS = {
    # 지도 위 아파트 단지 마커 — button 형태 (ComplexMarkerDefault_article 확인)
    "complex_marker": "button[class*='ComplexMarkerDefault_article']",
    # 단지 상세 패널 매물 목록 UL (247개 LI 확인)
    "article_list_ul": "[class*='ComplexArticleTab_article']",
    # 매물 카드 LI
    "article_items": "li[class*='ArticleCard_item']",
    # 단지명+동 (예: "힐스테이트영통 105동")
    "card_name": "[class*='ArticleCard_name']",
    # 거래유형+가격 (예: "매매 13억 5,000 ~ 14억")
    "card_price": "[class*='ArticleCard_area-price']",
    # 요약 항목 [0]유형 [1]면적 [2]층 [3]향
    "card_summary_items": "[class*='ArticleCard_item-summary']",
    # 패널 탭 버튼 (LineTab-module_link)
    "panel_tab_button": "button[class*='LineTab-module_link']",
    # 더보기 버튼 (매물목록 펼치기)
    "expand_button": "[class*='ArticleCard_button-expand']",
    # 패널 스크롤 영역
    "panel_scroll": "#complex_detail",
    # 면적 필터 (전체면적 칩 + 체크박스 레이어)
    "area_filter_chip": "button#면적, button[id='면적']",
    "area_filter_layer": "[class*='ComplexArticleFilter_area-filter'] [class*='CheckboxLayer']",
    "area_filter_items": "[class*='ComplexArticleFilter_area-filter'] [class*='CheckboxLayer'] ul li label",
}

# 딜레이 설정 (초)
DELAY_MIN = 1.5
DELAY_MAX = 3.0


def random_delay() -> float:
    return random.uniform(DELAY_MIN, DELAY_MAX)


# 출력 파일 기본 경로
OUTPUT_CSV = "output/apt_prices.csv"
OUTPUT_DB = "output/apt_prices.db"

# 브라우저 설정 (undetected-chromedriver)
HEADLESS = False
WINDOW_SIZE = (1400, 900)
UC_VERSION: int | None = 148  # Chrome 148.0.7778.217
