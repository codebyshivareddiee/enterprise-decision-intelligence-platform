"""AI-based document analyzer."""

import json

import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)
from app.knowledge.analyzer.base import DocumentAnalyzer
from app.knowledge.analyzer.models import ChunkProfile, DocumentAnalysisResult
from app.knowledge.parsers.models import ParsedDocument
from app.models.knowledge_asset import KnowledgeAsset
from app.models.knowledge_schema import KnowledgeSchema


class AIDocumentAnalyzer(DocumentAnalyzer):
    """Uses LLM to analyze document and select optimal processing strategy."""

    def __init__(
        self, client: AsyncOpenAI | None = None, model: str = "gpt-4o"
    ) -> None:
        self.client = client or AsyncOpenAI()
        self.model = model

    async def analyze(
        self,
        asset: KnowledgeAsset,
        parsed_doc: ParsedDocument,
        available_schemas: list[KnowledgeSchema],
    ) -> DocumentAnalysisResult | None:

        # Prepare schemas description
        schemas_info = []
        for schema in available_schemas:
            schemas_info.append(
                {
                    "id": str(schema.id),
                    "name": schema.name,
                    "description": schema.description,
                }
            )

        system_prompt = (
            "You are an expert Document Analyst for an enterprise AI platform.\n"
            "Your task is to analyze a document's metadata and sample content, and determine the optimal "
            "Knowledge Schema, Chunking Strategy, and Chunk Profile.\n\n"
            "AVAILABLE SCHEMAS:\n"
            f"{json.dumps(schemas_info, indent=2)}\n\n"
            "AVAILABLE CHUNKING STRATEGIES:\n"
            "- SingleDocumentChunker (for very short documents <= 1 page)\n"
            "- SlidingWindowChunker (for continuous long text without clear sections)\n"
            "- HeadingChunker (for text with many headings/sections)\n"
            "- ParagraphChunker (for documents where paragraph structure is primary)\n"
            "- HierarchicalChunker (for complex documents with nested TOCs)\n\n"
            "AVAILABLE CHUNK PROFILES:\n"
            "- SMALL (chunk_size=400, overlap=50)\n"
            "- MEDIUM (chunk_size=800, overlap=100)\n"
            "- LARGE (chunk_size=1200, overlap=150)\n"
            "- XLARGE (chunk_size=2000, overlap=200)\n\n"
            "You must output ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "matched_schema_id": "UUID string of the most appropriate schema or null",\n'
            '  "chunking_strategy": "string (one of the available strategies)",\n'
            '  "chunk_profile": "string (SMALL, MEDIUM, LARGE, XLARGE)",\n'
            '  "confidence": float (0.0 to 1.0),\n'
            '  "reasoning": "string explaining why these choices were made",\n'
            '  "detected_document_type": "string (e.g. Policy, Resume, Technical Spec)",\n'
            '  "detected_language": "string",\n'
            '  "estimated_complexity": "string (Low, Medium, High)",\n'
            '  "requires_human_confirmation": boolean\n'
            "}"
        )

        user_prompt = (
            f"USER DESCRIPTION:\n{asset.user_description or 'None provided'}\n\n"
            f"FILE METADATA:\n"
            f"- Name: {parsed_doc.filename}\n"
            f"- Extension: {parsed_doc.extension}\n"
            f"- Pages: {parsed_doc.page_count}\n"
            f"- Stats: {parsed_doc.document_statistics}\n"
            f"- Headings: {parsed_doc.headings[:20]} (truncated)\n\n"
            f"SAMPLED CONTENT:\n"
        )

        for page_num, text in parsed_doc.sampled_pages.items():
            user_prompt += f"--- Page {page_num} Sample ---\n{text}\n\n"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            result_json = response.choices[0].message.content
            if not result_json:
                return None

            data = json.loads(result_json)

            return DocumentAnalysisResult(
                matched_schema_id=data.get("matched_schema_id"),
                chunking_strategy=data.get("chunking_strategy", "SlidingWindowChunker"),
                chunk_profile=ChunkProfile(data.get("chunk_profile", "MEDIUM")),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", "No reasoning provided."),
                detected_document_type=data.get("detected_document_type"),
                detected_language=data.get("detected_language"),
                estimated_complexity=data.get("estimated_complexity"),
                requires_human_confirmation=bool(
                    data.get("requires_human_confirmation", False)
                ),
            )
        except Exception as e:
            # Fallback gracefully
            logger.error("ai_document_analyzer.failed", error=str(e))
            return None