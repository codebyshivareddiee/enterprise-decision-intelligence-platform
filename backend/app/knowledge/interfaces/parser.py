"""Parser interface."""

from abc import ABC, abstractmethod

from app.models.knowledge_asset import KnowledgeAsset


class DocumentParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    async def parse(self, asset: KnowledgeAsset) -> str:
        """Parse a KnowledgeAsset and extract its text content.

        Args:
            asset: The KnowledgeAsset to parse.

        Returns:
            The extracted plain text.

        Raises:
            ParsingError: If parsing fails.
        """
        pass
