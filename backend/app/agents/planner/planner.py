"""The Planner Agent implementation."""

import json
from pathlib import Path
from typing import Any

import jinja2

from app.agents.planner.exceptions import PlanGenerationError
from app.agents.planner.schemas import ExecutionPlan
from app.ai.manager import AIManager


class Planner:
    """The Planner Agent is the intelligence layer of the workflow.

    It analyzes the user request and business context to produce a structured
    ExecutionPlan (a DAG of steps) for the Orchestrator to execute.
    It never executes the plan itself.
    """

    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> jinja2.Template:
        """Load the planner prompt template from the filesystem."""
        prompt_path = Path(__file__).parent / "prompts" / "planner_prompt.jinja2"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Planner prompt not found at {prompt_path}")

        env = jinja2.Environment(loader=jinja2.FileSystemLoader(prompt_path.parent))
        return env.get_template("planner_prompt.jinja2")

    async def generate_plan(
        self,
        user_request: str,
        workspace_decision_context: dict[str, Any],
        organization: dict[str, Any] | None = None,
        lifecycle: dict[str, Any] | None = None,
        enabled_agents: list[str] | None = None,
        execution_history: list[dict[str, Any]] | None = None,
    ) -> ExecutionPlan:
        """Generate a DAG ExecutionPlan based on the provided business context.

        Args:
            user_request: The overarching goal the user wants to achieve.
            workspace_decision_context: Complete context including Goal, Metrics, Rules, etc.
            organization: Organization context.
            lifecycle: Workflow lifecycle states.
            enabled_agents: List of agents enabled in the registry.
            execution_history: Optional history of previous steps.


        Returns:
            ExecutionPlan: A structured DAG for the Orchestrator.

        Raises:
            PlanGenerationError: If the AI fails to generate a valid plan.
        """
        # Render the prompt with provided context
        prompt_content = self._prompt_template.render(
            organization=json.dumps(organization, default=str) if organization else "None",
            workspace_decision_context=json.dumps(workspace_decision_context, default=str),
            lifecycle=json.dumps(lifecycle, default=str) if lifecycle else "None",
            enabled_agents=json.dumps(enabled_agents, default=str) if enabled_agents else "None",
            execution_history=(
                json.dumps(execution_history, default=str) if execution_history else "None"
            ),
        )

        try:
            # The AIManager automatically handles schema enforcement via OpenAI structured outputs
            plan = await self.ai_manager.generate(
                prompt=f"User Request: {user_request}\n\nContext Context:\n{prompt_content}",
                response_schema=ExecutionPlan,
                system_prompt="You are a Principal AI Architect generating dynamic ExecutionPlans.",
                temperature=0.2,  # Low temp for structured logic
            )

            if not isinstance(plan, ExecutionPlan):
                raise PlanGenerationError(
                    "AIManager returned an invalid type, expected ExecutionPlan."
                )

            return plan

        except Exception as e:
            raise PlanGenerationError(
                f"Failed to generate execution plan: {str(e)}"
            ) from e
