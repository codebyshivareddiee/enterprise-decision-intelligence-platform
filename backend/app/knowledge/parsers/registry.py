"""Parser registry."""

from app.knowledge.exceptions import UnsupportedFormatError
from app.knowledge.interfaces.parser import DocumentParser
from app.knowledge.parsers.pdf_parser import PdfParser
from app.knowledge.parsers.txt_parser import TxtParser
from app.models.enums import AssetContentType


class ParserRegistry:
    """Registry for obtaining the appropriate parser for an asset content type."""

    def __init__(self) -> None:
        self._parsers: dict[AssetContentType, DocumentParser] = {
            AssetContentType.TEXT: TxtParser(),
            AssetContentType.PDF: PdfParser(),
        }

    def get_parser(self, content_type: AssetContentType) -> DocumentParser:
        """Get the parser for a specific content type.

        Args:
            content_type: The format of the asset.

        Returns:
            An instance of DocumentParser.

        Raises:
            UnsupportedFormatError: If no parser exists for the format.
        """
        parser = self._parsers.get(content_type)
        if not parser:
            raise UnsupportedFormatError(
                f"No parser registered for content type: {content_type}"
            )
        return parser
