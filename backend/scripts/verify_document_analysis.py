import asyncio
import os
import sys
from unittest.mock import AsyncMock
from uuid import uuid4

# Add the backend directory to the path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import AsyncOpenAI

from app.config.settings import get_settings
from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer
from app.knowledge.embedding.openai_embedder import OpenAIEmbedder
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.sparse.fastembed_sparse_generator import FastEmbedSparseGenerator
from app.models.enums import AssetContentType, AssetStatus
from app.models.knowledge_asset import KnowledgeAsset
from app.models.knowledge_schema import KnowledgeSchema


async def main():
    print("Starting Document Analysis Verification...")

    settings = get_settings()
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-..."):
        print("[FAIL] Error: OPENAI_API_KEY is not configured correctly.")
        sys.exit(1)

    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    parser_registry = ParserRegistry()
    embedder = OpenAIEmbedder(
        client=openai_client, model=settings.openai_embedding_model
    )
    sparse_generator = FastEmbedSparseGenerator()
    ai_analyzer = AIDocumentAnalyzer(client=openai_client)

    document_processor = DocumentProcessor(
        parser_registry=parser_registry,
        dense_embedder=embedder,
        sparse_generator=sparse_generator,
        ai_analyzer=ai_analyzer,
    )

    # Create mock schemas
    schema_resume = KnowledgeSchema(
        organization_id=uuid4(),
        name="Resume",
        description="Candidate resumes containing work history and skills.",
        fields=[],
        default_chunk_strategy="HeadingChunker",
        default_chunk_profile="MEDIUM",
        default_retrieval_strategy="semantic_hybrid",
    )
    schema_policy = KnowledgeSchema(
        organization_id=uuid4(),
        name="Company Policy",
        description="Official company policies (e.g. Leave Policy, Security Policy).",
        fields=[],
        default_chunk_strategy="ParagraphChunker",
        default_chunk_profile="LARGE",
        default_retrieval_strategy="semantic_dense",
    )
    available_schemas = [schema_resume, schema_policy]

    # 1. Test Rule-based Analyzer (Single Page)
    print("\n--- Test 1: Rule-Based (Single Page) ---")
    asset1 = KnowledgeAsset(
        organization_id=uuid4(),
        schema_id=uuid4(),  # Will be replaced if schema matches
        name="Short Note",
        content_type=AssetContentType.TEXT,
        status=AssetStatus.PENDING,
        raw_content="This is just a single short note. It should use SingleDocumentChunker.",
        uploaded_by=uuid4(),
        user_description="A quick short note.",
        dynamic_metadata={},
        content_hash=None,
    )
    chunks1 = await document_processor.process(asset1, available_schemas)
    print(
        f"Asset Processing Metadata:\n{asset1.processing_metadata.model_dump_json(indent=2)}"
    )
    print(f"Produced {len(chunks1)} chunks.")
    assert asset1.processing_metadata.selection_method == "schema_default"
    assert asset1.processing_metadata.chunking_strategy == "HeadingChunker"

    # 2. Test AI-based Analyzer (Policy)
    print("\n--- Test 2: AI-Based (Leave Policy) ---")
    # To bypass rule-based analyzer: > 1 page (>3000 chars), < 5 headings, no TOC, < 10000 chars.
    policy_text = (
        "This is a continuous paragraph explaining our leave policy. Employees are entitled to twenty days of annual leave. Sick leave is ten days. Maternity leave is fully covered for six months. "
        * 50
    )
    asset2 = KnowledgeAsset(
        organization_id=uuid4(),
        schema_id=uuid4(),
        name="Global Leave Policy 2026",
        content_type=AssetContentType.TEXT,
        status=AssetStatus.PENDING,
        raw_content=policy_text,
        uploaded_by=uuid4(),
        user_description="This document outlines our company's global leave policy including annual, sick, and maternity leave.",
        dynamic_metadata={},
        content_hash=None,
    )

    # Temporarily disable rule-based analyzer to force AI evaluation
    document_processor.rule_analyzer.analyze = AsyncMock(return_value=None)

    chunks2 = await document_processor.process(asset2, available_schemas)
    print(
        f"Asset Processing Metadata:\n{asset2.processing_metadata.model_dump_json(indent=2)}"
    )
    print(f"Matched Schema ID: {asset2.schema_id}")
    print(f"Produced {len(chunks2)} chunks.")

    # 3. Test Batch Processing
    print("\n--- Test 3: Batch Processing ---")
    asset3 = KnowledgeAsset(
        organization_id=uuid4(),
        schema_id=uuid4(),
        name="Global Leave Policy Part 2",
        content_type=AssetContentType.TEXT,
        status=AssetStatus.PENDING,
        raw_content=policy_text,
        uploaded_by=uuid4(),
        user_description="Continuation of policy.",
        dynamic_metadata={},
        content_hash=None,
    )
    batch_results, _ = await document_processor.process_batch(
        assets=[asset2, asset3],
        available_schemas=available_schemas,
        batch_description="Two similar policy documents.",
    )
    print(
        f"Batch processing produced {len(batch_results[asset2.id])} chunks for doc 1 and {len(batch_results[asset3.id])} chunks for doc 2."
    )
    assert (
        asset2.processing_metadata.chunking_strategy
        == asset3.processing_metadata.chunking_strategy
    )

    print("\n[OK] Document Analysis Verification Completed Successfully.")


if __name__ == "__main__":
    asyncio.run(main())
