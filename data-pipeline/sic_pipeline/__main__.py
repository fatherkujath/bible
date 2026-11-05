"""Scripture in Context data pipeline.

    python -m sic_pipeline all          fetch + verify + build + validate + attributions
    python -m sic_pipeline fetch        download pinned sources and verify hashes
    python -m sic_pipeline lock         refresh sources.lock.json after editing sources.json
    python -m sic_pipeline build        build build/reference.db
    python -m sic_pipeline validate     run validation checks on the built database
    python -m sic_pipeline attributions regenerate ATTRIBUTIONS.md
    python -m sic_pipeline export       write app/public/data/ (static JSON for the reader)
    python -m sic_pipeline reproduce    build twice from scratch and compare content hashes
"""
from __future__ import annotations

import json
import sys

from . import attributions, build, export, fetch, validate
from .common import REPORT_PATH


def _build_and_validate() -> bool:
    print("Building reference database")
    report = build.build()
    print("Validating")
    result = validate.run_checks(report)
    report["validation"] = result
    build.write_report(report)
    validate.print_result(result)
    return result["passed"]


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "all"
    if cmd == "fetch":
        print("Fetching sources")
        fetch.fetch_all()
    elif cmd == "lock":
        fetch.write_lock()
    elif cmd == "build":
        return 0 if _build_and_validate() else 1
    elif cmd == "validate":
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8")) if REPORT_PATH.exists() else {}
        result = validate.run_checks(report)
        validate.print_result(result)
        return 0 if result["passed"] else 1
    elif cmd == "attributions":
        attributions.generate()
    elif cmd == "export":
        export.export()
    elif cmd == "all":
        print("Fetching sources")
        fetch.fetch_all()
        ok = _build_and_validate()
        attributions.generate()
        if ok:
            print("Exporting app data")
            export.export()
        return 0 if ok else 1
    elif cmd == "reproduce":
        first = build.build()["content_sha256"]
        second = build.build()["content_sha256"]
        print(f"  first build : {first}\n  second build: {second}")
        same = first == second
        print("Reproducible" if same else "NOT reproducible")
        return 0 if same else 1
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
