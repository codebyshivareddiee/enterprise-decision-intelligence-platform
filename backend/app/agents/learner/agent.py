"""Learner Agent implementation."""

import json
from pathlib import Path

import jinja2

from app.agents.base.agent import BaseAgent
from app.agents.models.learner import PreferenceUpdateResult
from app.ai.manager import AIManager
from app.workflow.models import WorkflowState


class LearnerAgent(BaseAgent):
    """Generates preference updates based on human feedback."""

    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        prompt_path = Path(__file__).parent / "prompts" / "learner_prompt.jinja2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("learner_prompt.jinja2")

    @property
    def consumes(self) -> list[str]:
        return ["human_feedback", "final_decision", "workspace"]

    @property
    def produces(self) -> list[str]:
        return ["preference_update"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)

        prompt_content = self._prompt_template.render(
            human_feedback=json.dumps(state.human_feedback),
            final_decision=json.dumps(state.final_decision),
        )

        result = await self.ai_manager.generate(
            prompt=prompt_content,
            response_schema=PreferenceUpdateResult,
            system_prompt="You are a Learning Engine. Update preferences based on human decisions.",
            temperature=0.2,
        )

        if not isinstance(result, PreferenceUpdateResult):
            raise TypeError(
                "AIManager returned invalid type, expected PreferenceUpdateResult"
            )

        workspace_id = (
            state.workspace.get("id", "unknown_workspace")
            if state.workspace
            else "unknown_workspace"
        )
        result.workspace_id = str(workspace_id)

        state.preference_update = result
        return state
