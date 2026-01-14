"""
BDNS Document Processing Service

Processes PDF documents attached to BDNS grants on-demand.
Uses the existing PDFProcessor for text extraction.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import Grant
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


class BDNSDocumentService:
    """Service for processing BDNS PDF documents on-demand"""

    def __init__(self, db: Session):
        self.db = db
        self.pdf_processor = PDFProcessor()

    def process_grant_documents(self, grant_id: str) -> Dict[str, Any]:
        """
        Process all BDNS documents for a grant.

        Args:
            grant_id: The grant ID to process documents for

        Returns:
            Dictionary with processing results
        """
        grant = self.db.query(Grant).filter(Grant.id == grant_id).first()
        if not grant:
            return {"success": False, "error": "Grant not found"}

        if not grant.bdns_documents:
            return {"success": False, "error": "No documents to process"}

        if grant.bdns_documents_processed:
            return {
                "success": True,
                "message": "Documents already processed",
                "grant_id": grant_id,
                "processed_at": grant.bdns_documents_processed_at.isoformat() if grant.bdns_documents_processed_at else None,
                "document_count": len(grant.bdns_documents)
            }

        logger.info(f"Processing {len(grant.bdns_documents)} documents for grant {grant_id}")

        results = []
        combined_texts = []

        for doc in grant.bdns_documents:
            doc_result = self._process_single_document(doc, grant.bdns_code)
            results.append(doc_result)

            if doc_result["success"] and doc_result.get("text"):
                # Add document header and content
                combined_texts.append(
                    f"=== {doc.get('nombre', 'Documento sin nombre')} ===\n\n{doc_result['text']}"
                )

        # Update grant with results
        grant.bdns_documents_content = results
        grant.bdns_documents_combined_text = "\n\n---\n\n".join(combined_texts) if combined_texts else None
        grant.bdns_documents_processed = True
        grant.bdns_documents_processed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(grant)

        successful = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])

        logger.info(f"Processed grant {grant_id}: {successful} successful, {failed} failed")

        return {
            "success": True,
            "grant_id": grant_id,
            "total_documents": len(grant.bdns_documents),
            "processed_successfully": successful,
            "failed": failed,
            "results": results,
            "has_content": bool(grant.bdns_documents_combined_text)
        }

    def _process_single_document(self, doc: Dict[str, Any], bdns_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single BDNS document PDF.

        Args:
            doc: Document metadata dict with id, nombre, url, etc.
            bdns_code: The BDNS code of the grant (used to construct correct URL)

        Returns:
            Processing result with success status and extracted text
        """
        result = {
            "doc_id": doc.get("id"),
            "filename": doc.get("nombre"),
            "success": False,
            "text": None,
            "error": None
        }

        try:
            doc_id = doc.get("id")
            if not doc_id:
                result["error"] = "No document ID provided"
                return result

            # Always construct the correct URL format using bdns_code
            # Old grants may have incorrect URLs stored, so we rebuild it
            if bdns_code:
                url = f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{bdns_code}/document/{doc_id}"
            else:
                # Fallback to stored URL if no bdns_code
                url = doc.get("url")
                if not url:
                    result["error"] = "No URL or BDNS code available"
                    return result

            logger.info(f"Processing document: {doc.get('nombre')} from {url}")

            # Build metadata for PDF processor
            metadata = {
                "title": doc.get("nombre", "BDNS Document"),
                "department": "BDNS",
                "id": str(doc.get("id")),
                "pdf_url": url,
                "descripcion": doc.get("descripcion")
            }

            # Use existing PDFProcessor
            pdf_result = self.pdf_processor.process_grant_pdf(url, metadata)

            if pdf_result["success"]:
                result["success"] = True
                # Limit text size to 50KB per document
                result["text"] = pdf_result.get("text", "")[:50000]
                result["markdown"] = pdf_result.get("markdown", "")[:50000]
                result["extracted_info"] = pdf_result.get("extracted_info", {})
                logger.info(f"Successfully processed: {doc.get('nombre')}")
            else:
                result["error"] = pdf_result.get("error", "Unknown processing error")
                logger.warning(f"Failed to process {doc.get('nombre')}: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Exception processing document {doc.get('id')}: {e}")

        return result

    def get_document_content(self, grant_id: str, doc_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get processed content for grant documents.

        Args:
            grant_id: The grant ID
            doc_id: Optional specific document ID

        Returns:
            Document content or list of all document contents
        """
        grant = self.db.query(Grant).filter(Grant.id == grant_id).first()
        if not grant:
            return {"success": False, "error": "Grant not found"}

        if not grant.bdns_documents_processed:
            return {
                "success": False,
                "error": "Documents not yet processed",
                "documents": grant.bdns_documents,
                "processed": False
            }

        if doc_id is not None:
            # Find specific document
            content = next(
                (c for c in (grant.bdns_documents_content or []) if c.get("doc_id") == doc_id),
                None
            )
            if not content:
                return {"success": False, "error": f"Document {doc_id} not found"}
            return {"success": True, "content": content}

        return {
            "success": True,
            "documents": grant.bdns_documents,
            "content": grant.bdns_documents_content,
            "combined_text": grant.bdns_documents_combined_text,
            "processed_at": grant.bdns_documents_processed_at.isoformat() if grant.bdns_documents_processed_at else None
        }

    def process_unprocessed_grants(self, limit: int = 10) -> Dict[str, Any]:
        """
        Batch process grants with unprocessed documents.
        Useful for background processing.

        Args:
            limit: Maximum number of grants to process

        Returns:
            Statistics about processing
        """
        unprocessed = self.db.query(Grant).filter(
            Grant.source == "BDNS",
            Grant.bdns_documents.isnot(None),
            Grant.bdns_documents_processed == False
        ).limit(limit).all()

        stats = {
            "total_grants": len(unprocessed),
            "successful": 0,
            "failed": 0,
            "grants_processed": []
        }

        for grant in unprocessed:
            try:
                result = self.process_grant_documents(grant.id)
                if result.get("success"):
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
                stats["grants_processed"].append({
                    "grant_id": grant.id,
                    "success": result.get("success"),
                    "error": result.get("error")
                })
            except Exception as e:
                stats["failed"] += 1
                stats["grants_processed"].append({
                    "grant_id": grant.id,
                    "success": False,
                    "error": str(e)
                })

        return stats
