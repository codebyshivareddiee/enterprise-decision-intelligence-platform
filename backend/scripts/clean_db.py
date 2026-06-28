import asyncio
import os
import sys
import argparse
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from dotenv import load_dotenv
from app.config.settings import get_settings
from app.persistence.mongodb import client as mongo_client
from bson import ObjectId

async def clean_db(drop_all: bool = False):
    load_dotenv(dotenv_path=backend_dir / ".env")
    settings = get_settings()
    await mongo_client.connect(settings.mongodb_uri)
    db = mongo_client.get_mongo_client()[settings.mongodb_db_name]
    
    collections = await db.list_collection_names()
    for coll_name in collections:
        coll = db[coll_name]
        
        if drop_all:
            print(f"Clearing collection: {coll_name}")
            await coll.delete_many({})
        else:
            # Delete documents where _id is ObjectId
            cursor = coll.find({})
            async for doc in cursor:
                if isinstance(doc.get("_id"), ObjectId):
                    print(f"Deleting malformed doc from {coll_name}: {doc['_id']}")
                    await coll.delete_one({"_id": doc["_id"]})
                
    print("Cleanup complete.")
    await mongo_client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean MongoDB database.")
    parser.add_argument("--all", action="store_true", help="Drop all documents from all collections")
    args = parser.parse_args()
    
    asyncio.run(clean_db(drop_all=args.all))
