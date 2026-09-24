"""
Synthetic-only tests for download placement instructions.
"""
from feasibility import config, download


def test_manual_instructions_name_both_pufs(capsys):
    # Force empty discovery by pointing at a temp empty dir via monkeypatch-like call
    original = config.DATA_RAW_DIR
    try:
        # Use the real empty raw dir in this repo (no .dta files committed).
        found = download.find_longitudinal_file()
        assert found is None
        text = download._manual_instructions()
        assert "HC-245" in text
        assert "HC-233" in text
        assert "does not scrape" in text.lower() or "does not scrape" in text
    finally:
        assert config.DATA_RAW_DIR == original
