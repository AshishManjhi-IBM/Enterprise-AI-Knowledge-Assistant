"""
Document and chunk metadata management.
Provides Pydantic models for structured metadata handling.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


class DocumentMetadata(BaseModel):
    """
    Metadata for uploaded documents.
    
    Tracks document-level information including file details,
    processing status, and extracted metadata.
    """
    
    document_id: str = Field(
        default_factory=lambda: f"doc_{uuid4().hex[:12]}",
        description="Unique document identifier"
    )
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension (pdf, docx)")
    file_size: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Upload timestamp"
    )
    
    # Document-specific metadata
    page_count: Optional[int] = Field(None, description="Number of pages")
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")
    subject: Optional[str] = Field(None, description="Document subject")
    keywords: Optional[str] = Field(None, description="Document keywords")
    created_date: Optional[datetime] = Field(None, description="Document creation date")
    modified_date: Optional[datetime] = Field(None, description="Last modification date")
    
    # Processing metadata
    status: str = Field(default="pending", description="Processing status")
    chunks_created: int = Field(default=0, description="Number of chunks created")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Storage paths
    file_path: str = Field(..., description="Path to stored file")
    processed_path: Optional[str] = Field(None, description="Path to processed data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_a1b2c3d4e5f6",
                "filename": "annual_report.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "upload_date": "2026-06-23T08:00:00Z",
                "page_count": 45,
                "author": "John Doe",
                "title": "Annual Report 2025",
                "status": "completed",
                "chunks_created": 45,
                "processing_time": 2.3,
                "file_path": "data/raw/doc_a1b2c3d4e5f6.pdf"
            }
        }


class ChunkMetadata(BaseModel):
    """
    Metadata for document chunks.
    
    Tracks chunk-level information including position, content,
    and relationship to parent document.
    """
    
    chunk_id: str = Field(
        default_factory=lambda: f"chunk_{uuid4().hex[:12]}",
        description="Unique chunk identifier"
    )
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., description="Chunk position in document")
    total_chunks: int = Field(..., description="Total chunks in document")
    
    # Position information
    page_number: Optional[int] = Field(None, description="Source page number")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    
    # Content information
    char_count: int = Field(..., description="Number of characters in chunk")
    word_count: Optional[int] = Field(None, description="Number of words in chunk")
    
    # Document metadata (inherited)
    filename: Optional[str] = Field(None, description="Source filename")
    file_type: Optional[str] = Field(None, description="Source file type")
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")
    
    # Embedding information
    embedding_model: Optional[str] = Field(None, description="Embedding model used")
    embedding_dimension: Optional[int] = Field(None, description="Embedding dimension")
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Chunk creation timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_x1y2z3a4b5c6",
                "document_id": "doc_a1b2c3d4e5f6",
                "chunk_index": 12,
                "total_chunks": 45,
                "page_number": 5,
                "start_char": 12000,
                "end_char": 13000,
                "char_count": 1000,
                "word_count": 150,
                "filename": "annual_report.pdf",
                "file_type": "pdf",
                "embedding_model": "BAAI/bge-small-en-v1.5",
                "embedding_dimension": 384
            }
        }


class MetadataManager:
    """
    Manages document and chunk metadata operations.
    
    Provides utilities for creating, updating, and enriching metadata.
    """
    
    @staticmethod
    def create_document_metadata(
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        **kwargs
    ) -> DocumentMetadata:
        """
        Create document metadata from file information.
        
        Args:
            filename: Original filename
            file_type: File extension
            file_size: File size in bytes
            file_path: Path to stored file
            **kwargs: Additional metadata fields
            
        Returns:
            DocumentMetadata instance
        """
        return DocumentMetadata(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            **kwargs
        )
    
    @staticmethod
    def create_chunk_metadata(
        document_id: str,
        chunk_index: int,
        total_chunks: int,
        start_char: int,
        end_char: int,
        char_count: int,
        **kwargs
    ) -> ChunkMetadata:
        """
        Create chunk metadata.
        
        Args:
            document_id: Parent document ID
            chunk_index: Chunk position
            total_chunks: Total number of chunks
            start_char: Start character position
            end_char: End character position
            char_count: Number of characters
            **kwargs: Additional metadata fields
            
        Returns:
            ChunkMetadata instance
        """
        return ChunkMetadata(
            document_id=document_id,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            start_char=start_char,
            end_char=end_char,
            char_count=char_count,
            **kwargs
        )
    
    @staticmethod
    def enrich_chunk_metadata(
        chunk_metadata: ChunkMetadata,
        document_metadata: DocumentMetadata
    ) -> ChunkMetadata:
        """
        Enrich chunk metadata with document-level information.
        
        Args:
            chunk_metadata: Chunk metadata to enrich
            document_metadata: Source document metadata
            
        Returns:
            Enriched chunk metadata
        """
        # Update chunk with document info
        chunk_metadata.filename = document_metadata.filename
        chunk_metadata.file_type = document_metadata.file_type
        chunk_metadata.author = document_metadata.author
        chunk_metadata.title = document_metadata.title
        
        return chunk_metadata
    
    @staticmethod
    def update_document_status(
        metadata: DocumentMetadata,
        status: str,
        chunks_created: int = None,
        processing_time: float = None,
        error_message: str = None
    ) -> DocumentMetadata:
        """
        Update document processing status.
        
        Args:
            metadata: Document metadata to update
            status: New status (pending, processing, completed, failed)
            chunks_created: Number of chunks created
            processing_time: Processing time in seconds
            error_message: Error message if failed
            
        Returns:
            Updated document metadata
        """
        metadata.status = status
        
        if chunks_created is not None:
            metadata.chunks_created = chunks_created
        
        if processing_time is not None:
            metadata.processing_time = processing_time
        
        if error_message is not None:
            metadata.error_message = error_message
        
        return metadata
    
    @staticmethod
    def metadata_to_dict(metadata: BaseModel) -> Dict[str, Any]:
        """
        Convert metadata to dictionary.
        
        Args:
            metadata: Pydantic metadata model
            
        Returns:
            Dictionary representation
        """
        return metadata.model_dump(mode='json')
    
    @staticmethod
    def dict_to_document_metadata(data: Dict[str, Any]) -> DocumentMetadata:
        """
        Create DocumentMetadata from dictionary.
        
        Args:
            data: Dictionary with metadata fields
            
        Returns:
            DocumentMetadata instance
        """
        return DocumentMetadata(**data)
    
    @staticmethod
    def dict_to_chunk_metadata(data: Dict[str, Any]) -> ChunkMetadata:
        """
        Create ChunkMetadata from dictionary.
        
        Args:
            data: Dictionary with metadata fields
            
        Returns:
            ChunkMetadata instance
        """
        return ChunkMetadata(**data)


# Made with Bob