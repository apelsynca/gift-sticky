import base64
from types import SimpleNamespace

import pytest
from litestar import Litestar, post
from litestar.status_codes import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient
from pytest_mock import MockerFixture

from sticky.admin_auth import require_admin
from sticky.config import settings
from sticky.sqladmin import AdminAuth


@post("/protected", guards=[require_admin])
async def protected() -> None:
    return None


def basic_auth(credentials: bytes) -> dict[str, str]:
    return {"Authorization": f"Basic {base64.b64encode(credentials).decode()}"}


@pytest.fixture
def admin_settings(mocker: MockerFixture) -> None:
    mocker.patch.object(settings, "ADMIN_USERNAME", "root")
    mocker.patch.object(settings, "ADMIN_PASSWORD", "pa:ss-wörd")
    mocker.patch.object(settings, "ADMIN_AUTH_KEY", "signing-key")


@pytest.mark.usefixtures("admin_settings")
def test_guard_accepts_right_credentials() -> None:
    with TestClient(Litestar([protected])) as client:
        response = client.post(
            "/protected", headers=basic_auth("root:pa:ss-wörd".encode())
        )

    assert response.status_code == HTTP_201_CREATED


@pytest.mark.usefixtures("admin_settings")
@pytest.mark.parametrize(
    "headers",
    [
        {},
        basic_auth(b"root:wrong"),
        basic_auth(b"no-separator"),
        basic_auth(b"\xff\xfe"),
        {"Authorization": "Basic not-base64!"},
        {"Authorization": "Bearer token"},
    ],
)
def test_guard_rejects_wrong_credentials(headers: dict[str, str]) -> None:
    with TestClient(Litestar([protected])) as client:
        response = client.post("/protected", headers=headers)

    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_guard_rejects_everything_if_password_not_configured(
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(settings, "ADMIN_USERNAME", "root")
    mocker.patch.object(settings, "ADMIN_PASSWORD", "")

    with TestClient(Litestar([protected])) as client:
        response = client.post("/protected", headers=basic_auth(b"root:"))

    assert response.status_code == HTTP_401_UNAUTHORIZED


def make_request(form: dict[str, str]) -> SimpleNamespace:
    async def get_form() -> dict[str, str]:
        return form

    return SimpleNamespace(form=get_form, session={})


@pytest.mark.asyncio
@pytest.mark.usefixtures("admin_settings")
async def test_login_session_authenticates_and_holds_no_password() -> None:
    backend = AdminAuth(secret_key="signing-key")
    request = make_request({"username": "root", "password": "pa:ss-wörd"})

    assert await backend.login(request) is True
    assert "pa:ss-wörd" not in str(request.session)
    assert await backend.authenticate(request) is True


@pytest.mark.asyncio
@pytest.mark.usefixtures("admin_settings")
async def test_login_rejects_wrong_password_and_sets_no_session() -> None:
    backend = AdminAuth(secret_key="signing-key")
    request = make_request({"username": "root", "password": "wrong"})

    assert await backend.login(request) is False
    assert request.session == {}
    assert await backend.authenticate(request) is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("admin_settings")
async def test_authenticate_rejects_old_plaintext_session() -> None:
    backend = AdminAuth(secret_key="signing-key")
    request = make_request({})
    request.session["token"] = "root:pa:ss-wörd"

    assert await backend.authenticate(request) is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("admin_settings")
async def test_login_disabled_without_signing_key(mocker: MockerFixture) -> None:
    mocker.patch.object(settings, "ADMIN_AUTH_KEY", "")
    backend = AdminAuth(secret_key="")
    request = make_request({"username": "root", "password": "pa:ss-wörd"})

    assert await backend.login(request) is False
