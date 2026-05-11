import pytest
from httpx import AsyncClient, Response
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_sign_up_with_email(create_user: Response):
    json_res = create_user.json()

    assert create_user.status_code == 201
    assert json_res["status"] == "success"


@pytest.mark.asyncio
async def test_verify_email(verify_user: Response):
    json_res = verify_user.json()

    assert verify_user.status_code == 201
    assert json_res["status"] == "success"


@pytest.mark.asyncio
async def test_resend_otp_token(async_client: AsyncClient):
    path: str = "app.api.services.user_service.send_email.delay"

    resend_otp_payload: dict = {
        "email": "test_user_email",
    }

    with patch(path, new_callable=AsyncMock) as email_patch:
        res: Response = await async_client.post(
            "/auth/verify/resend",
            json=resend_otp_payload,
            headers={"x-api-version": "1"},
        )

    json_res = res.json()

    email_patch.assert_called_once()

    assert res.status_code == 201
    assert json_res["status"] == "success"


@pytest.mark.asyncio
async def test_login(async_client: AsyncClient, verify_user: Response):
    login_payload: dict = {
        "email": "test_user_email",
        "password": "test_user_password",
    }

    res: Response = await async_client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-api-version": "1"},
    )

    json_res = res.json()

    assert res.status_code == 201
    assert "access_token" in json_res


@pytest.mark.asyncio
async def test_sign_in_google(async_client: AsyncClient):
    url_path: str = "app.v1.routers.auth.Request.url_for"
    token_path: str = "app.v1.routers.auth.oauth.google.authorize_redirect"

    url_patch: AsyncMock = patch(url_path, new_callable=AsyncMock).start()
    token_patch: AsyncMock = patch(token_path, new_callable=AsyncMock).start()

    token_patch.return_value = None

    res: Response = await async_client.get(
        "/auth/google", headers={"x-api-version": "1"}
    )

    url_patch.stop()
    token_patch.stop()

    assert res.status_code == 302

    url_patch.assert_called_once()
    token_patch.assert_awaited_once()


@pytest.mark.asyncio
async def test_google_callback(async_client: AsyncClient):
    payload: dict = {
        "sub": "randomfakeid",
        "email": "test_user_email",
        "given_name": "test_first_name",
        "family_name": "test_last_name"
    }

    payload_path: str = "app.api.services.auth_service.decode_id_token"
    token_path: str = "app.api.routers.auth.oauth.google.authorize_access_token"

    token_patch: AsyncMock = patch(token_path, new_callable=AsyncMock).start()
    payload_patch: AsyncMock = patch(payload_path, new_callable=AsyncMock).start()

    payload_patch.return_value = payload

    res: Response = await async_client.post(
        "/auth/google/callback", headers={"x-api-version": "1"}
    )

    token_patch.stop()
    payload_patch.stop()

    json_res = res.json()

    assert res.status_code == 201
    assert "access_token" in json_res

    token_patch.assert_called_once()
    payload_patch.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, verify_user: Response):
    login_payload: dict = {
        "email": "test_user_email",
        "password": "test_user_password",
    }

    login_res: Response = await async_client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-api-version": "1"},
    )

    access_token = login_res.json()["access_token"]

    res: Response = await async_client.get(
        "/auth/me",
        headers={"x-api-version": "1", "Authorization": f"Bearer {access_token}"},
    )

    json_res = res.json()

    assert res.status_code == 200
    assert "test_user_email" == json_res["data"]["email"]


@pytest.mark.asyncio
async def test_unauthenticated_user(async_client: AsyncClient):
    res: Response = await async_client.get(
        "/auth/me",
        headers={"x-api-version": "1"},
    )

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_access_token(async_client: AsyncClient, verify_user: Response):
    login_payload: dict = {
        "email": "test_user_email",
        "password": "test_user_password",
    }

    await async_client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-api-version": "1"},
    )

    res = await async_client.get(
        "/auth/refresh",
        headers={"x-api-version": "1"},
    )
    json_res = res.json()

    assert res.status_code == 201
    assert "access_token" in json_res


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    login_payload: dict = {
        "email": "test_user_email",
        "password": "test_user_password",
    }

    login_res: Response = await async_client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-api-version": "1"},
    )

    access_token = login_res.json()["access_token"]

    res: Response = await async_client.post(
        "/auth/login",
        headers={"x-api-version": "1", "Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 200
