"""Verification script for the LangGraph Workflow Runtime.

This script tests the runtime against different scenarios without using actual AI agents.
It validates normal execution, parallel execution, interrupts, failure modes, and replanning.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.agents.planner.planner import Planner
from app.agents.planner.schemas import (
    AgentType,
    ExecutionPlan,
    ExecutionStep,
    FailureStrategy,
    WorkflowArtifact,
)
from app.workflow import AgentRegistry, ExecutionContext, WorkflowRuntime, WorkflowState


def setup_mock_registry() -> AgentRegistry:
    registry = AgentRegistry()

    # Mock Retriever Node
    def mock_retriever(state: WorkflowState) -> dict:
        print("[MOCK RETRIEVER] Executing...")
        return {"retrieved_chunks": {"chunks": [], "query_used": "mock"}}

    registry.register(
        agent_type=AgentType.RETRIEVER,
        node_implementation=mock_retriever,
        consumes=[WorkflowArtifact.USER_REQUEST],
        produces=[WorkflowArtifact.RETRIEVED_CHUNKS],
        description="Mock Retriever",
    )

    # Mock Reasoning Node
    def mock_reasoning(state: WorkflowState) -> dict:
        print("[MOCK REASONING] Executing...")
        return {
            "reasoning_result": {
                "entity_evaluations": [],
                "missing_information": [],
                "identified_risks": [],
                "identified_opportunities": [],
            }
        }

    registry.register(
        agent_type=AgentType.REASONING,
        node_implementation=mock_reasoning,
        consumes=[WorkflowArtifact.RETRIEVED_CHUNKS],
        produces=[WorkflowArtifact.REASONING_RESULT],
        description="Mock Reasoning",
    )

    # Mock Recommendation Node
    def mock_recommendation(state: WorkflowState) -> dict:
        print("[MOCK RECOMMENDATION] Executing...")
        return {
            "recommendation": {
                "recommendation": {
                    "entity_id": "123",
                    "rank": 1,
                    "final_score": 95.0,
                    "contributing_factors": [],
                },
                "confidence": 0.9,
                "alternatives": [],
                "risk_level": "LOW",
            }
        }

    registry.register(
        agent_type=AgentType.RECOMMENDATION,
        node_implementation=mock_recommendation,
        consumes=[WorkflowArtifact.REASONING_RESULT],
        produces=[WorkflowArtifact.RECOMMENDATION],
        description="Mock Recommendation",
    )

    # Mock Explanation Node (parallel with Recommendation)
    def mock_explanation(state: WorkflowState) -> dict:
        print("[MOCK EXPLANATION] Executing...")
        return {
            "explanation": {
                "summary": "This candidate is highly recommended.",
                "evidence_references": [],
                "applied_rules": [],
                "confidence_reasoning": "",
                "cited_chunks": [],
            }
        }

    registry.register(
        agent_type=AgentType.EXPLANATION,
        node_implementation=mock_explanation,
        consumes=[WorkflowArtifact.REASONING_RESULT],
        produces=[WorkflowArtifact.EXPLANATION],
        description="Mock Explanation",
    )

    return registry


def create_test_plan(
    requires_review: bool = False, trigger_replan: bool = False
) -> ExecutionPlan:
    # Build a DAG: Retriever -> Reasoning -> [Recommendation, Explanation]
    steps = [
        ExecutionStep(
            step_id="step_retrieve",
            agent_name=AgentType.RETRIEVER,
            objective="Retrieve knowledge",
            description="Mock",
            consumes=[WorkflowArtifact.USER_REQUEST],
            produces=[WorkflowArtifact.RETRIEVED_CHUNKS],
            depends_on=[],
            success_criteria="Chunks found",
            failure_strategy=FailureStrategy.FAIL_PLAN,
        ),
        ExecutionStep(
            step_id="step_reason",
            agent_name=AgentType.REASONING,
            objective="Analyze",
            description="Mock",
            consumes=[WorkflowArtifact.RETRIEVED_CHUNKS],
            produces=[WorkflowArtifact.REASONING_RESULT],
            depends_on=["step_retrieve"],
            success_criteria="Analysis done",
            failure_strategy=(
                FailureStrategy.REPLAN if trigger_replan else FailureStrategy.FAIL_PLAN
            ),
        ),
        ExecutionStep(
            step_id="step_recommend",
            agent_name=AgentType.RECOMMENDATION,
            objective="Recommend",
            description="Mock",
            consumes=[WorkflowArtifact.REASONING_RESULT],
            produces=[WorkflowArtifact.RECOMMENDATION],
            depends_on=["step_reason"],
            success_criteria="Recommendation generated",
        ),
        ExecutionStep(
            step_id="step_explain",
            agent_name=AgentType.EXPLANATION,
            objective="Explain",
            description="Mock",
            consumes=[WorkflowArtifact.REASONING_RESULT],
            produces=[WorkflowArtifact.EXPLANATION],
            depends_on=["step_reason"],
            success_criteria="Explanation generated",
        ),
    ]

    return ExecutionPlan(
        goal="Test Goal",
        summary="Test Summary",
        reasoning="Test Reasoning",
        execution_steps=steps,
        expected_outputs=[],
        requires_human_review=requires_review,
        replanning_conditions=[],
        completion_conditions=[],
    )


async def test_normal_execution():
    print("\n=== TEST 1: Normal Execution & Parallel Branches ===")
    registry = setup_mock_registry()
    plan = create_test_plan(requires_review=False)
    context = ExecutionContext(
        plan=plan, state=WorkflowState(), registry=registry, planner=Planner()
    )

    runtime = WorkflowRuntime(context)
    initial_state = WorkflowState(user_request="Find best candidate")

    final_state = await runtime.start(initial_state, thread_id="test1")

    assert "step_retrieve" in final_state.completed_steps
    assert "step_recommend" in final_state.completed_steps
    assert "step_explain" in final_state.completed_steps
    assert final_state.recommendation is not None
    assert final_state.explanation is not None
    assert final_state.is_interrupted is False
    print("Test 1 Passed!")


async def test_missing_artifact():
    print("\n=== TEST 2: Missing Artifact Validation ===")
    registry = setup_mock_registry()
    plan = create_test_plan(requires_review=False)
    context = ExecutionContext(
        plan=plan, state=WorkflowState(), registry=registry, planner=Planner()
    )

    runtime = WorkflowRuntime(context)
    # Don't provide user_request, which is required by Retriever
    initial_state = WorkflowState()

    final_state = await runtime.start(initial_state, thread_id="test2")

    assert "step_retrieve" in final_state.failed_steps
    assert len(final_state.errors) > 0
    assert "Missing artifact USER_REQUEST" in final_state.errors[0]
    print("Test 2 Passed!")


async def test_interrupt_resume():
    print("\n=== TEST 3: Interrupt & Resume ===")
    registry = setup_mock_registry()
    plan = create_test_plan(requires_review=True)
    context = ExecutionContext(
        plan=plan, state=WorkflowState(), registry=registry, planner=Planner()
    )

    runtime = WorkflowRuntime(context)
    initial_state = WorkflowState(user_request="Find best candidate")

    state = await runtime.start(initial_state, thread_id="test3")

    assert state.is_interrupted is True
    print("Workflow interrupted for human review.")

    # Now resume
    state = await runtime.resume(thread_id="test3", feedback={"decision": "Approved!"})

    assert state.is_interrupted is False
    assert state.human_feedback == {"decision": "Approved!"}
    print("Test 3 Passed!")


async def test_replanning():
    print("\n=== TEST 4: Replanning Trigger ===")
    registry = setup_mock_registry()

    # Overwrite REASONING to fail and trigger replanning
    def failing_reasoning(state: WorkflowState) -> dict:
        print("[MOCK REASONING] Failing to trigger replan...")
        raise ValueError("Confidence too low")

    registry.register(
        agent_type=AgentType.REASONING,
        node_implementation=failing_reasoning,
        consumes=[WorkflowArtifact.RETRIEVED_CHUNKS],
        produces=[WorkflowArtifact.REASONING_RESULT],
        description="Failing Mock",
    )

    plan = create_test_plan(trigger_replan=True)
    context = ExecutionContext(
        plan=plan, state=WorkflowState(), registry=registry, planner=Planner()
    )

    runtime = WorkflowRuntime(context)
    initial_state = WorkflowState(user_request="Find best candidate")

    final_state = await runtime.start(initial_state, thread_id="test4")

    assert "step_reason" in final_state.failed_steps
    assert final_state.requires_replanning is True
    assert "Confidence too low" in final_state.replanning_reason
    print("Test 4 Passed!")


async def main():
    await test_normal_execution()
    await test_missing_artifact()
    await test_interrupt_resume()
    await test_replanning()
    print("\nAll tests passed successfully! The Runtime is fully functional.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
