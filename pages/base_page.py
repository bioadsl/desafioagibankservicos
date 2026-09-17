from playwright.sync_api import Page, Locator, expect


class BasePage:
    """Base para Page Objects — helpers genéricos e waits explícitos."""

    URL_AGI = "https://agibank.com.br"
    URL_BLOG = "https://blogdoagi.com.br"

    def __init__(self, page: Page) -> None:
        self.page = page

    def go(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

    def w8vis(self, loc: Locator, timeout: int = 15000) -> Locator:
        expect(loc).to_be_visible(timeout=timeout)
        return loc

    def w8ena(self, loc: Locator, timeout: int = 15000) -> Locator:
        expect(loc).to_be_enabled(timeout=timeout)
        return loc

    def click(self, loc: Locator, timeout: int = 15000) -> None:
        self.w8vis(loc, timeout)
        self.w8ena(loc, timeout)
        loc.click()

    def fill(self, loc: Locator, text: str, timeout: int = 15000) -> None:
        self.w8vis(loc, timeout)
        loc.fill(text)

    def text(self, loc: Locator, timeout: int = 15000) -> str:
        self.w8vis(loc, timeout)
        return loc.inner_text()

    def select(self, loc: Locator, label: str, timeout: int = 15000) -> None:
        self.w8vis(loc, timeout)
        loc.select_option(label=label)
