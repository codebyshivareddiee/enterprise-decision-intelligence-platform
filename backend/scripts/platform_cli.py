import argparse
# ruff: noqa: E402, ANN201, ANN202, ANN204, E501
import asyncio
import sys
import time

# Add backend directory to sys.path to allow imports
from pathlib import Path
from uuid import uuid4

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from dotenv import load_dotenv
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from app.agents.explanation.agent import ExplanationAgent
from app.agents.learner.agent import LearnerAgent
from app.agents.planner.planner import Planner
from app.agents.planner.schemas import AgentType, ExecutionPlan
from app.agents.reasoning.agent import ReasoningAgent
from app.agents.recommendation.agent import RecommendationAgent
from app.agents.retriever.agent import RetrieverAgent
from app.agents.rule_checker.agent import RuleCheckerAgent
from app.ai.manager import AIManager
from app.ai.providers.openai_provider import OpenAIProvider
from app.config.settings import get_settings
from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer
from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.search.search_service import SearchService
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.knowledge.vectorstore.qdrant_store import QdrantStore
from app.models.business_rule import BusinessRule, RuleCondition, RuleOperator, RuleType
from app.models.decision_history import DecisionHistory
from app.models.enums import (
    AssetContentType,
    AssetStatus,
    DecisionOutcome,
    FieldType,
    UserRole,
    UserStatus,
    WorkspaceStatus,
)
from app.models.knowledge_asset import KnowledgeAsset
from app.models.knowledge_schema import KnowledgeSchema, SchemaField
from app.models.organization import Organization
from app.models.user import User
from app.models.workspace import Workspace
from app.persistence.mongodb import client as mongo_client
from app.persistence.mongodb.database import get_database
from app.persistence.mongodb.repositories.business_rule_repository import (
    BusinessRuleRepository,
)
from app.persistence.mongodb.repositories.decision_history_repository import (
    DecisionHistoryRepository,
)
from app.persistence.mongodb.repositories.knowledge_asset_repository import (
    KnowledgeAssetRepository,
)
from app.persistence.mongodb.repositories.knowledge_schema_repository import (
    KnowledgeSchemaRepository,
)
from app.persistence.mongodb.repositories.organization_repository import (
    OrganizationRepository,
)
from app.persistence.mongodb.repositories.preference_profile_repository import (
    PreferenceProfileRepository,
)
from app.persistence.mongodb.repositories.user_repository import UserRepository
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.workflow import AgentRegistry, ExecutionContext, WorkflowRuntime, WorkflowState
from scripts.demo_data import get_demo_scenarios


