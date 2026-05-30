"""
EkalavyaAI — RAG Ingestion Pipeline
Processes ICAI/NCERT PDFs into searchable vector chunks.

Pipeline:
1. PDF parsing (PyMuPDF + Gemini Vision for tables/diagrams)
2. Semantic chunking (300-600 tokens, sentence-boundary aware)
3. Metadata enrichment (exam, subject, chapter, page, source_type)
4. voyage-2 embeddings
5. Upsert to Pinecone + ElasticSearch
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Iterator

from config import settings

logger = logging.getLogger(__name__)


class PDFIngestionPipeline:
    """
    Complete RAG ingestion pipeline for educational PDFs.
    Run offline — not called during student sessions.
    """

    SOURCE_TYPE_MAP = {
        "icai": "ICAI",
        "ncert": "NCERT",
        "neet": "NEET_OFFICIAL",
        "coaching": "COACHING",
    }

    def __init__(self):
        self.embedder = None  # Lazy init
        self.pinecone_index = None
        self.es_client = None

    async def ingest_directory(self, directory: str, exam: str, subject: str):
        """Ingest all PDFs in a directory."""
        pdf_dir = Path(directory)
        pdfs = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdfs)} PDFs to ingest for {exam}/{subject}")

        for pdf_path in pdfs:
            try:
                await self.ingest_pdf(str(pdf_path), exam, subject)
                logger.info(f"✅ Ingested: {pdf_path.name}")
            except Exception as e:
                logger.error(f"❌ Failed to ingest {pdf_path.name}: {e}")

    async def ingest_pdf(self, pdf_path: str, exam: str, subject: str):
        """Ingest a single PDF into the knowledge base."""
        logger.info(f"Ingesting: {pdf_path}")

        # Step 1: Parse PDF
        raw_pages = await self._parse_pdf(pdf_path)
        logger.info(f"Parsed {len(raw_pages)} pages")

        # Step 2: Detect chapter structure
        chapters = self._detect_chapters(raw_pages)

        # Step 3: Chunk into semantic units
        all_chunks = []
        for chapter_info, pages in chapters.items():
            text = "\n\n".join(p["text"] for p in pages)
            chunks = list(self._semantic_chunk(text))
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "metadata": {
                        "exam": exam,
                        "subject": subject,
                        "chapter_name": chapter_info,
                        "source": Path(pdf_path).name,
                        "source_type": self._detect_source_type(pdf_path),
                        "page": pages[0]["page"] if pages else 0,
                        "chunk_index": i,
                    }
                })

        logger.info(f"Created {len(all_chunks)} chunks")

        # Step 4: Embed + upsert in batches
        await self._embed_and_upsert(all_chunks)

    async def _parse_pdf(self, pdf_path: str) -> list:
        """Parse PDF with PyMuPDF, use Gemini Vision for complex pages."""
        import fitz  # PyMuPDF

        pages = []
        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc):
            text = page.get_text("text")

            # If page has tables/images and little text → use Gemini Vision
            if len(text.strip()) < 100 and page.get_images():
                text = await self._extract_with_vision(page, page_num)

            pages.append({
                "page": page_num + 1,
                "text": text.strip(),
                "has_tables": "│" in text or "+-" in text,
            })

        doc.close()
        return [p for p in pages if p["text"]]

    async def _extract_with_vision(self, page, page_num: int) -> str:
        """Use Gemini 1.5 Pro Vision to extract text from complex pages."""
        try:
            import fitz
            import base64

            # Render page as image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for clarity
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode()

            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )

            response = await client.chat.completions.create(
                model="google/gemini-pro-1.5",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}"
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Extract all text from this educational textbook page. "
                                    "Preserve tables, formulas, and numbered lists. "
                                    "Return only the extracted text."
                                ),
                            },
                        ],
                    }
                ],
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Vision extraction failed for page {page_num}: {e}")
            return ""

    def _detect_chapters(self, pages: list) -> dict:
        """Group pages by chapter using heading detection."""
        import re

        chapters = {}
        current_chapter = "Introduction"

        chapter_patterns = [
            r"^Chapter\s+\d+[:\s]+(.+)$",
            r"^\d+\.\s+([A-Z][A-Za-z\s]+)$",
            r"^UNIT\s+\d+[:\s]+(.+)$",
        ]

        for page in pages:
            text = page["text"]
            first_line = text.split("\n")[0].strip()

            for pattern in chapter_patterns:
                match = re.match(pattern, first_line, re.IGNORECASE)
                if match:
                    current_chapter = match.group(1).strip()
                    break

            if current_chapter not in chapters:
                chapters[current_chapter] = []
            chapters[current_chapter].append(page)

        return chapters

    def _semantic_chunk(self, text: str) -> Iterator[str]:
        """
        Split text into semantic chunks of 300-600 tokens.
        Splits at sentence/paragraph boundaries.
        """
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_chunk = ""
        current_tokens = 0
        target_tokens = 400
        max_tokens = 600
        overlap_tokens = 50

        for para in paragraphs:
            para_tokens = len(para.split()) * 1.3  # Rough token estimate

            if current_tokens + para_tokens > max_tokens and current_chunk:
                yield current_chunk.strip()
                # Keep last few sentences as overlap
                sentences = current_chunk.split(". ")
                overlap = ". ".join(sentences[-2:]) if len(sentences) >= 2 else ""
                current_chunk = overlap + "\n\n" + para if overlap else para
                current_tokens = len(current_chunk.split()) * 1.3
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_tokens += para_tokens

            # Yield if at target size
            if current_tokens >= target_tokens and para.endswith("."):
                yield current_chunk.strip()
                current_chunk = ""
                current_tokens = 0

        if current_chunk.strip():
            yield current_chunk.strip()

    async def _embed_and_upsert(self, chunks: list):
        """Embed chunks and upsert to Pinecone + ElasticSearch."""
        from rag.embeddings import EmbeddingService

        if not self.embedder:
            self.embedder = EmbeddingService()

        # Process in batches of 50
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Get embeddings for batch
            texts = [c["text"] for c in batch]
            embeddings = await self.embedder.embed_batch(texts)

            # Upsert to Pinecone
            await self._upsert_pinecone(batch, embeddings, i)

            # Index to ElasticSearch
            await self._index_elasticsearch(batch, i)

            logger.info(f"Indexed batch {i//batch_size + 1}: {len(batch)} chunks")

    async def _upsert_pinecone(self, chunks: list, embeddings: list, offset: int):
        """Upsert vectors to Pinecone."""
        try:
            from pinecone import Pinecone

            if not self.pinecone_index:
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self.pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)

            vectors = [
                {
                    "id": f"chunk_{offset + i}_{hash(c['text']) % 1000000}",
                    "values": emb,
                    "metadata": {
                        **c["metadata"],
                        "text": c["text"][:1000],  # Metadata limit
                    },
                }
                for i, (c, emb) in enumerate(zip(chunks, embeddings))
            ]

            self.pinecone_index.upsert(vectors=vectors)
        except Exception as e:
            logger.error(f"Pinecone upsert error: {e}")

    async def _index_elasticsearch(self, chunks: list, offset: int):
        """Index chunks to ElasticSearch for BM25 retrieval."""
        try:
            from elasticsearch import AsyncElasticsearch

            if not self.es_client:
                self.es_client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])

            operations = []
            for i, chunk in enumerate(chunks):
                doc_id = f"chunk_{offset + i}_{hash(chunk['text']) % 1000000}"
                operations.append({"index": {"_index": settings.ELASTICSEARCH_INDEX, "_id": doc_id}})
                operations.append({"text": chunk["text"], "metadata": chunk["metadata"]})

            if operations:
                await self.es_client.bulk(operations=operations)
        except Exception as e:
            logger.error(f"ElasticSearch indexing error: {e}")

    def _detect_source_type(self, pdf_path: str) -> str:
        """Detect source type from filename."""
        filename = Path(pdf_path).name.lower()
        for key, value in self.SOURCE_TYPE_MAP.items():
            if key in filename:
                return value
        return "EDUCATIONAL"
