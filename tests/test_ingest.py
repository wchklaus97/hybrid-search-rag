from hybridrag.ingest import extract_period


def test_extract_period_normalises_year_ranges():
    assert extract_period("Head 26 spending, 2025/26 Q4") == "2025-26"
    assert extract_period("Tax year 2025-2026 guide") == "2025-26"
    assert extract_period("No year range here, only 2025 alone") == ""
    assert extract_period("Figures for 2024-2030 are projections") == ""  # not a one-year range
