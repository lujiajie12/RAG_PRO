from __future__ import annotations

from flask import current_app

from ..rag.cleaner import TextCleaner
from ..rag.indexer import KnowledgeIndexer
from ..rag.loaders import DocumentLoaderFactory as SourceDocumentLoaderFactory
from ..rag.metadata import DocumentMetadataExtractor
from ..rag.splitter import ParentChildSplitter
from ..repos.documents import DocumentRepository
from .parsers import ParserRegistry
from .storage import ObjectStorage


class IngestionPipeline:
    def __init__(
        self,
        repo: DocumentRepository | None = None,
        parser_registry: ParserRegistry | None = None,
        source_loader_factory: SourceDocumentLoaderFactory | None = None,
        cleaner: TextCleaner | None = None,
        metadata_extractor: DocumentMetadataExtractor | None = None,
        splitter: ParentChildSplitter | None = None,
        indexer: KnowledgeIndexer | None = None,
        storage: ObjectStorage | None = None,
    ) -> None:
        self.repo = repo or DocumentRepository()
        self.parser_registry = parser_registry or ParserRegistry()
        self.source_loader_factory = source_loader_factory or SourceDocumentLoaderFactory()
        self.cleaner = cleaner or TextCleaner()
        self.metadata_extractor = metadata_extractor or DocumentMetadataExtractor()
        self.splitter = splitter
        self.indexer = indexer or KnowledgeIndexer(self.repo)
        self.storage = storage

    def run(self, document_id: str) -> dict:
        document = self.repo.get(document_id)
        if document is None:
            return {"document_id": document_id, "status": "not_found"}

        document.parsed_type = self.parser_registry.resolve(document.file_name)

        try:
            storage = self.storage or self._build_storage()
            file_bytes = storage.download_bytes(current_app.config["MINIO_BUCKET"], document.storage_key)
            loaded_document = self.source_loader_factory.load_bytes(
                file_bytes,
                file_name=document.file_name,
                source_uri=document.storage_key,
            )

            parsed_document = self.parser_registry.parse(loaded_document)
            cleaned_document = self.cleaner.clean(parsed_document)
            enriched_document = self.metadata_extractor.extract(loaded_document, parsed_document, cleaned_document)
            splitter = self.splitter or ParentChildSplitter(
                parent_tokens=current_app.config.get("CHUNK_PARENT_TOKENS", 800),
                child_tokens=current_app.config.get("CHUNK_CHILD_TOKENS", 180),
                parent_overlap_tokens=current_app.config.get("CHUNK_PARENT_OVERLAP_TOKENS", 120),
                child_overlap_tokens=current_app.config.get("CHUNK_CHILD_OVERLAP_TOKENS", 40),
            )
            chunks = splitter.split(enriched_document.cleaned)
            index_summary = self.indexer.build_indexes(document, chunks)

            document.status = "indexed"
            document.chunk_count = len(chunks["children"])
            document.metadata_json = {
                "parser": parsed_document.parser_name,
                "preview": enriched_document.cleaned.preview,
                "cleaning": cleaned_document.cleaning_stats,
                "document_metadata": enriched_document.metadata,
                "parent_chunk_count": len(chunks["parents"]),
                "child_chunk_count": len(chunks["children"]),
                "indexing": index_summary,
            }
            self.repo.update(document)
            return {"document_id": document.id, "status": document.status, "parsed_type": document.parsed_type}
        except Exception as exc:
            document.status = "failed"
            document.metadata_json = {"error": str(exc), "parser": document.parsed_type}
            self.repo.update(document)
            return {"document_id": document.id, "status": document.status, "parsed_type": document.parsed_type}

    @staticmethod
    def _build_storage() -> ObjectStorage:
        return ObjectStorage(
            endpoint=current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_SECURE"],
        )
