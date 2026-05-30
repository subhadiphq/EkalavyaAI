"""
EkalavyaAI — Embedding Service
voyage-2 embeddings for semantic search (1024-dim).
"""
import logging
from typing import List

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """voyage-2 embedding model wrapper with caching."""

    def __init__(self):
        self._client = None
        self._redis = None

    def _get_client(self):
        if not self._client:
            import voyageai
            self._client = voyageai.AsyncClient(api_key=settings.OPENROUTER_API_KEY)
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text query."""
        # Check Redis cache
        cache_key = f"embed:{hash(text[:100])}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            import voyageai
            client = voyageai.AsyncClient()
            result = await client.embed([text], model="voyage-2", input_type="query")
            embedding = result.embeddings[0]
            await self._cache_embedding(cache_key, embedding)
            return embedding
        except Exception as e:
            logger.warning(f"voyage-2 failed: {e} — falling back to OpenAI ada-002")
            return await self._embed_fallback([text], "query")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of documents."""
        try:
            import voyageai
            client = voyageai.AsyncClient()
            # Process in batches of 128 (voyage limit)
            all_embeddings = []
            for i in range(0, len(texts), 128):
                batch = texts[i:i + 128]
                result = await client.embed(batch, model="voyage-2", input_type="document")
                all_embeddings.extend(result.embeddings)
            return all_embeddings
        except Exception as e:
            logger.warning(f"voyage-2 batch failed: {e} — using fallback")
            return await self._embed_fallback_batch(texts)

    async def _embed_fallback(self, texts: List[str], input_type: str) -> List[float]:
        """Fallback to OpenAI text-embedding-3-small via OpenRouter."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        response = await client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=texts,
        )
        return response.data[0].embedding

    async def _embed_fallback_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch fallback embeddings."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        all_embeddings = []
        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]
            response = await client.embeddings.create(
                model="openai/text-embedding-3-small",
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in response.data])
        return all_embeddings

    async def _get_cached(self, key: str):
        """Get cached embedding from Redis."""
        try:
            import redis.asyncio as redis
            import json
            r = redis.from_url(settings.REDIS_URL)
            cached = await r.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    async def _cache_embedding(self, key: str, embedding: List[float]):
        """Cache embedding in Redis for 24 hours."""
        try:
            import redis.asyncio as redis
            import json
            r = redis.from_url(settings.REDIS_URL)
            await r.setex(key, 86400, json.dumps(embedding))
        except Exception:
            pass


async def init_pinecone():
    """Initialize Pinecone index on startup."""
    try:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)

        # Create knowledge index if not exists
        if settings.PINECONE_INDEX_NAME not in [i.name for i in pc.list_indexes()]:
            pc.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")

        # Create memory index if not exists
        if settings.PINECONE_MEMORY_INDEX not in [i.name for i in pc.list_indexes()]:
            pc.create_index(
                name=settings.PINECONE_MEMORY_INDEX,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info(f"Created Pinecone memory index: {settings.PINECONE_MEMORY_INDEX}")

    except Exception as e:
        logger.warning(f"Pinecone init failed (may already exist): {e}")
