# Phase 1: Technical Specification

## Data Models & API Contracts

---

## 1. Data Models

### 1.1 Document Models

#### DocumentMetadata

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents."""

    document_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:12]}")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension (pdf, docx)")
    file_size: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    page_count: Optional[int] = Field(None, description="Number of pages")
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")
    created_date: Optional[datetime] = Field(None, description="Document creation date")

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
                "title": "Annual Report 2025"
            }
        }
```

#### ChunkMetadata

```python
class ChunkMetadata(BaseModel):
    """Metadata for document chunks."""

    chunk_id: str = Field(default_factory=lambda: f"chunk_{uuid4().hex[:12]}")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., description="Chunk position in document")
    total_chunks: int = Field(..., description="Total chunks in document")
    page_number: Optional[int] = Field(None, description="Source page number")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    content: str = Field(..., description="Chunk text content")
    embedding: Optional[list[float]] = Field(None, description="Vector embedding")

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
                "content": "The quarterly revenue increased by 15%..."
            }
        }
```

#### DocumentUploadRequest

```python
class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""

    # Files are handled via FastAPI's UploadFile
    # This model is for additional metadata if needed
    tags: Optional[list[str]] = Field(None, description="Document tags")
    category: Optional[str] = Field(None, description="Document category")

    class Config:
        json_schema_extra = {
            "example": {
                "tags": ["financial", "quarterly"],
                "category": "reports"
            }
        }
```

#### DocumentUploadResponse

```python
class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    status: str = Field(..., description="Upload status")
    document_id: str = Field(..., description="Generated document ID")
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    chunks_created: int = Field(..., description="Number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "document_id": "doc_a1b2c3d4e5f6",
                "filename": "annual_report.pdf",
                "file_size": 1024000,
                "chunks_created": 45,
                "processing_time": 2.3
            }
        }
```

#### DocumentListResponse

```python
class DocumentInfo(BaseModel):
    """Document information for listing."""

    document_id: str
    filename: str
    upload_date: datetime
    file_size: int
    chunks: int
    status: str = Field(..., description="indexed, processing, failed")

class DocumentListResponse(BaseModel):
    """Response model for document listing."""

    documents: list[DocumentInfo]
    total: int
    page: int = 1
    page_size: int = 50

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "document_id": "doc_a1b2c3d4e5f6",
                        "filename": "annual_report.pdf",
                        "upload_date": "2026-06-23T08:00:00Z",
                        "file_size": 1024000,
                        "chunks": 45,
                        "status": "indexed"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 50
            }
        }
```

### 1.2 Chat Models

#### ChatMessage

```python
class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What are the key findings?",
                "timestamp": "2026-06-23T08:30:00Z"
            }
        }
```

#### SourceReference

```python
class SourceReference(BaseModel):
    """Reference to source document."""

    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document filename")
    page_number: Optional[int] = Field(None, description="Page number")
    chunk_index: int = Field(..., description="Chunk index")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    excerpt: str = Field(..., description="Relevant text excerpt")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_a1b2c3d4e5f6",
                "document_name": "annual_report.pdf",
                "page_number": 5,
                "chunk_index": 12,
                "relevance_score": 0.89,
                "excerpt": "The quarterly revenue increased by 15%..."
            }
        }
```

#### ChatRequest

```python
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message/question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    top_k: int = Field(5, description="Number of documents to retrieve")
    include_sources: bool = Field(True, description="Include source references")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(512, ge=1, le=4096, description="Max response tokens")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the key findings in the report?",
                "conversation_id": "conv_456",
                "top_k": 5,
                "include_sources": True,
                "temperature": 0.7,
                "max_tokens": 512
            }
        }
```

#### ChatResponse

```python
class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    answer: str = Field(..., description="Generated answer")
    sources: list[SourceReference] = Field(default_factory=list)
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time: float = Field(..., description="Processing time in seconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used in generation")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the annual report, the key findings are...",
                "sources": [
                    {
                        "document_id": "doc_a1b2c3d4e5f6",
                        "document_name": "annual_report.pdf",
                        "page_number": 5,
                        "chunk_index": 12,
                        "relevance_score": 0.89,
                        "excerpt": "The quarterly revenue increased by 15%..."
                    }
                ],
                "conversation_id": "conv_456",
                "timestamp": "2026-06-23T08:30:00Z",
                "processing_time": 1.2,
                "tokens_used": 245
            }
        }
```

---

## 2. API Endpoints

### 2.1 Document Management API

#### Upload Documents

```
POST /api/v1/documents/upload
Content-Type: multipart/form-data
```

**Request Body**:

```
files: List[UploadFile]  # Multiple files
tags: Optional[str]       # JSON string of tags
category: Optional[str]   # Document category
```

**Response**: `200 OK`

```json
{
	"status": "success",
	"documents": [
		{
			"document_id": "doc_a1b2c3d4e5f6",
			"filename": "annual_report.pdf",
			"file_size": 1024000,
			"chunks_created": 45,
			"processing_time": 2.3
		}
	]
}
```

**Error Responses**:

- `400 Bad Request`: Invalid file type or size
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Processing failed

#### List Documents

```
GET /api/v1/documents
Query Parameters:
  - page: int (default: 1)
  - page_size: int (default: 50)
  - status: str (optional: indexed, processing, failed)
```

**Response**: `200 OK`

```json
{
	"documents": [
		{
			"document_id": "doc_a1b2c3d4e5f6",
			"filename": "annual_report.pdf",
			"upload_date": "2026-06-23T08:00:00Z",
			"file_size": 1024000,
			"chunks": 45,
			"status": "indexed"
		}
	],
	"total": 1,
	"page": 1,
	"page_size": 50
}
```

#### Get Document Details

```
GET /api/v1/documents/{document_id}
```

**Response**: `200 OK`

```json
{
	"document_id": "doc_a1b2c3d4e5f6",
	"filename": "annual_report.pdf",
	"file_type": "pdf",
	"file_size": 1024000,
	"upload_date": "2026-06-23T08:00:00Z",
	"page_count": 45,
	"chunks": 45,
	"status": "indexed",
	"metadata": {
		"author": "John Doe",
		"title": "Annual Report 2025",
		"created_date": "2025-12-31T00:00:00Z"
	}
}
```

**Error Responses**:

- `404 Not Found`: Document not found

#### Delete Document

```
DELETE /api/v1/documents/{document_id}
```

**Response**: `200 OK`

```json
{
	"status": "success",
	"message": "Document deleted successfully",
	"document_id": "doc_a1b2c3d4e5f6"
}
```

**Error Responses**:

- `404 Not Found`: Document not found
- `500 Internal Server Error`: Deletion failed

### 2.2 Chat API

#### Send Chat Message

```
POST /api/v1/chat
Content-Type: application/json
```

**Request Body**:

```json
{
	"message": "What are the key findings in the report?",
	"conversation_id": "conv_456",
	"top_k": 5,
	"include_sources": true,
	"temperature": 0.7,
	"max_tokens": 512
}
```

**Response**: `200 OK`

```json
{
	"answer": "Based on the annual report, the key findings are:\n1. Revenue increased by 15%\n2. Operating costs decreased by 8%\n3. Market share grew to 23%",
	"sources": [
		{
			"document_id": "doc_a1b2c3d4e5f6",
			"document_name": "annual_report.pdf",
			"page_number": 5,
			"chunk_index": 12,
			"relevance_score": 0.89,
			"excerpt": "The quarterly revenue increased by 15% compared to the previous year..."
		},
		{
			"document_id": "doc_a1b2c3d4e5f6",
			"document_name": "annual_report.pdf",
			"page_number": 8,
			"chunk_index": 20,
			"relevance_score": 0.85,
			"excerpt": "Operating costs were reduced by 8% through efficiency improvements..."
		}
	],
	"conversation_id": "conv_456",
	"timestamp": "2026-06-23T08:30:00Z",
	"processing_time": 1.2,
	"tokens_used": 245
}
```

**Error Responses**:

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: No documents indexed
- `500 Internal Server Error`: Generation failed

#### Get Conversation History

```
GET /api/v1/chat/conversations/{conversation_id}
```

**Response**: `200 OK`

```json
{
	"conversation_id": "conv_456",
	"messages": [
		{
			"role": "user",
			"content": "What are the key findings?",
			"timestamp": "2026-06-23T08:30:00Z"
		},
		{
			"role": "assistant",
			"content": "Based on the annual report...",
			"timestamp": "2026-06-23T08:30:01Z"
		}
	],
	"created_at": "2026-06-23T08:30:00Z",
	"updated_at": "2026-06-23T08:30:01Z"
}
```

#### Clear Conversation

```
DELETE /api/v1/chat/conversations/{conversation_id}
```

**Response**: `200 OK`

```json
{
	"status": "success",
	"message": "Conversation cleared",
	"conversation_id": "conv_456"
}
```

---

## 3. Database Schema

### 3.1 Documents Table

```sql
CREATE TABLE documents (
    document_id VARCHAR(50) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    page_count INTEGER,
    author VARCHAR(255),
    title VARCHAR(500),
    created_date TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    file_path VARCHAR(500) NOT NULL,
    INDEX idx_upload_date (upload_date),
    INDEX idx_status (status)
);
```

### 3.2 Chunks Table

```sql
CREATE TABLE chunks (
    chunk_id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    page_number INTEGER,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
    INDEX idx_document_id (document_id),
    INDEX idx_chunk_index (document_id, chunk_index)
);
```

### 3.3 Conversations Table

```sql
CREATE TABLE conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);
```

### 3.4 Messages Table

```sql
CREATE TABLE messages (
    message_id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_timestamp (timestamp)
);
```

---

## 4. File Storage Structure

```
data/
├── raw/                          # Original uploaded files
│   ├── doc_a1b2c3d4e5f6.pdf
│   └── doc_x7y8z9a0b1c2.docx
├── processed/                    # Processed chunks (JSON)
│   ├── doc_a1b2c3d4e5f6/
│   │   ├── metadata.json
│   │   └── chunks.json
│   └── doc_x7y8z9a0b1c2/
│       ├── metadata.json
│       └── chunks.json
└── vectorstore/                  # FAISS indices
    ├── faiss_index.bin
    ├── metadata.json
    └── backup/
        └── faiss_index_20260623.bin
```

---

## 5. Error Handling

### Error Response Format

```json
{
	"error": {
		"code": "DOCUMENT_PROCESSING_FAILED",
		"message": "Failed to process document",
		"details": "PDF file is corrupted or encrypted",
		"timestamp": "2026-06-23T08:30:00Z"
	}
}
```

### Error Codes

| Code                   | Description                | HTTP Status |
| ---------------------- | -------------------------- | ----------- |
| `INVALID_FILE_TYPE`    | Unsupported file format    | 400         |
| `FILE_TOO_LARGE`       | File exceeds size limit    | 413         |
| `DOCUMENT_NOT_FOUND`   | Document ID not found      | 404         |
| `PROCESSING_FAILED`    | Document processing error  | 500         |
| `EMBEDDING_FAILED`     | Embedding generation error | 500         |
| `RETRIEVAL_FAILED`     | Vector search error        | 500         |
| `GENERATION_FAILED`    | LLM generation error       | 500         |
| `NO_DOCUMENTS_INDEXED` | No documents available     | 404         |
| `INVALID_CONVERSATION` | Conversation not found     | 404         |

---

## 6. Configuration Schema

### Environment Variables

```bash
# RAG Configuration
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
FAISS_INDEX_PATH=data/vectorstore/faiss_index
TOP_K_RETRIEVAL=5

# Document Processing
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=.pdf,.docx
UPLOAD_DIR=data/raw
PROCESSED_DIR=data/processed

# Performance
BATCH_SIZE=32
MAX_CONCURRENT_UPLOADS=5
EMBEDDING_BATCH_SIZE=100
```

---

## 7. Performance Metrics

### Monitoring Endpoints

#### System Metrics

```
GET /api/v1/metrics
```

**Response**:

```json
{
	"documents": {
		"total": 150,
		"indexed": 148,
		"processing": 2,
		"failed": 0
	},
	"chunks": {
		"total": 6750,
		"average_per_document": 45
	},
	"storage": {
		"raw_files_size_mb": 1536,
		"vector_index_size_mb": 256
	},
	"performance": {
		"avg_upload_time_sec": 2.3,
		"avg_retrieval_time_sec": 0.15,
		"avg_generation_time_sec": 1.2
	}
}
```

---

## 8. Security Considerations

### File Upload Security

- Validate file extensions
- Check file size limits
- Scan for malware (future)
- Sanitize filenames
- Isolate processing environment

### API Security

- Rate limiting on endpoints
- Authentication (future)
- Input validation
- SQL injection prevention
- XSS protection

### Data Privacy

- Secure file storage
- Encrypted connections
- Access logging
- Data retention policies

---

**Document Version**: 1.0
**Last Updated**: 2026-06-23
**Author**: Bob (Planning Mode)
**Status**: Ready for Implementation
