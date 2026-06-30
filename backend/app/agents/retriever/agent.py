"""Retriever Agent implementation."""

import uuid

import json
from pathlib import Path
import jinja2

from app.agents.base.agent import BaseAgent
from app.agents.models.retriever import RetrievedChunk, RetrieverResult, OptimizedQuery
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.ai.manager import AIManager
from app.workflow.models import WorkflowState


class RetrieverAgent(BaseAgent):
    """Fetches the most relevant knowledge chunks for a given query."""

    def __init__(self, knowledge_manager: KnowledgeManager | None = None, ai_manager: AIManager | None = None) -> None:
        self.knowledge_manager = knowledge_manager
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        prompt_path = Path(__file__).parent / "prompts" / "retriever_prompt.jinja2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("retriever_prompt.jinja2")

    @property
    def consumes(self) -> list[str]:
        return ["user_request", "selected_knowledge_asset_ids", "organization"]

    @property
    def produces(self) -> list[str]:
        return ["retrieved_chunks"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)
        
        await self.emit_progress(state, "Initializing Retriever Agent...")

        # If knowledge manager is not provided, this is a mock execution or error
        if not self.knowledge_manager:
            await self.emit_progress(state, "No knowledge manager available. Skipping retrieval.")
            state.retrieved_chunks = RetrieverResult(chunks=[], query_used=str(state.user_request))
            return state

        if not state.selected_knowledge_asset_ids:
            await self.emit_progress(state, "No knowledge assets selected. Skipping retrieval.")
            state.retrieved_chunks = RetrieverResult(chunks=[], query_used=str(state.user_request))
            return state

        await self.emit_progress(state, "Optimizing search query...")

        prompt_content = self._prompt_template.render(
            workspace_context=json.dumps(state.workspace_context) if state.workspace_context else "None",
            planner_goal=state.plan.goal if state.plan else "None",
            user_request=state.user_request or "None",
        )

        optimized_result = await self.ai_manager.generate(
            prompt=prompt_content,
            response_schema=OptimizedQuery,
            system_prompt="You are a strict search query optimizer. Output only structured data.",
            temperature=0.1,
        )

        if not isinstance(optimized_result, OptimizedQuery):
            raise TypeError("AIManager returned invalid type, expected OptimizedQuery")

        query = optimized_result.optimized_query
            
        await self.emit_progress(state, f"Searching {len(state.selected_knowledge_asset_ids)} attached knowledge assets with optimized query...")

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

        search_results = await self.knowledge_manager.retrieve(
            organization_id=organization_id,
            selected_asset_ids=selected_asset_ids,
            query=query,
            top_k=10,
        )

        chunks = []
        await self.emit_progress(state, f"Retrieved {len(search_results)} relevant chunks from knowledge base.")
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
