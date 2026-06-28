"""Parser models."""

from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    """A document that has been parsed to extract structural metadata."""

    text: str = Field(description="The full text content of the document.")
    filename: str | None = Field(
        default=None, description="The name of the original file."
    )
    extension: str | None = Field(
        default=None, description="The extension of the original file."
    )
    page_count: int | None = Field(
        default=None, description="The total number of pages."
    )
    document_statistics: dict[str, int | float] = Field(
        default_factory=dict,
        description="Statistics like word count, character count, etc.",
    )
    headings: list[str] = Field(
        default_factory=list, description="List of detected headings."
    )
    table_of_contents: str | None = Field(
        default=None, description="Extracted table of contents, if any."
    )
    section_titles: list[str] = Field(
        default_factory=list, description="Extracted section titles."
    )
    sampled_pages: dict[int, str] = Field(
        default_factory=dict,
        description="Smart sample of pages. Key is page number, value is page text.",
    )
