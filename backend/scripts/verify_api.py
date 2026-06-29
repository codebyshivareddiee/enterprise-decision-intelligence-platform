"""Verify the API layer endpoints against the running application.

This script uses httpx.AsyncClient with the FastAPI application directly
so we don't need to spin up a background server process.
"""

import asyncio
import uuid
from dotenv import load_dotenv

load_dotenv()

import httpx
from httpx import ASGITransport

from app.auth.dependencies import get_current_user
from app.auth.models import Membership, Role, User
from app.main import app, lifespan


def mock_get_current_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="fake",
        memberships=[
            Membership(
                organization_id=uuid.uuid4(), role=Role.PLATFORM_ADMIN, workspace_ids=[]
            )
        ],
    )


app.dependency_overrides[get_current_user] = mock_get_current_user


async def main() -> None:
    """Verify all API endpoints sequentially."""
    print("Starting API verification against ASGI app...")

    async with lifespan(app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver/api/v1",
            timeout=30.0,
        ) as client:

            # 1. Health
            print("\n--- Testing GET /health ---")
            response = await client.get("/health")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.json()}")
            assert response.status_code == 200, "Health check failed"

            # 2. Create Organization
            print("\n--- Testing POST /organizations ---")
            org_payload = {
                "name": "Acme Corp",
                "slug": "acme-corp",
                "contact_email": "admin@acmecorp.com",
                "industry": "Manufacturing",
                "size": "ENTERPRISE",
                "status": "ACTIVE",
            }
            response = await client.post("/organizations", json=org_payload)
            print(f"Status: {response.status_code}")
            org_data = response.json()
            print(f"Body: {org_data}")
            assert response.status_code == 201, "Create organization failed"
            org_id = org_data["data"]["id"]

            # 3. Create Workspace
            print("\n--- Testing POST /workspaces ---")
            ws_payload = {
                "organization_id": org_id,
                "owner_id": str(uuid.uuid4()),
                "name": "Factory Automation Hub",
                "description": "Managing automation decisions",
                "status": "active",
                "goal": "Optimize factory operations",
                "success_metrics": "Reduced downtime",
                "decision_points": "Cost vs uptime",
                "workspace_summary": {},
            }
            response = await client.post("/workspaces", json=ws_payload)
            print(f"Status: {response.status_code}")
            ws_data = response.json()
            print(f"Body: {ws_data}")
            assert response.status_code == 201, "Create workspace failed"
            ws_id = ws_data["data"]["id"]

            # 4. Upload Knowledge
            print("\n--- Testing POST /knowledge/upload ---")
            # We need a dummy file
            files = {
                "file": (
                    "test_doc.txt",
                    b"This is a test document about factory machines.",
                    "text/plain",
                )
            }
            data = {
                "workspace_id": ws_id,
                "organization_id": org_id,
                "description": "Test factory documentation",
            }
            response = await client.post("/knowledge/upload", data=data, files=files)
            print(f"Status: {response.status_code}")
            print(f"Body: {response.json()}")
            assert response.status_code == 200, "Upload knowledge failed"

            # 5. Search Knowledge
            print("\n--- Testing POST /knowledge/search ---")
            response = await client.post(
                "/knowledge/search",
                params={
                    "organization_id": org_id,
                    "query": "factory machines",
                    "top_k": 3,
                },
            )
            print(f"Status: {response.status_code}")
            print(f"Body: {response.json()}")
            assert response.status_code == 200, "Search knowledge failed"

            # 6. Execute Decision Workflow
            print("\n--- Testing POST /decisions/execute ---")
            execute_payload = {
                "workspace_id": ws_id,
                "user_request": "Should we upgrade machine X to a newer model?",
            }
            response = await client.post("/decisions/execute", json=execute_payload)
            print(f"Status: {response.status_code}")
            exec_data = response.json()
            print(f"Body: {exec_data}")
            # Note: Depending on Planner/Workflow mocking or real API availability, this might fail or succeed.
            # For now, just print the response.
            if response.status_code == 200:
                decision_id = exec_data["decision_id"]

                # 7. Record Outcome
                print("\n--- Testing POST /decisions/outcome ---")
                outcome_payload = {
                    "decision_id": decision_id,
                    "human_decision": "Approve the upgrade",
                    "feedback": "Upgrading will reduce downtime by 15%",
                    "final_outcome": None,
                }
                response = await client.post("/decisions/outcome", json=outcome_payload)
                print(f"Status: {response.status_code}")
                print(f"Body: {response.json()}")

        print("\nAPI verification completed.")

if __name__ == "__main__":
    asyncio.run(main())
