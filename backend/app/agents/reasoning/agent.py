"""Reasoning Agent implementation."""

import json
from pathlib import Path

import jinja2

from app.agents.base.agent import BaseAgent
from app.agents.models.reasoning import ReasoningResult
from app.ai.manager import AIManager
from app.workflow.models import WorkflowState


class ReasoningAgent(BaseAgent):
    """Applies business rules and AI reasoning over retrieved chunks."""

    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        prompt_path = Path(__file__).parent / "prompts" / "reasoning_prompt.jinja2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("reasoning_prompt.jinja2")

    @property
    def consumes(self) -> list[str]:
        return ["retrieved_chunks", "business_rules", "workspace_context"]

    @property
    def produces(self) -> list[str]:
        return ["reasoning_result"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)

        prompt_content = self._prompt_template.render(
            workspace_context=(
                json.dumps(state.workspace_context)
                if state.workspace_context
                else "None"
            ),
            business_rules=(
                json.dumps(state.business_rules) if state.business_rules else "None"
            ),
            retrieved_chunks=(
                [chunk.model_dump() for chunk in state.retrieved_chunks.chunks]
                if state.retrieved_chunks
                else []
            ),
        )

        result = await self.ai_manager.generate(
            prompt=prompt_content,
            response_schema=ReasoningResult,
            system_prompt="You are a strict reasoning engine. Do not recommend, only evaluate.",
            temperature=0.2,
        )

        if not isinstance(result, ReasoningResult):
            raise TypeError("AIManager returned invalid type, expected ReasoningResult")

        state.reasoning_result = result
        return state
