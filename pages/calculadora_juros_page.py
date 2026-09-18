import re
import pytest

pytest.skip(
    "Requisito: o projeto não deve conter nada relacionado a calculadoras.",
    allow_module_level=True,
)

from playwright.sync_api import Page, expect

from pages.base_page import BasePage, debug_page


class CalculadoraJurosPage(BasePage):
    PATH = "/calculadora-de-juros-compostos"

    MODO_DIVIDA = "Dívida"
    MODO_INVEST = "Investimento"

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
        debug_page(self.page, "calculadora_juros_compostos")
        expect(self.page).to_have_url(
            re.compile(r"juros|agibank", re.IGNORECASE), timeout=20000
        )
        form = self.page.locator(
            "form:has(input):visible, [data-testid*='calculadora']:visible, "
            "[class*='calculadora']:visible, [id*='calculadora']:visible, "
            "section:has(input[placeholder]):visible, article:has(input):visible, "
            "section:has(input[type='number']):visible"
        ).first
        expect(form).to_be_visible(timeout=30000)

    def _smart_fill(self, label_re: re.Pattern, extra_sel: str, nth_fallback: int, value: str) -> None:
        loc = self.page.get_by_label(label_re).or_(self.page.locator(extra_sel))
        if loc.count() == 0 or not loc.first.is_visible():
            alt = self.page.locator(
                "input[type='text']:visible,input[type='number']:visible,input:not([type]):visible"
            )
            if alt.count() > nth_fallback:
                loc = alt.nth(nth_fallback)
        try:
            expect(loc.first).to_be_visible(timeout=12000)
            loc.first.fill(value)
        except Exception:
            try:
                loc.first.click()
                loc.first.fill(value)
            except Exception:
                try:
                    loc.first.focus()
                    self.page.keyboard.type(value)
                except Exception:
                    loc.first.evaluate(
                        "(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); e.dispatchEvent(new Event('change', {bubbles:true})); }",
                        value,
                    )

    def _toggle_modo(self, is_divida: bool) -> None:
        key_txt = re.compile(r"d[íi]vida|devedor", re.I) if is_divida else re.compile(r"investimento|invest|aplica[cç][aã]o", re.I)
        for _ in range(2):
            try:
                r = self.page.get_by_role("radio", name=key_txt)
                if r.count() > 0 and r.first.is_visible():
                    try:
                        r.first.check(timeout=3000)
                    except Exception:
                        r.first.click(timeout=3000)
                    self.page.wait_for_timeout(300)
                    return
            except Exception:
                pass
            try:
                t = (
                    self.page.get_by_role("tab", name=key_txt)
                    .or_(self.page.get_by_role("button", name=key_txt))
                    .or_(
                        self.page.locator(
                            "button[class*='tab']:visible,[role=tab]:visible,label[for*='divida']:visible,label[for*='invest']:visible"
                        )
                    )
                )
                if t.count() > 0:
                    for cand in t.all():
                        try:
                            if not cand.is_visible():
                                continue
                            txt = cand.inner_text().lower()
                            if re.search(r"d[íi]vida|devedor" if is_divida else r"invest|aplica", txt):
                                cand.click(timeout=3000)
                                self.page.wait_for_timeout(400)
                                return
                        except Exception:
                            continue
            except Exception:
                pass
            self.page.wait_for_timeout(300)

    def modo_divida(self) -> None:
        self._toggle_modo(True)

    def modo_investimento(self) -> None:
        self._toggle_modo(False)

    def set_valor_inicial(self, v: str, nth: int = 0) -> None:
        self._smart_fill(
            re.compile(r"valor\s*inicial|montante|capital|valor\s*presente|principal|valor\s*do\s*empr[eé]stimo|valor\s*investido", re.I),
            "input[name*='valor']:visible,input[name*='montante']:visible,input[name*='principal']:visible,input[id*='valor']:visible,input[id*='montante']:visible,input[placeholder*='valor']:visible,input[placeholder*='montante']:visible",
            nth,
            v,
        )

    def set_taxa(self, v: str, nth: int = 1) -> None:
        self._smart_fill(
            re.compile(r"taxa\s*de\s*juros|taxa\s*ao|juros\s*ao|taxa\s*anual|taxa\s*mensal|juros", re.I),
            "input[name*='taxa']:visible,input[name*='juros']:visible,input[id*='taxa']:visible,input[id*='juros']:visible,input[placeholder*='taxa']:visible,input[placeholder*='juros']:visible",
            nth,
            v,
        )

    def set_periodo(self, v: str, nth: int = 2) -> None:
        self._smart_fill(
            re.compile(r"per[ií]odo|prazo|tempo|meses|anos|parcela", re.I),
            "input[name*='periodo']:visible,input[name*='prazo']:visible,input[name*='tempo']:visible,input[id*='periodo']:visible,input[id*='prazo']:visible,input[placeholder*='período']:visible,input[placeholder*='periodo']:visible,input[placeholder*='prazo']:visible",
            nth,
            v,
        )

    def set_valor_mensal(self, v: str, nth: int = 3) -> None:
        self._smart_fill(
            re.compile(r"valor\s*mensal|aporte\s*mensal|parcela\s*mensal|mensal|aporte|dep[oó]sito\s*mensal", re.I),
            "input[name*='mensal']:visible,input[name*='aporte']:visible,input[id*='mensal']:visible,input[id*='aporte']:visible,input[placeholder*='mensal']:visible,input[placeholder*='aporte']:visible",
            nth,
            v,
        )

    def _clicar_calcular(self) -> None:
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
                self.page.locator(
                    "input[type=submit]:visible,button[type=submit]:visible,button[class*='calc']:visible"
                ).first.click(timeout=4000)
            except Exception:
                self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1200)

    def calcular(self) -> None:
        self._clicar_calcular()

    def calc_divida(self, ini: str, taxa: str, periodo: str) -> None:
        self.modo_divida()
        self.set_valor_inicial(ini, 0)
        self.set_taxa(taxa, 1)
        self.set_periodo(periodo, 2)
        self._clicar_calcular()

    def calc_investimento(self, ini: str, mensal: str, taxa: str, periodo: str) -> None:
        self.modo_investimento()
        self.set_valor_inicial(ini, 0)
        self.set_valor_mensal(mensal, 1)
        self.set_taxa(taxa, 2)
        self.set_periodo(periodo, 3)
        self._clicar_calcular()

    def resultado(self) -> str:
        loc = self.page.locator(
            "div[class*='resultado']:visible, section[class*='result']:visible, "
            "div[class*='result']:visible, [data-testid*='result']:visible, "
            "[class*='montante']:visible, [class*='total']:visible, [id*='resultado']:visible"
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
            "div[class*='resultado']:visible, section[class*='result']:visible, "
            "div[class*='result']:visible, [id*='resultado']:visible, div[id*='result']:visible"
        )
        return loc.count() > 0 and any(e.is_visible() for e in loc.all())

    def modo_divida_ativo(self) -> bool:
        sel = (
            self.page.get_by_role("radio", name=re.compile(r"d[íi]vida|devedor", re.I))
            .or_(
                self.page.locator(
                    "button[class*='tab']:visible,[role=tab]:visible,label[for*='divida']:visible"
                )
            )
        )
        for t in sel.all():
            try:
                if t.count() == 0 or not t.is_visible():
                    continue
                cls = t.get_attribute("class") or ""
                pressed = t.get_attribute("aria-pressed")
                checked = t.get_attribute("checked")
                if pressed == "true" or checked in ("", "checked", "true") or "active" in cls:
                    txt = (t.inner_text() or t.get_attribute("value") or "").lower()
                    if re.search(r"d[íi]vida|devedor", txt):
                        return True
            except Exception:
                continue
        return False

    def modo_invest_ativo(self) -> bool:
        sel = (
            self.page.get_by_role("radio", name=re.compile(r"investimento|invest|aplica[cç][aã]o", re.I))
            .or_(
                self.page.locator(
                    "button[class*='tab']:visible,[role=tab]:visible,label[for*='invest']:visible"
                )
            )
        )
        for t in sel.all():
            try:
                if t.count() == 0 or not t.is_visible():
                    continue
                cls = t.get_attribute("class") or ""
                pressed = t.get_attribute("aria-pressed")
                checked = t.get_attribute("checked")
                if pressed == "true" or checked in ("", "checked", "true") or "active" in cls:
                    txt = (t.inner_text() or t.get_attribute("value") or "").lower()
                    if re.search(r"invest|aplica", txt):
                        return True
            except Exception:
                continue
        return False
