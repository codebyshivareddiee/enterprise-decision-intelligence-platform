"""Knowledge Layer Exception Models."""


class KnowledgeLayerError(Exception):
    """Base exception for all Knowledge Layer errors."""

    pass


class UnsupportedFormatError(KnowledgeLayerError):
    """Raised when an asset format is not supported for parsing."""

    pass


class ParsingError(KnowledgeLayerError):
    """Raised when parsing an asset fails."""

    pass


class ChunkingError(KnowledgeLayerError):
    """Raised when chunking a document fails."""

    pass


class EmbeddingError(KnowledgeLayerError):
    """Raised when generating embeddings fails."""

    pass


class SparseGenerationError(KnowledgeLayerError):
    """Raised when generating sparse vectors fails."""

    pass


class VectorStoreError(KnowledgeLayerError):
    """Raised when an operation on the vector store fails."""

    pass
