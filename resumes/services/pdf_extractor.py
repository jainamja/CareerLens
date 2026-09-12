import pymupdf as fitz  # PyMuPDF
import re
import logging

logger = logging.getLogger(__name__)

class PDFExtractionError(Exception):
    """Custom exception for PDF extraction failures."""
    pass

def process_resume_pdf(file_path):
    """
    Extracts text from a PDF file using PyMuPDF and normalizes it.
    Returns the normalized text.
    Raises PDFExtractionError if extraction fails.
    """
    try:
        with fitz.open(file_path) as doc:
            if doc.needs_pass:
                raise PDFExtractionError("This PDF is password protected. Please upload an unlocked PDF.")
                
            if doc.page_count == 0:
                raise PDFExtractionError("No pages found in this PDF.")

            text_parts = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text_parts.append(page.get_text("text"))
            
        raw_text = "\n".join(text_parts)
        
        # Normalize: remove excessive blank lines and whitespace
        normalized_text = re.sub(r'\n{3,}', '\n\n', raw_text)
        normalized_text = normalized_text.strip()
        
        if not normalized_text:
            raise PDFExtractionError("No readable text was found in this PDF. Please upload a text-based resume.")
            
        return normalized_text
        
    except fitz.FileDataError:
        logger.error(f"Corrupted PDF file encountered: {file_path}")
        raise PDFExtractionError("We couldn't read this PDF. Please upload a valid PDF file.")
    except PDFExtractionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting text from {file_path}: {str(e)}", exc_info=True)
        raise PDFExtractionError("An unexpected error occurred while processing your resume.")
