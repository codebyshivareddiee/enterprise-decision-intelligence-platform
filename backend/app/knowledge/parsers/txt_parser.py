"""TXT document parser."""

from app.models.knowledge_asset import KnowledgeAsset
from app.knowledge.interfaces.parser import DocumentParser
from app.knowledge.exceptions import ParsingError

class TxtParser(DocumentParser):
    """Parses plain text KnowledgeAssets."""

    async def parse(self, asset: KnowledgeAsset) -> str:
        """Parse a TXT KnowledgeAsset.
        
        Since we don't have a real file system or object store in this demo,
        we assume `asset.raw_content` contains the text if it's already a string,
        or we would fetch from `asset.file_path`.
        
        Args:
            asset: The TXT KnowledgeAsset.
            
        Returns:
            The plain text content.
            
        Raises:
            ParsingError: If content is missing or cannot be read.
        """
        try:
            if asset.raw_content:
                return str(asset.raw_content)
            
            # In a real implementation, we would download from asset.file_path here
            # For hackathon/demo, we assume raw_content is populated for TXT
            raise ParsingError(f"No raw_content found for TXT asset {asset.id}")
            
        except Exception as e:
            raise ParsingError(f"Failed to parse TXT asset {asset.id}: {str(e)}") from e
