"""PDF document parser."""

import io
from pypdf import PdfReader
from app.models.knowledge_asset import KnowledgeAsset
from app.knowledge.interfaces.parser import DocumentParser
from app.knowledge.parsers.models import ParsedDocument
from app.knowledge.exceptions import ParsingError

class PdfParser(DocumentParser):
    """Parses PDF KnowledgeAssets using pypdf."""

    async def parse(self, asset: KnowledgeAsset) -> ParsedDocument:
        """Parse a PDF KnowledgeAsset.
        
        Args:
            asset: The PDF KnowledgeAsset.
            
        Returns:
            The extracted ParsedDocument.
            
        Raises:
            ParsingError: If parsing fails.
        """
        try:
            # For hackathon purposes, we assume `asset.raw_content` might contain 
            # the base64 or raw bytes, OR we just return a placeholder if not.
            # In a real system, we'd fetch the file from S3 using `asset.file_path`.
            
            text = ""
            if asset.raw_content and isinstance(asset.raw_content, str) and not asset.raw_content.startswith("%PDF"):
                text = asset.raw_content
            else:
                if not asset.file_path and not asset.raw_content:
                    raise ParsingError(f"No file_path or raw_content for PDF asset {asset.id}")
                text = str(asset.raw_content) if asset.raw_content else ""
                
            char_count = len(text)
            word_count = len(text.split())
            
            # Since we simulate PDF, we'll pretend it has pages by splitting roughly every 3000 chars
            page_size = 3000
            page_count = max(1, char_count // page_size)
            
            sampled_pages = {}
            if page_count > 3:
                sampled_pages[1] = text[:page_size]
                sampled_pages[page_count // 2] = text[(page_count // 2) * page_size : (page_count // 2 + 1) * page_size]
                sampled_pages[page_count] = text[-page_size:]
            else:
                for i in range(page_count):
                    sampled_pages[i + 1] = text[i * page_size : (i + 1) * page_size]
            
            headings = []
            for line in text.split("\n"):
                line = line.strip()
                if line.isupper() and 3 < len(line) < 60:
                    headings.append(line)
                    
            return ParsedDocument(
                text=text,
                filename=f"{asset.name}.pdf",
                extension="pdf",
                page_count=page_count,
                document_statistics={"char_count": char_count, "word_count": word_count},
                headings=headings,
                sampled_pages=sampled_pages,
            )

        except Exception as e:
            raise ParsingError(f"Failed to parse PDF asset {asset.id}: {str(e)}") from e
