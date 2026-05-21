"""
RAG service: ingests PDF safety policy documents into ChromaDB
and answers questions using LangChain retrieval chain.
Implemented in Phase 4.
"""


class RAGService:
    def ingest_document(self, document_id: int, db) -> None:
        raise NotImplementedError("RAGService not yet implemented — Phase 4")

    def query(self, question: str, context: dict | None = None) -> str:
        raise NotImplementedError("RAGService not yet implemented — Phase 4")
