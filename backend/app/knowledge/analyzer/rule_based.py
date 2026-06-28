"""Rule-based document analyzer."""

from app.knowledge.analyzer.base import DocumentAnalyzer
from app.knowledge.analyzer.models import DocumentAnalysisResult, ChunkProfile
from app.models.knowledge_asset import KnowledgeAsset
from app.models.knowledge_schema import KnowledgeSchema
from app.knowledge.parsers.models import ParsedDocument

class RuleBasedAnalyzer(DocumentAnalyzer):
    """Deterministically classifies documents based on structural metadata."""

    def __init__(self, confidence_threshold: float = 0.8) -> None:
        self.confidence_threshold = confidence_threshold

    async def analyze(
        self, 
        asset: KnowledgeAsset,
        parsed_doc: ParsedDocument, 
        available_schemas: list[KnowledgeSchema]
    ) -> DocumentAnalysisResult | None:
        
        # Rule 1: Single page document -> SingleDocumentChunker
        if parsed_doc.page_count and parsed_doc.page_count == 1:
            return DocumentAnalysisResult(
                matched_schema_id=None,  # Rule-based doesn't guess schema as well as AI
                chunking_strategy="SingleDocumentChunker",
                chunk_profile=ChunkProfile.SMALL,
                confidence=0.9,
                reasoning="Document is a single page.",
                detected_document_type="Single Page",
            )
            
        # Rule 2: Contains many headings -> HeadingChunker
        if parsed_doc.headings and len(parsed_doc.headings) > 5:
            return DocumentAnalysisResult(
                matched_schema_id=None,
                chunking_strategy="HeadingChunker",
                chunk_profile=ChunkProfile.MEDIUM,
                confidence=0.85,
                reasoning=f"Document contains {len(parsed_doc.headings)} headings.",
                detected_document_type="Structured Document",
            )
            
        # Rule 3: Contains table of contents -> HierarchicalChunker
        if parsed_doc.table_of_contents:
            return DocumentAnalysisResult(
                matched_schema_id=None,
                chunking_strategy="HierarchicalChunker",
                chunk_profile=ChunkProfile.LARGE,
                confidence=0.9,
                reasoning="Document contains a table of contents.",
                detected_document_type="Complex Document",
            )
            
        # Rule 4: Very long continuous text without many headings -> SlidingWindowChunker
        char_count = parsed_doc.document_statistics.get("char_count", 0)
        if isinstance(char_count, int) and char_count > 10000:
            return DocumentAnalysisResult(
                matched_schema_id=None,
                chunking_strategy="SlidingWindowChunker",
                chunk_profile=ChunkProfile.MEDIUM,
                confidence=0.8,
                reasoning="Document is long and lacks clear heading structure.",
                detected_document_type="Continuous Text",
            )
            
        # If no rules match with sufficient confidence, return None
        return None
