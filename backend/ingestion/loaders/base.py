"""
Base document loader interface.
All document loaders must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from backend.core.logging import get_logger

logger = get_logger(__name__)


class DocumentLoadError(Exception):
    """Exception raised when document loading fails."""
    pass


class BaseDocumentLoader(ABC):
    """
    Abstract base class for document loaders.
    
    All document loaders must implement the load() method to extract
    content and metadata from files.
    """
    
    def __init__(self):
        """Initialize the document loader."""
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def load(self, file_path: Path) -> Dict[str, Any]:
        """
        Load document and extract content and metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing:
                - content: str - Extracted text content
                - metadata: dict - Document metadata
                - pages: list[dict] - Page-level content (optional)
                
        Raises:
            DocumentLoadError: If document loading fails
        """
        pass
    
    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if loader supports the given file format.
        
        Args:
            file_extension: File extension (e.g., '.pdf', '.docx')
            
        Returns:
            True if format is supported, False otherwise
        """
        pass
    
    def _extract_base_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract basic file metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with basic metadata
        """
        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "file_size": stat.st_size,
            "file_path": str(file_path.absolute()),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    def _validate_file(self, file_path: Path) -> None:
        """
        Validate that file exists and is readable.
        
        Args:
            file_path: Path to the file
            
        Raises:
            DocumentLoadError: If file is invalid
        """
        if not file_path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise DocumentLoadError(f"Path is not a file: {file_path}")
        
        if not file_path.stat().st_size > 0:
            raise DocumentLoadError(f"File is empty: {file_path}")
        
        if not self.supports_format(file_path.suffix.lower()):
            raise DocumentLoadError(
                f"Unsupported file format: {file_path.suffix}"
            )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove null bytes
        text = text.replace("\x00", "")
        
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        return text.strip()
    
    async def load_batch(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Load multiple documents in batch.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of loaded documents
        """
        results = []
        for file_path in file_paths:
            try:
                result = await self.load(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")
                results.append({
                    "error": str(e),
                    "file_path": str(file_path),
                    "metadata": self._extract_base_metadata(file_path)
                })
        return results


# Made with Bob