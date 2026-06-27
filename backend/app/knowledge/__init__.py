"""Knowledge Layer.

This module provides the entire lifecycle for knowledge ingestion, processing,
and retrieval, hiding the complexities of parsing, embedding, and vector
database interactions behind the KnowledgeManager.
"""

from .manager.knowledge_manager import KnowledgeManager
from .models.search import SearchResult, MetadataFilter
from .models.chunk import DocumentChunk
from .exceptions.knowledge_exceptions import KnowledgeLayerError

__all__ = [
    "KnowledgeManager",
    "SearchResult",
    "MetadataFilter",
    "DocumentChunk",
    "KnowledgeLayerError",
]
