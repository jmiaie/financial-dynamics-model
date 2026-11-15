"""Tests for the fail-closed behaviour of the historical-regime-study pack verifier.

Every test works on a copy of the committed pack under ``tmp_path``; the real
repository tree is never written to. Figure and table regeneration checks are
deliberately not exercised (renderer / git dependent).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_REL = Path("publication/historical-regime-study")
SCRIPT = REPO_ROOT / PACK_REL / "scripts" / "verify_pack.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="verify_pack.py not present")


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_pack_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(root: Path, *checks: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT), "--repo-root", str(root)]
    for c in checks:
        cmd += ["--check", c]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    """Minimal copy of the pack plus every file its source map cites."""
    root = tmp_path / "repo"
    src_pack = REPO_ROOT / PACK_REL
    dst_pack = root / PACK_REL
    shutil.copytree(src_pack, dst_pack, ignore=shutil.ignore_patterns("figures", "__pycache__"))
    smap = json.loads((src_pack / "tables" / "source_map.json").read_text(encoding="utf-8"))
    for rel in {row["file"] for row in smap}:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, dst)
    return root


def _cited_files(root: Path) -> list[str]:
    smap = json.loads((root / PACK_REL / "tables" / "source_map.json").read_text("utf-8"))
    return sorted({r["file"] for r in smap if r.get("kind", "whole_file_sha256") != "field_value"})


def _flip_last_byte(path: Path) -> None:
    data = bytearray(path.read_bytes())
    data[-1] ^= 0x01
    path.write_bytes(bytes(data))


def test_sha256_file_known_input(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_bytes(b"abc")
    assert _load_module().sha256_file(f) == hashlib.sha256(b"abc").hexdigest()
    assert (
        _load_module().sha256_file(f)
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_committed_pack_passes_offline_checks(pack: Path) -> None:
    r = _run(pack, "hashes", "citations", "no-rerun")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RESULT: all 3 check(s) passed" in r.stdout


def test_one_byte_tamper_of_pinned_file_fails_hashes(pack: Path) -> None:
    target = pack / _cited_files(pack)[0]
    _flip_last_byte(target)
    r = _run(pack, "hashes")
    assert r.returncode != 0
    assert "FAIL [hashes]" in r.stdout
    assert "hash mismatch" in r.stdout


def test_every_pinned_file_is_individually_protected(pack: Path) -> None:
    for rel in _cited_files(pack):
        path = pack / rel
        original = path.read_bytes()
        _flip_last_byte(path)
        try:
            r = _run(pack, "hashes")
            assert r.returncode != 0, f"tamper of {rel} was not detected"
        finally:
            path.write_bytes(original)


def test_missing_pinned_file_fails_hashes(pack: Path) -> None:
    (pack / _cited_files(pack)[0]).unlink()
    r = _run(pack, "hashes")
    assert r.returncode != 0
    assert "cited file missing on disk" in r.stdout


def test_missing_source_map_fails_hashes(pack: Path) -> None:
    (pack / PACK_REL / "tables" / "source_map.json").unlink()
    r = _run(pack, "hashes")
    assert r.returncode != 0
    assert "missing" in r.stdout


def test_wrong_recorded_field_value_fails_hashes(pack: Path) -> None:
    smap_path = pack / PACK_REL / "tables" / "source_map.json"
    smap = json.loads(smap_path.read_text(encoding="utf-8"))
    row = next(r for r in smap if r.get("kind") == "field_value")
    row["sha256"] = "0" * 64
    smap_path.write_text(json.dumps(smap), encoding="utf-8")
    r = _run(pack, "hashes")
    assert r.returncode != 0
    assert "field-value mismatch" in r.stdout


def test_stale_hash_literal_in_source_gate_fails(pack: Path) -> None:
    gate = pack / PACK_REL / "SOURCE-GATE.md"
    gate.write_text(gate.read_text("utf-8") + "\n" + "ab" * 32 + "\n", encoding="utf-8")
    r = _run(pack, "hashes")
    assert r.returncode != 0
    assert "SOURCE-GATE.md cites hash" in r.stdout


def test_unresolvable_citation_fails(pack: Path) -> None:
    reg = pack / PACK_REL / "CLAIM-REGISTER.md"
    reg.write_text(reg.read_text("utf-8") + "\n`bogus.row.id_that_does_not_exist`\n", "utf-8")
    r = _run(pack, "citations")
    assert r.returncode != 0
    assert "bogus.row.id_that_does_not_exist" in r.stdout


def test_wildcard_citation_without_match_fails(pack: Path) -> None:
    reg = pack / PACK_REL / "CLAIM-REGISTER.md"
    reg.write_text(reg.read_text("utf-8") + "\n`nomatch.*.nothing`\n", "utf-8")
    assert _run(pack, "citations").returncode != 0


def test_forbidden_rerun_invocation_fails_no_rerun(pack: Path) -> None:
    bad = pack / PACK_REL / "scripts" / "evil.py"
    bad.write_text(
        'import subprocess\nsubprocess.run(["python", "scripts/run_historical_regime_study.py"])\n',
        encoding="utf-8",
    )
    r = _run(pack, "no-rerun")
    assert r.returncode != 0
    assert "evil.py" in r.stdout


def test_figures_check_fails_closed_without_committed_pngs(pack: Path) -> None:
    # The fixture copy has no figures/ directory: an empty figure set must fail
    # (or fail on a missing matplotlib pin) -- never pass. No rendering happens.
    r = _run(pack, "figures")
    assert r.returncode != 0
    assert "FAIL [figures]" in r.stdout
