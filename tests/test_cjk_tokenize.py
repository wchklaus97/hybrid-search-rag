import subprocess
import sys
from pathlib import Path

from hybridrag.cjk_tokenize import STOPWORDS, tokenize


def test_chinese_becomes_overlapping_bigrams():
    assert tokenize("資料外洩") == ["資料", "料外", "外洩"]


def test_lone_cjk_character_stays_a_unigram():
    assert tokenize("X 字 Y") == ["x", "字", "y"]


def test_latin_lowercased_and_stopwords_dropped():
    assert tokenize("How do I contact the Compliance Officer?") == ["contact", "compliance", "officer"]
    assert {"how", "the", "do"} <= STOPWORDS


def test_thousands_separators_removed_so_amounts_match():
    assert tokenize("HKD 5,000") == tokenize("hkd 5000") == ["hkd", "5000"]
    assert tokenize("RMB 50,000") == ["rmb", "50000"]


def test_codes_keep_shape_and_parts():
    assert tokenize("FIN-07") == ["fin-07", "fin", "07"]


def test_full_width_forms_are_normalised():
    assert tokenize("ＨＫＤ　５，０００") == ["hkd", "5000"]  # full-width letters, space, digits and comma


def test_code_mixed_hong_kong_sentence():
    toks = tokenize("如懷疑資料外洩，須喺 24 小時內通知 Compliance Officer")
    assert {"外洩", "資料", "24", "小時", "compliance", "officer"} <= set(toks)


def test_module_is_standalone():
    """cjk_tokenize.py must work when copied alone: loading it must not import the package."""
    path = Path(__file__).parent.parent / "src" / "hybridrag" / "cjk_tokenize.py"
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('cjk_tokenize', {str(path)!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "assert m.tokenize('年假 FIN-07') == ['年假', 'fin-07', 'fin', '07']\n"
        "print(any(name.startswith('hybridrag') for name in sys.modules))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip()
    assert out == "False"
