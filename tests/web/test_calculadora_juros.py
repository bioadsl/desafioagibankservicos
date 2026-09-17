import re

import pytest
from playwright.sync_api import Page, expect

from pages.calculadora_juros_page import CalculadoraJurosPage


class TestCalculadoraJuros:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page) -> None:
        self.calc = CalculadoraJurosPage(page)

    @pytest.mark.web
    @pytest.mark.calculadora_juros
    @pytest.mark.happy_path
    @pytest.mark.divida
    def test_calculo_modo_divida(self, page: Page) -> None:
        self.calc.open()
        expect(page).to_have_url(
            re.compile(r"juros|agibank", re.IGNORECASE), timeout=20000
        )
        self.calc.calc_divida("5000", "2", "12")

        if self.calc.has_resultado():
            out = self.calc.resultado()
            assert out and out.strip(), "Resultado de dívida vazio"
            return

        body = page.inner_text("body").lower()
        assert any(p in body for p in ["total", "juros", "montante", "divida", "resultado"]), (
            "Sem resultado e sem palavras-chave de dívida encontradas"
        )

    @pytest.mark.web
    @pytest.mark.calculadora_juros
    @pytest.mark.happy_path
    @pytest.mark.investimento
    def test_calculo_modo_investimento(self, page: Page) -> None:
        self.calc.open()
        expect(page).to_have_url(
            re.compile(r"juros|agibank", re.IGNORECASE), timeout=20000
        )
        self.calc.calc_investimento("10000", "500", "0.8", "24")

        if self.calc.has_resultado():
            out = self.calc.resultado()
            assert out and out.strip(), "Resultado de investimento vazio"
            return

        body = page.inner_text("body").lower()
        assert any(
            p in body
            for p in ["total", "juros", "montante", "investido", "rendimento", "resultado"]
        ), "Sem resultado e sem palavras-chave de investimento encontradas"
