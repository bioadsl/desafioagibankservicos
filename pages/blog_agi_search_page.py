import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class BlogAgiSearchPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._lupa = page.locator(
            "button[aria-label*='pesquisa'], a[aria-label*='pesquisa'], "
            "button[aria-label*='busca'], a[aria-label*='busca'], "
            "[class*='search-toggle'], [class*='search-icon'], svg[class*='search']"
        )
        self.search = page.locator(
            "input[type='search'], input[name='s'], input[name*='search'], "
            "input[id*='search'], [placeholder*='pesquisar'], [placeholder*='buscar'], "
            "[placeholder*='Digite sua busca']"
        ).filter(visible=True)
        self._submit = page.get_by_role(
            "button", name=re.compile(r"pesquisar|buscar|search", re.IGNORECASE)
        )
        self._posts = page.locator(
            "article[class*='post'], div[class*='post'], li[class*='search-result'], "
            "h2[class*='entry-title'], h3[class*='title'] a"
        ).filter(visible=True)
        self._empty = page.locator(
            "div[class*='no-results'], section[class*='not-found'], "
            "p:has-text('nenhum resultado'), p:has-text('Nenhum resultado'), "
            "h1:has-text('nada encontrado'), h1:has-text('Nada encontrado')"
        ).filter(visible=True)
        self._page_title = page.locator(
            "h1[class*='page-title'], h2[class*='page-title']"
        )

    def open(self) -> None:
        self.go(self.URL_BLOG)
        self.page.wait_for_load_state("networkidle")

    def _toggle_search_if_needed(self) -> None:
        if self.search.count() > 0 and self.search.first.is_visible():
            return
        for cand in [self._lupa.first, self._lupa]:
            try:
                if cand.count() > 0:
                    self.page.mouse.click(0, 0)
                    try:
                        cand.click(timeout=5000, force=True)
                    except Exception:
                        try:
                            cand.dispatch_event("click")
                        except Exception:
                            pass
                    self.page.wait_for_timeout(500)
                    if self.search.count() > 0 and self.search.first.is_visible():
                        return
            except Exception:
                continue

    def pesquisar(self, termo: str) -> None:
        self.open()
        self._toggle_search_if_needed()
        field = self.search.first
        expect(field).to_be_visible(timeout=10000)
        try:
            field.click()
            field.fill(termo)
        except Exception:
            try:
                field.focus()
                self.page.keyboard.type(termo, delay=30)
            except Exception:
                self.page.evaluate(
                    """([sel, val]) => {
                        const el = document.querySelector(sel);
                        if (!el) return;
                        el.style.visibility = 'visible';
                        el.style.display = 'block';
                        el.removeAttribute('disabled');
                        el.removeAttribute('readonly');
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    ["input.search-field,input[name='s']", termo],
                )
        if self._submit.count() > 0 and self._submit.first.is_visible():
            try:
                self._submit.first.click(timeout=5000)
            except Exception:
                field.press("Enter")
        else:
            field.press("Enter")
        self.page.wait_for_load_state("domcontentloaded")

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
        for e in self._page_title.all():
            if e.is_visible():
                return e.inner_text().strip()
        return ""
