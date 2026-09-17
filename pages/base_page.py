import os
from pathlib import Path

from playwright.sync_api import Page, Locator, expect


REPORTS_DIR = Path("reports")


def debug_page(page: Page, name: str) -> None:
    REPORTS_DIR.mkdir(exist_ok=True, parents=True)
    safe = name.translate({ord(c): "_" for c in ":/\\ "})
    try:
        page.screenshot(path=str(REPORTS_DIR / f"debug_{safe}.png"), full_page=True)
    except Exception:
        pass
    try:
        print(f"\n[DEBUG:{name}] URL..........: {page.url}")
    except Exception:
        pass
    try:
        print(f"[DEBUG:{name}] TITLE........: {page.title()!r}")
    except Exception:
        pass
    try:
        body = page.locator("body").inner_text(timeout=3000).strip() or ""
        print(f"[DEBUG:{name}] BODY[0:2000].: {body[:2000]!r}")
    except Exception:
        try:
            body = page.content()[:2000]
            print(f"[DEBUG:{name}] HTML[0:2000].: {body!r}")
        except Exception:
            print(f"[DEBUG:{name}] BODY.........: <unavailable>")


class BasePage:
    """Base para Page Objects — helpers genéricos e waits explícitos."""

    URL_AGI = os.environ.get("URL_AGI", "https://agibank.com.br").rstrip("/")
    URL_BLOG = os.environ.get("URL_BLOG", "https://blogdoagi.com.br").rstrip("/")

    def __init__(self, page: Page) -> None:
        self.page = page

    def go(self, url: str, debug_name: str | None = None) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_load_state("networkidle")
        if debug_name:
            debug_page(self.page, debug_name)
