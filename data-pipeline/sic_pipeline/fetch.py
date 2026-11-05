"""Download each source at its pinned commit and verify file hashes.

Only the files listed in sources.json are checked out (sparse, shallow), so the
large upstream repositories are never cloned in full. Downloaded files live in
data-pipeline/.cache/ and are never committed: STEPBible asks that copies of its
files not be re-posted, and the lockfile hashes make the download reproducible.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .common import CACHE_DIR, LOCKFILE, load_manifest, source_dir


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, check=True,
                         capture_output=True, text=True)
    return out.stdout.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_source(src: dict) -> None:
    dest = source_dir(src["id"])
    dest.mkdir(parents=True, exist_ok=True)
    if not (dest / ".git").exists():
        _git(dest, "init", "-q")
        _git(dest, "remote", "add", "origin", src["repo"])
    have = ""
    try:
        have = _git(dest, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        pass
    missing = [f for f in src["files"] if not (dest / f).exists()]
    if have == src["commit"] and not missing:
        print(f"  {src['id']}: cached at {src['commit'][:12]}")
        return
    print(f"  {src['id']}: fetching {src['commit'][:12]} from {src['repo']}")
    _git(dest, "config", "core.sparseCheckout", "true")
    _git(dest, "config", "core.quotePath", "false")
    sparse = dest / ".git" / "info" / "sparse-checkout"
    sparse.parent.mkdir(parents=True, exist_ok=True)
    # Leading slash anchors each pattern; escape glob characters in file names.
    lines = ["/" + f.replace("[", r"\[").replace("*", r"\*") for f in src["files"]]
    sparse.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(dest, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", src["commit"])
    _git(dest, "checkout", "-q", "--force", src["commit"])
    still = [f for f in src["files"] if not (dest / f).exists()]
    if still:
        raise SystemExit(f"{src['id']}: files missing at pinned commit: {still}")


def fetch_all(verify: bool = True) -> None:
    manifest = load_manifest()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for src in manifest["sources"]:
        fetch_source(src)
    if verify:
        verify_hashes(manifest)


def compute_hashes(manifest: dict) -> dict:
    lock = {}
    for src in manifest["sources"]:
        lock[src["id"]] = {
            "commit": src["commit"],
            "files": {f: sha256(source_dir(src["id"]) / f) for f in src["files"]},
        }
    return lock


def write_lock() -> None:
    manifest = load_manifest()
    fetch_all(verify=False)
    lock = compute_hashes(manifest)
    LOCKFILE.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {LOCKFILE.name}")


def verify_hashes(manifest: dict) -> None:
    if not LOCKFILE.exists():
        raise SystemExit("sources.lock.json is missing; run `python -m sic_pipeline lock`.")
    lock = json.loads(LOCKFILE.read_text(encoding="utf-8"))
    actual = compute_hashes(manifest)
    problems = []
    for sid, entry in actual.items():
        want = lock.get(sid)
        if not want or want["commit"] != entry["commit"]:
            problems.append(f"{sid}: commit in sources.json is not in the lockfile")
            continue
        for f, h in entry["files"].items():
            if want["files"].get(f) != h:
                problems.append(f"{sid}: hash mismatch for {f}")
    if problems:
        raise SystemExit("Source verification failed:\n  " + "\n  ".join(problems))
    print("  all source files match sources.lock.json")
