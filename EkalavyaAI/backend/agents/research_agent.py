"""
EkalavyaAI — Agent 2: Research Agent
Hybrid RAG: Pinecone vector search + ElasticSearch BM25 → Cohere Rerank

Responsibilities:
- Retrieve verified educational content from ICAI/NCERT sources
- Hybrid retrieval for maximum coverage
- Cohere reranking for quality
- Source citation tracking
"""
import logging
from typing import Optional

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Agent 2 — Research Agent

    Primary: GPT-4o (OpenRouter) for synthesis
    Backup 1: DeepSeek V3 (OpenRouter — free tier)
    Backup 2: Gemini 1.5 Flash (Google — free)
    Free Fallback: Llama 3.1 70B (Groq)
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.RESEARCH_MODEL_PRIMARY,
                provider="openrouter",
                max_tokens=4096,
                temperature=0.2,
            ),
            ModelConfig(
                model=settings.RESEARCH_MODEL_BACKUP1,
                provider="openrouter",
                max_tokens=4096,
                temperature=0.2,
            ),
            ModelConfig(
                model="google/gemini-flash-1.5",
                provider="openrouter",
                max_tokens=4096,
                temperature=0.2,
            ),
            ModelConfig(
                model=settings.RESEARCH_MODEL_FREE,
                provider="groq",
                max_tokens=3000,
                temperature=0.2,
            ),
        ]
        super().__init__("ResearchAgent", fallback_chain)

    async def run(self, state: dict) -> list:
        """
        Retrieve and rank educational content for the given chapter.
        Returns top-8 ranked chunks with source citations.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        subject = state.get("subject", "")
        chapter_name = state.get("chapter_name", "")
        chapter_id = state.get("chapter_id")
        query = state.get("query") or f"{chapter_name} {subject} {exam}"

        logger.info(f"[ResearchAgent] Retrieving for: {chapter_name} ({exam})")

        # Step 1: Parallel vector + BM25 retrieval
        vector_results, bm25_results = await self._parallel_retrieval(
            query=query,
            exam=exam,
            chapter_id=chapter_id,
        )

        # Step 2: Merge results
        all_chunks = self._merge_results(vector_results, bm25_results)

        if not all_chunks:
            logger.warning(f"[ResearchAgent] No chunks found for {chapter_name}")
            return []

        # Step 3: Cohere Rerank
        reranked = await self._rerank_with_cohere(query, all_chunks)

        # Step 4: Return top-8
        top_chunks = reranked[:settings.RAG_FINAL_TOP_K]
        logger.info(f"[ResearchAgent] Retrieved {len(top_chunks)} chunks after reranking")
        return top_chunks

    async def _parallel_retrieval(
        self, query: str, exam: str, chapter_id: Optional[str]
    ) -> tuple:
        """Run Pinecone and ElasticSearch retrievals in parallel."""
        import asyncio
        vector_task = self._vector_search(query, exam, chapter_id)
        bm25_task = self._bm25_search(query, exam, chapter_id)
        results = await asyncio.gather(vector_task, bm25_task, return_exceptions=True)

        vector_results = results[0] if not isinstance(results[0], Exception) else []
        bm25_results = results[1] if not isinstance(results[1], Exception) else []
        return vector_results, bm25_results

    async def _vector_search(
        self, query: str, exam: str, chapter_id: Optional[str]
    ) -> list:
        """Pinecone semantic vector search."""
        try:
            from rag.embeddings import EmbeddingService
            from pinecone import Pinecone

            embedder = EmbeddingService()
            query_vector = await embedder.embed_text(query)

            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            index = pc.Index(settings.PINECONE_INDEX_NAME)

            # Build filter
            filter_dict = {"exam": {"$eq": exam}}
            if chapter_id:
                filter_dict["chapter_id"] = {"$eq": chapter_id}

            results = index.query(
                vector=query_vector,
                top_k=settings.RAG_TOP_K_VECTOR,
                filter=filter_dict,
                include_metadata=True,
            )

            chunks = []
            for match in results.get("matches", []):
                chunks.append({
                    "text": match["metadata"].get("text", ""),
                    "score": match["score"],
                    "source": "vector",
                    "metadata": match["metadata"],
                    "chunk_id": match["id"],
                })
            return chunks

        except Exception as e:
            logger.error(f"[ResearchAgent] Vector search error: {e}")
            return []

    async def _bm25_search(
        self, query: str, exam: str, chapter_id: Optional[str]
    ) -> list:
        """ElasticSearch BM25 keyword search."""
        try:
            from elasticsearch import AsyncElasticsearch

            es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])

            # Build ES query
            es_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["text^2", "metadata.topic", "metadata.source"],
                                    "type": "best_fields",
                                }
                            }
                        ],
                        "filter": [{"term": {"metadata.exam": exam}}],
                    }
                },
                "size": settings.RAG_TOP_K_BM25,
            }

            if chapter_id:
                es_query["query"]["bool"]["filter"].append(
                    {"term": {"metadata.chapter_id": chapter_id}}
                )

            response = await es.search(index=settings.ELASTICSEARCH_INDEX, body=es_query)
            await es.close()

            chunks = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                chunks.append({
                    "text": source.get("text", ""),
                    "score": hit["_score"],
                    "source": "bm25",
                    "metadata": source.get("metadata", {}),
                    "chunk_id": hit["_id"],
                })
            return chunks

        except Exception as e:
            logger.error(f"[ResearchAgent] BM25 search error: {e}")
            return []

    def _merge_results(self, vector_results: list, bm25_results: list) -> list:
        """Merge and deduplicate results from both sources."""
        seen_ids = set()
        merged = []

        # Add all vector results first
        for chunk in vector_results:
            cid = chunk.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                merged.append(chunk)

        # Add unique BM25 results
        for chunk in bm25_results:
            cid = chunk.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                merged.append(chunk)

        return merged

    async def _rerank_with_cohere(self, query: str, chunks: list) -> list:
        """Use Cohere Rerank to sort by relevance."""
        try:
            import cohere
            co = cohere.AsyncClient(api_key=settings.COHERE_API_KEY)

            documents = [chunk["text"] for chunk in chunks if chunk.get("text")]
            if not documents:
                return chunks

            results = await co.rerank(
                query=query,
                documents=documents,
                top_n=min(settings.RAG_FINAL_TOP_K, len(documents)),
                model="rerank-english-v3.0",
            )

            reranked = []
            for result in results.results:
                chunk = chunks[result.index].copy()
                chunk["rerank_score"] = result.relevance_score
                reranked.append(chunk)

            # Sort by credibility (ICAI > NCERT > coaching notes)
            return self._sort_by_credibility(reranked)

        except Exception as e:
            logger.warning(f"[ResearchAgent] Cohere rerank failed: {e} — using raw order")
            return chunks[:settings.RAG_FINAL_TOP_K]

    def _sort_by_credibility(self, chunks: list) -> list:
        """Sort chunks by source credibility."""
        credibility_order = {"ICAI": 1, "NCERT": 2, "NEET_OFFICIAL": 2, "COACHING": 3}

        def credibility_key(chunk):
            source = chunk.get("metadata", {}).get("source_type", "COACHING")
            score = chunk.get("rerank_score", 0)
            cred = credibility_order.get(source, 4)
            return (cred, -score)

        return sorted(chunks, key=credibility_key)
