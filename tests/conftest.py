import os
import sys
import json
from typing import Generator

import pytest
import pytest_html
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.api_logger import ApiLogger  # noqa: E402

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
API_LOGS_DIR = os.path.join(REPORTS_DIR, "api_logs")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(API_LOGS_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Generator[Browser, None, None]:
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
        ],
    )
    yield browser
    browser.close()


UA_FALLBACK = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)


@pytest.fixture(scope="function")
def context(browser: Browser, request: pytest.FixtureRequest) -> Generator[BrowserContext, None, None]:
    traces_dir = os.path.join(REPORTS_DIR, "traces")
    os.makedirs(traces_dir, exist_ok=True)
    safe = request.node.name.translate({ord(c): "_" for c in ":/\\ "})
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=UA_FALLBACK,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        ignore_https_errors=True,
        color_scheme="light",
        device_scale_factor=1,
        is_mobile=False,
        has_touch=False,
        java_script_enabled=True,
        extra_http_headers={
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Ch-Ua-Mobile": "?0",
        },
        permissions=["geolocation"],
        record_video_dir=os.path.join(REPORTS_DIR, "videos"),
        record_video_size={"width": 1280, "height": 720},
    )
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    ctx.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US','en'] });
    Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
    Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    window.chrome = { runtime: {}, loadTimes: () => ({}), csi: () => ({}) };
    if (window.screen) {
        Object.defineProperty(window.screen, 'width', { get: () => 1920 });
        Object.defineProperty(window.screen, 'height', { get: () => 1080 });
        Object.defineProperty(window.screen, 'availWidth', { get: () => 1920 });
        Object.defineProperty(window.screen, 'availHeight', { get: () => 1040 });
        Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
    }
    const __origGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(p) {
        if (p === 37445) return 'Intel Inc.';
        if (p === 37446) return 'Mesa Intel(R) UHD Graphics 630 (CFL GT2)';
        return __origGetParameter.call(this, p);
    };
    """)
    ctx.set_default_timeout(15000)
    ctx.set_default_navigation_timeout(30000)
    yield ctx
    try:
        ctx.tracing.stop(path=os.path.join(traces_dir, f"{safe}.zip"))
    except Exception:
        pass
    try:
        ctx.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    pg = context.new_page()
    yield pg
    failed = False
    try:
        rep = getattr(request.node, "rep_call", None) or getattr(request.node, "rep_teardown", None)
        failed = bool(rep and rep.failed)
    except Exception:
        pass
    if failed:
        safe = request.node.name.translate({ord(c): "_" for c in ":/\\ "})
        try:
            pg.screenshot(
                path=os.path.join(REPORTS_DIR, f"FAIL_{safe}.png"),
                full_page=True,
            )
        except Exception:
            pass
        try:
            with open(os.path.join(REPORTS_DIR, f"FAIL_{safe}.html"), "w", encoding="utf-8") as f:
                f.write(pg.content())
        except Exception:
            pass
    try:
        pg.close()
    except Exception:
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="session")
def dog_api_base_url() -> str:
    return "https://dog.ceo/api"


@pytest.fixture(scope="session")
def api_logger() -> Generator[ApiLogger, None, None]:
    yield ApiLogger(log_dir=API_LOGS_DIR)


@pytest.fixture(scope="function")
def api_client(
    dog_api_base_url: str,
    api_logger: ApiLogger,
    request: pytest.FixtureRequest,
) -> Generator["DogApiClient", None, None]:
    """Cliente HTTP por teste; grava transações no report HTML após execução."""
    client = DogApiClient(dog_api_base_url, api_logger)
    yield client

    txs = client.tx_list()
    safe = request.node.name.translate({ord(c): "_" for c in ":/\\ "})
    html_path = os.path.join(API_LOGS_DIR, f"{safe}_{request.node.fspath.purebasename or 'test'}_tx.html")
    try:
        _write_tx_html(txs, html_path, request.node.nodeid)
    except Exception:
        pass


def _fmt_html_body(b) -> str:
    if b is None or b == "":
        return "<i>vazio</i>"
    if isinstance(b, (dict, list)):
        try:
            s = json.dumps(b, ensure_ascii=False, indent=2)
        except Exception:
            s = str(b)
    else:
        s = str(b)
    s = s[:8000] + ("..." if len(s) > 8000 else "")
    return (
        '<pre style="background:#f7f7f7;border:1px solid #ddd;padding:6px;border-radius:3px;'
        'margin:2px 0;white-space:pre-wrap;max-height:320px;overflow:auto;">' + s + "</pre>"
    )


def _write_tx_html(txs, path: str, test_id: str) -> None:
    if not txs:
        return
    rows = []
    for t in txs:
        has_err = bool(t.errors)
        color = "#c9302c" if has_err else "#337ab7"
        badge = (
            f'<span style="color:#fff;background:#c9302c;padding:2px 6px;border-radius:3px;font-size:11px;">'
            f"{len(t.errors)} ERRO(S)</span>"
            if has_err
            else ""
        )
        req_h = "<br>".join(f"{k}: {v}" for k, v in t.req_headers.items()) or "<i>vazio</i>"
        res_h = "<br>".join(f"{k}: {v}" for k, v in (t.res_headers or {}).items()) or "<i>vazio</i>"
        errs_row = ""
        if has_err:
            err_items = "".join(f"<li>{e}</li>" for e in t.errors)
            errs_row = (
                f'<tr><th style="text-align:left;padding:4px;color:#c9302c;">Erros Validação</th>'
                f'<td style="padding:4px;color:#c9302c;">{err_items}</td></tr>'
            )
        rows.append(
            f"""
            <div style="border:1px solid {color};border-radius:4px;margin-bottom:12px;overflow:hidden;">
              <div style="background:{color};color:#fff;padding:8px 12px;font-weight:bold;">
                {t.id} &nbsp;|&nbsp; {t.method} {t.url} &nbsp;|&nbsp; {t.res_status} {t.res_reason}
                &nbsp;<small>({t.elapsed_ms}ms)</small> {badge}
              </div>
              <div style="padding:8px 12px;">
                <table style="width:100%;border-collapse:collapse;">
                  <tr><th style="text-align:left;width:140px;padding:4px;">Timestamp</th><td style="padding:4px;">{t.timestamp}</td></tr>
                  <tr><th style="text-align:left;padding:4px;">Request Headers</th><td style="padding:4px;">{req_h}</td></tr>
                  <tr><th style="text-align:left;padding:4px;">Request Body</th><td style="padding:4px;">{_fmt_html_body(t.req_body)}</td></tr>
                  <tr><th style="text-align:left;padding:4px;">Response Headers</th><td style="padding:4px;">{res_h}</td></tr>
                  <tr><th style="text-align:left;padding:4px;">Response Body</th><td style="padding:4px;">{_fmt_html_body(t.res_body)}</td></tr>
                  {errs_row}
                </table>
              </div>
            </div>
            """
        )

    html = (
        """<!DOCTYPE html><html><head><meta charset="UTF-8">
        <title>API Transactions - """
        + test_id
        + """</title></head>
        <body style="font-family:Arial,sans-serif;font-size:13px;padding:20px;">
        <h2>Transações HTTP do Teste</h2>
        <p style="color:#555;">Teste: <code>"""
        + test_id
        + f"""</code> &nbsp;|&nbsp; Total de transações: <b>{len(txs)}</b></p>
        {''.join(rows)}
        </body></html>"""
    )
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(html)


class DogApiClient:
    """Cliente tipado para Dog API; usa ApiLogger para captura e validação."""

    _WRITE_CT = {"POST", "PUT", "PATCH"}

    def __init__(self, base_url: str, logger: ApiLogger) -> None:
        self.base = base_url.rstrip("/")
        self.logger = logger
        self._ids: list[str] = []

    def _headers(self, extra: dict | None = None) -> dict:
        base = {
            "Accept": "application/json",
            "User-Agent": "DesafioAgibankTestAutomation/1.0",
        }
        if extra:
            base.update(extra)
        return base

    def _do(self, method: str, path: str, **kw):
        before = len(self.logger.txs)
        extra_headers = (
            {"Content-Type": "application/json", **(kw.pop("headers", None) or {})}
            if method in self._WRITE_CT
            else kw.pop("headers", None)
        )
        resp = self.logger.request(
            method,
            self.base + path,
            headers=self._headers(extra_headers),
            **kw,
        )
        self._track(before)
        return resp

    def get(self, path: str, **kw):
        return self._do("GET", path, **kw)

    def post(self, path: str, **kw):
        return self._do("POST", path, **kw)

    def put(self, path: str, **kw):
        return self._do("PUT", path, **kw)

    def delete(self, path: str, **kw):
        return self._do("DELETE", path, **kw)

    def _track(self, before: int) -> None:
        self._ids.extend(t.id for t in self.logger.txs[before:])

    def tx_list(self):
        present = set(self._ids)
        return [t for t in self.logger.txs if t.id in present]


# ======================================================================
# pytest-html hooks
# ======================================================================


def pytest_configure(config) -> None:
    try:
        meta = config._metadata  # type: ignore[attr-defined]
    except Exception:
        meta = None
    if meta is None:
        return
    meta["Projeto"] = "Desafio Agibank - QA Automação (Web + API)"
    meta["Módulo API"] = "Dog API (https://dog.ceo/dog-api)"
    meta["Módulo Web"] = "Agibank + Blog do Agi (Playwright POM)"
    meta["Log API (txt)"] = _relative_if(_latest_log(".log"))
    meta["Log API (json)"] = _relative_if(_latest_log(".json"))
    meta["Pasta Transacoes"] = os.path.relpath(API_LOGS_DIR, PROJECT_ROOT)


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    """Anti-regressao: avisa com WARNING se --html foi fornecido mas 0 testes
    foram realmente EXECUTADOS (nao so coletados, ex: --collect-only).

    Esse era o bug do report vazio: addopts do pytest.ini tinha --html, entao
    pytest --collect-only sobrescrevia o report com 0 resultados.
    """

    import sys as _sys

    def _tem_html_flag() -> bool:
        argv_flag = any(a.startswith("--html") for a in _sys.argv[1:])
        try:
            cfg1 = bool(getattr(config.option, "htmlpath", None))
        except Exception:
            cfg1 = False
        try:
            cfg2 = bool(getattr(config.option, "html", None))
        except Exception:
            cfg2 = False
        return bool(argv_flag or cfg1 or cfg2)

    html_flag = _tem_html_flag()

    try:
        stats = getattr(terminalreporter, "stats", {}) or {}
    except Exception:
        stats = {}

    executed_keys = {"passed", "failed", "error", "skipped", "xfailed", "xpassed"}
    total_exec = sum(len(stats.get(k, [])) for k in executed_keys)

    if html_flag and total_exec == 0:
        warning = "\n".join([
            "",
            "=" * 72,
            "!!  AVISO  !!  RELATORIO HTML PODE ESTAR VAZIO / SEM SERVICOS",
            "=" * 72,
            "- Voce forneceu --html=... mas 0 testes foram executados.",
            "- Isso normalmente acontece quando voce roda:",
            "    * pytest --collect-only          (so coleta, nao roda os testes)",
            "    * pytest -m marker_que_nao_existe  (0 testes batem o marker)",
            "    * pytest -k keyword_nao_existe    (0 testes batem o keyword)",
            "",
            "   [CORRETO] Para gerar um relatorio COM os resultados dos servicos,",
            "   remova --collect-only e rode os testes de verdade:",
            "   * API: pytest -m api -vv --html=reports/report.html",
            "   * Web+API completo (CI): pytest -vv --html=reports/report.html",
            "=" * 72,
            "",
        ])
        try:
            terminalreporter.write(warning, red=True, bold=True)
            terminalreporter.write("\n", flush=True)
        except Exception:
            try:
                print(warning, file=_sys.stderr, flush=True)
            except Exception:
                print(warning)


def _relative_if(p: str) -> str:
    return os.path.relpath(p, PROJECT_ROOT) if p else "<n/a>"


def _latest_log(ext: str = ".log") -> str:
    try:
        files = sorted(f for f in os.listdir(API_LOGS_DIR) if f.endswith(ext))
        return os.path.join(API_LOGS_DIR, files[-1]) if files else ""
    except Exception:
        return ""


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not hasattr(item, "_request"):
        return

    try:
        client = item.funcargs.get("api_client")
    except Exception:
        client = None

    try:
        extra = list(getattr(report, "extra", []) or [])
    except Exception:
        extra = []

    if client is not None:
        try:
            txs = client.tx_list()
        except Exception:
            txs = []
        if txs:
            blocks = []
            for t in txs:
                has_err = bool(t.errors)
                color = "#c9302c" if has_err else "#337ab7"
                try:
                    req_h = "<br>".join(
                        f"{k}: {v}" for k, v in (t.req_headers or {}).items()
                    ) or "<i>vazio</i>"
                except Exception:
                    req_h = "<i>indisponivel</i>"
                try:
                    res_h = "<br>".join(
                        f"{k}: {v}" for k, v in (t.res_headers or {}).items()
                    ) or "<i>vazio</i>"
                except Exception:
                    res_h = "<i>indisponivel</i>"
                badge = (
                    (
                        f" &nbsp; <span style='background:#fff;color:{color};"
                        f"padding:1px 6px;border-radius:3px;font-size:11px;'>"
                        f"{len(t.errors)} FALHA(S)</span>"
                    )
                    if has_err
                    else ""
                )
                errs_html = (
                    (
                        f'<p style="margin-top:6px;color:{color};font-weight:bold;">'
                        f"Falhas de validação:</p>"
                        f'<ul style="margin:0;color:{color};">'
                        f'{"".join(f"<li>{e}</li>" for e in t.errors)}</ul>'
                    )
                    if has_err
                    else ""
                )
                blocks.append(
                    f"""
                    <details style="margin-bottom:10px;border:1px solid {color};border-radius:4px;overflow:hidden;">
                      <summary style="cursor:pointer;background:{color};color:#fff;padding:6px 10px;font-weight:bold;">
                        {getattr(t, 'id', 'TX')} &mdash; {getattr(t, 'method', 'GET')} {getattr(t, 'url', '')} &nbsp; status: <b>{getattr(t, 'res_status', '')} {getattr(t, 'res_reason', '')}</b>
                        &nbsp;<small>({getattr(t, 'elapsed_ms', 0)} ms)</small>{badge}
                      </summary>
                      <div style="padding:8px 12px;font-family:monospace;font-size:12px;">
                        <p style="margin:2px 0;"><b>Timestamp:</b> {getattr(t, 'timestamp', '')}</p>
                        <p style="margin:2px 0;"><b>Request Headers:</b><br>{req_h}</p>
                        <p style="margin:2px 0;"><b>Request Body:</b><br>{_fmt_html_body(getattr(t, 'req_body', ''))}</p>
                        <p style="margin:2px 0;"><b>Response Headers:</b><br>{res_h}</p>
                        <p style="margin:2px 0;"><b>Response Body:</b><br>{_fmt_html_body(getattr(t, 'res_body', ''))}</p>
                        {errs_html}
                      </div>
                    </details>
                    """
                )

            html_body = (
                f'<div style="margin-top:8px;">'
                f'<h4 style="margin:4px 0;color:#333;">Transações HTTP executadas ({len(txs)})</h4>'
                + "".join(blocks)
                + "</div>"
            )
            try:
                extra.append(pytest_html.extras.html(html_body))
            except Exception:
                extra.append({"type": "html", "content": html_body, "value": html_body})

    if extra:
        try:
            report.extras = extra
        except Exception:
            try:
                report.extra = extra
            except Exception:
                pass
