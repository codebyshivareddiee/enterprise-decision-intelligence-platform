"""Verification script for the AI Layer."""

import asyncio

from pydantic import BaseModel

from app.ai.manager import AIManager
from app.config.settings import get_settings


class VerifySchema(BaseModel):
    message: str
    status_code: int


async def main() -> None:
    print("Initializing AIManager...")
    # Load settings to verify env vars are present (or defaults are ok)
    settings = get_settings()
    manager = AIManager()

    print("\n--- 1. Health Check ---")
    health = await manager.health_check()
    print(f"Health status: {health}")
    assert health.get("status") == "ok", "Health check failed"

    print("\n--- 2. Plain Text Generation ---")
    prompt = "Return only the word SUCCESS"
    print(f"Prompt: {prompt}")
    text_result = await manager.generate(prompt=prompt, temperature=0.0)
    print(f"Result: {text_result}")

    print("\n--- 3. Structured JSON Generation ---")
    prompt_json = "Create a response with message='All good' and status_code=200."
    print(f"Prompt: {prompt_json}")
    json_result = await manager.generate(
        prompt=prompt_json, response_schema=VerifySchema, temperature=0.0
    )
    print(f"Result type: {type(json_result)}")
    print(f"Result data: {json_result}")

    assert isinstance(json_result, VerifySchema), "Result is not of type VerifySchema"
    # Note: AI might rephrase the message, but it should be a VerifySchema.

    print("\n--- 4. Embeddings ---")
    texts = ["Decision Intelligence Platform", "Enterprise AI"]
    print(f"Texts: {texts}")
    embeddings = await manager.embed(texts)
    print(f"Generated {len(embeddings)} embeddings.")
    if embeddings:
        print(f"Dimension of first embedding: {len(embeddings[0])}")

    assert len(embeddings) == 2, "Expected 2 embeddings"

    print("\n[SUCCESS] All AI Layer verification steps completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
