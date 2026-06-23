"""
PDF document loader using PyPDF2.
"""

from typing import Dict, Any, List
from pathlib import Path
import PyPDF2
from backend.ingestion.loaders.base import BaseDocumentLoader, DocumentLoadError


class PDFLoader(BaseDocumentLoader):
    """
    Loader for PDF documents.
    
    Extracts text content and metadata from PDF files using PyPDF2.
    Supports encrypted PDFs with password.
    """
    
    def __init__(self, password: str = None):
        """
        Initialize PDF loader.
        
        Args:
            password: Optional password for encrypted PDFs
        """
        super().__init__()
        self.password = password
    
    def supports_format(self, file_extension: str) -> bool:
        """Check if file extension is .pdf"""
        return file_extension.lower() in ['.pdf']
    
    async def load(self, file_path: Path) -> Dict[str, Any]:
        """
        Load PDF document and extract content.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with content, metadata, and pages
            
        Raises:
            DocumentLoadError: If PDF loading fails
        """
        self._validate_file(file_path)
        
        try:
            with open(file_path, 'rb') as file:
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Handle encrypted PDFs
                if pdf_reader.is_encrypted:
                    if self.password:
                        try:
                            pdf_reader.decrypt(self.password)
                        except Exception as e:
                            raise DocumentLoadError(
                                f"Failed to decrypt PDF with provided password: {e}"
                            )
                    else:
                        raise DocumentLoadError(
                            "PDF is encrypted but no password provided"
                        )
                
                # Extract metadata
                metadata = self._extract_pdf_metadata(pdf_reader, file_path)
                
                # Extract pages
                pages = self._extract_pages(pdf_reader)
                
                # Combine all page content
                content = "\n\n".join([page["content"] for page in pages])
                content = self._clean_text(content)
                
                self.logger.info(
                    f"Successfully loaded PDF: {file_path.name} "
                    f"({len(pages)} pages, {len(content)} chars)"
                )
                
                return {
                    "content": content,
                    "metadata": metadata,
                    "pages": pages
                }
                
        except PyPDF2.errors.PdfReadError as e:
            raise DocumentLoadError(f"Failed to read PDF: {e}")
        except Exception as e:
            raise DocumentLoadError(f"Unexpected error loading PDF: {e}")
    
    def _extract_pdf_metadata(
        self, 
        pdf_reader: PyPDF2.PdfReader, 
        file_path: Path
    ) -> Dict[str, Any]:
        """
        Extract metadata from PDF.
        
        Args:
            pdf_reader: PyPDF2 reader object
            file_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        # Get base metadata
        metadata = self._extract_base_metadata(file_path)
        
        # Add PDF-specific metadata
        metadata.update({
            "page_count": len(pdf_reader.pages),
            "is_encrypted": pdf_reader.is_encrypted,
        })
        
        # Extract PDF info if available
        if pdf_reader.metadata:
            pdf_info = pdf_reader.metadata
            
            # Common PDF metadata fields
            if pdf_info.title:
                metadata["title"] = pdf_info.title
            if pdf_info.author:
                metadata["author"] = pdf_info.author
            if pdf_info.subject:
                metadata["subject"] = pdf_info.subject
            if pdf_info.creator:
                metadata["creator"] = pdf_info.creator
            if pdf_info.producer:
                metadata["producer"] = pdf_info.producer
            if pdf_info.creation_date:
                metadata["creation_date"] = str(pdf_info.creation_date)
            if pdf_info.modification_date:
                metadata["modification_date"] = str(pdf_info.modification_date)
        
        return metadata
    
    def _extract_pages(self, pdf_reader: PyPDF2.PdfReader) -> List[Dict[str, Any]]:
        """
        Extract content from all pages.
        
        Args:
            pdf_reader: PyPDF2 reader object
            
        Returns:
            List of page dictionaries
        """
        pages = []
        
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            try:
                # Extract text from page
                text = page.extract_text()
                
                # Clean text
                text = self._clean_text(text)
                
                pages.append({
                    "page_number": page_num,
                    "content": text,
                    "char_count": len(text)
                })
                
            except Exception as e:
                self.logger.warning(
                    f"Failed to extract text from page {page_num}: {e}"
                )
                pages.append({
                    "page_number": page_num,
                    "content": "",
                    "char_count": 0,
                    "error": str(e)
                })
        
        return pages
    
    def _clean_text(self, text: str) -> str:
        """
        Clean PDF-specific text artifacts.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Call parent cleaning
        text = super()._clean_text(text)
        
        # Remove common PDF artifacts
        # Remove form feed characters
        text = text.replace("\f", "\n")
        
        # Remove excessive newlines (more than 2)
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        return text


# Made with Bob