"""
PDF contract document text extraction
"""

from pathlib import Path
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from PDF document
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text as string
    """
    
    doc = None  # ADDED: Initialize for finally block
    
    try:
        doc = fitz.open(str(pdf_path))
        
        text_parts = []
        
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            
            if page_text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")
        
        full_text = "\n\n".join(text_parts)
        
        return full_text if full_text.strip() else "[No text extracted from PDF]"
        
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"
    
    finally:
        # FIXED: Ensure document is always closed
        if doc is not None:
            doc.close()


def extract_pdf_metadata(pdf_path: Path) -> dict:
    """
    Extract PDF metadata
    
    Returns:
        Dictionary with title, author, page count, etc.
    """
    
    doc = None
    
    try:
        doc = fitz.open(str(pdf_path))
        
        metadata = {
            "page_count": doc.page_count,
            "title": doc.metadata.get("title", "Untitled"),
            "author": doc.metadata.get("author", "Unknown"),
            "subject": doc.metadata.get("subject", ""),
            "keywords": doc.metadata.get("keywords", ""),
            "created": doc.metadata.get("creationDate", ""),
            "modified": doc.metadata.get("modDate", ""),
        }
        
        return metadata
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if doc is not None:
            doc.close()