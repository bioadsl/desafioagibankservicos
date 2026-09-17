"""Testes Dog API (dog.ceo). Cada chamada HTTP passa por ApiLogger.

Cada transação tem asserts automáticos de status, headers, payload e schema,
além de ser registrada em report/api_logs e embutida no report.html.
"""

from __future__ import annotations

from typing import Any

import pytest
from utils.api_logger import IMG_URL_RE


BREED = "hound"
BREED_INVALID = "raca_inexistente_xyz_999111"


# Schemas (estrutura do JSON de resposta)


def list_all_schema(body: Any) -> None:
    assert isinstance(body, dict), f"Body not dict ({type(body).__name__})"
    msg = body["message"]
    assert isinstance(msg, dict), "'message' must be a dict of breeds->sub-breeds"
    assert len(msg) > 0, "Breeds list empty"

    for race, subs in msg.items():
        assert isinstance(race, str) and race.strip(), f"Bad breed name: {race!r}"
        assert isinstance(subs, list), f"Breed '{race}' value not list"
        for s in subs:
            assert isinstance(s, str) and s.strip(), f"Bad sub-breed in {race}: {s!r}"


def breed_images_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    msg = body["message"]
    assert isinstance(msg, list) and len(msg) > 0, "Image list empty"
    bad = [u for u in msg if not IMG_URL_RE.match(u or "")]
    assert len(bad) == 0, f"Invalid image URL(s). Examples: {bad[:5]}"


def random_img_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    msg = body["message"]
    assert isinstance(msg, str) and msg.strip(), "Single image URL missing/empty"
    assert IMG_URL_RE.match(msg), f"Invalid image URL: {msg!r}"


def error_schema(body: Any) -> None:
    assert isinstance(body, dict), "Error body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st.lower() == "error", (
        f"Expected status='error' for error response, got {st!r}"
    )
    assert "message" in body, "Error response missing 'message'"


# Custom validators (recebem response + transaction)


def assert_status_success(resp, tx) -> None:
    body = resp.json()
    assert body.get("status") == "success", (
        f"status field != 'success'. Got {body.get('status')!r}. {tx.method} {tx.url}"
    )


def assert_has_hound(resp, tx) -> None:
    breeds = resp.json().get("message", {})
    assert isinstance(breeds, dict), "message not dict"
    assert BREED in breeds, f"Breed '{BREED}' not found in list-all. Total: {len(breeds)}"


def assert_min_hound_imgs(resp, tx) -> None:
    urls = resp.json().get("message", [])
    assert isinstance(urls, list), "message not list"
    assert len(urls) >= 10, f"Expected >= 10 images for '{BREED}', got {len(urls)}"


# ======================================================================
# Test Suite
# ======================================================================


class TestDogApi:
    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_list_all_status_200(self, api_client) -> None:
        api_client.get(
            "/breeds/list/all",
            expect_status=[200],
            req_headers=["Accept", "User-Agent"],
            res_content_type="application/json",
            res_fields={"status": str, "message": dict},
            schema=list_all_schema,
            validators=[assert_status_success, assert_has_hound],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_list_all_contract(self, api_client) -> None:
        api_client.get(
            "/breeds/list/all",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": dict},
            schema=list_all_schema,
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_list_all_not_empty(self, api_client) -> None:
        resp = api_client.get(
            "/breeds/list/all",
            expect_status=[200],
            res_fields={"status": str, "message": dict},
            schema=list_all_schema,
        )
        breeds = resp.json()["message"]
        assert len(breeds) >= 10, (
            f"Expected >= 10 breeds. Got {len(breeds)}. First 10: {list(breeds)[:10]}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_breed_images_valid_breed_200(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/images",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=breed_images_schema,
            validators=[assert_status_success, assert_min_hound_imgs],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_breed_images_valid_breed_contract(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/images",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=breed_images_schema,
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_breed_images_all_urls_valid(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/images",
            expect_status=[200],
            res_fields={"status": str, "message": list},
        )
        urls = resp.json()["message"]
        assert isinstance(urls, list) and urls, f"Expected non-empty list, got {urls!r}"

        bad = []
        for i, u in enumerate(urls):
            if not (isinstance(u, str) and u.strip()):
                bad.append(f"[{i}] empty/non-string: {u!r}")
                continue
            if not IMG_URL_RE.match(u):
                bad.append(f"[{i}] bad format: {u!r}")

        assert len(bad) == 0, (
            f"{len(bad)} URL issue(s) in '{BREED}' images:\n" + "\n".join(bad[:20])
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_random_image_status_200(self, api_client) -> None:
        api_client.get(
            "/breeds/image/random",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            validators=[assert_status_success],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_random_image_contract(self, api_client) -> None:
        api_client.get(
            "/breeds/image/random",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            schema=random_img_schema,
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.erro
    def test_breed_images_invalid_breed_error(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED_INVALID}/images",
            expect_status=[200, 404],
            res_fields={"status": str, "message": object},
            schema=error_schema,
        )
        body = resp.json()
        http = resp.status_code
        st = body.get("status")

        if http == 404:
            assert st == "error" or st is not None, (
                f"HTTP 404 mas campo status = {st!r}. Esperado 'error'."
            )
            return

        if http == 200:
            assert st == "error", (
                f"HTTP 200 com raça inválida, mas status = {st!r} (esperado 'error')."
            )
            assert body.get("message") is not None, "Error response missing message detail"
            return

        pytest.fail(f"Unexpected HTTP {http}. Expect 200 (status='error') or 404.")
