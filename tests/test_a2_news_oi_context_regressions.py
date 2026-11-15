"""A2 follow-up: ten user-managed slots, optional news and four Dhan OI contexts."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"


def test_news_and_four_oi_filters_are_selectable_without_a_fake_vote():
    source = (ROOT / "scanner_engine.py").read_text(encoding="utf-8")
    ast.parse(source)
    namespace = {}
    exec(compile(source, str(ROOT / "scanner_engine.py"), "exec"), namespace)
    assert namespace["DEFAULT_FILTERS"] and len(namespace["DEFAULT_FILTERS"]) == 10
    names = namespace["ALL_FILTERS"]
    for name in ("News Headlines", "OI Support", "OI Resistance", "OI Profile", "Max Pain"):
        assert name in names
    assert len(names) == len(set(names))
    assert 'add("News Headlines",None' in source
    assert 'add(name,None,"WAIT: Dhan option-chain metrics' in source


def test_mobile_filter_context_is_display_only_and_slots_stay_ten():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert 'filter_selected=list(dict.fromkeys' in source
    assert '[:MAX_ACTIVE_FILTERS]' in source
    assert 'elif len(filter_selected)>=MAX_ACTIVE_FILTERS:' in source
    assert 'def enrich_context_filter_rows(sym,rows):' in source
    assert 'row["vote"]=None' in source
    assert 'data=dhan_option_metrics' in source
    assert 'news_cache.get(sym)' in source
    assert 'report_rows=enrich_context_filter_rows(sym,' in source
    assert 'rows=enrich_context_filter_rows(sym,' in source
