import re

from playwright.sync_api import Page
from pages.base_page import BasePage


class CalculadoraJurosPage(BasePage):
    PATH = "/calculadora-de-juros-compostos"

    MODO_DIVIDA = "Dívida"
    MODO_INVEST = "Investimento"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._btn_divida = page.get_by_role(
            "button", name=re.compile(r"d[íi]vida", re.IGNORECASE)
        )
        self._btn_invest = page.get_by_role(
            "button", name=re.compile(r"investimento", re.IGNORECASE)
        )

        self._v_ini = page.locator(
            "input[id*='valorInicial'], input[name*='valorInicial'], input[id*='montante'], "
            "[placeholder*='valor'], [placeholder*='montante']"
        )
        self._taxa = page.locator(
            "input[id*='taxa'], input[name*='taxa'], [placeholder*='taxa'], [placeholder*='juros']"
        )
        self._periodo = page.locator(
            "input[id*='periodo'], input[name*='periodo'], [placeholder*='período'], "
            "[placeholder*='meses'], [placeholder*='anos']"
        )
        self._mensal = page.locator(
            "input[id*='mensal'], input[name*='mensal'], [placeholder*='mensal'], [placeholder*='aporte']"
        )

        self._btn_calc = page.get_by_role(
            "button", name=re.compile(r"calcular", re.IGNORECASE)
        )
        self._out = page.locator(
            "div[class*='resultado'], section[class*='result'], div[class*='result']"
        )

    def open(self) -> None:
        self.go(f"{self.URL_AGI}{self.PATH}")

    def modo_divida(self) -> None:
        if self._btn_divida.count() > 0:
            self.click(self._btn_divida.first)

    def modo_investimento(self) -> None:
        if self._btn_invest.count() > 0:
            self.click(self._btn_invest.first)

    def set_valor_inicial(self, v: str) -> None:
        self.fill(self._v_ini.first, v)

    def set_taxa(self, v: str) -> None:
        self.fill(self._taxa.first, v)

    def set_periodo(self, v: str) -> None:
        self.fill(self._periodo.first, v)

    def set_valor_mensal(self, v: str) -> None:
        if self._mensal.count() > 0:
            self.fill(self._mensal.first, v)

    def calcular(self) -> None:
        self.click(self._btn_calc.first)

    def calc_divida(self, ini: str, taxa: str, periodo: str) -> None:
        self.modo_divida()
        self.set_valor_inicial(ini)
        self.set_taxa(taxa)
        self.set_periodo(periodo)
        self.calcular()

    def calc_investimento(self, ini: str, mensal: str, taxa: str, periodo: str) -> None:
        self.modo_investimento()
        self.set_valor_inicial(ini)
        self.set_valor_mensal(mensal)
        self.set_taxa(taxa)
        self.set_periodo(periodo)
        self.calcular()

    def resultado(self) -> str:
        return self.text(self._out.first)

    def has_resultado(self) -> bool:
        return self._out.first.is_visible()

    def modo_divida_ativo(self) -> bool:
        if self._btn_divida.count() == 0:
            return False
        b = self._btn_divida.first
        return (
            b.get_attribute("aria-pressed") == "true"
            or "active" in (b.get_attribute("class") or "")
        )

    def modo_invest_ativo(self) -> bool:
        if self._btn_invest.count() == 0:
            return False
        b = self._btn_invest.first
        return (
            b.get_attribute("aria-pressed") == "true"
            or "active" in (b.get_attribute("class") or "")
        )
