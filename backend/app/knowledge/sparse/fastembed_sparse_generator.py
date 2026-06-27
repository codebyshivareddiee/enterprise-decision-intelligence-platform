"""FastEmbed sparse vector generator."""

import asyncio
from typing import cast
from fastembed import SparseTextEmbedding
from app.knowledge.interfaces.sparse import SparseGenerator
from app.knowledge.exceptions import SparseGenerationError

class FastEmbedSparseGenerator(SparseGenerator):
    """Generates sparse vectors using FastEmbed (SPLADE/BM25)."""

    def __init__(self, model_name: str = "Qdrant/bm25") -> None:
        """Initialize the FastEmbed sparse generator.
        
        Args:
            model_name: The FastEmbed sparse model to use (default: Qdrant/bm25).
        """
        self.model_name = model_name
        # Instantiating the model might download weights, but it is synchronous
        try:
            self.model = SparseTextEmbedding(model_name=self.model_name)
        except Exception as e:
            raise SparseGenerationError(f"Failed to initialize FastEmbed model {model_name}: {str(e)}") from e

    async def generate_sparse_chunks(self, chunks: list[str]) -> list[tuple[list[int], list[float]]]:
        """Generate sparse vectors for a batch of text chunks.

        Args:
            chunks: A list of text strings.

        Returns:
            A list of tuples containing (indices, values) for the sparse vector.

        Raises:
            SparseGenerationError: If sparse vector generation fails.
        """
        if not chunks:
            return []
            
        try:
            # fastembed is synchronous, so we run it in an executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            
            def _embed() -> list[tuple[list[int], list[float]]]:
                results = list(self.model.embed(chunks))
                # FastEmbed returns an object with .indices and .values (which are numpy arrays)
                return [(result.indices.tolist(), result.values.tolist()) for result in results]

            return await loop.run_in_executor(None, _embed)
        except Exception as e:
            raise SparseGenerationError(f"Failed to generate sparse vectors for chunks: {str(e)}") from e

    async def generate_sparse_query(self, query: str) -> tuple[list[int], list[float]]:
        """Generate a sparse vector for a single search query.

        Args:
            query: The search query text.

        Returns:
            A tuple containing (indices, values) for the sparse vector.

        Raises:
            SparseGenerationError: If sparse vector generation fails.
        """
        try:
            loop = asyncio.get_running_loop()
            
            def _embed() -> tuple[list[int], list[float]]:
                # For queries, it is recommended to use the query specific method if supported, 
                # but SparseTextEmbedding standard usage for BM25 is just embed
                results = list(self.model.embed([query]))
                result = results[0]
                return (result.indices.tolist(), result.values.tolist())

            return await loop.run_in_executor(None, _embed)
        except Exception as e:
            raise SparseGenerationError(f"Failed to generate sparse vector for query: {str(e)}") from e
