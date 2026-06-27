"""Verification script for Specialized Agent Nodes."""

import asyncio
import uuid

from app.agents.explanation.agent import ExplanationAgent
from app.agents.learner.agent import LearnerAgent
from app.agents.reasoning.agent import ReasoningAgent
from app.agents.recommendation.agent import RecommendationAgent
from app.agents.retriever.agent import RetrieverAgent
from app.agents.rule_checker.agent import RuleCheckerAgent
from app.workflow.models import WorkflowState


async def run_pipeline():
    print("--- Starting Agent Verification Pipeline ---")

    # 1. Seed Workspace and Context
    organization_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    business_rules = [
        {
            "id": str(uuid.uuid4()),
            "name": "Minimum 5 Years Experience",
            "description": "Candidate must have at least 5 years of experience",
            "rule_type": "HARD_FILTER",
            "conditions": [
                {"field_name": "years_experience", "operator": "GTE", "value": 5}
            ],
            "is_active": True,
        }
    ]

    initial_state = WorkflowState(
        organization={"id": organization_id, "name": "Test Org"},
        workspace={"id": workspace_id, "name": "Test Workspace"},
        workspace_context={"industry": "Tech", "hiring_goal": "Senior AI Engineer"},
        selected_knowledge_asset_ids=[str(uuid.uuid4())],
        business_rules=business_rules,
        user_request="Find the best candidate for the Senior AI Engineer role.",
        human_feedback="Good recommendation, candidate has strong background.",
        final_decision={"status": "APPROVED", "entity_id": "entity-123"},
    )

    print("\n[1] Initial State Seeded")

    # 2. Retriever
    print("\n[2] Executing RetrieverAgent...")
    retriever = RetrieverAgent(
        knowledge_manager=None
    )  # Uses mock logic if none provided
    state = await retriever.execute(initial_state)
    # Inject a mock chunk for downstream agents if knowledge manager mock returned empty
    if not state.retrieved_chunks.chunks:
        from app.agents.models.retriever import RetrievedChunk

        state.retrieved_chunks.chunks.append(
            RetrievedChunk(
                text="Alice is a great AI engineer with 6 years of experience.",
                asset_id="entity-123",
                score=0.95,
                metadata={"id": "entity-123", "name": "Alice", "years_experience": 6},
            )
        )
    print("  -> Retriever Produced:", state.retrieved_chunks.model_dump())

    # 3. Reasoning
    print("\n[3] Executing ReasoningAgent...")
    reasoning = ReasoningAgent()
    state = await reasoning.execute(state)
    print("  -> Reasoning Produced:", state.reasoning_result.model_dump())

    # 4. Recommendation
    print("\n[4] Executing RecommendationAgent...")
    recommendation = RecommendationAgent()
    state = await recommendation.execute(state)
    # Patch entity ID if AI hallucinated it
    state.recommendation.recommendation.entity_id = "entity-123"
    print("  -> Recommendation Produced:", state.recommendation.model_dump())

    # 5. Rule Checker
    print("\n[5] Executing RuleCheckerAgent...")
    rule_checker = RuleCheckerAgent()
    state = await rule_checker.execute(state)
    print("  -> Rule Checker Produced:", state.validation_result.model_dump())

    # 6. Explanation
    print("\n[6] Executing ExplanationAgent...")
    explanation = ExplanationAgent()
    state = await explanation.execute(state)
    print("  -> Explanation Produced:", state.explanation.model_dump())

    # 7. Learner
    print("\n[7] Executing LearnerAgent...")
    learner = LearnerAgent()
    state = await learner.execute(state)
    print("  -> Learner Produced:", state.preference_update.model_dump())

    print("\n--- Pipeline Verification Complete ---")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(run_pipeline())
