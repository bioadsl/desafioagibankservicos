import re
import pytest

pytest.skip(
    "Requisito: o projeto não deve conter nada relacionado a calculadoras.",
    allow_module_level=True,
)

from playwright.sync_api import Page, expect

from pages.base_page import BasePage, debug_page


class CalculadoraDiasUteisPage(BasePage):
    PATH = "/calculadora-de-dias-uteis"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.page = page

    def _aceitar_cookies(self) -> None:
        for sel in [
            self.page.get_by_role("button", name=re.compile(r"aceitar|concordo|accept|consent", re.I)),
            self.page.locator("button:has-text('Aceitar'):visible, button:has-text('Concordo'):visible, button#accept-cookies:visible, [id*='cookie'] button:has-text('Aceitar'):visible"),
        ]:
            try:
                if sel.count() > 0 and sel.first.is_visible():
                    sel.first.click(timeout=3000)
                    self.page.wait_for_timeout(300)
                    return
            except Exception:
                continue

    def open(self) -> None:
        self.go(f"{self.URL_AGI}{self.PATH}")
        self.page.wait_for_load_state("networkidle")
        self._aceitar_cookies()
        debug_page(self.page, "calculadora_dias_uteis")
        expect(self.page).to_have_url(
            re.compile(r"dias-uteis|agibank", re.IGNORECASE), timeout=20000
        )
        form = self.page.locator(
            "form:has(input):visible, [data-testid*='calculadora']:visible, "
            "[class*='calculadora']:visible, [id*='calculadora']:visible, "
            "section:has(input[placeholder]):visible, article:has(input):visible"
        ).first
        expect(form).to_be_visible(timeout=30000)

    def calcular_dias(self, ini: str, fim: str) -> None:
        start = (
            self.page.get_by_label(
                re.compile(r"data\s*inicial|data\s*de\s*in[ií]cio|primeira\s*data|start\s*date|in[ií]cio", re.I)
            )
            .or_(
                self.page.locator(
                    "input[name*='inicio']:visible, input[name*='start']:visible, "
                    "input[id*='inicial']:visible, input[placeholder*='inicial']:visible, "
                    "input[placeholder*='início']:visible, input[type='date']:visible, "
                    "input[aria-label*='inicial']:visible"
                ).first
            )
        )
        end = (
            self.page.get_by_label(
                re.compile(r"data\s*final|data\s*fim|segunda\s*data|end\s*date|fim", re.I)
            )
            .or_(
                self.page.locator(
                    "input[name*='fim']:visible, input[name*='end']:visible, "
                    "input[id*='final']:visible, input[placeholder*='final']:visible, "
                    "input[aria-label*='final']:visible"
                )
            )
        )

        try:
            if start.count() == 0 or not start.first.is_visible():
                alt = self.page.locator(
                    "input[type='text']:visible,input[type='date']:visible,input[type='number']:visible,input:not([type]):visible"
                )
                if alt.count() >= 2:
                    start = alt.nth(0)
                    end = alt.nth(1)
        except Exception:
            alt = self.page.locator(
                "input[type='text']:visible,input[type='date']:visible,input[type='number']:visible,input:not([type]):visible"
            )
            if alt.count() >= 2:
                start = alt.nth(0)
                end = alt.nth(1)

        expect(start.first).to_be_visible(timeout=15000)
        expect(end.first).to_be_visible(timeout=15000)

        try:
            start.first.fill(ini)
        except Exception:
            try:
                start.first.click()
                start.first.fill(ini)
            except Exception:
                try:
                    start.first.focus()
                    self.page.keyboard.type(ini)
                except Exception:
                    start.first.evaluate("(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); e.dispatchEvent(new Event('change', {bubbles:true})); }", ini)
        try:
            end.first.fill(fim)
        except Exception:
            try:
                end.first.click()
                end.first.fill(fim)
            except Exception:
                try:
                    end.first.focus()
                    self.page.keyboard.type(fim)
                except Exception:
                    end.first.evaluate("(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); e.dispatchEvent(new Event('change', {bubbles:true})); }", fim)

        btn = (
            self.page.get_by_role("button", name=re.compile(r"calcular|simular|enviar|submit", re.I))
            .or_(
                self.page.locator(
                    "input[type=submit]:visible,button[type=submit]:visible,[role=button]:visible,a[role=button]:visible,button[type=button]:visible"
                )
            )
        )
        try:
            if btn.count() > 0:
                expect(btn.first).to_be_visible(timeout=8000)
                btn.first.click(timeout=5000)
            else:
                self.page.keyboard.press("Enter")
        except Exception:
            try:
                self.page.locator("input[type=submit]:visible,button[type=submit]:visible,button[class*='calc']:visible").first.click(timeout=4000)
            except Exception:
                self.page.keyboard.press("Enter")

        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def calcular(self) -> None:
        btn = (
            self.page.get_by_role("button", name=re.compile(r"calcular|simular|enviar|submit", re.I))
            .or_(
                self.page.locator(
                    "input[type=submit]:visible,button[type=submit]:visible,[role=button]:visible,a[role=button]:visible,button[type=button]:visible"
                )
            )
        )
        try:
            if btn.count() > 0:
                expect(btn.first).to_be_visible(timeout=8000)
                btn.first.click(timeout=5000)
            else:
                self.page.keyboard.press("Enter")
        except Exception:
            self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def resultado(self) -> str:
        loc = self.page.locator(
            "div[class*='resultado']:visible, span[class*='resultado']:visible, "
            "section[class*='result']:visible, [id*='resultado']:visible, "
            "div[id*='result']:visible, strong:has-text('dias'):visible, "
            "p:has-text('dias úteis'):visible, p:has-text('úteis'):visible"
        )
        if loc.count() == 0:
            return ""
        for e in loc.all():
            try:
                txt = e.inner_text().strip()
                if txt:
                    return txt
            except Exception:
                continue
        return ""

    def has_resultado(self) -> bool:
        loc = self.page.locator(
            "div[class*='resultado']:visible, span[class*='resultado']:visible, "
            "section[class*='result']:visible, [id*='resultado']:visible, div[id*='result']:visible"
        )
        return loc.count() > 0 and any(e.is_visible() for e in loc.all())

    def mensagens_erro(self) -> str:
        loc = self.page.locator(
            "span[class*='erro']:visible, div[class*='error']:visible, "
            "small[class*='error']:visible, [role='alert']:visible, "
            "[class*='obrigat']:visible, [class*='required']:visible, "
            "div:has-text('obrigatório'):visible, span:has-text('obrigatório'):visible"
        )
        return " ".join(
            e.inner_text().strip()
            for e in loc.all()
            if e.is_visible() and e.inner_text().strip()
        )

    def has_erro(self) -> bool:
        loc = self.page.locator(
            "span[class*='erro']:visible, div[class*='error']:visible, "
            "small[class*='error']:visible, [role='alert']:visible, "
            "[class*='obrigat']:visible, [class*='required']:visible"
        )
        return any(e.is_visible() for e in loc.all())
