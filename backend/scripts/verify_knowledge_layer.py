import sys
import os
import asyncio
from uuid import uuid4

# Add the backend directory to the path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.settings import get_settings
from app.persistence.mongodb import client as mongo_client
from qdrant_client import AsyncQdrantClient
from openai import AsyncOpenAI

from app.models.organization import Organization
from app.models.user import User
from app.models.enums import UserRole, UserStatus, WorkspaceStatus, FieldType, AssetContentType, AssetStatus
from app.models.knowledge_schema import KnowledgeSchema, SchemaField
from app.models.workspace import Workspace
from app.models.knowledge_asset import KnowledgeAsset
from app.models.lifecycle_definition import LifecycleDefinition, LifecycleStage

from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.search.search_service import SearchService
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.knowledge.vectorstore.qdrant_store import QdrantStore

async def main():
    print("Starting Knowledge Layer Verification...")
    
    settings = get_settings()
    
    # 1. Verify Environment
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-..."):
        print("[FAIL] Error: OPENAI_API_KEY is not configured correctly in .env.")
        sys.exit(1)
        
    print("[OK] Configuration verified")

    try:
        # 2. Connect to MongoDB
        await mongo_client.connect(settings.mongodb_uri)
        db = mongo_client.get_mongo_client()[settings.mongodb_db_name]
        print("[OK] Connected to MongoDB")
        
        # We will directly use Motor collections for seeding instead of repositories for simplicity in this verification script
        org_coll = db["organizations"]
        user_coll = db["users"]
        schema_coll = db["knowledge_schemas"]
        workspace_coll = db["workspaces"]
        asset_coll = db["knowledge_assets"]
        lifecycle_coll = db["lifecycle_definitions"]

        # Reset demo data
        await org_coll.delete_many({"name": "XL Ventures Demo"})
        print("[OK] Reset demo data")

        # 3. Connect to Qdrant
        qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        q_exists = await qdrant.collection_exists(settings.qdrant_collection_name)
        if not q_exists:
            print(f"Collection {settings.qdrant_collection_name} does not exist in Qdrant yet. It will be created.")
        print("[OK] Connected to Qdrant")

        # 4. Connect to OpenAI
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        print("[OK] Connected to OpenAI")

        # 5. Initialize Knowledge Manager
        print("Initializing Knowledge Manager components...")
        parser_registry = ParserRegistry()
        embedder = OpenAIEmbedder(client=openai_client, model=settings.openai_embedding_model)
        sparse_generator = FastEmbedSparseGenerator()
        vector_store = QdrantStore(
            client=qdrant, 
            collection_name=settings.qdrant_collection_name
        )
        
        # Ensure collection is initialized
        await vector_store.initialize_collection()
        print("[OK] Initialized Qdrant collection")

        document_processor = DocumentProcessor(
            parser_registry=parser_registry,
            dense_embedder=embedder,
            sparse_generator=sparse_generator,
            ai_analyzer=AIDocumentAnalyzer(client=openai_client)
        )
        search_service = SearchService(
            dense_embedder=embedder,
            sparse_generator=sparse_generator,
            vector_store=vector_store
        )
        knowledge_manager = KnowledgeManager(
            document_processor=document_processor,
            vector_store=vector_store,
            search_service=search_service
        )
        
        # 6. Seed Data
        org = Organization(name="XL Ventures Demo", domains=["xlventures.com"], slug="xl-ventures-demo", contact_email="contact@xlventures.com")
        await org_coll.insert_one(org.model_dump(mode="json"))
        print("[OK] Seeded organization")
        
        user = User(
            organization_id=org.id,
            email="admin@xlventures.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        await user_coll.insert_one(user.model_dump(mode="json"))
        print("[OK] Seeded user")
        
        schema = KnowledgeSchema(
            organization_id=org.id,
            name="Resume",
            description="Candidate resume schema",
            fields=[
                SchemaField(name="name", label="Name", field_type=FieldType.STRING, required=True),
                SchemaField(name="skills", label="Skills", field_type=FieldType.LIST, required=True)
            ]
        )
        await schema_coll.insert_one(schema.model_dump(mode="json"))
        print("[OK] Seeded knowledge schema")
        
        lifecycle = LifecycleDefinition(
            organization_id=org.id,
            name="Resume Lifecycle",
            description="Hiring pipeline",
            stages=[
                LifecycleStage(id=str(uuid4()), name="Applied", order=1),
                LifecycleStage(id=str(uuid4()), name="Interview", order=2)
            ]
        )
        await lifecycle_coll.insert_one(lifecycle.model_dump(mode="json"))
        
        asset = KnowledgeAsset(
            organization_id=org.id,
            schema_id=schema.id,
            name="Sample AI Engineer Resume",
            content_type=AssetContentType.TEXT,
            status=AssetStatus.PENDING,
            raw_content="John Doe is an expert AI Engineer with 5 years of experience in Python, FastAPI, and RAG architectures. He has built several production-ready Knowledge Layers and Vector Store integrations using Qdrant and OpenAI. John excels at Clean Architecture and asynchronous Python programming.",
            uploaded_by=user.id
        )
        
        # In a real scenario we'd create the workspace, but we need the asset ID first
        workspace = Workspace(
            organization_id=org.id,
            name="Hiring AI Engineer",
            description="Demo workspace for hiring",
            knowledge_schema_id=schema.id,
            lifecycle_definition_id=lifecycle.id,
            status=WorkspaceStatus.ACTIVE,
            selected_knowledge_asset_ids=[asset.id],
            owner_id=user.id
        )
        await workspace_coll.insert_one(workspace.model_dump(mode="json"))
        print("[OK] Created workspace")
        
        await asset_coll.insert_one(asset.model_dump(mode="json"))
        print("[OK] Uploaded asset")
        
        # 7. Index Asset
        print("Indexing asset through KnowledgeManager...")
        point_ids = await knowledge_manager.index_asset(asset, [schema])
        
        # Update asset in MongoDB to simulate what a real repository/workflow would do
        asset.status = AssetStatus.READY
        asset.qdrant_point_ids = point_ids
        await asset_coll.update_one({"id": str(asset.id)}, {"$set": {"status": asset.status.value, "qdrant_point_ids": point_ids}})
        print(f"[OK] Indexed {len(point_ids)} chunks into Qdrant")
        
        # 8. Retrieve
        print("Retrieving chunks...")
        query = "Looking for an AI engineer with FastAPI and RAG experience"
        results = await knowledge_manager.retrieve(
            organization_id=org.id,
            selected_asset_ids=[asset.id],
            query=query,
            top_k=5
        )
        
        print(f"[OK] Retrieved {len(results)} chunks")
        assert len(results) > 0, "No chunks were retrieved!"
        
        print("\n--- Search Results ---")
        for idx, result in enumerate(results):
            print(f"Result {idx+1} [Score: {result.score:.4f}]")
            print(f"Asset ID: {result.chunk.asset_id}")
            print(f"Metadata: {result.chunk.metadata}")
            print(f"Content: {result.chunk.content}\n")
            
        print("[OK] Knowledge Layer verification completed successfully")
        
    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mongo_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
