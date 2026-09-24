"""
Locate user-supplied MEPS files. Does not download from AHRQ.

Requires HC-245 in data/raw/. HC-233 is optional (linkage validation /
SDOH weight provenance only).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config


def _manual_instructions() -> str:
    longi = config.MEPS_LONGITUDINAL
    sdoh = config.MEPS_SDOH_CONSOLIDATED
    return f"""
No required MEPS data file found in {config.DATA_RAW_DIR}.

This pipeline does not scrape or guess a download URL. Place files yourself:

  REQUIRED - Panel 24 longitudinal (includes Round-5 SDOH items):
    1. Go to: {longi['doc_url']}
    2. Download the "{longi['stata_zip_hint']}"
    3. Unzip and place the .dta file at:
         {config.DATA_RAW_DIR / longi['expected_filename']}
       (or any *.dta whose name starts with h245 / H245)

  OPTIONAL - 2021 full-year consolidated (validation / SDOHWT21F only):
    1. Go to: {sdoh['doc_url']}
    2. Download the "{sdoh['stata_zip_hint']}"
    3. Place at:
         {config.DATA_RAW_DIR / sdoh['expected_filename']}
    {sdoh['note']}

Then re-run this pipeline.
"""


def _sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _match_stem(path: Path, expected: str) -> bool:
    stem = path.stem.lower()
    target = Path(expected).stem.lower()
    return stem == target or stem.startswith(target)


def find_longitudinal_file() -> Path | None:
    config.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    candidates = sorted(config.DATA_RAW_DIR.glob("*.dta")) + sorted(
        config.DATA_RAW_DIR.glob("*.DTA")
    )
    for path in candidates:
        if _match_stem(path, config.MEPS_LONGITUDINAL["expected_filename"]):
            return path
    return None


def find_optional_consolidated_file() -> Path | None:
    candidates = sorted(config.DATA_RAW_DIR.glob("*.dta")) + sorted(
        config.DATA_RAW_DIR.glob("*.DTA")
    )
    for path in candidates:
        if _match_stem(path, config.MEPS_SDOH_CONSOLIDATED["expected_filename"]):
            return path
    return None


def record_provenance(files: dict[str, Path]) -> dict:
    records = []
    for role, path in files.items():
        meta = (
            config.MEPS_LONGITUDINAL
            if role == "longitudinal"
            else config.MEPS_SDOH_CONSOLIDATED
        )
        records.append(
            {
                "role": role,
                "dataset_name": meta["dataset_name"],
                "puf_id": meta["puf_id"],
                "coverage": meta["coverage"],
                "source_doc_url": meta["doc_url"],
                "file_name": path.name,
                "file_size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    payload = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "User-supplied file(s); not fetched automatically by this pipeline.",
        "files": records,
    }
    out_path = config.DATA_RAW_DIR / "provenance.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> dict[str, Path]:
    longitudinal = find_longitudinal_file()
    if longitudinal is None:
        print(_manual_instructions())
        sys.exit(1)
    files: dict[str, Path] = {"longitudinal": longitudinal}
    optional = find_optional_consolidated_file()
    if optional is not None:
        files["consolidated_2021"] = optional
    record = record_provenance(files)
    for entry in record["files"]:
        print(
            f"Found {entry['role']}: {entry['file_name']} "
            f"({entry['file_size_bytes']:,} bytes, sha256={entry['sha256'][:12]}...)"
        )
    if "consolidated_2021" not in files:
        print(
            "Note: HC-233 not found. Proceeding with HC-245-only SDOH columns "
            "(optional file; see docs/data_sources.md)."
        )
    return files


if __name__ == "__main__":
    main()
