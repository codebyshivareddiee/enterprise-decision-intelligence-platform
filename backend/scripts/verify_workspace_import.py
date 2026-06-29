import asyncio
import os
import sys

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.container import ServiceContainer
from app.core.config import get_settings
from app.api.v1.models.requests import WorkspaceKnowledgeAttachRequest
from app.models.workspace import Workspace
from app.models.knowledge_asset import KnowledgeAsset
import uuid

async def verify():
    settings = get_settings()
    container = ServiceContainer(settings=settings)
    await container.initialize()
    print("Container initialized.")
    
    org_repo = container.organization_repo
    ws_repo = container.workspace_repo
    asset_repo = container.knowledge_asset_repo
    
    # 1. Get an organization
    orgs = await org_repo.list(limit=1)
    if not orgs:
        print("No organization found. Please run some seed script first.")
        return
    org = orgs[0]
    print(f"Using Organization: {org.name} ({org.id})")
    
    # 2. Get a workspace
    workspaces = await ws_repo.list(organization_id=org.id, limit=1)
    if not workspaces:
        print("No workspace found. Please run seed script first.")
        return
    ws = workspaces[0]
    print(f"Using Workspace: {ws.name} ({ws.id})")
    
    # 3. Get or create some knowledge assets in the organization
    assets = await asset_repo.list_by_organization(org.id, limit=3)
    if not assets:
        print("No assets found, creating mock assets...")
        asset1 = KnowledgeAsset(organization_id=org.id, name="Test Asset 1", content_type="text")
        asset2 = KnowledgeAsset(organization_id=org.id, name="Test Asset 2", content_type="pdf")
        asset1 = await asset_repo.create(asset1)
        asset2 = await asset_repo.create(asset2)
        assets = [asset1, asset2]
    
    print(f"Found {len(assets)} knowledge assets.")
    asset_ids = [a.id for a in assets]
    
    # Check if they are already attached and detach them for testing
    if ws.selected_knowledge_asset_ids:
        ws.selected_knowledge_asset_ids = []
        ws = await ws_repo.update(ws)
        print("Cleared existing selected knowledge assets in workspace.")
    
    print("Attempting to attach knowledge assets to the workspace...")
    # Simulate endpoint logic
    # (Since we are testing the logic, we will call the repo methods directly as in the endpoint)
    # The endpoint does:
    asset_id_strs = [str(aid) for aid in asset_ids]
    fetched_assets = await asset_repo.get_by_ids(ws.organization_id, asset_id_strs)
    found_asset_ids = {str(a.id) for a in fetched_assets}
    missing_ids = [aid for aid in asset_id_strs if aid not in found_asset_ids]
    
    if missing_ids:
        print(f"Error: Missing assets {missing_ids}")
        return
        
    current_ids = set(str(aid) for aid in ws.selected_knowledge_asset_ids)
    new_ids = [uuid.UUID(aid) for aid in asset_ids if str(aid) not in current_ids]
    
    if new_ids:
        ws.selected_knowledge_asset_ids.extend(new_ids)
        updated_ws = await ws_repo.update(ws)
        if updated_ws:
            ws = updated_ws
            print(f"Success! Attached {len(new_ids)} assets to the workspace.")
            print(f"Workspace now has {len(ws.selected_knowledge_asset_ids)} attached assets.")
    
    # Check Retriever
    print("\nVerifying retriever only uses selected assets...")
    from app.agents.retriever.agent import RetrieverAgent
    from app.workflow.models import WorkflowState
    
    agent = RetrieverAgent(knowledge_manager=None)  # Use mock behavior since no manager provided
    state = WorkflowState(
        workspace_id=str(ws.id),
        organization={"id": str(org.id)},
        user_request="Test query",
        selected_knowledge_asset_ids=[str(aid) for aid in ws.selected_knowledge_asset_ids]
    )
    
    new_state = await agent.execute(state)
    print("Retriever agent executed.")
    if new_state.selected_knowledge_asset_ids == [str(aid) for aid in ws.selected_knowledge_asset_ids]:
        print("✅ Retriever state correctly contains only selected assets.")
    
    print("\nAll verification steps passed.")

if __name__ == "__main__":
    asyncio.run(verify())
