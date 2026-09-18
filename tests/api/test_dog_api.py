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
SUB_BREED = "afghan"
SUB_BREED_INVALID = "sub_raca_inexistente_xyz_123"
EXPECTED_HOUND_SUB_BREEDS = {
    "afghan", "basset", "blood", "english", "ibizan", "plott", "walker",
}


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


def breed_random_img_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st == "success", (
        f"Expected status='success', got {st!r}"
    )
    msg = body["message"]
    assert isinstance(msg, str) and msg.strip(), "Breed random image URL missing/empty"
    assert IMG_URL_RE.match(msg), f"Invalid breed random image URL: {msg!r}"


def breed_random_multiple_schema(body: Any, expected_n: int = 3) -> None:
    assert isinstance(body, dict), "Body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st == "success", (
        f"Expected status='success', got {st!r}"
    )
    msg = body["message"]
    assert isinstance(msg, list), f"message must be list (got {type(msg).__name__})"
    assert len(msg) == expected_n, (
        f"Expected {expected_n} image URLs, got {len(msg)}. Values: {msg}"
    )
    bad = [u for u in msg if not (isinstance(u, str) and IMG_URL_RE.match(u or ""))]
    assert len(bad) == 0, f"Invalid image URL(s) in breed random/{expected_n}: {bad[:5]}"


def sub_breed_list_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st == "success", (
        f"Expected status='success', got {st!r}"
    )
    msg = body["message"]
    assert isinstance(msg, list), f"message must be list (got {type(msg).__name__})"
    assert len(msg) > 0, "Sub-breed list empty"
    bad = [s for s in msg if not (isinstance(s, str) and s.strip())]
    assert len(bad) == 0, f"Invalid sub-breed name(s): {bad[:5]}"


def sub_breed_images_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st == "success", (
        f"Expected status='success', got {st!r}"
    )
    msg = body["message"]
    assert isinstance(msg, list) and len(msg) > 0, "Sub-breed image list empty"
    bad = [u for u in msg if not IMG_URL_RE.match(u or "")]
    assert len(bad) == 0, f"Invalid sub-breed image URL(s). Examples: {bad[:5]}"


def sub_breed_random_img_schema(body: Any) -> None:
    assert isinstance(body, dict), "Body not dict"
    st = body.get("status")
    assert isinstance(st, str) and st == "success", (
        f"Expected status='success', got {st!r}"
    )
    msg = body["message"]
    assert isinstance(msg, str) and msg.strip(), (
        "Sub-breed random image URL missing/empty"
    )
    assert IMG_URL_RE.match(msg), (
        f"Invalid sub-breed random image URL: {msg!r}"
    )


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


def assert_has_expected_sub_breeds(resp, tx) -> None:
    subs = set(resp.json().get("message", []))
    missing = EXPECTED_HOUND_SUB_BREEDS - subs
    assert len(missing) == 0, (
        f"Missing expected sub-breeds for '{BREED}': {sorted(missing)}. "
        f"Got: {sorted(subs)}"
    )


def assert_min_sub_breed_imgs(resp, tx) -> None:
    urls = resp.json().get("message", [])
    assert isinstance(urls, list), "message not list"
    assert len(urls) >= 5, (
        f"Expected >= 5 images for '{BREED}/{SUB_BREED}', got {len(urls)}"
    )


