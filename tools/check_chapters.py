"""Phase 2 exit check: every chapter loads, and every context tab shows either
sourced content or "No sourced material yet." — never a blank panel or an error.

Usage (from the repo root, with the built site served on port 4173):
    cd app/out && python3 -m http.server 4173 &
    python3 tools/check_chapters.py [--base http://localhost:4173] [--chrome /usr/bin/google-chrome]

Requires: pip install playwright (uses an installed Chrome).
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
TABS = ["text", "world", "places", "people", "terms", "xrefs"]
EMPTY = "No sourced material yet."


async def check_chapter(page, base: str, cid: str) -> list[str]:
    problems: list[str] = []
    await page.goto(f"{base}/read/{cid}/#v1", wait_until="domcontentloaded")
    try:
        # Wait for real verses (or a load error), not the "Loading…" placeholder.
        await page.wait_for_function(
            "document.querySelector('.verse') || document.body.innerText.includes('could not be loaded')",
            timeout=30000)
    except Exception:
        return [f"{cid}: page did not render"]
    if await page.locator("text=could not be loaded").count():
        return [f"{cid}: chapter data failed to load"]
    if await page.locator(".verse").count() == 0:
        return [f"{cid}: no verses"]
    for scope in ("verse 1", "whole chapter"):
        if scope == "whole chapter":
            btn = page.locator("text=Show whole chapter")
            if await btn.count():
                await btn.first.click()
        for tab in TABS:
            await page.click(f"#tab-{tab}")
            panel = page.locator(f"#panel-{tab}")
            text = (await panel.inner_text()).strip()
            has_content = await panel.locator(".card, .verse, table, .article, li").count() > 0
            says_empty = EMPTY in text or "Choose a verse number" in text
            if not (has_content or says_empty):
                problems.append(f"{cid} [{scope}] {tab}: panel is blank")
            if "could not be loaded" in text:
                problems.append(f"{cid} [{scope}] {tab}: load error")
    return problems


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:4173")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    books = json.loads((ROOT / "app/public/data/books.json").read_text(encoding="utf-8"))
    ids = [f"{b['osis']}.{c}" for b in books for c in b["chapters"]]
    queue: asyncio.Queue[str] = asyncio.Queue()
    for i in ids:
        queue.put_nowait(i)
    problems: list[str] = []
    errors: list[str] = []
    done = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=args.chrome, args=["--no-sandbox"])

        async def worker() -> None:
            nonlocal done
            ctx = await browser.new_context(viewport={"width": 1366, "height": 900})
            # Map tiles are external; block them so the check doesn't depend on the network.
            await ctx.route("https://tiles.openfreemap.org/**", lambda r: r.abort())
            page = await ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            while not queue.empty():
                cid = queue.get_nowait()
                problems.extend(await check_chapter(page, args.base, cid))
                done += 1
                if done % 100 == 0:
                    print(f"  checked {done}/{len(ids)} chapters", flush=True)
            await ctx.close()

        await asyncio.gather(*(worker() for _ in range(args.workers)))
        await browser.close()

    print(f"Checked {done} chapters x {len(TABS)} tabs x 2 views.")
    page_errors = sorted(set(e for e in errors if "openfreemap" not in e and "Failed to fetch" not in e))
    kinds: dict[str, int] = {}
    for line in problems:
        kinds[line.split(": ", 1)[-1]] = kinds.get(line.split(": ", 1)[-1], 0) + 1
    for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d} x {k}")
    for line in problems[:50]:
        print("  PROBLEM", line)
    for line in page_errors[:20]:
        print("  SCRIPT ERROR", line)
    ok = not problems and not page_errors
    print("Exit check PASSED" if ok else f"Exit check FAILED ({len(problems)} problems, {len(page_errors)} script errors)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