class PlatformCLI:
    def __init__(self, debug_mode: bool = False):
        self.debug = debug_mode
        self.settings = None
        self.db = None
        self.qdrant = None
        self.openai = None
        self.knowledge_manager = None
        self.planner = None

        # Repositories
        self.org_repo = None
        self.workspace_repo = None
        self.schema_repo = None
        self.asset_repo = None
        self.rule_repo = None
        self.decision_repo = None
        self.preference_repo = None
        self.user_repo = None

        # Context
        self.org = None
        self.workspace = None
        self.schema = None
        self.user = None

        self.execution_traces = []
        self.decision_traces = []

    def log_debug(self, message: str):
        if self.debug:
            print(f"\033[90m[DEBUG] {message}\033[0m")

    async def setup(self):
        print("Bootstrapping Enterprise Decision Intelligence Platform...")
        env_path = backend_dir / ".env"
        load_dotenv(dotenv_path=env_path)
        self.settings = get_settings()

        if not self.settings.openai_api_key or self.settings.openai_api_key.startswith(
            "sk-..."
        ):
            print("ERROR: OPENAI_API_KEY is not configured correctly.")
            sys.exit(1)

        # Connect MongoDB
        self.log_debug("Connecting to MongoDB...")
        await mongo_client.connect(self.settings.mongodb_uri)
        self.db = get_database()

        # Init Repositories
        self.org_repo = OrganizationRepository(self.db)
        self.workspace_repo = WorkspaceRepository(self.db)
        self.schema_repo = KnowledgeSchemaRepository(self.db)
        self.asset_repo = KnowledgeAssetRepository(self.db)
        self.rule_repo = BusinessRuleRepository(self.db)
        self.decision_repo = DecisionHistoryRepository(self.db)
        self.preference_repo = PreferenceProfileRepository(self.db)
        self.user_repo = UserRepository(self.db)

        # Connect Qdrant
        self.log_debug("Connecting to Qdrant...")
        self.qdrant = AsyncQdrantClient(
            url=self.settings.qdrant_url, api_key=self.settings.qdrant_api_key
        )

        # Connect OpenAI
        self.log_debug("Connecting to OpenAI...")
        self.openai = AsyncOpenAI(api_key=self.settings.openai_api_key)

        # Init Knowledge Layer
        self.log_debug("Initializing Knowledge Layer...")
        parser_registry = ParserRegistry()
        embedder = OpenAIEmbedder(
            client=self.openai, model=self.settings.openai_embedding_model
        )
        sparse_generator = FastEmbedSparseGenerator()
        vector_store = QdrantStore(
            client=self.qdrant, collection_name=self.settings.qdrant_collection_name
        )
        await vector_store.initialize_collection()

        document_processor = DocumentProcessor(
            parser_registry=parser_registry,
            dense_embedder=embedder,
            sparse_generator=sparse_generator,
            ai_analyzer=AIDocumentAnalyzer(client=self.openai),
        )
        search_service = SearchService(
            dense_embedder=embedder,
            sparse_generator=sparse_generator,
            vector_store=vector_store,
        )
        self.knowledge_manager = KnowledgeManager(
            document_processor=document_processor,
            vector_store=vector_store,
            search_service=search_service,
        )

        # Init AI Layer & Planner
        self.log_debug("Initializing Planner...")
        ai_manager = AIManager(provider=OpenAIProvider())
        self.planner = Planner(ai_manager=ai_manager)

        # Setup Context
        await self._setup_context()

        print("[OK] Platform successfully initialized.\n")

    async def _setup_context(self):
        self.log_debug("Fetching demo scenarios...")
        scenarios = get_demo_scenarios()
        
        print("\nAvailable Demo Scenarios:")
        for key, sc in scenarios.items():
            print(f"  - {key}: {sc.name}")
        
        selected = input("\nEnter scenario key (default: vendor): ").strip().lower()
        if not selected or selected not in scenarios:
            selected = "vendor"
            
        scenario = scenarios[selected]
        print(f"\nLoading Scenario: {scenario.name}")
        
        # Get or create Org
        orgs = await self.org_repo.list()
        self.org = next((o for o in orgs if o.slug == scenario.organization.slug), None)
        if not self.org:
            self.log_debug(f"Creating Organization: {scenario.organization.name}")
            self.org = scenario.organization
            await self.org_repo.create(self.org)

        # Get or create User
        users = await self.user_repo.list(organization_id=self.org.id)
        if users:
            self.user = users[0]
        else:
            self.log_debug("Creating default User")
            self.user = User(
                organization_id=self.org.id,
                email="admin@acme.com",
                full_name="Admin User",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            await self.user_repo.create(self.user)

        # Get or create Schema
        schemas = await self.schema_repo.list(organization_id=self.org.id)
        self.schema = next((s for s in schemas if s.name == scenario.schema.name), None)
        if not self.schema:
            self.log_debug(f"Creating KnowledgeSchema: {scenario.schema.name}")
            self.schema = scenario.schema
            # Ensure org ID is set
            self.schema.organization_id = self.org.id
            await self.schema_repo.create(self.schema)

        # Get or create Workspace
        workspaces = await self.workspace_repo.list(organization_id=self.org.id)
        self.workspace = next((w for w in workspaces if w.name == scenario.workspace_name), None)
        if not self.workspace:
            self.log_debug(f"Creating Workspace: {scenario.workspace_name}")
            self.workspace = Workspace(
                organization_id=self.org.id,
                name=scenario.workspace_name,
                description=scenario.workspace_description,
                knowledge_schema_id=self.schema.id,
                status=WorkspaceStatus.ACTIVE,
                owner_id=self.user.id,
                selected_knowledge_asset_ids=[],
            )
            await self.workspace_repo.create(self.workspace)

        # Get or create some business rules
        rules = await self.rule_repo.list(organization_id=self.org.id, workspace_id=self.workspace.id)
        if not rules:
            self.log_debug("Creating default BusinessRule")
            rule1 = BusinessRule(
                organization_id=self.org.id,
                workspace_id=self.workspace.id,
                name="Minimum 5 Years Experience",
                description="Candidate must have at least 5 years of experience",
                rule_type=RuleType.HARD_FILTER,
                conditions=[
                    RuleCondition(
                        field_name="years_experience",
                        operator=RuleOperator.GTE,
                        value=5,
                    )
                ],
                is_active=True,
            )
            await self.rule_repo.create(rule1)

        self.log_debug(
            f"Context setup complete. Org: {self.org.name}, Workspace: {self.workspace.name}"
        )

    async def run(self):
        await self.setup()

        while True:
            print("=" * 50)
            print("Enterprise Decision Intelligence Platform")
            print("=" * 50)
            print(f"Organization: {self.org.name}")
            print(f"Workspace:    {self.workspace.name}")
            print("\nSelect:")
            print("1. Upload Knowledge")
            print("2. Execute Decision Workflow")
            print("3. Record Decision Outcome")
            print("4. View Execution History")
            print("5. Exit\n")

            try:
                choice = input("Enter choice (1-5): ").strip()
            except EOFError:
                break

            if choice == "1":
                await self.menu_upload_knowledge()
            elif choice == "2":
                await self.menu_execute_workflow()
            elif choice == "3":
                await self.menu_record_outcome()
            elif choice == "4":
                self.menu_view_history()
            elif choice == "5":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

    async def menu_upload_knowledge(self):
        print("\n--- Upload Knowledge ---")
        doc_content = input("Enter document content (simulating upload):\n> ").strip()
        if not doc_content:
            print("Content cannot be empty.")
            return

        description = input("Enter a 2-3 line description of the document:\n> ").strip()

        start_time = time.time()

        # 1. Create Asset in DB
        self.log_debug("Creating KnowledgeAsset in database...")
        asset = KnowledgeAsset(
            organization_id=self.org.id,
            schema_id=self.schema.id,
            name=f"Uploaded Knowledge {str(uuid4())[:8]}",
            description=description,
            content_type=AssetContentType.TEXT,
            status=AssetStatus.PENDING,
            raw_content=doc_content,
            uploaded_by=self.user.id
        )
        await self.asset_repo.create(asset)

        print("\nProcessing document...")

        # 2. Index via Knowledge Manager
        try:
            point_ids = await self.knowledge_manager.index_asset(asset, [self.schema])

            # 3. Update Asset
            self.log_debug("Updating Asset status and qdrant IDs...")
            asset.status = AssetStatus.READY
            asset.qdrant_point_ids = point_ids
            await self.asset_repo.update(asset)

            # 4. Attach to Workspace if not already
            if str(asset.id) not in [
                str(aid) for aid in self.workspace.selected_knowledge_asset_ids
            ]:
                self.workspace.selected_knowledge_asset_ids.append(asset.id)
                await self.workspace_repo.update(self.workspace)
                self.log_debug(
                    f"Attached asset {asset.id} to workspace {self.workspace.id}"
                )

            duration = time.time() - start_time
            print("\n[OK] Document stored successfully.")
            print(f"Detected Knowledge Schema: {self.schema.name}")
            print(f"Indexed Chunks: {len(point_ids)}")
            print(f"Time Taken: {duration:.2f}s")

            trace_entry = (
                f"Knowledge Upload: Indexed {len(point_ids)} chunks in {duration:.2f}s"
            )
            self.execution_traces.append(trace_entry)

        except Exception as e:
            print(f"ERROR processing document: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    async def _setup_runtime_context(self, plan: ExecutionPlan) -> ExecutionContext:
        registry = AgentRegistry()

        # Register real agents
        self.log_debug("Registering real agents in LangGraph runtime...")
        registry.register(
            agent_type=AgentType.RETRIEVER,
            node_implementation=RetrieverAgent(
                knowledge_manager=self.knowledge_manager
            ).execute,
            description="Fetch relevant knowledge chunks",
            consumes=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RETRIEVER
                for art in step.consumes
            ],
            produces=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RETRIEVER
                for art in step.produces
            ],
        )
        registry.register(
            agent_type=AgentType.REASONING,
            node_implementation=ReasoningAgent().execute,
            description="Evaluate rules and context",
            consumes=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.REASONING
                for art in step.consumes
            ],
            produces=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.REASONING
                for art in step.produces
            ],
        )
        registry.register(
            agent_type=AgentType.RECOMMENDATION,
            node_implementation=RecommendationAgent().execute,
            description="Score and rank candidates",
            consumes=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RECOMMENDATION
                for art in step.consumes
            ],
            produces=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RECOMMENDATION
                for art in step.produces
            ],
        )
        registry.register(
            agent_type=AgentType.EXPLANATION,
            node_implementation=ExplanationAgent().execute,
            description="Provide reasoning explanation",
            consumes=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.EXPLANATION
                for art in step.consumes
            ],
            produces=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.EXPLANATION
                for art in step.produces
            ],
        )
        registry.register(
            agent_type=AgentType.RULE_CHECKER,
            node_implementation=RuleCheckerAgent().execute,
            description="Validate against business rules",
            consumes=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RULE_CHECKER
                for art in step.consumes
            ],
            produces=[
                art
                for step in plan.execution_steps
                if step.agent_name == AgentType.RULE_CHECKER
                for art in step.produces
            ],
        )

        initial_state = WorkflowState()
        context = ExecutionContext(
            plan=plan, state=initial_state, registry=registry, planner=self.planner
        )
        return context

    async def menu_execute_workflow(self):
        print("\n--- Execute Decision Workflow ---")
        prompt = input("What decision would you like to make?\n> ").strip()
        if not prompt:
            print("Prompt cannot be empty.")
            return

        print("\n[1] Generating Execution Plan via Planner...")
        start_time = time.time()

        assets = []
        for aid in self.workspace.selected_knowledge_asset_ids:
            a = await self.asset_repo.get_by_id(aid)
            if a:
                assets.append(a)
        rules = await self.rule_repo.list(organization_id=self.org.id, workspace_id=self.workspace.id)
        
        if not assets:
            print(
                "WARNING: No knowledge assets found in this workspace. Retrieval might return empty results."
            )

        try:
            plan = await self.planner.generate_plan(
                user_request=prompt,
                organization=self.org.model_dump(mode="json"),
                workspace=self.workspace.model_dump(mode="json"),
                knowledge_assets=[a.model_dump(mode="json") for a in assets],
                knowledge_schema=self.schema.model_dump(mode="json"),
                business_rules=[r.model_dump(mode="json") for r in rules],
                enabled_agents=[a.value for a in AgentType],
            )
            planner_time = time.time() - start_time
            print(f"Plan generated in {planner_time:.2f}s.")
            print(f"Goal: {plan.goal}")
            print(f"Requires Human Review: {plan.requires_human_review}")

            print("\n--- Execution Plan ---")
            for step in plan.execution_steps:
                deps = ", ".join(step.depends_on) if step.depends_on else "None"
                print(f"[{step.agent_name.value}] - {step.objective}")
                print(f"  Dependencies: {deps}")
                print(f"  Produces: {[p.value for p in step.produces]}")

            if self.debug:
                print("\n[DEBUG] Full Execution Plan JSON:")
                print(plan.model_dump_json(indent=2))

            print("\n[2] Executing LangGraph Runtime...")
            runtime_context = await self._setup_runtime_context(plan)
            runtime = WorkflowRuntime(runtime_context)

            initial_state = WorkflowState(
                user_request=prompt,
                organization=self.org.model_dump(mode="json"),
                workspace=self.workspace.model_dump(mode="json"),
                workspace_context={},
                selected_knowledge_asset_ids=[str(a.id) for a in assets],
                business_rules=[r.model_dump(mode="json") for r in rules],
            )

            thread_id = str(uuid4())
            runtime_start = time.time()
            state = await runtime.start(initial_state, thread_id=thread_id)

            print("\nLangGraph Execution Progress:")
            print(f"Completed Nodes: {state.completed_steps}")
            if state.failed_steps:
                print(f"Failed Nodes: {state.failed_steps}")
            if state.errors:
                for err in state.errors:
                    print(f"Error: {err}")

            if self.debug:
                print(
                    f"\n[DEBUG] State Keys Populated: {list(state.model_dump(exclude_unset=True).keys())}"
                )

            if state.is_interrupted:
                print("\n" + "!" * 50)
                print("HUMAN REVIEW REQUIRED")
                print("!" * 50)
                if state.recommendation and state.recommendation.recommendation:
                    print(
                        f"Recommended Entity ID: {state.recommendation.recommendation.entity_id}"
                    )
                    print(
                        f"Recommendation Score: {state.recommendation.recommendation.final_score}"
                    )
                if state.explanation and state.explanation.summary:
                    print(f"Explanation:\n{state.explanation.summary}")
                if state.validation_result:
                    print(f"Rule Validation Passed: {state.validation_result.is_valid}")
                    if not state.validation_result.is_valid:
                        print("Violated Rules:")
                        for v in state.validation_result.violated_rules:
                            print(f"  - [{v.rule_id}] {v.rule_description}: {v.violation_detail}")

                approve = input("\nApprove? (Y/N): ").strip().upper()
                if approve == "Y":
                    feedback = {"decision": "APPROVED"}
                else:
                    reason = input("Please provide feedback for rejection:\n> ").strip()
                    feedback = {"decision": "REJECTED", "feedback": reason}

                print("Resuming workflow through LangGraph...")
                resume_start = time.time()
                state = await runtime.resume(thread_id=thread_id, feedback=feedback)
                runtime_time = (resume_start - runtime_start) + (
                    time.time() - resume_start
                )
            else:
                runtime_time = time.time() - runtime_start

            print("\n[3] Final Result:")
            rec_id = "N/A"
            if state.recommendation and state.recommendation.recommendation:
                rec_id = state.recommendation.recommendation.entity_id
                print(f"Final Entity ID: {rec_id}")
                print(f"Final Score: {state.recommendation.recommendation.final_score}")
            if state.explanation and state.explanation.summary:
                print(f"Summary:\n{state.explanation.summary}")

            if state.failed_steps:
                print("WARNING: Some steps failed during execution.")

            duration = time.time() - start_time

            # Record Traces
            exec_trace = (
                f"Workflow '{prompt[:20]}...'\n"
                f"  Planner: {planner_time:.2f}s\n"
                f"  Runtime: {runtime_time:.2f}s\n"
                f"  Total: {duration:.2f}s\n"
                f"  Agents Executed: {state.completed_steps}"
            )
            self.execution_traces.append(exec_trace)

            dec_trace = (
                f"Decision Request: '{prompt}'\n"
                f"  Goal: {plan.goal}\n"
                f"  Recommendation: {rec_id}\n"
                f"  Outcome: Pending user recording"
            )
            self.decision_traces.append(dec_trace)

        except Exception as e:
            print(f"ERROR executing workflow: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    async def menu_record_outcome(self):
        print("\n--- Record Decision Outcome ---")
        entity_id = input(
            "Enter Entity ID that was acted upon (e.g., candidate ID):\n> "
        ).strip()
        outcome = input(
            "Enter Business Outcome (e.g., APPROVED, REJECTED, HIRED):\n> "
        ).strip()
        feedback = input("Enter any qualitative feedback:\n> ").strip()

        if not entity_id or not outcome:
            print("Entity ID and Outcome are required.")
            return

        print("\nInvoking Learner Agent...")
        start_time = time.time()

        learner = LearnerAgent()

        state = WorkflowState(
            organization=self.org.model_dump(mode="json"),
            workspace=self.workspace.model_dump(mode="json"),
            final_decision={"entity_id": entity_id, "status": outcome},
            human_feedback=feedback,
        )

        try:
            result = await learner.execute(state)

            if result and result.preference_update:
                print(f"Learning Signal: {result.preference_update.learning_signal}")
                print(f"Learned Attributes: {result.preference_update.learned_attributes}")
            
            self.log_debug("Persisting DecisionRecord to database...")
            # Persist to decision history
            # Convert status string to enum if possible, else fallback
            try:
                db_status = DecisionOutcome[outcome.upper()]
            except KeyError:
                db_status = (
                    DecisionOutcome.APPROVED
                    if outcome.upper() in ["APPROVED", "HIRED"]
                    else DecisionOutcome.REJECTED
                )
                
            try:
                import uuid
                asset_uuid = uuid.UUID(entity_id)
            except Exception:
                asset_uuid = uuid4()
                
            record = DecisionHistory(
                organization_id=str(self.org.id),
                workspace_id=str(self.workspace.id),
                recommendation_id=str(uuid4()),
                asset_id=str(asset_uuid),
                decided_by=str(self.user.id),
                outcome=db_status,
                lifecycle_stage="Completed",
                notes=feedback
            )
            await self.decision_repo.create(record)

            duration = time.time() - start_time
            print(
                f"\n[OK] Learning signal and decision record persisted to MongoDB in {duration:.2f}s."
            )

            self.execution_traces.append(f"Record Outcome: {duration:.2f}s")

        except Exception as e:
            print(f"ERROR recording outcome: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    def menu_view_history(self):
        print("\n=================================================")
        print("Execution Trace")
        print("=================================================")
        if not self.execution_traces:
            print("No traces available.")
        else:
            for t in self.execution_traces:
                print("-" * 50)
                print(t)

        print("\n=================================================")
        print("Decision Trace")
        print("=================================================")
        if not self.decision_traces:
            print("No decisions recorded in this session.")
        else:
            for d in self.decision_traces:
                print("-" * 50)
                print(d)


async def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Decision Intelligence Platform CLI"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed internal traces",
    )
    args = parser.parse_args()

    cli = PlatformCLI(debug_mode=args.debug)
    try:
        await cli.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nFatal Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
