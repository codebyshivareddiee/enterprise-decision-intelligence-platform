"""Knowledge Manager."""

from uuid import UUID

from app.knowledge.exceptions import KnowledgeLayerError
from app.knowledge.interfaces.vector_store import VectorStore
from app.knowledge.manager.document_processor import DocumentProcessor
from app.knowledge.models.search import MetadataFilter, SearchResult
from app.knowledge.search.search_service import SearchService
from app.models.knowledge_asset import KnowledgeAsset


class KnowledgeManager:
    """Main interface for the Knowledge Layer.

    Coordinates the ingestion, retrieval, and lifecycle of knowledge assets.
    The rest of the platform should only communicate with this manager.
    """

    def __init__(
        self,
        document_processor: DocumentProcessor,
        vector_store: VectorStore,
        search_service: SearchService,
    ) -> None:
        """Initialize the knowledge manager.

        Args:
            document_processor: Coordinates parsing, chunking, and embedding.
            vector_store: The vector database for storing/deleting chunks.
            search_service: The service to perform hybrid search.
        """
        self.document_processor = document_processor
        self.vector_store = vector_store
        self.search_service = search_service

    async def index_asset(self, asset: KnowledgeAsset) -> list[str]:
        """Index a new knowledge asset into the vector store.

        Args:
            asset: The KnowledgeAsset domain object to index.

        Returns:
            A list of Qdrant point IDs representing the inserted chunks.

        Raises:
            KnowledgeLayerError: If the ingestion fails.
        """
        try:
            prepared_chunks = await self.document_processor.process(asset)
            point_ids = await self.vector_store.upsert_chunks(prepared_chunks)
            return point_ids
        except Exception as e:
            if not isinstance(e, KnowledgeLayerError):
                raise KnowledgeLayerError(
                    f"Failed to index asset {asset.id}: {str(e)}"
                ) from e
            raise

    async def retrieve(
        self,
        organization_id: UUID,
        selected_asset_ids: list[UUID] | None,
        query: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Retrieve relevant knowledge chunks for a query.

        Args:
            organization_id: The ID of the organization to scope the search.
            selected_asset_ids: Optional list of specific asset IDs to filter by.
            query: The search query text.
            top_k: The number of results to return.

        Returns:
            A list of SearchResult objects containing the relevant chunks.

        Raises:
            KnowledgeLayerError: If retrieval fails.
        """
        try:
            filters = MetadataFilter(
                organization_id=organization_id,
                selected_asset_ids=selected_asset_ids,
            )
            return await self.search_service.search(
                query=query, filters=filters, top_k=top_k
            )
        except Exception as e:
            if not isinstance(e, KnowledgeLayerError):
                raise KnowledgeLayerError(
                    f"Failed to retrieve chunks for query '{query}': {str(e)}"
                ) from e
            raise

    async def delete_asset(self, asset_id: UUID) -> None:
        """Delete all indexed chunks for a given asset.

        Args:
            asset_id: The ID of the asset to remove from the vector store.

        Raises:
            KnowledgeLayerError: If deletion fails.
        """
        try:
            await self.vector_store.delete_by_asset_id(asset_id)
        except Exception as e:
            if not isinstance(e, KnowledgeLayerError):
                raise KnowledgeLayerError(
                    f"Failed to delete asset {asset_id} from vector store: {str(e)}"
                ) from e
            raise

    async def reindex_asset(self, asset: KnowledgeAsset) -> list[str]:
        """Re-index an existing knowledge asset.

        This will delete any existing chunks for the asset and insert new ones.

        Args:
            asset: The KnowledgeAsset domain object to re-index.

        Returns:
            A list of new Qdrant point IDs representing the inserted chunks.

        Raises:
            KnowledgeLayerError: If re-indexing fails.
        """
        try:
            await self.delete_asset(asset.id)
            return await self.index_asset(asset)
        except Exception as e:
            if not isinstance(e, KnowledgeLayerError):
                raise KnowledgeLayerError(
                    f"Failed to reindex asset {asset.id}: {str(e)}"
                ) from e
            raise
