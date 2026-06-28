import sys
import os
import asyncio
from uuid import uuid4
import json
from unittest.mock import AsyncMock

# Add the backend directory to the path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.settings import get_settings
from openai import AsyncOpenAI
from app.models.knowledge_asset import KnowledgeAsset
from app.models.enums import AssetContentType, AssetStatus
from app.models.knowledge_schema import KnowledgeSchema
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer

async def main():
    print("Starting Document Analysis Verification...")
    
    settings = get_settings()
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-..."):
        print("[FAIL] Error: OPENAI_API_KEY is not configured correctly.")
        sys.exit(1)
        
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    parser_registry = ParserRegistry()
    embedder = OpenAIEmbedder(client=openai_client, model=settings.openai_embedding_model)
    sparse_generator = FastEmbedSparseGenerator()
    ai_analyzer = AIDocumentAnalyzer(client=openai_client)
    
    document_processor = DocumentProcessor(
        parser_registry=parser_registry,
        dense_embedder=embedder,
        sparse_generator=sparse_generator,
        ai_analyzer=ai_analyzer
    )
    
    # Create mock schemas
    schema_resume = KnowledgeSchema(
        organization_id=uuid4(),
        name="Resume",
        description="Candidate resumes containing work history and skills.",
        fields=[]
    )
    schema_policy = KnowledgeSchema(
        organization_id=uuid4(),
        name="Company Policy",
        description="Official company policies (e.g. Leave Policy, Security Policy).",
        fields=[]
    )
    available_schemas = [schema_resume, schema_policy]
    
    # 1. Test Rule-based Analyzer (Single Page)
    print("\n--- Test 1: Rule-Based (Single Page) ---")
    asset1 = KnowledgeAsset(
        organization_id=uuid4(),
        schema_id=uuid4(), # Will be replaced if schema matches
        name="Short Note",
        content_type=AssetContentType.TEXT,
        status=AssetStatus.PENDING,
        raw_content="This is just a single short note. It should use SingleDocumentChunker.",
        uploaded_by=uuid4(),
        user_description="A quick short note."
    )
    chunks1 = await document_processor.process(asset1, available_schemas)
    print(f"Asset Processing Metadata:\n{asset1.processing_metadata.model_dump_json(indent=2)}")
    print(f"Produced {len(chunks1)} chunks.")
    assert asset1.processing_metadata.selection_method == "rule_based"
    assert asset1.processing_metadata.chunking_strategy == "SingleDocumentChunker"
    
    # 2. Test AI-based Analyzer (Policy)
    print("\n--- Test 2: AI-Based (Leave Policy) ---")
    # To bypass rule-based analyzer: > 1 page (>3000 chars), < 5 headings, no TOC, < 10000 chars.
    policy_text = "This is a continuous paragraph explaining our leave policy. Employees are entitled to twenty days of annual leave. Sick leave is ten days. Maternity leave is fully covered for six months. " * 50
    asset2 = KnowledgeAsset(
        organization_id=uuid4(),
        schema_id=uuid4(),
        name="Global Leave Policy 2026",
        content_type=AssetContentType.TEXT,
        status=AssetStatus.PENDING,
        raw_content=policy_text,
        uploaded_by=uuid4(),
        user_description="This document outlines our company's global leave policy including annual, sick, and maternity leave."
    )
    
    # Temporarily disable rule-based analyzer to force AI evaluation
    document_processor.rule_analyzer.analyze = AsyncMock(return_value=None)
    
    chunks2 = await document_processor.process(asset2, available_schemas)
    print(f"Asset Processing Metadata:\n{asset2.processing_metadata.model_dump_json(indent=2)}")
    print(f"Matched Schema ID: {asset2.schema_id}")
    print(f"Produced {len(chunks2)} chunks.")
    
    print("\n[OK] Document Analysis Verification Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(main())
