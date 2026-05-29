"""
RAG service: ingests PDF safety policy documents into ChromaDB
and answers questions using semantic retrieval.

Dependencies (install when needed):
  pip install chromadb langchain-community langchain-openai
  pip install sentence-transformers  # for local embeddings (no API key needed)

The service degrades gracefully:
  - If chromadb is not installed: ingest/query return False/"" with a warning
  - If no embedder is available: same
  - If a document fails to parse: logs error, returns False

Entry points:
  rag_service.ingest_document(document_id, file_path) → bool
  rag_service.query(question, n_results=4) → str  (empty if unavailable)
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self) -> None:
        self._client     = None
        self._collection = None
        self._embedder   = None

    # ── Lazy init ──────────────────────────────────────────────────────────────

    def _init_chroma(self) -> bool:
        if self._client is not None:
            return True
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            from app.config import settings

            self._client = chromadb.PersistentClient(
                path=settings.vector_db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=settings.vector_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialised at '%s'", settings.vector_db_path)
            return True
        except ImportError:
            logger.warning("chromadb not installed — RAG disabled. Run: pip install chromadb")
            return False
        except Exception as exc:
            logger.warning("ChromaDB init failed: %s", exc)
            return False

    def _get_embedder(self):
        if self._embedder is not None:
            return self._embedder

        # Try sentence-transformers (free, local, no API key needed)
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self._embedder = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )
            logger.info("Using HuggingFace embeddings (all-MiniLM-L6-v2)")
            return self._embedder
        except Exception:
            pass

        # Fall back to OpenAI embeddings if API key is set
        try:
            from langchain_openai import OpenAIEmbeddings
            from app.config import settings
            if settings.llm_api_key:
                self._embedder = OpenAIEmbeddings(api_key=settings.llm_api_key)
                logger.info("Using OpenAI embeddings")
                return self._embedder
        except Exception:
            pass

        logger.warning(
            "No embedder available. Install sentence-transformers: "
            "pip install sentence-transformers"
        )
        return None

    # ── Public API ─────────────────────────────────────────────────────────────

    def ingest_document(self, document_id: int, file_path: str) -> bool:
        """
        Chunk a PDF and store embeddings in ChromaDB.
        Returns True on success, False on any failure.
        """
        if not self._init_chroma():
            return False

        embedder = self._get_embedder()
        if embedder is None:
            return False

        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            loader = PyPDFLoader(file_path)
            docs   = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=512, chunk_overlap=64
            )
            chunks = splitter.split_documents(docs)

            if not chunks:
                logger.warning("document_id=%s produced no chunks.", document_id)
                return False

            texts      = [c.page_content for c in chunks]
            embeddings = embedder.embed_documents(texts)
            ids        = [f"doc{document_id}_chunk{i}" for i in range(len(texts))]
            metadatas  = [
                {"document_id": document_id, "page": c.metadata.get("page", 0)}
                for c in chunks
            ]

            self._collection.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
            )
            logger.info(
                "Ingested document_id=%s  chunks=%d", document_id, len(chunks)
            )
            return True

        except ImportError as exc:
            logger.warning(
                "Missing dependency for PDF ingestion: %s. "
                "Run: pip install pypdf langchain-community",
                exc,
            )
            return False
        except Exception as exc:
            logger.error(
                "Failed to ingest document_id=%s: %s", document_id, exc
            )
            return False

    def query(self, question: str, n_results: int = 4) -> str:
        """
        Retrieve the most relevant policy document chunks for a question.
        Returns concatenated text or empty string if unavailable.
        """
        if not self._init_chroma():
            return ""

        embedder = self._get_embedder()
        if embedder is None:
            return ""

        try:
            q_embedding = embedder.embed_query(question)
            results = self._collection.query(
                query_embeddings=[q_embedding],
                n_results=n_results,
            )
            if results and results.get("documents"):
                chunks = results["documents"][0]
                return "\n\n".join(chunks)
        except Exception as exc:
            logger.warning("RAG query failed: %s", exc)

        return ""

    def collection_count(self) -> int:
        """Return number of stored chunks (0 if unavailable)."""
        if not self._init_chroma() or self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0


rag_service = RAGService()
