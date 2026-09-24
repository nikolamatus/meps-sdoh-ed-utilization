"""Synthetic-only tests for download placement instructions."""
from feasibility import download


def test_manual_instructions_name_both_pufs():
    text = download._manual_instructions()
    assert "HC-245" in text
    assert "HC-233" in text
    assert "does not scrape" in text


def test_find_longitudinal_respects_empty_dir(tmp_path, monkeypatch):
    from feasibility import config

    monkeypatch.setattr(config, "DATA_RAW_DIR", tmp_path)
    assert download.find_longitudinal_file() is None
