"""Intercepta requisições HTTP, valida transações e persiste logs.

Uso interno pelos testes de API; valida status, headers, payloads, schema
e grava cada transação em txt/json para auditoria/debug.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Iterable
from typing import Optional

import requests

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

SEC_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "Referrer-Policy",
]

HEADER_FORMAT_RULES = {"Host": re.compile(r".+")}

IMG_URL_RE = re.compile(r"^https?://.+\.(jpg|jpeg|png|gif|webp)$", re.IGNORECASE)
JSON_CT_RE = re.compile(r"^application/json(;.+)?$", re.IGNORECASE)


@dataclass
class Transaction:
    id: str
    timestamp: str
    method: str
    url: str
    req_headers: dict[str, str]
    req_body: Optional[Any] = None
    res_status: Optional[int] = None
    res_reason: Optional[str] = None
    res_headers: Optional[dict[str, str]] = None
    res_body: Optional[Any] = None
    elapsed_ms: Optional[float] = None
    errors: list[str] = field(default_factory=list)

    def pretty(self) -> str:
        s = self
        body_ok = lambda b: b not in (None, "", b"")

        def fmt_body(b) -> list[str]:
            if not body_ok(b):
                return ["<empty>"]
            if isinstance(b, (dict, list)):
                try:
                    return json.dumps(b, ensure_ascii=False, indent=4).splitlines()
                except Exception:
                    pass
            text = str(b)
            if len(text) > 2000:
                text = text[:2000] + "..."
            return [text]

        lines = [
            "=" * 100,
            f"[{s.timestamp}] TX #{s.id}",
            "=" * 100,
            "--- REQUEST ---",
            f"Method  : {s.method}",
            f"URL     : {s.url}",
            "Headers :",
        ]
        lines += [f"  - {k}: {v}" for k, v in s.req_headers.items()]
        lines.append("Body    :")
        lines += [("    " + l) if i else l for i, l in enumerate(fmt_body(s.req_body))]

        lines += [
            "",
            "--- RESPONSE ---",
            f"Status    : {s.res_status} {s.res_reason}",
            f"Time (ms) : {s.elapsed_ms}",
        ]
        if s.res_headers:
            lines.append("Headers   :")
            lines += [f"  - {k}: {v}" for k, v in s.res_headers.items()]
        lines.append("Body      :")
        lines += [("    " + l) if i else l for i, l in enumerate(fmt_body(s.res_body))]

        if s.errors:
            lines += ["", "--- VALIDATION ERRORS ---"]
            lines += [f"  [{i}] {e}" for i, e in enumerate(s.errors, 1)]
        lines.append("=" * 100 + "\n")
        return "\n".join(lines)


def _dump_json(obj: Any, indent=2) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)
    except Exception:
        return str(obj)


def _to_dict(h) -> dict[str, str]:
    if h is None:
        return {}
    return dict(h) if isinstance(h, dict) else {k: v for k, v in h.items()}


class ApiLogger:
    def __init__(self, log_dir: str) -> None:
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.txs: list[Transaction] = []
        self._n = 0
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._txt = os.path.join(self.log_dir, f"api_transactions_{ts}.log")
        self._json = os.path.join(self.log_dir, f"api_transactions_{ts}.json")

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    def request(
        self,
        method: str,
        url: str,
        *,
        expect_status: Iterable[int] | None = None,
        req_headers: Iterable[str] | None = None,
        req_fields: dict[str, type] | None = None,
        res_headers: Iterable[str] | None = None,
        res_fields: dict[str, type] | None = None,
        schema: Any = None,
        check_sec: bool = False,
        req_content_type: str | None = None,
        res_content_type: str | None = "application/json",
        validators: list | None = None,
        **kw: Any,
    ) -> requests.Response:
        m = str(method).upper()
        if m not in VALID_METHODS:
            raise ValueError(f"Invalid HTTP method: {method}")

        self._n += 1
        txid = f"T{self._n:04d}"
        ts = datetime.now().isoformat(timespec="milliseconds")

        hdrs = dict(kw.get("headers", {}) or {})
        body = kw.get("json", kw.get("data", None))

        tx = Transaction(
            id=txid,
            timestamp=ts,
            method=m,
            url=url,
            req_headers=_to_dict(hdrs),
            req_body=body,
        )

        start = datetime.now()
        try:
            resp = requests.request(m, url, timeout=kw.pop("timeout", 30), **kw)
        except Exception as exc:
            tx.errors.append(f"HTTP call exception: {exc!r}")
            self._save(tx)
            raise AssertionError(tx.errors[-1])

        tx.res_status = resp.status_code
        tx.res_reason = resp.reason
        tx.elapsed_ms = round((datetime.now() - start).total_seconds() * 1000, 2)
        tx.res_headers = _to_dict(resp.headers)

        try:
            tx.res_body = resp.json()
        except Exception:
            tx.res_body = resp.text[:4000] if resp.text else None

        errs: list[str] = []
        steps = [
            (expect_status is not None, lambda: _assert_status(resp, list(expect_status))),
            (bool(req_headers), lambda: _assert_headers(tx.req_headers, list(req_headers), "Request")),
            (
                bool(req_content_type) and m not in SAFE_METHODS,
                lambda: _assert_ct(tx.req_headers, req_content_type, "Request"),
            ),
            (bool(req_fields), lambda: _assert_fields(tx.req_body, req_fields, "Request")),
            (bool(res_headers), lambda: _assert_headers(tx.res_headers or {}, list(res_headers), "Response")),
            (
                bool(res_content_type),
                lambda: self.__assert_res_ct(tx, res_content_type, expect_status, errs),
            ),
            (check_sec and (tx.res_status or 0) < 500, lambda: _assert_sec(tx.res_headers or {})),
            (bool(res_fields), lambda: _assert_fields(tx.res_body, res_fields, "Response")),
            (schema is not None and callable(schema), lambda: self.__run_schema(schema, tx.res_body, errs)),
            (bool(validators), lambda: self.__run_validators(validators, resp, tx, errs)),
            (True, lambda: _assert_flow(m, tx)),
        ]

        for enabled, fn in steps:
            if not enabled:
                continue
            try:
                fn()
            except AssertionError as exc:
                errs.append(str(exc))

        tx.errors = errs
        self.txs.append(tx)
        self._save(tx)

        if errs:
            raise AssertionError(
                f"TX #{txid} failed in {len(errs)} check(s):\n"
                + "\n".join(f"  - {e}" for e in errs)
                + f"\n\nstatus={tx.res_status} | {tx.method} {tx.url}"
            )

        return resp

    # ------------------------------------------------------------------
    # Helpers internos (evitam try/except duplicados em steps)
    # ------------------------------------------------------------------
    @staticmethod
    def __assert_res_ct(tx, expected, expect_status, errs) -> None:
        try:
            _assert_ct(tx.res_headers or {}, expected, "Response")
        except AssertionError as exc:
            if expect_status and all(s >= 400 for s in expect_status):
                errs.append(f"[Warning - Response Content-Type]: {exc}")
                return
            raise

    @staticmethod
    def __run_schema(fn, body, errs) -> None:
        try:
            fn(body)
        except AssertionError as exc:
            raise AssertionError(f"[Schema]: {exc}")
        except Exception as exc:
            raise AssertionError(f"[Schema exception]: {exc!r}")

    @staticmethod
    def __run_validators(items, resp, tx, errs) -> None:
        for idx, v in enumerate(items, 1):
            if not callable(v):
                raise AssertionError(f"[Validator #{idx}]: not callable")
            try:
                v(resp, tx)
            except AssertionError as exc:
                raise AssertionError(f"[Validator #{idx}]: {exc}")
            except Exception as exc:
                raise AssertionError(f"[Validator #{idx} exception]: {exc!r}")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save(self, tx: Transaction) -> None:
        try:
            with open(self._txt, "a", encoding="utf-8") as fp:
                fp.write(tx.pretty() + "\n")
        except Exception as exc:
            print(f"[ERROR] Failed write TX txt log: {exc}")

        try:
            payload = [asdict(t) for t in [*self.txs, tx]]
            with open(self._json, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2, default=str)
        except Exception as exc:
            print(f"[ERROR] Failed write TX json log: {exc}")

    @property
    def txt_log(self) -> str:
        return self._txt

    @property
    def json_log(self) -> str:
        return self._json


# ======================================================================
# Pure validators
# ======================================================================


def _assert_status(resp: requests.Response, expected: list[int]) -> None:
    if resp.status_code not in expected:
        raise AssertionError(
            f"[HTTP Status] Expected {expected}, got {resp.status_code} {resp.reason}. "
            f"URL: {resp.request.method} {resp.url}"
        )


def _assert_headers(hdrs: dict[str, str], required: list[str], side: str) -> None:
    low = {k.lower(): k for k in hdrs.keys()}
    missing = [h for h in required if h.lower() not in low]
    if missing:
        raise AssertionError(
            f"[Headers {side}] Missing required headers: {missing}. Present: {list(hdrs)}"
        )
    for name, rx in HEADER_FORMAT_RULES.items():
        if name in hdrs and not rx.match(hdrs[name]):
            raise AssertionError(f"[Headers {side}] Bad format for '{name}': {hdrs[name]!r}")


def _assert_ct(hdrs: dict[str, str], expected: str, side: str) -> None:
    actual = next((v for k, v in hdrs.items() if k.lower() == "content-type"), None)
    if actual is None:
        raise AssertionError(f"[Content-Type {side}] Header missing. Expected: {expected}")

    if expected == "application/json":
        ok = bool(JSON_CT_RE.match(actual))
    else:
        ok = expected.lower() in actual.lower()
    if not ok:
        raise AssertionError(f"[Content-Type {side}] Expected '{expected}', got '{actual}'.")


def _assert_fields(payload: Any, schema: dict[str, type], side: str) -> None:
    if payload is None:
        raise AssertionError(f"[Payload {side}] Empty/None. Required fields: {list(schema)}")
    if not isinstance(payload, dict):
        raise AssertionError(f"[Payload {side}] Not a dict: {type(payload).__name__}")
    for field_name, expected_type in schema.items():
        if field_name not in payload:
            raise AssertionError(
                f"[Payload {side}] Missing required field '{field_name}'. Keys: {list(payload)}"
            )
        val = payload[field_name]
        if not isinstance(val, expected_type):
            raise AssertionError(
                f"[Payload {side}] Field '{field_name}' bad type. "
                f"Expected {expected_type.__name__}, got {type(val).__name__} (val: {val!r})"
            )
        if isinstance(val, (str, list, dict)) and len(val) == 0:
            raise AssertionError(
                f"[Payload {side}] Empty field '{field_name}' ({expected_type.__name__}). val={val!r}"
            )


def _assert_sec(hdrs: dict[str, str]) -> None:
    low = {k.lower() for k in hdrs.keys()}
    missing = [h for h in SEC_HEADERS if h.lower() not in low]
    if missing:
        raise AssertionError(f"[Security Headers] Missing recommended: {missing}")


def _assert_flow(method: str, tx: Transaction) -> None:
    if tx.res_status == 201 and method not in {"POST", "PUT"}:
        raise AssertionError(
            f"[Flow Consistency] Status 201 Created with method {method}. Expect POST/PUT."
        )
    if tx.res_status == 204 and tx.res_body not in (None, "", b""):
        raise AssertionError("[Flow Consistency] 204 No Content returned body.")
    if tx.res_status and tx.res_status >= 400 and isinstance(tx.res_body, dict):
        if tx.res_status == 404:
            return
        error_keys = {"error", "message", "status"}
        if not any(k.lower() in error_keys for k in tx.res_body.keys()):
            raise AssertionError(
                f"[Flow Consistency] Error response {tx.res_status} without standard "
                f"keys (error/message/status). Keys: {list(tx.res_body)}"
            )
