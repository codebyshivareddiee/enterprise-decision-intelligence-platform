"""Script to verify Authentication & Authorization."""



import asyncio
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()
import httpx
from httpx import ASGITransport
from httpx import ASGITransport
from app.main import app, lifespan

BASE_URL = "http://testserver/api/v1"


async def verify_auth() -> None:
    async with lifespan(app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL, timeout=30.0
        ) as client:
            email = f"test_{uuid.uuid4()}@example.com"
            password = "SecurePassword123!"

            print(f"1. Registering user: {email}")
            resp = await client.post(
                "/auth/register",
                json={"email": email, "password": password, "full_name": "Test User"},
            )
            if resp.status_code != 201:
                print(f"Failed to register: {resp.text}")
                sys.exit(1)

            print("2. Logging in...")
            resp = await client.post(
                "/auth/login", data={"username": email, "password": password}
            )
            if resp.status_code != 200:
                print(f"Failed to login: {resp.text}")
                sys.exit(1)

            tokens = resp.json()
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            print("3. Calling protected endpoint without token...")
            resp = await client.get("/auth/me")
            if resp.status_code != 401:
                print("Expected 401 Unauthorized")
                sys.exit(1)

            print("4. Calling protected endpoint with token...")
            resp = await client.get("/auth/me", headers=headers)
            if resp.status_code != 200:
                print(f"Expected 200, got {resp.status_code}: {resp.text}")
                sys.exit(1)

            print("5. Calling endpoint requiring specific permissions...")
            resp = await client.post(
                "/organizations",
                json={"name": "Test", "domain": "test.com"},
                headers=headers,
            )
            if resp.status_code != 403:
                print(f"Expected 403 Forbidden, got {resp.status_code}")
                sys.exit(1)

            print("6. Refreshing token...")
            resp = await client.post(
                "/auth/refresh", json={"refresh_token": refresh_token}
            )
            if resp.status_code != 200:
                print(f"Refresh failed: {resp.text}")
                sys.exit(1)
            new_access_token = resp.json()["access_token"]

            print("7. Changing password...")
            resp = await client.post(
                "/auth/change-password",
                json={
                    "old_password": password,
                    "new_password": "NewSecurePassword123!",
                },
                headers={"Authorization": f"Bearer {new_access_token}"},
            )
            if resp.status_code != 200:
                print(f"Change password failed: {resp.text}")
                sys.exit(1)

            print("8. Logging in with new password...")
            resp = await client.post(
                "/auth/login",
                data={"username": email, "password": "NewSecurePassword123!"},
            )
            if resp.status_code != 200:
                print("Login with new password failed")
                sys.exit(1)

            print("All authentication verification checks passed! [OK]")

if __name__ == "__main__":
    asyncio.run(verify_auth())
