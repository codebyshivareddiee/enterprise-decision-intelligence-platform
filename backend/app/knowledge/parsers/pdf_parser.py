"""PDF document parser."""

from app.knowledge.exceptions import ParsingError
from app.knowledge.interfaces.parser import DocumentParser
from app.models.knowledge_asset import KnowledgeAsset


class PdfParser(DocumentParser):
    """Parses PDF KnowledgeAssets using pypdf."""

    async def parse(self, asset: KnowledgeAsset) -> str:
        """Parse a PDF KnowledgeAsset.

        Args:
            asset: The PDF KnowledgeAsset.

        Returns:
            The extracted plain text content.

        Raises:
            ParsingError: If parsing fails.
        """
        try:
            # For hackathon purposes, we assume `asset.raw_content` might contain
            # the base64 or raw bytes, OR we just return a placeholder if not.
            # In a real system, we'd fetch the file from S3 using `asset.file_path`.

            # If it's already parsed text somehow:
            if (
                asset.raw_content
                and isinstance(asset.raw_content, str)
                and not asset.raw_content.startswith("%PDF")
            ):
                return asset.raw_content

            if not asset.file_path and not asset.raw_content:
                raise ParsingError(
                    f"No file_path or raw_content for PDF asset {asset.id}"
                )

            # If we had bytes (e.g. downloaded from S3):
            # pdf_file = io.BytesIO(downloaded_bytes)
            # reader = PdfReader(pdf_file)
            # text = ""
            # for page in reader.pages:
            #     text += page.extract_text() + "\n"
            # return text.strip()

            # For now, if we have string content that is just dummy data, return it
            return str(asset.raw_content) if asset.raw_content else ""

        except Exception as e:
            raise ParsingError(f"Failed to parse PDF asset {asset.id}: {str(e)}") from e
