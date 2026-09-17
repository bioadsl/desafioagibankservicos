import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class CalculadoraJurosPage(BasePage):
    PATH = "/calculadora-de-juros-compostos"

    MODO_DIVIDA = "Dívida"
    MODO_INVEST = "Investimento"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.page_title = page.get_by_role(
            "heading", level=2, name=re.compile(r"juros|calculadora", re.IGNORECASE)
        ).or_(page.get_by_role("heading").filter(has_text=re.compile(r"juros|compostos", re.I)))
        self._btn_divida = (
            page.get_by_role(
                "tab", name=re.compile(r"d[íi]vida|devedor", re.IGNORECASE)
            ).or_(page.get_by_role("button").filter(has_text=re.compile(r"d[íi]vida|devedor", re.I)))
        )
        self._btn_invest = (
            page.get_by_role(
                "tab", name=re.compile(r"investimento|aplicação|aplicacao", re.IGNORECASE)
            ).or_(page.get_by_role("button").filter(has_text=re.compile(r"investimento|aplicação", re.I)))
        )
        self._tabs = page.locator(
            "button[class*='tab'], [role=tab], label[for*='divida'], label[for*='invest']"
        ).filter(visible=True)
        self._v_ini_label = page.get_by_label(
            re.compile(r"valor\s*inicial|montante|capital|valor\s*presente|valor\s*do\s*empr[eé]stimo", re.I)
        )
        self._taxa_label = page.get_by_label(
            re.compile(r"taxa\s*de\s*juros|taxa\s*ao|juros\s*ao", re.IGNORECASE)
        )
        self._periodo_label = page.get_by_label(
            re.compile(r"per[ií]odo|prazo|tempo|meses|anos", re.IGNORECASE)
        )
        self._mensal_label = page.get_by_label(
            re.compile(r"valor\s*mensal|aporte\s*mensal|parcela|mensal", re.IGNORECASE)
        )
        self._txt_inputs = page.locator(
            "input[type='text'],input[type='number'],input:not([type])"
        ).filter(visible=True)
        self._btn_calc = page.get_by_role(
            "button", name=re.compile(r"calcular|simular|enviar", re.IGNORECASE)
        ).or_(page.locator(
            "input[type=submit],button[type=submit],[role=button],a[role=button]"
        ).filter(visible=True))
        self._out = page.locator(
            "div[class*='resultado'], section[class*='result'], div[class*='result'], "
            "[data-testid*='result'], [class*='montante'], [class*='total']"
        ).filter(visible=True)

    def open(self) -> None:
        self.go(f"{self.URL_AGI}{self.PATH}")
        self.page.wait_for_load_state("networkidle")
        expect(self.page).to_have_url(
            re.compile(r"juros|agibank", re.IGNORECASE), timeout=20000
        )
        try:
            expect(self.page_title.first).to_be_visible(timeout=10000)
        except Exception:
            pass

    def modo_divida(self) -> None:
        if self._btn_divida.count() > 0:
            try:
                self._btn_divida.first.click(timeout=5000)
            except Exception:
                if self._tabs.count() > 0:
                    for t in self._tabs.all():
                        try:
                            if re.search(r"d[íi]vida|devedor", t.inner_text(), re.I):
                                t.click(timeout=3000)
                                break
                        except Exception:
                            continue
        self.page.wait_for_timeout(400)

    def modo_investimento(self) -> None:
        if self._btn_invest.count() > 0:
            try:
                self._btn_invest.first.click(timeout=5000)
            except Exception:
                if self._tabs.count() > 0:
                    for t in self._tabs.all():
                        try:
                            if re.search(r"invest|aplica", t.inner_text(), re.I):
                                t.click(timeout=3000)
                                break
                        except Exception:
                            continue
        self.page.wait_for_timeout(400)

    def _nth_text(self, n: int):
        if self._txt_inputs.count() > n:
            return self._txt_inputs.nth(n)
        return self._txt_inputs.first

    def _smart_fill(self, label_loc, n: int, value: str) -> None:
        try:
            if label_loc.count() > 0 and label_loc.first.is_visible():
                self.fill(label_loc.first, value)
                return
        except Exception:
            pass
        self.fill(self._nth_text(n), value)

    def set_valor_inicial(self, v: str) -> None:
        self._smart_fill(self._v_ini_label, 0, v)

    def set_taxa(self, v: str) -> None:
        self._smart_fill(self._taxa_label, 1, v)

    def set_periodo(self, v: str) -> None:
        self._smart_fill(self._periodo_label, 2, v)

    def set_valor_mensal(self, v: str) -> None:
        self._smart_fill(self._mensal_label, 3, v)

    def calcular(self) -> None:
        try:
            expect(self._btn_calc.first).to_be_visible(timeout=8000)
            self.click(self._btn_calc.first)
        except Exception:
            self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

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

    def modo_divida_ativo(self) -> bool:
        for t in [self._btn_divida.first] + self._tabs.all():
            try:
                if t.count() == 0:
                    continue
                cls = t.get_attribute("class") or ""
                pressed = t.get_attribute("aria-pressed")
                if pressed == "true" or "active" in cls:
                    txt = t.inner_text().lower()
                    if re.search(r"d[íi]vida|devedor", txt):
                        return True
            except Exception:
                continue
        return False

    def modo_invest_ativo(self) -> bool:
        for t in [self._btn_invest.first] + self._tabs.all():
            try:
                if t.count() == 0:
                    continue
                cls = t.get_attribute("class") or ""
                pressed = t.get_attribute("aria-pressed")
                if pressed == "true" or "active" in cls:
                    txt = t.inner_text().lower()
                    if re.search(r"invest|aplica", txt):
                        return True
            except Exception:
                continue
        return False
