import os
os.environ['OPENAI_API_KEY'] = 'mock'
import asyncio
import os
import sys
import uuid
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.container import ServiceContainer
from app.config.settings import get_settings
from app.api.v1.models.requests import WorkflowExecuteRequest
from app.api.v1.decisions import execute_decision
from fastapi import Request, BackgroundTasks
from starlette.datastructures import State

async def test_error():
    try:
        settings = get_settings()
        container = ServiceContainer(settings=settings)
        await container.initialize()
        
        ws_repo = container.workspace_repo
        workspaces = await ws_repo.list()
        if not workspaces:
            print('No workspaces found.')
            return
        ws = workspaces[-1]
        
        request = WorkflowExecuteRequest(workspace_id=ws.id, user_request='test request')
        req = Request({'type': 'http', 'state': {}})
        req.state = State()
        req.state.request_id = 'test-id'
        req.state.user_id = str(uuid.uuid4())
        
        bg = BackgroundTasks()
        
        await execute_decision(
            request=request,
            req=req,
            background_tasks=bg,
            planner=container.planner,
            workspace_repo=ws_repo,
            recommendation_repo=container.recommendation_repo,
            knowledge_manager=container.knowledge_manager,
            audit_repo=container.audit_repo
        )
        print('SUCCESS')
    except Exception as e:
        print('ERROR OCCURRED:')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_error())
