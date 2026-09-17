import re

from playwright.sync_api import Page
from pages.base_page import BasePage


class BlogAgiSearchPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._lupa = page.locator(
            "button[aria-label*='pesquisa'], a[aria-label*='pesquisa'], "
            "button[aria-label*='busca'], a[aria-label*='busca'], "
            "[class*='search-toggle'], [class*='search-icon'], svg[class*='search']"
        )
        self._search = page.locator(
            "input[type='search'], input[name*='s'], input[name*='search'], "
            "input[id*='search'], [placeholder*='pesquisar'], [placeholder*='buscar']"
        )
        self._submit = page.get_by_role(
            "button", name=re.compile(r"pesquisar|buscar|search", re.IGNORECASE)
        )
        self._posts = page.locator(
            "article[class*='post'], div[class*='post'], li[class*='search-result'], "
            "h2[class*='entry-title'], h3[class*='title'] a"
        )
        self._empty = page.locator(
            "div[class*='no-results'], section[class*='not-found'], "
            "p:has-text('nenhum resultado'), p:has-text('Nenhum resultado'), "
            "h1:has-text('nada encontrado'), h1:has-text('Nada encontrado')"
        )
        self._page_title = page.locator(
            "h1[class*='page-title'], h2[class*='page-title']"
        )

    def open(self) -> None:
        self.go(self.URL_BLOG)

    def click_lupa(self) -> None:
        for loc in (self._lupa.first, self._lupa):
            try:
                if loc.count() > 0:
                    self.click(loc)
                    break
            except Exception:
                continue

    def fill_busca(self, termo: str, _tries: int = 0) -> None:
        if _tries > 1:
            self._search.first.fill(termo)
            return
        el = self._search.first
        if el.count() > 0 and el.is_visible():
            self.fill(el, termo)
            return
        try:
            self.page.locator(".search-field,.search-form input,[class*='search'] input").first.wait_for(
                state="visible", timeout=6000
            )
        except Exception:
            pass
        if el.count() > 0 and el.is_visible():
            self.fill(el, termo)
        else:
            self.fill_busca(termo, _tries + 1)

    def submit(self) -> None:
        if self._submit.count() > 0 and self._submit.first.is_visible():
            self.click(self._submit.first)
        else:
            self._search.first.press("Enter")

    def pesquisar(self, termo: str) -> None:
        self.open()
        self.click_lupa()
        self.fill_busca(termo)
        self.submit()

    def qtd_resultados(self) -> int:
        return self._posts.count()

    def has_resultados(self) -> bool:
        return self.qtd_resultados() > 0

    def titulos(self) -> list[str]:
        return [
            e.inner_text().strip()
            for e in self._posts.all()
            if e.is_visible() and e.inner_text().strip()
        ]

    def sem_resultados_visivel(self) -> bool:
        return any(e.is_visible() for e in self._empty.all())

    def msg_sem_resultados(self) -> str:
        for e in self._empty.all():
            if e.is_visible():
                return e.inner_text().strip()
        return ""

    def titulo_pagina(self) -> str:
        return self.text(self._page_title.first) if self._page_title.count() > 0 else ""
