"""Chunking strategy factory."""

from app.knowledge.analyzer.models import ChunkingConfig
from app.knowledge.chunkers.heading_chunker import HeadingChunker
from app.knowledge.chunkers.single_document_chunker import SingleDocumentChunker
from app.knowledge.chunkers.sliding_window_chunker import SlidingWindowChunker
from app.knowledge.interfaces.chunker import DocumentChunker


class ChunkingStrategyFactory:
    """Creates the appropriate chunker based on strategy name and config."""

    @staticmethod
    def create(strategy_name: str, config: ChunkingConfig) -> DocumentChunker:
        """Create a chunker instance.

        Args:
            strategy_name: Name of the strategy (e.g. 'HeadingChunker').
            config: ChunkingConfig containing size and overlap.

        Returns:
            An instance of a DocumentChunker.
        """
        if strategy_name == "SingleDocumentChunker":
            return SingleDocumentChunker(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )
        elif strategy_name == "HeadingChunker":
            return HeadingChunker(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )
        elif strategy_name == "SlidingWindowChunker":
            return SlidingWindowChunker(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )
        else:
            # Fallback to sliding window
            return SlidingWindowChunker(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )
