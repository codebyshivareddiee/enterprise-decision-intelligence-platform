"""PDF document parser."""

import logging
import re

from pypdf import PdfReader

from app.knowledge.exceptions import ParsingError
from app.knowledge.interfaces.parser import DocumentParser
from app.knowledge.parsers.models import ParsedDocument
from app.models.knowledge_asset import KnowledgeAsset

logger = logging.getLogger(__name__)

# PDFs yielding fewer characters than this are rejected as unreadable
# (likely scanned/image-only documents).
MIN_EXTRACTED_TEXT_LENGTH = 50


class PdfParser(DocumentParser):
    """Parses PDF KnowledgeAssets using pypdf."""

    async def parse(self, asset: KnowledgeAsset) -> ParsedDocument:
        """Parse a PDF KnowledgeAsset by extracting text with pypdf.

        Reads from ``asset.file_path`` (a temp file written by the upload
        endpoint). Validates that meaningful text was extracted before
        returning.

        Args:
            asset: The PDF KnowledgeAsset. Must have ``file_path`` set to
                   a readable PDF file on disk.

        Returns:
            The extracted ParsedDocument containing readable text.

        Raises:
            ParsingError: If the file cannot be read, pypdf fails, or the
                          PDF yields no meaningful text.
        """
        try:
            if not asset.file_path:
                raise ParsingError(
                    f"No file_path for PDF asset {asset.id}. "
                    f"PDF files must be uploaded as binary files."
                )

            # ----------------------------------------------------------
            # 1. Extract text from every page using pypdf
            # ----------------------------------------------------------
            reader = PdfReader(asset.file_path)

            pages_text: list[str] = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)

            full_text = "\n\n".join(pages_text)

            # ----------------------------------------------------------
            # 2. Normalize whitespace
            # ----------------------------------------------------------
            # Collapse horizontal whitespace runs (spaces/tabs) into a
            # single space, but preserve intentional line breaks.
            full_text = re.sub(r"[ \t]+", " ", full_text)
            # Collapse 3+ consecutive newlines into exactly 2
            full_text = re.sub(r"\n{3,}", "\n\n", full_text)
            full_text = full_text.strip()

            # ----------------------------------------------------------
            # 3. Validate extracted text quality
            # ----------------------------------------------------------
            if len(full_text) < MIN_EXTRACTED_TEXT_LENGTH:
                raise ParsingError(
                    f"PDF asset {asset.id} yielded only {len(full_text)} "
                    f"characters of text. The PDF may be scanned or "
                    f"image-only. Minimum required: "
                    f"{MIN_EXTRACTED_TEXT_LENGTH} characters."
                )

            # ----------------------------------------------------------
            # 4. Verification logging
            # ----------------------------------------------------------
            logger.info(
                "pdf_text_extracted | asset_id=%s | text_length=%d | "
                "first_500_chars=%.500s",
                asset.id,
                len(full_text),
                full_text[:500],
            )

            # ----------------------------------------------------------
            # 5. Build document statistics
            # ----------------------------------------------------------
            char_count = len(full_text)
            word_count = len(full_text.split())
            page_count = len(reader.pages)

            # Sampled pages: first, middle, last (or all if ≤ 3 pages)
            sampled_pages: dict[int, str] = {}
            if page_count > 3:
                sampled_pages[1] = pages_text[0].strip()
                mid = page_count // 2
                sampled_pages[mid + 1] = pages_text[mid].strip()
                sampled_pages[page_count] = pages_text[-1].strip()
            else:
                for i, pt in enumerate(pages_text):
                    sampled_pages[i + 1] = pt.strip()

            # Detect headings: lines that are ALL CAPS and short
            headings: list[str] = []
            for line in full_text.split("\n"):
                line = line.strip()
                if line and line.isupper() and 3 < len(line) < 60:
                    headings.append(line)

            return ParsedDocument(
                text=full_text,
                filename=f"{asset.name}.pdf",
                extension="pdf",
                page_count=page_count,
                document_statistics={
                    "char_count": char_count,
                    "word_count": word_count,
                },
                headings=headings,
                sampled_pages=sampled_pages,
            )

        except ParsingError:
            raise
        except Exception as e:
            raise ParsingError(
                f"Failed to parse PDF asset {asset.id}: {str(e)}"
            ) from e
