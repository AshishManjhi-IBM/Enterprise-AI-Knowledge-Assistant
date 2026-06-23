"""
Text chunking utilities for document processing.
Uses LangChain's RecursiveCharacterTextSplitter for intelligent text splitting.
"""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.core.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class DocumentChunker:
    """
    Handles text chunking with configurable parameters.
    
    Uses recursive character text splitting to maintain semantic coherence
    while respecting chunk size limits.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None,
        length_function: callable = len,
    ):
        """
        Initialize document chunker.
        
        Args:
            chunk_size: Maximum size of each chunk (default from settings)
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting
            length_function: Function to calculate text length
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.separators = separators or settings.chunk_separators
        self.length_function = length_function
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=self.length_function,
            is_separator_regex=False,
        )
        
        logger.info(
            f"Initialized DocumentChunker: "
            f"chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        total_chunks = len(chunks)
        
        for i, chunk_text in enumerate(chunks):
            chunk_obj = {
                "content": chunk_text,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "start_char": self._calculate_start_char(text, chunk_text, i),
                "end_char": self._calculate_end_char(text, chunk_text, i),
                "char_count": len(chunk_text),
            }
            
            # Add document metadata if provided
            if metadata:
                chunk_obj["metadata"] = metadata.copy()
            
            chunk_objects.append(chunk_obj)
        
        logger.info(
            f"Created {total_chunks} chunks from text "
            f"({len(text)} chars)"
        )
        
        return chunk_objects
    
    def chunk_document(
        self, 
        document: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document with its metadata.
        
        Args:
            document: Document dictionary with 'content' and 'metadata'
            
        Returns:
            List of chunk dictionaries
        """
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        
        return self.chunk_text(content, metadata)
    
    def chunk_pages(
        self,
        pages: List[Dict[str, Any]],
        base_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk document pages individually while preserving page numbers.
        
        Args:
            pages: List of page dictionaries with 'content' and 'page_number'
            base_metadata: Base metadata to attach to all chunks
            
        Returns:
            List of chunk dictionaries with page information
        """
        all_chunks = []
        
        for page in pages:
            page_content = page.get("content", "")
            page_number = page.get("page_number")
            
            if not page_content.strip():
                continue
            
            # Create metadata for this page
            page_metadata = base_metadata.copy() if base_metadata else {}
            if page_number is not None:
                page_metadata["page_number"] = page_number
            
            # Chunk the page
            page_chunks = self.chunk_text(page_content, page_metadata)
            
            all_chunks.extend(page_chunks)
        
        # Update chunk indices to be global across all pages
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_index"] = i
            chunk["total_chunks"] = len(all_chunks)
        
        logger.info(
            f"Created {len(all_chunks)} chunks from {len(pages)} pages"
        )
        
        return all_chunks
    
    def _calculate_start_char(
        self, 
        full_text: str, 
        chunk_text: str, 
        chunk_index: int
    ) -> int:
        """
        Calculate the starting character position of a chunk.
        
        Args:
            full_text: Complete text
            chunk_text: Chunk text
            chunk_index: Index of the chunk
            
        Returns:
            Starting character position
        """
        try:
            # Find the chunk in the full text
            # Account for overlap by searching from previous chunk end
            search_start = max(0, chunk_index * (self.chunk_size - self.chunk_overlap))
            pos = full_text.find(chunk_text, search_start)
            return pos if pos != -1 else search_start
        except Exception:
            return chunk_index * (self.chunk_size - self.chunk_overlap)
    
    def _calculate_end_char(
        self, 
        full_text: str, 
        chunk_text: str, 
        chunk_index: int
    ) -> int:
        """
        Calculate the ending character position of a chunk.
        
        Args:
            full_text: Complete text
            chunk_text: Chunk text
            chunk_index: Index of the chunk
            
        Returns:
            Ending character position
        """
        start_char = self._calculate_start_char(full_text, chunk_text, chunk_index)
        return start_char + len(chunk_text)
    
    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
            }
        
        chunk_sizes = [chunk["char_count"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_chars": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
        }


# Made with Bob