def assert_sub_breed_urls_all_match_path(resp, tx) -> None:
    urls = resp.json().get("message", [])
    path_token = f"/breeds/{BREED}-{SUB_BREED}/"
    misplaced = [u for u in urls if path_token not in (u or "")]
    assert len(misplaced) == 0, (
        f"{len(misplaced)} URL(s) from /breed/{BREED}/{SUB_BREED}/images do NOT contain "
        f"'{path_token}': {misplaced[:5]}"
    )


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

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_breed_random_image_single(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/images/random",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            schema=breed_random_img_schema,
            validators=[assert_status_success],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_breed_random_image_single_contract(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/images/random",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            schema=breed_random_img_schema,
        )
        body = resp.json()
        msg = body["message"]
        assert f"/breeds/{BREED}-" in msg or f"/breeds/{BREED}/" in msg, (
            f"Random image breed endpoint should return image for '{BREED}'. Got: {msg!r}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_breed_random_images_three_contract(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/images/random/3",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=lambda b: breed_random_multiple_schema(b, expected_n=3),
            validators=[assert_status_success],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_breed_random_images_three_belong_to_breed(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/images/random/3",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
        )
        urls = resp.json()["message"]
        assert isinstance(urls, list) and len(urls) == 3, (
            f"Expected exactly 3 URLs. Got {len(urls)}: {urls}"
        )
        misplaced = [
            u for u in urls
            if f"/breeds/{BREED}-" not in (u or "") and f"/breeds/{BREED}/" not in (u or "")
        ]
        assert len(misplaced) == 0, (
            f"{len(misplaced)} URL(s) from /breed/{BREED}/images/random/3 do NOT look like "
            f"'{BREED}' breed images: {misplaced}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_sub_breed_list_status_200(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/list",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=sub_breed_list_schema,
            validators=[assert_status_success, assert_has_expected_sub_breeds],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_sub_breed_list_contract(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/list",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=sub_breed_list_schema,
        )
        subs = resp.json()["message"]
        duplicates = {s for s in subs if subs.count(s) > 1}
        assert len(duplicates) == 0, f"Duplicate sub-breed(s): {sorted(duplicates)}"
        assert SUB_BREED in subs, (
            f"Sub-breed '{SUB_BREED}' not found in {BREED}/list. Got: {subs}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_sub_breed_images_status_200(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=sub_breed_images_schema,
            validators=[
                assert_status_success,
                assert_min_sub_breed_imgs,
                assert_sub_breed_urls_all_match_path,
            ],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_sub_breed_images_all_urls_valid_and_match_sub(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
        )
        urls = resp.json()["message"]
        assert isinstance(urls, list) and urls, (
            f"Expected non-empty list, got {urls!r}"
        )

        path_token = f"/breeds/{BREED}-{SUB_BREED}/"
        bad_fmt, bad_path = [], []
        for i, u in enumerate(urls):
            if not (isinstance(u, str) and u.strip()):
                bad_fmt.append(f"[{i}] empty/non-string: {u!r}")
                continue
            if not IMG_URL_RE.match(u):
                bad_fmt.append(f"[{i}] bad URL format: {u!r}")
            if path_token not in u:
                bad_path.append(u)

        assert len(bad_fmt) == 0, (
            f"{len(bad_fmt)} URL format issue(s) in '{BREED}/{SUB_BREED}' images:\n"
            + "\n".join(bad_fmt[:15])
        )
        assert len(bad_path) == 0, (
            f"{len(bad_path)} URL(s) do NOT contain '{path_token}': {bad_path[:5]}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_sub_breed_random_image_single_status_200(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images/random",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            schema=sub_breed_random_img_schema,
            validators=[assert_status_success],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.contrato
    def test_sub_breed_random_image_single_contract(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images/random",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": str},
            schema=sub_breed_random_img_schema,
        )
        msg = resp.json()["message"]
        path_token = f"/breeds/{BREED}-{SUB_BREED}/"
        assert path_token in msg, (
            f"Sub-breed random endpoint should return URL with '{path_token}'. Got: {msg!r}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_sub_breed_random_images_three_contract(self, api_client) -> None:
        api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images/random/3",
            expect_status=[200],
            req_headers=["Accept"],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
            schema=lambda b: breed_random_multiple_schema(b, expected_n=3),
            validators=[assert_status_success],
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.funcional
    def test_sub_breed_random_images_three_all_match_sub_breed(
        self, api_client
    ) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/{SUB_BREED}/images/random/3",
            expect_status=[200],
            res_content_type="application/json",
            res_fields={"status": str, "message": list},
        )
        urls = resp.json()["message"]
        assert isinstance(urls, list) and len(urls) == 3, (
            f"Expected exactly 3 URLs for sub-breed random/3. Got {len(urls)}: {urls}"
        )
        path_token = f"/breeds/{BREED}-{SUB_BREED}/"
        misplaced = [u for u in urls if path_token not in (u or "")]
        assert len(misplaced) == 0, (
            f"{len(misplaced)} URL(s) from /breed/{BREED}/{SUB_BREED}/images/random/3 "
            f"do NOT contain '{path_token}': {misplaced}"
        )

    @pytest.mark.api
    @pytest.mark.dog_api
    @pytest.mark.erro
    def test_sub_breed_images_invalid_sub_breed_error(self, api_client) -> None:
        resp = api_client.get(
            f"/breed/{BREED}/{SUB_BREED_INVALID}/images",
            expect_status=[200, 404],
            res_fields={"status": str, "message": object},
            schema=error_schema,
        )
        body = resp.json()
        http = resp.status_code
        st = body.get("status")

        if http == 404:
            assert st == "error" or st is not None, (
                f"HTTP 404 (invalid sub-breed) mas status = {st!r}. Esperado 'error'."
            )
            return

        if http == 200:
            assert st == "error", (
                f"HTTP 200 com sub-raça inválida, mas status = {st!r} (esperado 'error')."
            )
            assert body.get("message") is not None, (
                "Error response (invalid sub-breed) missing message detail"
            )
            return

        pytest.fail(
            f"Unexpected HTTP {http} for invalid sub-breed. "
            f"Expect 200 (status='error') or 404."
        )
