"""Agent registry for the workflow runtime."""

from collections.abc import Callable

from pydantic import BaseModel, Field

from app.agents.planner.schemas import AgentType, WorkflowArtifact
from app.workflow.exceptions import AgentNotRegisteredError


class NodeDefinition(BaseModel):
    """Metadata for a registered agent node in the workflow."""

    agent_type: AgentType = Field(description="The type of agent")
    node_implementation: Callable = Field(
        description="The actual callable node function"
    )
    consumes: list[WorkflowArtifact] = Field(
        default_factory=list, description="Artifacts required by this node"
    )
    produces: list[WorkflowArtifact] = Field(
        default_factory=list, description="Artifacts produced by this node"
    )
    description: str = Field(description="Description of the node's capabilities")

    class Config:
        arbitrary_types_allowed = True


class AgentRegistry:
    """Registry mapping AgentTypes to their node implementations."""

    def __init__(self) -> None:
        self._registry: dict[AgentType, NodeDefinition] = {}

    def register(
        self,
        agent_type: AgentType,
        node_implementation: Callable,
        consumes: list[WorkflowArtifact],
        produces: list[WorkflowArtifact],
        description: str,
    ) -> None:
        """Register an agent node in the registry."""
        self._registry[agent_type] = NodeDefinition(
            agent_type=agent_type,
            node_implementation=node_implementation,
            consumes=consumes,
            produces=produces,
            description=description,
        )

    def get(self, agent_type: AgentType) -> NodeDefinition:
        """Get the node definition for an agent type.

        Raises:
            AgentNotRegisteredError: If the agent type is not registered.
        """
        if agent_type not in self._registry:
            raise AgentNotRegisteredError(
                f"Agent '{agent_type.value}' is not registered."
            )
        return self._registry[agent_type]

    def is_registered(self, agent_type: AgentType) -> bool:
        """Check if an agent type is registered."""
        return agent_type in self._registry

def build_default_registry(knowledge_manager=None, ai_manager=None) -> AgentRegistry:
    """Helper to build a registry with all default agents."""
    from app.agents.retriever.agent import RetrieverAgent
    from app.agents.reasoning.agent import ReasoningAgent
    from app.agents.recommendation.agent import RecommendationAgent
    from app.agents.rule_checker.agent import RuleCheckerAgent
    from app.agents.explanation.agent import ExplanationAgent
    
    registry = AgentRegistry()
    
    registry.register(
        agent_type=AgentType.RETRIEVER,
        node_implementation=RetrieverAgent(knowledge_manager=knowledge_manager).execute,
        consumes=[WorkflowArtifact.USER_REQUEST],
        produces=[WorkflowArtifact.RETRIEVED_CHUNKS],
        description="Retrieves knowledge chunks"
    )
    registry.register(
        agent_type=AgentType.REASONING,
        node_implementation=ReasoningAgent(ai_manager=ai_manager).execute,
        consumes=[WorkflowArtifact.RETRIEVED_CHUNKS],
        produces=[WorkflowArtifact.REASONING_RESULT],
        description="Applies reasoning to retrieved chunks"
    )
    registry.register(
        agent_type=AgentType.RECOMMENDATION,
        node_implementation=RecommendationAgent(ai_manager=ai_manager).execute,
        consumes=[WorkflowArtifact.REASONING_RESULT],
        produces=[WorkflowArtifact.RECOMMENDATION],
        description="Produces final recommendation"
    )
    registry.register(
        agent_type=AgentType.RULE_CHECKER,
        node_implementation=RuleCheckerAgent().execute,
        consumes=[WorkflowArtifact.RECOMMENDATION],
        produces=[WorkflowArtifact.VALIDATION_RESULT],
        description="Validates recommendation against business rules"
    )
    registry.register(
        agent_type=AgentType.EXPLANATION,
        node_implementation=ExplanationAgent(ai_manager=ai_manager).execute,
        consumes=[WorkflowArtifact.RECOMMENDATION],
        produces=[WorkflowArtifact.EXPLANATION],
        description="Provides natural language explanation"
    )
    
    from app.agents.learner.agent import LearnerAgent
    registry.register(
        agent_type=AgentType.LEARNER,
        node_implementation=LearnerAgent(ai_manager=ai_manager).execute,
        consumes=[WorkflowArtifact.HUMAN_FEEDBACK, WorkflowArtifact.FINAL_DECISION],
        produces=[WorkflowArtifact.PREFERENCE_UPDATE],
        description="Generates preference updates based on human feedback"
    )
    
    return registry

