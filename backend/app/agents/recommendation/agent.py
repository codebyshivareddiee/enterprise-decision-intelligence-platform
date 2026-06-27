"""Recommendation Agent implementation."""

from pathlib import Path

import jinja2

from app.agents.base.agent import BaseAgent
from app.agents.models.recommendation import RecommendationResult
from app.ai.manager import AIManager
from app.workflow.models import WorkflowState


class RecommendationAgent(BaseAgent):
    """Produces a final ranked recommendation from scored candidates."""

    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        prompt_path = Path(__file__).parent / "prompts" / "recommendation_prompt.jinja2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("recommendation_prompt.jinja2")

    @property
    def consumes(self) -> list[str]:
        return ["reasoning_result"]

    @property
    def produces(self) -> list[str]:
        return ["recommendation"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)

        prompt_content = self._prompt_template.render(
            reasoning_result=(
                state.reasoning_result.model_dump() if state.reasoning_result else None
            )
        )

        result = await self.ai_manager.generate(
            prompt=prompt_content,
            response_schema=RecommendationResult,
            system_prompt="You are a strict recommendation engine. Output only structured data, no explanations.",
            temperature=0.2,
        )

        if not isinstance(result, RecommendationResult):
            raise TypeError(
                "AIManager returned invalid type, expected RecommendationResult"
            )

        state.recommendation = result
        return state
