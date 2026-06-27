"""Qdrant vector store implementation."""

import uuid
from typing import cast
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseVector,
    FilterSelector,
    Prefetch,
    FusionQuery,
)
from app.knowledge.interfaces.vector_store import VectorStore
from app.knowledge.models.chunk import PreparedChunk
from app.knowledge.models.search import MetadataFilter, SearchResult
from app.knowledge.exceptions import VectorStoreError

class QdrantStore(VectorStore):
    """Vector store implementation using Qdrant."""

    def __init__(
        self, 
        client: AsyncQdrantClient, 
        collection_name: str = "knowledge_vectors",
        dense_vector_name: str = "dense",
        sparse_vector_name: str = "sparse",
    ) -> None:
        """Initialize the Qdrant store.
        
        Args:
            client: The async Qdrant client.
            collection_name: The name of the collection.
            dense_vector_name: Name of the dense vector field.
            sparse_vector_name: Name of the sparse vector field.
        """
        self.client = client
        self.collection_name = collection_name
        self.dense_vector_name = dense_vector_name
        self.sparse_vector_name = sparse_vector_name

    async def initialize_collection(self, dense_dim: int = 1536) -> None:
        """Create the collection if it doesn't exist."""
        try:
            exists = await self.client.collection_exists(self.collection_name)
            if not exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        self.dense_vector_name: VectorParams(
                            size=dense_dim,
                            distance=Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        self.sparse_vector_name: SparseVectorParams()
                    }
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Qdrant collection: {str(e)}") from e

    async def upsert_chunks(self, chunks: list[PreparedChunk]) -> list[str]:
        """Upsert prepared chunks into the vector store."""
        if not chunks:
            return []
            
        try:
            points = []
            point_ids = []
            
            for prepared in chunks:
                point_ids.append(prepared.chunk.chunk_id)
                points.append(
                    PointStruct(
                        id=prepared.chunk.chunk_id,
                        vector={
                            self.dense_vector_name: prepared.dense_vector,
                            self.sparse_vector_name: SparseVector(
                                indices=prepared.sparse_indices,
                                values=prepared.sparse_values,
                            ),
                        },
                        payload={
                            "asset_id": str(prepared.chunk.asset_id),
                            "chunk_index": prepared.chunk.chunk_index,
                            "content": prepared.chunk.content,
                            **prepared.chunk.metadata,
                        }
                    )
                )
                
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return point_ids
        except Exception as e:
            raise VectorStoreError(f"Failed to upsert chunks to Qdrant: {str(e)}") from e

    async def search(
        self, 
        dense_vector: list[float], 
        sparse_vector: tuple[list[int], list[float]], 
        filters: MetadataFilter, 
        top_k: int = 10
    ) -> list[SearchResult]:
        """Perform a hybrid search in the vector store."""
        try:
            must_conditions = [
                FieldCondition(
                    key="organization_id",
                    match=MatchValue(value=str(filters.organization_id))
                )
            ]
            
            if filters.selected_asset_ids:
                # We do an OR over the selected assets, or an IN condition if supported, 
                # but in qdrant MatchAny is essentially IN.
                must_conditions.append(
                    FieldCondition(
                        key="asset_id",
                        match=MatchValue(value=[str(aid) for aid in filters.selected_asset_ids]) # type: ignore
                    )
                )

            filter_query = Filter(must=must_conditions) # type: ignore
            
            # Use Qdrant's native hybrid search with prefetch and RRF fusion
            results = await self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using=self.dense_vector_name,
                        limit=top_k,
                        filter=filter_query,
                    ),
                    Prefetch(
                        query=SparseVector(indices=sparse_vector[0], values=sparse_vector[1]),
                        using=self.sparse_vector_name,
                        limit=top_k,
                        filter=filter_query,
                    )
                ],
                query=FusionQuery.RRF,
                limit=top_k,
                with_payload=True,
            )
            
            from app.knowledge.models.chunk import DocumentChunk
            
            final_results = []
            for hit in results.points:
                payload = cast(dict, hit.payload)
                asset_id = uuid.UUID(payload["asset_id"])
                
                # Reconstruct chunk
                metadata = {k: v for k, v in payload.items() if k not in ["asset_id", "chunk_index", "content"]}
                
                chunk = DocumentChunk(
                    chunk_id=str(hit.id),
                    asset_id=asset_id,
                    chunk_index=payload["chunk_index"],
                    content=payload["content"],
                    metadata=metadata
                )
                
                final_results.append(SearchResult(chunk=chunk, score=hit.score))
                
            return final_results
        except Exception as e:
            raise VectorStoreError(f"Failed to search Qdrant: {str(e)}") from e

    async def delete_by_asset_id(self, asset_id: uuid.UUID) -> None:
        """Delete all chunks associated with a specific KnowledgeAsset."""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="asset_id",
                                match=MatchValue(value=str(asset_id))
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to delete chunks for asset {asset_id}: {str(e)}") from e
