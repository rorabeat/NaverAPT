import re

# 한국 아파트에서 일반적으로 부르는 표준 평형 (공급면적 기준)
STANDARD_PYEONG = (25, 29, 33)
PYEONG_M2 = 3.305785  # 1평 = 3.305785㎡


def _parse_supply_m2(area_text: str) -> float | None:
    """'87.12A㎡ (62.8A) 161' → 87.12 (공급면적 우선)"""
    m = re.search(r"([\d.]+)\s*[A-Za-z]?㎡", area_text)
    if m:
        return float(m.group(1))
    return None


def supply_m2_to_pyeong(supply_m2: float) -> int | None:
    """공급면적(㎡)을 25/29/33평 버킷으로 변환. ±2.0평 허용.
    87.87㎡ = 26.58평이므로 1.5 허용 시 누락 → 2.0으로 조정.
    """
    pyeong = supply_m2 / PYEONG_M2
    for bucket in STANDARD_PYEONG:
        if abs(pyeong - bucket) <= 2.0:
            return bucket
    return None


def parse_area_option(area_text: str) -> tuple[float | None, int | None]:
    """면적 필터 항목 텍스트 → (공급면적㎡, 표준평수)"""
    supply = _parse_supply_m2(area_text)
    if supply is None:
        return None, None
    return supply, supply_m2_to_pyeong(supply)


def _parse_name_dong(name_text: str) -> tuple[str, str]:
    """
    "힐스테이트영통 105동" → ("힐스테이트영통", "105")
    "래미안아파트" → ("래미안아파트", "")
    """
    m = re.match(r"^(.+?)\s*(\d+)동$", name_text.strip())
    if m:
        return m.group(1).strip(), m.group(2)
    return name_text.strip(), ""


def _parse_deal_price(price_text: str) -> tuple[str, str, str]:
    """
    "매매 13억 5,000 ~ 14억" → ("매매", "135000", "140000")
    "전세 5억" → ("전세", "50000", "50000")
    """
    price_text = price_text.strip()

    deal_type = ""
    for dt in ("매매", "전세", "월세"):
        if price_text.startswith(dt):
            deal_type = dt
            price_text = price_text[len(dt):].strip()
            break

    def to_man(s: str) -> str:
        s = s.replace(",", "").replace(" ", "")
        m = re.match(r"(\d+)억(\d+)?", s)
        if m:
            uk = int(m.group(1)) * 10000
            rem = int(m.group(2)) if m.group(2) else 0
            return str(uk + rem)
        m2 = re.match(r"(\d+)", s)
        return m2.group(1) if m2 else ""

    if "~" in price_text:
        parts = price_text.split("~")
        return deal_type, to_man(parts[0]), to_man(parts[1])
    return deal_type, to_man(price_text), to_man(price_text)


def _parse_area(area_text: str) -> str:
    """
    "111A㎡ (전용84A)" → "84"
    "84.99㎡" → "84.99"
    """
    # 전용면적 우선 추출
    m = re.search(r"전용\s*([\d.]+)", area_text)
    if m:
        return m.group(1)
    m = re.search(r"([\d.]+)\s*㎡", area_text)
    if m:
        return m.group(1)
    return area_text.strip()


def _parse_floor(floor_text: str) -> tuple[str, str]:
    """
    "21/27층" → ("21", "27")
    "중/25층" → ("중", "25")
    "5층" → ("5", "")
    """
    t = floor_text.strip()
    # "숫자/숫자층" or "prefix/숫자층"
    m = re.match(r"(.+?)/(\d+)층", t)
    if m:
        return m.group(1), m.group(2)
    m2 = re.match(r"(\d+)층", t)
    if m2:
        return m2.group(1), ""
    return "", ""


def _parse_listing_date(raw_text: str) -> str:
    """raw_text에서 날짜 패턴 추출 → "2026.06.06" → "2026-06-06" """
    m = re.search(r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})", raw_text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m2 = re.search(r"(\d{4})[./\-](\d{1,2})", raw_text)
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}"
    return ""


def parse_article(raw: dict) -> dict | None:
    """crawler 가 추출한 raw dict 를 정제된 record 로 변환한다."""
    name_text = raw.get("name_text", "")
    price_text = raw.get("price_text", "")

    if not name_text and not price_text:
        return None

    complex_name, dong = _parse_name_dong(name_text)
    deal_type, price_min, price_max = _parse_deal_price(price_text)
    area_m2 = _parse_area(raw.get("area_text", ""))
    floor, total_floors = _parse_floor(raw.get("floor_text", ""))
    listing_date = _parse_listing_date(raw.get("raw_text", ""))

    return {
        "complex_name": complex_name,
        "dong": dong,
        "deal_type": deal_type,
        "price_min": price_min,   # 만원 단위
        "price_max": price_max,   # 만원 단위 (단일가면 price_min 과 동일)
        "area_m2": area_m2,
        "floor": floor,
        "total_floors": total_floors,
        "direction": raw.get("direction", ""),
        "building_type": raw.get("building_type", ""),
        "listing_date": listing_date,
    }
