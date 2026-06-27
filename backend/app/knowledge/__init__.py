"""Knowledge Layer.

This module provides the entire lifecycle for knowledge ingestion, processing,
and retrieval, hiding the complexities of parsing, embedding, and vector
database interactions behind the KnowledgeManager.
"""

from .exceptions.knowledge_exceptions import KnowledgeLayerError
from .manager.knowledge_manager import KnowledgeManager
from .models.chunk import DocumentChunk
from .models.search import MetadataFilter, SearchResult

__all__ = [
    "KnowledgeManager",
    "SearchResult",
    "MetadataFilter",
    "DocumentChunk",
    "KnowledgeLayerError",
]
