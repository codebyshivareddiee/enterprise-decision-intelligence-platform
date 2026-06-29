"""Verify the Planner Agent with multiple scenarios."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add backend to PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.planner.planner import Planner
from app.ai.manager import AIManager
from app.ai.providers.openai_provider import OpenAIProvider


async def run_scenario(
    planner: Planner, scenario_name: str, request: str, context: dict
):
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"REQUEST: {request}")
    print(f"{'='*80}")

    plan = await planner.generate_plan(
        user_request=request,
        organization=context.get("organization"),
        workspace_decision_context=context["workspace_decision_context"],
        enabled_agents=context.get("enabled_agents"),
    )

    print("\n--- DAG PLAN SUMMARY ---")
    print(f"Goal: {plan.goal}")
    print(f"Summary: {plan.summary}")
    print(f"Reasoning: {plan.reasoning}")
    print(f"Requires Human Review: {plan.requires_human_review}")
    print(f"Review Reason: {plan.human_review_reason or 'None'}")

    print("\n--- EXECUTION STEPS (DAG) ---")
    for step in plan.execution_steps:
        print(f"\nStep ID: {step.step_id} (Agent: {step.agent_name.value})")
        print(f"  Objective: {step.objective}")
        print(f"  Depends On: {step.depends_on}")
        print(f"  Consumes: {[a.value for a in step.consumes]}")
        print(f"  Produces: {[a.value for a in step.produces]}")
        print(f"  Success Criteria: {step.success_criteria}")

    print(f"\n{'='*80}")
    return plan


async def main():
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set.")
        return

    ai_manager = AIManager(provider=OpenAIProvider())
    planner = Planner(ai_manager=ai_manager)

    # Common mock context
    context = {
        "organization": {"id": "org_1", "name": "XL Ventures"},
        "enabled_agents": [
            "RETRIEVER",
            "REASONING",
            "RULE_CHECKER",
            "RECOMMENDATION",
            "EXPLANATION",
            "LEARNER",
        ],
        "workspace_decision_context": {
            "id": "ws_1",
            "name": "AI Engineering Hiring",
            "goal": "Hire the best AI Engineer",
            "success_metrics": "Time to hire < 30 days",
            "decision_points": "Evaluate Python and RAG experience",
            "workspace_summary": {
                "total_assets": 3,
                "semantic_summaries": {"common_skills": ["Python", "OpenAI"]},
            },
            "knowledge_schema": {
                "fields": [
                    {"name": "candidate_name", "type": "STRING"},
                    {"name": "years_experience", "type": "INTEGER"},
                    {"name": "skills", "type": "LIST"},
                    {"name": "status", "type": "STRING"},
                ],
                "default_chunk_strategy": "HeadingChunker",
                "default_chunk_profile": "MEDIUM",
                "default_retrieval_strategy": "semantic_hybrid",
            },
            "knowledge_assets": [
                {"id": "doc_1", "title": "John Doe Resume", "type": "PDF"},
                {"id": "doc_2", "title": "Jane Smith Profile", "type": "LINKEDIN"},
                {
                    "id": "doc_3",
                    "title": "Role Requirements - AI Engineer",
                    "type": "TEXT",
                },
            ],
            "business_rules": [
                {
                    "name": "Min Experience",
                    "type": "HARD_FILTER",
                    "condition": "years_experience >= 5",
                },
                {
                    "name": "Required Skills",
                    "type": "HARD_FILTER",
                    "condition": "skills IN ['Python', 'OpenAI']",
                },
            ],
        },
    }

    # Scenario 1: Standard Hiring Pipeline (Full DAG)
    await run_scenario(
        planner,
        "1. Full Hiring Workflow",
        "Find the best AI Engineer for this role.",
        context,
    )

    # Scenario 2: Simple Query (No Rules/Recommendations Needed)
    # The planner should realize it only needs Retrieval and Reasoning/Explanation.
    await run_scenario(
        planner,
        "2. Simple Informational Query",
        "What are the mandatory skills required for the AI Engineer role based on our documents?",
        context,
    )

    # Scenario 3: High Stakes / Compliance check
    # Should flag requires_human_review = True and use Rule Checker explicitly
    await run_scenario(
        planner,
        "3. Compliance Verification",
        "Strictly verify if candidate John Doe meets all our business rules and minimum experience requirements before we proceed with an offer.",
        context,
    )


if __name__ == "__main__":
    asyncio.run(main())
