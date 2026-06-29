"""Document analyzer interface."""

from abc import ABC, abstractmethod

from app.knowledge.analyzer.models import DocumentAnalysisResult
from app.knowledge.parsers.models import ParsedDocument
from app.models.knowledge_asset import KnowledgeAsset
from app.models.knowledge_schema import KnowledgeSchema


class DocumentAnalyzer(ABC):
    """Abstract base class for document analyzers."""

    @abstractmethod
    async def analyze(
        self,
        asset: KnowledgeAsset,
        parsed_doc: ParsedDocument,
        available_schemas: list[KnowledgeSchema],
    ) -> DocumentAnalysisResult | None:
        """Analyze a parsed document to determine optimal processing.

        Args:
            asset: The KnowledgeAsset being processed.
            parsed_doc: The structural metadata from the parser.
            available_schemas: List of valid schemas for this organization.

        Returns:
            DocumentAnalysisResult if successful, or None if the analyzer
            cannot confidently determine a strategy.
        """
        pass
