"""FastAPI dependencies for injecting services, repositories, and context."""

from collections.abc import AsyncGenerator
from typing import TypeVar

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore

from app.persistence.mongodb.database import get_database
from app.persistence.mongodb.repositories.organization_repository import OrganizationRepository
from app.persistence.mongodb.repositories.workspace_repository import WorkspaceRepository
from app.persistence.mongodb.repositories.knowledge_asset_repository import KnowledgeAssetRepository
from app.persistence.mongodb.repositories.decision_history_repository import DecisionHistoryRepository
from app.persistence.mongodb.repositories.business_rule_repository import BusinessRuleRepository

# AI Layer
from app.ai.manager import AIManager
from app.ai.providers.openai_provider import OpenAIProvider

# Knowledge Layer
# Since setting up KnowledgeManager requires DocumentProcessor, VectorStore, etc.,
# we will provide a simplified dependency here or assume it's created on startup.
# For now, we will instantiate it on demand or use a simple provider.
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.knowledge.vectorstore.qdrant_store import QdrantStore
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.search.search_service import SearchService

# Workflow Layer
from app.agents.planner.planner import Planner

T = TypeVar("T")


def get_db() -> AsyncIOMotorDatabase:
    """Return the Motor database instance."""
    return get_database()


def get_organization_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> OrganizationRepository:
    """Return the OrganizationRepository."""
    return OrganizationRepository(db)


def get_workspace_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> WorkspaceRepository:
    """Return the WorkspaceRepository."""
    return WorkspaceRepository(db)


def get_knowledge_asset_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> KnowledgeAssetRepository:
    """Return the KnowledgeAssetRepository."""
    return KnowledgeAssetRepository(db)


def get_decision_history_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DecisionHistoryRepository:
    """Return the DecisionHistoryRepository."""
    return DecisionHistoryRepository(db)


def get_business_rule_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BusinessRuleRepository:
    """Return the BusinessRuleRepository."""
    return BusinessRuleRepository(db)


from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.knowledge.parsers.registry import ParserRegistry


def get_ai_manager() -> AIManager:
    """Return the AIManager."""
    # Instantiating on the fly is lightweight since OpenAIProvider doesn't hold heavy state
    provider = OpenAIProvider()
    return AIManager(provider=provider)


from app.config.settings import get_settings
from qdrant_client import AsyncQdrantClient

def get_knowledge_manager(
    ai_manager: AIManager = Depends(get_ai_manager),
) -> KnowledgeManager:
    """Return the KnowledgeManager."""
    # In a real app, these would be cached singletons. 
    # For this task, we initialize them here.
    settings = get_settings()
    qdrant_client = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )
    vector_store = QdrantStore(
        client=qdrant_client,
        collection_name=settings.qdrant_collection_name
    )
    
    client = getattr(ai_manager._provider, "client", None)
    dense_embedder = OpenAIEmbedder(client=client)
    sparse_generator = FastEmbedSparseGenerator()
    
    search_service = SearchService(
        vector_store=vector_store, 
        dense_embedder=dense_embedder,
        sparse_generator=sparse_generator,
    )
    
    parser_registry = ParserRegistry()
    
    document_processor = DocumentProcessor(
        parser_registry=parser_registry,
        dense_embedder=dense_embedder,
        sparse_generator=sparse_generator,
    )
    return KnowledgeManager(
        document_processor=document_processor,
        vector_store=vector_store,
        search_service=search_service,
    )


def get_planner(
    ai_manager: AIManager = Depends(get_ai_manager),
) -> Planner:
    """Return the Planner agent."""
    return Planner(ai_manager=ai_manager)



def get_request_context(request: Request) -> dict[str, str]:
    """Extract context variables from the request for use in endpoints."""
    return {
        "request_id": request.headers.get("X-Request-ID", ""),
        "organization_id": request.headers.get("X-Organization-ID", ""),
        "workspace_id": request.headers.get("X-Workspace-ID", ""),
        "user_id": request.headers.get("X-User-ID", ""),
    }
