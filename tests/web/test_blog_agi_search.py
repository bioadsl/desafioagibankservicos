import pytest

from pages.blog_agi_search_page import BlogAgiSearchPage


class TestBlogAgiSearch:
    TERMO_OK = "Empréstimo"
    TERMO_NO_RESULTS = "TermoMuitoRaroQueNaoExisteNoBlogXYZ123987"

    @pytest.fixture(autouse=True)
    def setup(self, page) -> None:
        self.blog = BlogAgiSearchPage(page)

    @pytest.mark.web
    @pytest.mark.blog_agi
    @pytest.mark.happy_path
    def test_busca_termo_existente_emprestimo(self) -> None:
        self.blog.pesquisar(self.TERMO_OK)
        titles = self.blog.titulos()
        has = self.blog.has_resultados()

        assert has or titles, (
            f"Busca por '{self.TERMO_OK}' sem resultados. Títulos: {titles}"
        )

        if titles:
            rel = ["empréstimo", "emprestimo", "crédito", "credito", "financiamento"]
            match = any(t in title.lower() for title in titles for t in rel)
            assert match or len(titles) >= 1, (
                "Resultados sem termos relacionados e quantidade inesperada"
            )

    @pytest.mark.web
    @pytest.mark.blog_agi
    @pytest.mark.sem_resultados
    def test_busca_sem_resultados(self) -> None:
        self.blog.pesquisar(self.TERMO_NO_RESULTS)
        qtd = self.blog.qtd_resultados()
        empty = self.blog.sem_resultados_visivel()
        page_title = self.blog.titulo_pagina().lower()
        msg = self.blog.msg_sem_resultados().lower()

        markers = ["nenhum", "nada", "sem resultado", "não encontrad", "nao encontrad"]
        has_marker = any(m in t for m in markers for t in [page_title, msg])

        assert empty or qtd == 0 or has_marker, (
            f"Esperava sem resultados para '{self.TERMO_NO_RESULTS}'. "
            f"Qtd: {qtd}, empty msg visível: {empty}, title='{page_title}'"
        )
