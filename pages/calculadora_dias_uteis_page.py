import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class CalculadoraDiasUteisPage(BasePage):
    PATH = "/calculadora-de-dias-uteis"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.page_title = page.get_by_role(
            "heading", level=2, name=re.compile(r"dias úteis|calculadora", re.IGNORECASE)
        ).or_(page.get_by_role("heading").filter(has_text=re.compile(r"dias úteis|calculadora", re.I)))
        self._dt_ini_label = page.get_by_label(
            re.compile(r"data\s*inicial|data\s*de\s*in[ií]cio", re.IGNORECASE)
        )
        self._dt_fim_label = page.get_by_label(
            re.compile(r"data\s*final|data\s*fim", re.IGNORECASE)
        )
        self._dt_ini = page.locator(
            "input[type='text'],input[type='date'],input[type='number'],input:not([type])"
        ).filter(visible=True)
        self._dt_fim = page.locator(
            "input[type='text'],input[type='date'],input[type='number'],input:not([type])"
        ).filter(visible=True)
        self._btn_calc = page.get_by_role(
            "button", name=re.compile(r"calcular|simular|enviar", re.IGNORECASE)
        ).or_(page.locator(
            "input[type=submit],button[type=submit],[role=button],a[role=button]"
        ).filter(visible=True))
        self._out = page.locator(
            "div[class*='resultado'], span[class*='resultado'], section[class*='result'], "
            "p:has-text('úteis'), p:has-text('dias'), [data-testid*='result']"
        ).filter(visible=True)
        self._err = page.locator(
            "span[class*='erro'], div[class*='error'], small[class*='error'], [role='alert'], "
            "[class*='obrigat'], [class*='required']"
        ).filter(visible=True)

    def open(self) -> None:
        self.go(f"{self.URL_AGI}{self.PATH}")
        self.page.wait_for_load_state("networkidle")
        expect(self.page).to_have_url(
            re.compile(r"dias-uteis|agibank", re.IGNORECASE), timeout=20000
        )
        try:
            expect(self.page_title.first).to_be_visible(timeout=10000)
        except Exception:
            pass

    def _input_ini(self):
        if self._dt_ini_label.count() > 0 and self._dt_ini_label.first.is_visible():
            return self._dt_ini_label.first
        return self._dt_ini.nth(0)

    def _input_fim(self):
        if self._dt_fim_label.count() > 0 and self._dt_fim_label.first.is_visible():
            return self._dt_fim_label.first
        return self._dt_ini.nth(1) if self._dt_ini.count() > 1 else self._dt_fim.nth(0)

    def set_data_inicial(self, data: str) -> None:
        self.fill(self._input_ini(), data)

    def set_data_final(self, data: str) -> None:
        self.fill(self._input_fim(), data)

    def calcular(self) -> None:
        try:
            expect(self._btn_calc.first).to_be_visible(timeout=8000)
            self.click(self._btn_calc.first)
        except Exception:
            self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(800)

    def calcular_dias(self, ini: str, fim: str) -> None:
        self.set_data_inicial(ini)
        self.set_data_final(fim)
        self.calcular()

    def resultado(self) -> str:
        if self._out.count() == 0:
            return ""
        for e in self._out.all():
            try:
                txt = e.inner_text().strip()
                if txt:
                    return txt
            except Exception:
                continue
        return ""

    def has_resultado(self) -> bool:
        return self._out.count() > 0 and any(e.is_visible() for e in self._out.all())

    def mensagens_erro(self) -> str:
        return " ".join(
            e.inner_text().strip()
            for e in self._err.all()
            if e.is_visible() and e.inner_text().strip()
        )

    def has_erro(self) -> bool:
        return any(e.is_visible() for e in self._err.all())
