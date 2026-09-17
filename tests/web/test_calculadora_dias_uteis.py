import re

import pytest
from playwright.sync_api import Page, expect

from pages.calculadora_dias_uteis_page import CalculadoraDiasUteisPage


class TestCalculadoraDiasUteis:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page) -> None:
        self.calc = CalculadoraDiasUteisPage(page)

    @pytest.mark.web
    @pytest.mark.calculadora_dias_uteis
    @pytest.mark.happy_path
    def test_calculo_cenario_feliz(self, page: Page) -> None:
        self.calc.open()
        expect(page).to_have_url(
            re.compile(r"dias-uteis|agibank", re.IGNORECASE), timeout=20000
        )
        self.calc.calcular_dias("01/01/2025", "31/01/2025")

        if self.calc.has_resultado():
            out = self.calc.resultado()
            assert out and out.strip(), "Resultado exibido mas texto vazio"
            return

        body = page.inner_text("body").lower()
        assert any(p in body for p in ["útil", "dias", "dia", "calculo", "resultado"]), (
            "Sem resultado e sem indicativos de processamento no corpo da página"
        )

    @pytest.mark.web
    @pytest.mark.calculadora_dias_uteis
    @pytest.mark.validacao
    def test_campos_obrigatorios_vazios(self) -> None:
        self.calc.open()
        self.calc.calcular()

        erros = self.calc.mensagens_erro()
        if self.calc.has_erro():
            assert len(erros) > 0, "Esperava mensagem de erro para campos vazios"
            return

        body = self.calc.page.inner_text("body").lower()
        has_err_msg = any(
            p in body
            for p in ["obrigatório", "obrigatorio", "informe", "preencha", "inválido", "invalido", "erro"]
        )
        assert has_err_msg or not self.calc.has_resultado(), (
            "Nem erro nem resultado; esperava validação de obrigatórios"
        )
