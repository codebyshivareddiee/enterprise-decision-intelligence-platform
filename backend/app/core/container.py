"""Service Container for dependency injection."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from qdrant_client import AsyncQdrantClient

from app.config.settings import Settings
from app.persistence.mongodb.repositories.organization_repository import OrganizationRepository
from app.persistence.mongodb.repositories.workspace_repository import WorkspaceRepository
from app.persistence.mongodb.repositories.knowledge_asset_repository import KnowledgeAssetRepository
from app.persistence.mongodb.repositories.decision_history_repository import DecisionHistoryRepository
from app.persistence.mongodb.repositories.business_rule_repository import BusinessRuleRepository
from app.persistence.mongodb.repositories.audit_repository import AuditRepository
from app.persistence.mongodb.repositories.user_repository import UserRepository

from app.ai.manager import AIManager
from app.ai.providers.openai_provider import OpenAIProvider

from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.knowledge.vectorstore.qdrant_store import QdrantStore
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.search.search_service import SearchService

from app.agents.planner.planner import Planner
from app.auth.service import AuthService


class ServiceContainer:
    """Centralized service container for dependency injection."""
    
    def __init__(self, settings: Settings) -> None:
        import time
        self.start_time = time.time()
        self.settings = settings
        
        # Database
        self.mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db: AsyncIOMotorDatabase = self.mongo_client[settings.mongodb_db_name]
        
        # Repositories
        self.organization_repo = OrganizationRepository(self.db)
        self.workspace_repo = WorkspaceRepository(self.db)
        self.knowledge_asset_repo = KnowledgeAssetRepository(self.db)
        self.decision_history_repo = DecisionHistoryRepository(self.db)
        self.business_rule_repo = BusinessRuleRepository(self.db)
        self.audit_repo = AuditRepository(self.db)
        self.user_repo = UserRepository(self.db)
        
        # AI
        self.ai_provider = OpenAIProvider()
        self.ai_manager = AIManager(provider=self.ai_provider)
        
        # Knowledge
        self.qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.vector_store = QdrantStore(
            client=self.qdrant_client,
            collection_name=settings.qdrant_collection_name
        )
        
        client = getattr(self.ai_provider, "client", None)
        self.dense_embedder = OpenAIEmbedder(client=client)
        self.sparse_generator = FastEmbedSparseGenerator()
        
        self.search_service = SearchService(
            vector_store=self.vector_store,
            dense_embedder=self.dense_embedder,
            sparse_generator=self.sparse_generator,
        )
        self.parser_registry = ParserRegistry()
        self.document_processor = DocumentProcessor(
            parser_registry=self.parser_registry,
            dense_embedder=self.dense_embedder,
            sparse_generator=self.sparse_generator,
        )
        
        self.knowledge_manager = KnowledgeManager(
            document_processor=self.document_processor,
            vector_store=self.vector_store,
            search_service=self.search_service,
        )
        
        # Planner
        self.planner = Planner(ai_manager=self.ai_manager)
        
        # Auth
        self.auth_service = AuthService(
            user_repo=self.user_repo,
            audit_repo=self.audit_repo,
        )

    async def close(self) -> None:
        """Close external connections."""
        self.mongo_client.close()
        await self.qdrant_client.close()
