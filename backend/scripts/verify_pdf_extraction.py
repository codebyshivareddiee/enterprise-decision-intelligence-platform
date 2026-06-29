"""Verify PDF text extraction fix.

Creates a PDF with known text content using fpdf2, then runs it through
the PdfParser to verify readable text is extracted (not binary garbage).

Usage:
    cd backend
    uv run python scripts/verify_pdf_extraction.py
"""

import asyncio
import logging
import sys
import tempfile

# Configure logging to see verification output
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

# ── Known content that must survive round-trip ────────────────────
RESUME_LINES = [
    "John Smith",
    "Senior Software Engineer",
    "",
    "SUMMARY",
    "Experienced software engineer with 8+ years of expertise in Python, FastAPI,",
    "and large language model (LLM) integration. Proven track record of designing",
    "scalable microservices and AI-powered decision intelligence platforms.",
    "",
    "SKILLS",
    "Python, FastAPI, Django, PostgreSQL, MongoDB, Qdrant, Docker, Kubernetes,",
    "LangChain, OpenAI API, AWS, CI/CD",
    "",
    "EXPERIENCE",
    "Lead Engineer - XL Ventures (2022-Present)",
    "- Architected enterprise decision intelligence platform",
    "- Designed knowledge ingestion pipeline with PDF parsing, chunking, embedding",
    "- Integrated multi-agent reasoning with LangGraph",
    "",
    "Senior Developer - TechCorp (2018-2022)",
    "- Built RESTful APIs serving 10M+ requests per day",
    "- Migrated monolith to microservices architecture",
    "",
    "EDUCATION",
    "M.S. Computer Science - Stanford University (2018)",
    "B.S. Computer Science - UC Berkeley (2016)",
]


def create_test_pdf_bytes() -> bytes:
    """Create a PDF containing resume text using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for line in RESUME_LINES:
        if line == "":
            pdf.ln(5)
        else:
            pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


async def verify_pdf_parser():
    """Run the PdfParser on a test PDF and verify output."""
    from app.knowledge.parsers.pdf_parser import PdfParser
    from app.models.knowledge_asset import KnowledgeAsset
    from app.models.enums import AssetContentType, AssetStatus
    import uuid

    parser = PdfParser()

    # ── Step 1: Create a test PDF ────────────────────────────────
    logger.info("=" * 70)
    logger.info("STEP 1: Creating test PDF with known resume content")
    logger.info("=" * 70)

    pdf_bytes = create_test_pdf_bytes()
    logger.info(f"  PDF size: {len(pdf_bytes)} bytes")

    # Write to temp file (simulating what the upload endpoint does)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    logger.info(f"  Temp file: {tmp.name}")

    # ── Step 2: Create a KnowledgeAsset pointing to the file ─────
    asset = KnowledgeAsset(
        organization_id=uuid.uuid4(),
        schema_id=uuid.uuid4(),
        name="John_Smith_Resume",
        content_type=AssetContentType.PDF,
        status=AssetStatus.PENDING,
        raw_content=None,  # No text yet — parser will extract it
        file_path=tmp.name,
        uploaded_by=uuid.uuid4(),
    )

    # ── Step 3: Parse ────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 2: Running PdfParser.parse()")
    logger.info("=" * 70)

    parsed_doc = await parser.parse(asset)

    # ── Step 4: Verify ───────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 3: Verification Results")
    logger.info("=" * 70)

    logger.info(f"  Extracted text length: {len(parsed_doc.text)} chars")
    logger.info(f"  Page count: {parsed_doc.page_count}")
    logger.info(f"  Word count: {parsed_doc.document_statistics.get('word_count', 'N/A')}")
    logger.info(f"  Headings found: {parsed_doc.headings}")

    logger.info("")
    logger.info("  -- First 500 characters --")
    logger.info(f"  {parsed_doc.text[:500]}")

    # ── Assertions ───────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 4: Assertions")
    logger.info("=" * 70)

    errors = []

    # Text must contain key phrases from the resume
    for phrase in ["John Smith", "Python", "FastAPI", "Stanford University"]:
        if phrase in parsed_doc.text:
            logger.info(f"  PASS: Contains '{phrase}'")
        else:
            msg = f"  FAIL: MISSING '{phrase}' in extracted text!"
            logger.error(msg)
            errors.append(msg)

    # Must NOT contain PDF binary markers
    for marker in ["%%EOF", "%PDF", "endobj"]:
        if marker in parsed_doc.text:
            msg = f"  FAIL: FOUND binary marker '{marker}' in extracted text!"
            logger.error(msg)
            errors.append(msg)
        else:
            logger.info(f"  PASS: No binary marker '{marker}'")

    # Must have reasonable length
    if len(parsed_doc.text) > 100:
        logger.info(f"  PASS: Text length ({len(parsed_doc.text)}) > 100 chars")
    else:
        msg = f"  FAIL: Text too short: {len(parsed_doc.text)} chars"
        logger.error(msg)
        errors.append(msg)

    # Clean up
    import os
    os.unlink(tmp.name)

    return errors


async def verify_validation():
    """Verify that empty/image-only PDFs are rejected."""
    from pypdf import PdfWriter
    from app.knowledge.parsers.pdf_parser import PdfParser
    from app.knowledge.exceptions import ParsingError
    from app.models.knowledge_asset import KnowledgeAsset
    from app.models.enums import AssetContentType, AssetStatus
    import uuid

    parser = PdfParser()

    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 5: Validation - Reject empty PDFs")
    logger.info("=" * 70)

    # Create a PDF with a blank page (no text)
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    writer.write(tmp)
    tmp.close()

    asset = KnowledgeAsset(
        organization_id=uuid.uuid4(),
        schema_id=uuid.uuid4(),
        name="Empty_PDF",
        content_type=AssetContentType.PDF,
        status=AssetStatus.PENDING,
        raw_content=None,
        file_path=tmp.name,
        uploaded_by=uuid.uuid4(),
    )

    errors = []
    try:
        await parser.parse(asset)
        msg = "  FAIL: Empty PDF was NOT rejected - expected ParsingError!"
        logger.error(msg)
        errors.append(msg)
    except ParsingError as e:
        logger.info(f"  PASS: Empty PDF correctly rejected: {e}")
    finally:
        import os
        os.unlink(tmp.name)

    return errors


async def main():
    logger.info("")
    logger.info("=" * 70)
    logger.info("  PDF TEXT EXTRACTION VERIFICATION")
    logger.info("=" * 70)
    logger.info("")

    errors1 = await verify_pdf_parser()
    errors2 = await verify_validation()

    all_errors = errors1 + errors2

    logger.info("")
    logger.info("=" * 70)
    if all_errors:
        logger.error(f"FAILED: {len(all_errors)} assertion(s) failed")
        for e in all_errors:
            logger.error(f"  {e}")
        logger.info("=" * 70)
        sys.exit(1)
    else:
        logger.info("ALL VERIFICATIONS PASSED")
        logger.info("PDF text extraction is working correctly.")
        logger.info("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
