"""Retriever Agent implementation."""

import uuid

from app.agents.base.agent import BaseAgent
from app.agents.models.retriever import RetrievedChunk, RetrieverResult
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.workflow.models import WorkflowState


class RetrieverAgent(BaseAgent):
    """Fetches the most relevant knowledge chunks for a given query."""

    def __init__(self, knowledge_manager: KnowledgeManager | None = None) -> None:
        self.knowledge_manager = knowledge_manager

    @property
    def consumes(self) -> list[str]:
        return ["user_request", "selected_knowledge_asset_ids", "organization"]

    @property
    def produces(self) -> list[str]:
        return ["retrieved_chunks"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)

        # If knowledge manager is not provided, this is a mock execution or error
        if not self.knowledge_manager:
            # Fallback for verification script or testing if no manager injected
            result = RetrieverResult(chunks=[], query_used=str(state.user_request))
            state.retrieved_chunks = result
            return state

        organization_id = (
            uuid.UUID(state.organization["id"])
            if state.organization and "id" in state.organization
            else uuid.uuid4()
        )
        selected_asset_ids = (
            [uuid.UUID(asset_id) for asset_id in state.selected_knowledge_asset_ids]
            if state.selected_knowledge_asset_ids
            else None
        )

        query = str(state.user_request)

        search_results = await self.knowledge_manager.retrieve(
            organization_id=organization_id,
            selected_asset_ids=selected_asset_ids,
            query=query,
            top_k=10,
        )

        chunks = []
        for res in search_results:
            chunks.append(
                RetrievedChunk(
                    text=res.chunk.content,
                    asset_id=str(
                        res.chunk.metadata.get("asset_id", str(res.chunk.asset_id))
                    ),
                    score=res.score,
                    metadata=res.chunk.metadata,
                )
            )

        result = RetrieverResult(chunks=chunks, query_used=query)

        state.retrieved_chunks = result
        return state
