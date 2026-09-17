import re

from playwright.sync_api import Page
from pages.base_page import BasePage


class CalculadoraDiasUteisPage(BasePage):
    PATH = "/calculadora-de-dias-uteis"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dt_ini = page.locator(
            "input[id*='dataInicial'], input[name*='dataInicial'], [placeholder*='inicial i']"
        )
        self._dt_fim = page.locator(
            "input[id*='dataFinal'], input[name*='dataFinal'], [placeholder*='final']"
        )
        self._btn_calc = page.get_by_role(
            "button", name=re.compile(r"calcular", re.IGNORECASE)
        )
        self._out = page.locator(
            "div[class*='resultado'], span[class*='resultado'], section[class*='result']"
        )
        self._err = page.locator(
            "span[class*='erro'], div[class*='error'], small[class*='error'], [role='alert']"
        )

    def open(self) -> None:
        self.go(f"{self.URL_AGI}{self.PATH}")

    def set_data_inicial(self, data: str) -> None:
        self.fill(self._dt_ini.first, data)

    def set_data_final(self, data: str) -> None:
        self.fill(self._dt_fim.first, data)

    def calcular(self) -> None:
        self.click(self._btn_calc.first)

    def calcular_dias(self, ini: str, fim: str) -> None:
        self.set_data_inicial(ini)
        self.set_data_final(fim)
        self.calcular()

    def resultado(self) -> str:
        return self.text(self._out.first)

    def has_resultado(self) -> bool:
        return self._out.first.is_visible()

    def mensagens_erro(self) -> str:
        return " ".join(
            e.inner_text() for e in self._err.all() if e.is_visible()
        )

    def has_erro(self) -> bool:
        return any(e.is_visible() for e in self._err.all())
