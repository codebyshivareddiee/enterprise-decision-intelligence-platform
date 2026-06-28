"""TXT document parser."""

from app.knowledge.exceptions import ParsingError
from app.knowledge.interfaces.parser import DocumentParser
from app.knowledge.parsers.models import ParsedDocument
from app.models.knowledge_asset import KnowledgeAsset


class TxtParser(DocumentParser):
    """Parses plain text KnowledgeAssets."""

    async def parse(self, asset: KnowledgeAsset) -> ParsedDocument:
        """Parse a TXT KnowledgeAsset.

        Since we don't have a real file system or object store in this demo,
        we assume `asset.raw_content` contains the text if it's already a string,
        or we would fetch from `asset.file_path`.

        Args:
            asset: The TXT KnowledgeAsset.

        Returns:
            The ParsedDocument containing the plain text and metadata.

        Raises:
            ParsingError: If content is missing or cannot be read.
        """
        try:
            if asset.raw_content:
                text = str(asset.raw_content)
                # Compute basic stats
                char_count = len(text)
                word_count = len(text.split())

                # Sample logic for text: just take first, middle, last 1000 chars if long
                sampled_pages = {}
                if char_count > 3000:
                    sampled_pages[1] = text[:1000]
                    sampled_pages[2] = text[
                        char_count // 2 - 500 : char_count // 2 + 500
                    ]
                    sampled_pages[3] = text[-1000:]
                else:
                    sampled_pages[1] = text

                # Detect rudimentary headings (lines starting with # or ALL CAPS short lines)
                headings = []
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("# ") or (line.isupper() and len(line) < 50):
                        headings.append(line)

                return ParsedDocument(
                    text=text,
                    filename=f"{asset.name}.txt",
                    extension="txt",
                    page_count=1,
                    document_statistics={
                        "char_count": char_count,
                        "word_count": word_count,
                    },
                    headings=headings,
                    sampled_pages=sampled_pages,
                )

            # In a real implementation, we would download from asset.file_path here
            # For hackathon/demo, we assume raw_content is populated for TXT
            raise ParsingError(f"No raw_content found for TXT asset {asset.id}")

        except Exception as e:
            raise ParsingError(f"Failed to parse TXT asset {asset.id}: {str(e)}") from e
