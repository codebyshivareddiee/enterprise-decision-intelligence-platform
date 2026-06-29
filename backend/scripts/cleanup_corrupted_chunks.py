"""Clean up corrupted PDF chunks from Qdrant.

Deletes all Qdrant chunks for assets that were indexed with corrupted
binary PDF data (before the PDF parser fix). After running this script,
re-upload the original PDF files through the fixed upload endpoint.

Usage:
    cd backend
    uv run python scripts/cleanup_corrupted_chunks.py
"""

import asyncio
import sys
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

from app.config.settings import Settings


# These asset IDs were identified from the decision execution logs as
# containing corrupted binary PDF data in Qdrant.
CORRUPTED_ASSET_IDS = [
    "8f385ca7-de0b-44d0-a950-fd4baa9eebe1",
    "820fd8ec-9b59-4974-ba0b-49f46963630d",
]


async def main():
    settings = Settings()

    print("=" * 70)
    print("  CORRUPTED CHUNK CLEANUP")
    print("=" * 70)
    print()
    print(f"  Qdrant URL: {settings.qdrant_url}")
    print(f"  Collection: {settings.qdrant_collection_name}")
    print(f"  Assets to clean: {len(CORRUPTED_ASSET_IDS)}")
    print()

    client = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )

    try:
        for asset_id in CORRUPTED_ASSET_IDS:
            print(f"  Deleting chunks for asset {asset_id}...")
            await client.delete(
                collection_name=settings.qdrant_collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="asset_id",
                                match=MatchValue(value=asset_id),
                            )
                        ]
                    )
                ),
            )
            print(f"    DONE - Corrupted chunks deleted for {asset_id}")

        print()
        print("=" * 70)
        print("  ALL CORRUPTED CHUNKS DELETED")
        print()
        print("  Next steps:")
        print("  1. Delete the corrupted assets from MongoDB (optional)")
        print("  2. Re-upload the original PDF files via the /knowledge/upload endpoint")
        print("  3. The fixed PdfParser will now extract readable text with pypdf")
        print("  4. Run a decision to verify readable chunks are retrieved")
        print("=" * 70)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
