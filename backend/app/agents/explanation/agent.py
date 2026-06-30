"""Explanation Agent implementation."""

from pathlib import Path

import jinja2

from app.agents.base.agent import BaseAgent
from app.agents.models.explanation import ExplanationResult
from app.ai.manager import AIManager
from app.workflow.models import WorkflowState


class ExplanationAgent(BaseAgent):
    """Generates a human-readable explanation for each recommendation."""

    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        prompt_path = Path(__file__).parent / "prompts" / "explanation_prompt.jinja2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("explanation_prompt.jinja2")

    @property
    def consumes(self) -> list[str]:
        return ["recommendation", "validation_result", "retrieved_chunks"]

    @property
    def produces(self) -> list[str]:
        return ["explanation"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)
        
        await self.emit_progress(state, "Synthesizing reasoning into human-readable explanation...")

        prompt_content = self._prompt_template.render(
            recommendation=(
                state.recommendation.model_dump() if state.recommendation else None
            ),
            validation_result=(
                state.validation_result.model_dump()
                if state.validation_result
                else None
            ),
            retrieved_chunks=(
                [chunk.model_dump() for chunk in state.retrieved_chunks.chunks]
                if state.retrieved_chunks
                else []
            ),
        )

        result = await self.ai_manager.generate(
            prompt=prompt_content,
            response_schema=ExplanationResult,
            system_prompt="You are an explainability engine. Produce clear and traceable reasoning.",
            temperature=0.2,
        )
        
        await self.emit_progress(state, "Explanation generated successfully.")

        if not isinstance(result, ExplanationResult):
            raise TypeError(
                "AIManager returned invalid type, expected ExplanationResult"
            )

        state.explanation = result
        return state
