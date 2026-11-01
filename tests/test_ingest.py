from hybridrag.ingest import extract_period


def test_extract_period_normalises_year_ranges():
    assert extract_period("Head 26 spending, 2025/26 Q4") == "2025-26"
    assert extract_period("Tax year 2025-2026 guide") == "2025-26"
    assert extract_period("No year range here, only 2025 alone") == ""
    assert extract_period("Figures for 2024-2030 are projections") == ""  # not a one-year range


def test_year_ranges_finds_every_range_in_the_text():
    from hybridrag.ingest import year_ranges

    text = "2025/26 稅率；2019–2020 課稅年度；2024-25 寬減；無年份"
    assert year_ranges(text) == {"2025-26", "2019-20", "2024-25"}
    assert year_ranges("沒有年份") == set()
