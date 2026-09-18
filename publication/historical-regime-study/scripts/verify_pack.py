#!/usr/bin/env python3
"""CI verification script for the D10-A publication pack.

Runs entirely offline against the already-committed repository state. It
NEVER invokes `scripts/run_historical_regime_study.py` or
`scripts/acquire_yf_fd_etfs_daily.py`, and makes no network calls -- it only
reads already-committed files, recomputes hashes, re-runs the two
deterministic generator scripts, and diffs their output against what is
already committed.

Checks performed (each prints a clear PASS/FAIL and the script exits
non-zero if any check fails):

1. hashes    -- every unique (file, sha256) pair recorded in
                tables/source_map.json is re-verified against the real file
                on disk (fail closed: missing file or hash mismatch is a
                hard failure), and every 64-hex-character hash literal
                quoted in SOURCE-GATE.md is confirmed to be a member of that
                same freshly-verified hash set.
2. tables    -- re-running scripts/generate_tables.py reproduces the
                committed tables/ directory byte-for-byte (via `git diff
                --exit-code`).
3. figures   -- re-running scripts/generate_figures.py reproduces the
                committed figures/*.png; byte-identical is tried first, and
                only on failure does this fall back to a pixel-content
                comparison, with the outcome logged explicitly either way.
                The committed PNGs are deleted before generation, so if
                generation is skipped or writes nothing (e.g. matplotlib is
                missing) the check FAILS: a figure missing after the run is
                never scored as a byte-identical match against the file's own
                stale bytes.
4. citations -- every citation identifier quoted in CLAIM-REGISTER.md
                resolves to a real row_id in tables/source_map.json
                (citations containing `*` are matched against row_ids as
                shell globs, so `primary.*.persistence.self_trans` matches
                any period).
5. no-rerun  -- self-audit: neither this script nor the two generator
                scripts reference scripts/run_historical_regime_study.py or
                scripts/acquire_yf_fd_etfs_daily.py.

Usage:
    python publication/historical-regime-study/scripts/verify_pack.py
    python publication/historical-regime-study/scripts/verify_pack.py --check hashes
(run from the repository root; also works from any cwd via --repo-root)
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PACK_DIR = Path("publication/historical-regime-study")
FORBIDDEN_SCRIPTS = [
    "scripts/run_historical_regime_study.py",
    "scripts/acquire_yf_fd_etfs_daily.py",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(msg, flush=True)


class CheckFailure(Exception):
    pass


def check_hashes(repo_root: Path) -> None:
    log("=== Check: hashes ===")
    smap_path = repo_root / PACK_DIR / "tables" / "source_map.json"
    if not smap_path.exists():
        raise CheckFailure(f"missing {smap_path} -- run generate_tables.py first")
    smap = json.loads(smap_path.read_text(encoding="utf-8"))

    # 1a. Every row with kind == "whole_file_sha256" (the default -- see
    # generate_tables.py's SourceMap docstring) must have `sha256` equal to
    # the real whole-file hash of `file`. A small number of rows are
    # kind == "field_value": `sha256` there is the *value* of an embedded
    # JSON field (e.g. dataset_canonical), not a hash of `file` itself, and
    # those are verified separately in step 1c below.
    file_to_hash: dict[str, str] = {}
    field_value_rows: list[dict[str, str]] = []
    for row in smap:
        if row.get("kind", "whole_file_sha256") == "field_value":
            field_value_rows.append(row)
            continue
        f, h = row["file"], row["sha256"]
        if f in file_to_hash and file_to_hash[f] != h:
            raise CheckFailure(
                f"internal inconsistency in source_map.json: {f} has two different "
                f"recorded whole-file hashes ({file_to_hash[f]} vs {h})"
            )
        file_to_hash[f] = h

    verified_hashes: set[str] = set()
    n_checked = 0
    for rel_path, expected_hash in sorted(file_to_hash.items()):
        abs_path = repo_root / rel_path
        if not abs_path.exists():
            raise CheckFailure(f"cited file missing on disk: {rel_path}")
        actual_hash = sha256_file(abs_path)
        if actual_hash != expected_hash:
            raise CheckFailure(
                f"hash mismatch for {rel_path}: source_map.json says "
                f"{expected_hash}, actual is {actual_hash}"
            )
        verified_hashes.add(actual_hash)
        n_checked += 1
    log(f"PASS: {n_checked} unique cited files re-verified (whole-file sha256) against source_map.json")

    # 1c. field_value rows: re-derive the actual field value from the file
    # and confirm it matches what source_map.json recorded. Currently this
    # is just the two dataset_canonical fields.
    n_field_checked = 0
    for row in field_value_rows:
        abs_path = repo_root / row["file"]
        if not abs_path.exists():
            raise CheckFailure(f"cited file missing on disk: {row['file']}")
        if row["key_path"] == "sha256.dataset_canonical":
            doc = json.loads(abs_path.read_text(encoding="utf-8"))
            actual_value = doc["sha256"]["dataset_canonical"]
        else:
            raise CheckFailure(
                f"unrecognized field_value key_path (verify_pack.py needs a new case): "
                f"{row['row_id']} -> {row['key_path']}"
            )
        if actual_value != row["sha256"]:
            raise CheckFailure(
                f"field-value mismatch for {row['row_id']} ({row['file']}#{row['key_path']}): "
                f"source_map.json says {row['sha256']}, actual is {actual_value}"
            )
        # These field values (dataset_canonical) look like sha256 hashes and
        # are quoted verbatim in SOURCE-GATE.md, so they must also count as
        # "known good" for the literal-hash-citation check below, even
        # though they are not whole-file hashes.
        verified_hashes.add(actual_value)
        n_field_checked += 1
    log(f"PASS: {n_field_checked} embedded field-value citation(s) re-derived and matched")

    # 1d. Every 64-hex-char hash literal quoted in SOURCE-GATE.md must be a
    # member of the freshly-verified hash set above (i.e. not stale/hand-typed).
    source_gate_path = repo_root / PACK_DIR / "SOURCE-GATE.md"
    text = source_gate_path.read_text(encoding="utf-8")
    cited_hashes = set(re.findall(r"[0-9a-f]{64}", text))
    unverifiable = cited_hashes - verified_hashes
    if unverifiable:
        raise CheckFailure(
            "SOURCE-GATE.md cites hash(es) not found among the freshly-verified "
            f"file hash set (possible stale/typo): {sorted(unverifiable)}"
        )
    log(f"PASS: all {len(cited_hashes)} distinct sha256 literals in SOURCE-GATE.md "
        f"are verified-current file hashes")


def check_tables(repo_root: Path) -> None:
    log("=== Check: tables (regeneration must be byte-identical to committed) ===")
    script = repo_root / PACK_DIR / "scripts" / "generate_tables.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
    )
    log(result.stdout)
    if result.returncode != 0:
        log(result.stderr)
        raise CheckFailure("generate_tables.py exited non-zero")

    diff = subprocess.run(
        ["git", "diff", "--exit-code", "--stat", "--", str(PACK_DIR / "tables")],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        log(diff.stdout)
        raise CheckFailure(
            "committed tables/ differ from freshly regenerated output -- "
            "the pack's tables are not reproducible from the committed artifacts"
        )
    log("PASS: regenerated tables/ byte-identical to committed output")


def _compare_png_pixels(path_a: Path, path_b: Path) -> tuple[bool, str]:
    """Best-effort content-level PNG comparison, used only as a fallback
    when byte-identical regeneration fails (e.g. cross-environment
    font/freetype rendering differences). Returns (equivalent, detail)."""
    try:
        import numpy as np
        from matplotlib import image as mpimg
    except ImportError as exc:  # pragma: no cover - matplotlib is a base dep
        return False, f"cannot run pixel fallback, missing dependency: {exc}"

    arr_a = mpimg.imread(path_a)
    arr_b = mpimg.imread(path_b)
    if arr_a.shape != arr_b.shape:
        return False, f"shape mismatch {arr_a.shape} vs {arr_b.shape}"
    diff = np.abs(arr_a.astype(float) - arr_b.astype(float))
    mean_abs_diff = float(diff.mean())
    max_abs_diff = float(diff.max())
    # Tolerance: mean per-channel difference under 1/255 (i.e. sub-single-bit
    # on average) and no single pixel/channel off by more than ~2/255 --
    # tight enough to catch a genuinely different figure, loose enough to
    # tolerate anti-aliasing/font-hinting variance across environments.
    equivalent = mean_abs_diff < (1.0 / 255.0) and max_abs_diff < (3.0 / 255.0)
    detail = f"shape={arr_a.shape}, mean_abs_diff={mean_abs_diff:.6f}, max_abs_diff={max_abs_diff:.6f}"
    return equivalent, detail


def check_figures(repo_root: Path) -> None:
    log("=== Check: figures (regeneration must match committed, byte-ideal / pixel-fallback) ===")
    figures_dir = repo_root / PACK_DIR / "figures"
    committed_pngs = sorted(figures_dir.glob("*.png"))
    # Fail closed on an EMPTY committed-figure set. This branch used to log
    # SKIP and return success when no committed PNG was found -- so deleting
    # both tracked PNGs turned the whole check green without generating
    # anything at all (found by independent re-review, 2026-09-18). A pack
    # that ships figures must reproduce them; absence of the committed files
    # is a failure, not a skipped check.
    if not committed_pngs:
        raise CheckFailure(
            f"no committed figures/*.png found in {figures_dir} -- nothing to "
            f"verify, and no evidence the figures regenerate. Refusing to "
            f"report a PASS on an empty figure set."
        )

    # Snapshot committed bytes, then remove the committed PNGs from disk so a
    # skipped or no-op generation cannot be scored as a byte-identical PASS
    # against the file's own stale bytes -- that fail-open path silently
    # turned a missing matplotlib into "all figures reproduced".
    committed_bytes = {p.name: p.read_bytes() for p in committed_pngs}
    try:
        for _p in committed_pngs:
            _p.unlink()

        script = repo_root / PACK_DIR / "scripts" / "generate_figures.py"
        result = subprocess.run(
            [sys.executable, str(script), "--repo-root", str(repo_root)],
            capture_output=True,
            text=True,
        )
        log(result.stdout)
        if result.returncode != 0:
            log(result.stderr)
            raise CheckFailure("generate_figures.py exited non-zero")

        any_pixel_fallback = False
        for name, old_bytes in committed_bytes.items():
            new_path = figures_dir / name
            if not new_path.exists():
                raise CheckFailure(
                    f"{name}: regeneration produced no file -- generation was "
                    f"skipped (matplotlib missing?) or wrote nothing. A missing "
                    f"figure is a FAILURE, not a byte-identical PASS against the "
                    f"stale committed file."
                )
            new_bytes = new_path.read_bytes()
            if new_bytes == old_bytes:
                log(f"PASS (byte-identical): {name}")
                continue
            # Byte-identical failed -- fall back to a content-level comparison.
            # Restore the committed bytes to a temp file for comparison, then
            # write the regenerated bytes back (the regenerated file is already
            # on disk at new_path).
            tmp_committed = new_path.with_suffix(".committed.png")
            tmp_committed.write_bytes(old_bytes)
            try:
                equivalent, detail = _compare_png_pixels(tmp_committed, new_path)
            finally:
                tmp_committed.unlink(missing_ok=True)
            if not equivalent:
                raise CheckFailure(
                    f"{name}: NOT byte-identical to committed AND pixel-content "
                    f"comparison exceeded tolerance ({detail}) -- treating as a "
                    f"real regression, not environment noise"
                )
            any_pixel_fallback = True
            log(
                f"PASS (pixel-content-equivalent, NOT byte-identical -- "
                f"cross-environment rendering variance, within tolerance: {detail}): {name}"
            )

        if any_pixel_fallback:
            log(
                "NOTE: at least one figure required the pixel-content fallback rather than "
                "a byte-identical match. This is logged, not hidden -- matplotlib version "
                "is pinned in the CI workflow to minimize this, but exact freetype/font "
                "rendering can still vary by runner image."
            )
        else:
            log("PASS: all committed figures reproduced byte-identically")
    finally:
        # Restore every removed file on EVERY path -- a non-zero generator
        # exit, a missing output, or a byte mismatch must not leave the tree
        # with its git-tracked figures deleted. (Re-review 2026-09-18: the
        # earlier restore covered the missing-output path only, so the
        # "regenerated files are restored" claim in SOURCE-GATE.md held for
        # the tested path but not universally.)
        for _n, _old in committed_bytes.items():
            _q = figures_dir / _n
            if not _q.exists():
                _q.write_bytes(_old)

def check_citations(repo_root: Path) -> None:
    log("=== Check: citations (every CLAIM-REGISTER.md row_id resolves) ===")
    smap_path = repo_root / PACK_DIR / "tables" / "source_map.json"
    smap = json.loads(smap_path.read_text(encoding="utf-8"))
    existing_ids = {row["row_id"] for row in smap}

    claim_text = (repo_root / PACK_DIR / "CLAIM-REGISTER.md").read_text(encoding="utf-8")
    # Case-sensitive and wildcard-capable: the previous lowercase-only pattern
    # matched 19 of the 35 identifiers actually cited, silently skipping the
    # rest (16 wildcard/uppercase ones, every one of which resolves) while
    # reporting "all ... resolve".
    candidates = set(re.findall(r"`([A-Za-z_*][A-Za-z0-9_*]*\.[A-Za-z0-9_.*]+)`", claim_text))

    unresolved: list[str] = []
    for candidate in sorted(candidates):
        if candidate in existing_ids:
            continue
        if "*" in candidate and any(
            fnmatch.fnmatchcase(rid, candidate) for rid in existing_ids
        ):
            continue
        unresolved.append(candidate)

    if unresolved:
        raise CheckFailure(
            f"{len(unresolved)} citation(s) in CLAIM-REGISTER.md do not resolve to any "
            f"row in tables/source_map.json: {unresolved}"
        )
    log(f"PASS: all {len(candidates)} citation identifiers in CLAIM-REGISTER.md resolve")


def check_no_rerun(repo_root: Path) -> None:
    """Self-audit: neither generator script (nor this verifier itself)
    invokes the empirical study runner or the data-acquisition script via
    subprocess/os.system/Popen. A plain textual mention (e.g. in a docstring
    citing the reproduction command) is fine; an actual invocation is not."""
    log("=== Check: no-rerun (self-audit against re-running the empirical study) ===")
    scripts_dir = repo_root / PACK_DIR / "scripts"
    offenders: list[str] = []
    for py_file in sorted(scripts_dir.glob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SCRIPTS:
            if re.search(rf"(subprocess\.\w+|os\.system|os\.popen|Popen)\s*\([^)]*{re.escape(forbidden)}", text):
                offenders.append(f"{py_file.name} invokes {forbidden}")
    if offenders:
        raise CheckFailure(f"forbidden re-run invocation(s) found: {offenders}")
    log("PASS: neither generator script invokes the empirical study runner or acquisition script")


CHECKS = {
    "hashes": check_hashes,
    "tables": check_tables,
    "figures": check_figures,
    "citations": check_citations,
    "no-rerun": check_no_rerun,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument(
        "--check",
        choices=sorted(CHECKS),
        action="append",
        help="Run only this check (repeatable). Default: run all.",
    )
    args = parser.parse_args()
    repo_root: Path = args.repo_root.resolve()
    selected = args.check or sorted(CHECKS)

    failures: list[str] = []
    for name in selected:
        try:
            CHECKS[name](repo_root)
        except CheckFailure as exc:
            log(f"FAIL [{name}]: {exc}")
            failures.append(name)
        log("")

    if failures:
        log(f"RESULT: {len(failures)}/{len(selected)} check(s) failed: {failures}")
        sys.exit(1)
    log(f"RESULT: all {len(selected)} check(s) passed")


if __name__ == "__main__":
    main()
