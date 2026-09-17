import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class BlogAgiSearchPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.page = page

    def pesquisar(self, termo: str) -> None:
        self.page.goto(
            self.URL_BLOG,
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_load_state("networkidle")

        toggle = self.page.get_by_role(
            "button", name="Pesquisar"
        ).or_(
            self.page.locator(
                "[aria-label*='pesquis'], [aria-label*='buscar'], "
                ".search-toggle, .search-button, "
                "button[class*='search'], a[class*='search'], "
                "svg[class*='search']"
            ).first
        ).first

        try:
            if toggle.count() > 0:
                if toggle.first.is_visible():
                    toggle.first.click(timeout=5000)
                else:
                    try:
                        toggle.first.dispatch_event("click")
                    except Exception:
                        pass
                self.page.wait_for_timeout(700)
        except Exception:
            pass

        search_input = self.page.locator(
            "input[name='s']:visible, "
            "input[type='search']:visible, "
            "input[placeholder*='Digite sua busca']:visible, "
            "input[placeholder*='Pesquisar']:visible, "
            "input[placeholder*='pesquisar']:visible, "
            "input[class*='search-field']:visible, "
            ".search-form input:visible"
        ).first

        expect(search_input).to_be_visible(timeout=15000)
        try:
            search_input.click()
            search_input.fill(termo)
        except Exception:
            try:
                search_input.focus()
                self.page.keyboard.type(termo, delay=30)
            except Exception:
                self.page.evaluate(
                    """([sel, val]) => {
                        const el = document.querySelector(sel);
                        if (!el) return;
                        const unwrap = el.closest('div,form,section,header') || el;
                        ['style','display','visibility','hidden'].forEach(a => {
                            unwrap.removeAttribute(a); el.removeAttribute(a);
                        });
                        unwrap.style.setProperty('display','block','important');
                        unwrap.style.setProperty('visibility','visible','important');
                        unwrap.style.setProperty('opacity','1','important');
                        el.style.setProperty('display','block','important');
                        el.style.setProperty('visibility','visible','important');
                        el.removeAttribute('disabled'); el.removeAttribute('readonly');
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    ["input.search-field,input[name='s'],input[type='search']", termo],
                )

        try:
            btn = self.page.get_by_role(
                "button", name=re.compile(r"pesquisar|buscar|search", re.I)
            )
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=5000)
            else:
                search_input.press("Enter")
        except Exception:
            search_input.press("Enter")

        self.page.wait_for_load_state("domcontentloaded")

    def qtd_resultados(self) -> int:
        return self.page.locator(
            "article[class*='post']:visible, div[class*='post']:visible, "
            "li[class*='search-result']:visible, h2[class*='entry-title']:visible, "
            "h3[class*='title'] a:visible"
        ).count()

    def has_resultados(self) -> bool:
        return self.qtd_resultados() > 0

    def titulos(self) -> list[str]:
        loc = self.page.locator(
            "article[class*='post'] h2:visible, h2[class*='entry-title']:visible, "
            "h3[class*='title'] a:visible, h2:has(a[href*='/']):visible"
        )
        return [
            e.inner_text().strip()
            for e in loc.all()
            if e.is_visible() and e.inner_text().strip()
        ]

    def sem_resultados_visivel(self) -> bool:
        loc = self.page.locator(
            "div[class*='no-results']:visible, section[class*='not-found']:visible, "
            "p:has-text('nenhum resultado'):visible, p:has-text('Nenhum resultado'):visible, "
            "h1:has-text('nada encontrado'):visible, h1:has-text('Nada encontrado'):visible, "
            "h2:has-text('nada encontrado'):visible, h2:has-text('Nada encontrado'):visible"
        )
        return any(e.is_visible() for e in loc.all())

    def msg_sem_resultados(self) -> str:
        loc = self.page.locator(
            "div[class*='no-results']:visible, section[class*='not-found']:visible, "
            "p:has-text('nenhum resultado'):visible, p:has-text('Nenhum resultado'):visible, "
            "h1:has-text('nada encontrado'):visible, h1:has-text('Nada encontrado'):visible"
        )
        for e in loc.all():
            if e.is_visible():
                return e.inner_text().strip()
        return ""

    def titulo_pagina(self) -> str:
        loc = self.page.locator(
            "h1[class*='page-title']:visible, h2[class*='page-title']:visible, "
            "h1:visible"
        )
        for e in loc.all():
            if e.is_visible():
                return e.inner_text().strip()
        return ""
