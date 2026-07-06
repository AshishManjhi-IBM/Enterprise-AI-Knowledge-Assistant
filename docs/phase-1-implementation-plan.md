# Phase 1: Basic RAG Implementation Plan

## Overview

Phase 1 transforms the Enterprise Agentic RAG Platform from a foundation with LLM provider abstraction into a working RAG chatbot capable of ingesting documents, creating embeddings, and generating contextual answers.

**Timeline**: 2 weeks (14 days)
**Status**: Planning Complete, Ready for Implementation
**Dependencies**: Phase 0, 0.25, 0.5 (Completed)

---

## Architecture Overview

```mermaid
graph TB
    subgraph "User Interface"
        UI[Streamlit UI]
        DocUpload[Document Upload Page]
        ChatUI[Chat Interface]
    end

    subgraph "API Layer"
        API[FastAPI Backend]
        DocRoute[/api/v1/documents]
        ChatRoute[/api/v1/chat]
    end

    subgraph "Document Processing"
        Loader[Document Loaders]
        PDFLoader[PDF Loader]
        DOCXLoader[DOCX Loader]
        Chunker[Text Chunker]
        MetaExtract[Metadata Extractor]
    end

    subgraph "Embedding & Storage"
        EmbedService[Embedding Service]
        BGE[BAAI/bge-small-en-v1.5]
        FAISS[FAISS Vector Store]
    end

    subgraph "Retrieval & Generation"
        Retriever[Retriever Service]
        RAGChain[RAG Chain]
        LLMFactory[LLM Factory]
    end

    UI --> DocUpload
    UI --> ChatUI
    DocUpload --> DocRoute
    ChatUI --> ChatRoute

    DocRoute --> Loader
    Loader --> PDFLoader
    Loader --> DOCXLoader
    PDFLoader --> Chunker
    DOCXLoader --> Chunker
    Chunker --> MetaExtract
    MetaExtract --> EmbedService
    EmbedService --> BGE
    BGE --> FAISS

    ChatRoute --> RAGChain
    RAGChain --> Retriever
    Retriever --> FAISS
    Retriever --> RAGChain
    RAGChain --> LLMFactory
    LLMFactory --> ChatRoute
```

---

## Component Specifications

### 1. Document Ingestion Pipeline

#### 1.1 Document Loaders

**Base Loader Interface** (`backend/ingestion/loaders/base.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    async def load(self, file_path: Path) -> Dict[str, Any]:
        """Load document and extract content."""
        pass

    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """Check if loader supports file format."""
        pass
```

**PDF Loader** (`backend/ingestion/loaders/pdf_loader.py`)

- Library: PyPDF2
- Features:
  - Page-by-page extraction
  - Metadata extraction (title, author, creation date)
  - Text cleaning and normalization
  - Handle encrypted PDFs (with password support)

**DOCX Loader** (`backend/ingestion/loaders/docx_loader.py`)

- Library: python-docx
- Features:
  - Paragraph extraction
  - Table content extraction
  - Header/footer handling
  - Style preservation in metadata

#### 1.2 Text Chunking

**Chunking Strategy** (`backend/ingestion/chunking.py`)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentChunker:
    """Handles text chunking with overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = ["\n\n", "\n", " ", ""]
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
```

**Configuration**:

- Default chunk size: 1000 characters
- Default overlap: 200 characters
- Separators: Paragraph → Line → Space → Character
- Preserve sentence boundaries when possible

#### 1.3 Metadata Management

**Metadata Schema** (`backend/ingestion/metadata.py`)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    page_number: Optional[int] = None
    chunk_index: int
    total_chunks: int
    source_path: str
    author: Optional[str] = None
    title: Optional[str] = None
    created_date: Optional[datetime] = None
```

---

### 2. Embedding Service

**Embedding Model** (`backend/llm/embeddings.py`)

```python
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingService:
    """Handles text embedding generation."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # BGE-small dimension

    async def embed_documents(
        self,
        texts: List[str]
    ) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts, show_progress_bar=True)

    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for single query."""
        return self.model.encode([text])[0]
```

**Model Selection**: BAAI/bge-small-en-v1.5

- Dimension: 384
- Performance: Excellent for English text
- Size: ~133MB
- Speed: Fast inference on CPU
- Quality: High retrieval accuracy

---

### 3. Vector Store

**FAISS Integration** (`backend/retrievers/vector_store.py`)

```python
import faiss
import numpy as np
from typing import List, Tuple
from pathlib import Path

class FAISSVectorStore:
    """FAISS vector store wrapper."""

    def __init__(self, dimension: int = 384, index_path: Path = None):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.index_path = index_path
        self.metadata_store = []

    def add_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[dict]
    ):
        """Add vectors with metadata to index."""
        self.index.add(vectors)
        self.metadata_store.extend(metadata)

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5
    ) -> List[Tuple[dict, float]]:
        """Search for k nearest neighbors."""
        distances, indices = self.index.search(
            query_vector.reshape(1, -1), k
        )
        results = [
            (self.metadata_store[idx], float(dist))
            for idx, dist in zip(indices[0], distances[0])
        ]
        return results

    def save(self):
        """Persist index to disk."""
        if self.index_path:
            faiss.write_index(self.index, str(self.index_path))

    def load(self):
        """Load index from disk."""
        if self.index_path and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
```

**Index Configuration**:

- Index Type: IndexFlatL2 (exact search)
- Distance Metric: L2 (Euclidean)
- Persistence: Save/load from disk
- Metadata: Stored separately in JSON

---

### 4. RAG Chain

**RAG Implementation** (`backend/llm/rag_chain.py`)

```python
from typing import List, Dict, Any
from backend.providers.factory import LLMFactory
from backend.retrievers.retriever import RetrieverService
from backend.core.logging import get_logger

logger = get_logger(__name__)

class RAGChain:
    """RAG chain combining retrieval and generation."""

    def __init__(
        self,
        retriever: RetrieverService,
        llm_factory: LLMFactory,
        top_k: int = 5
    ):
        self.retriever = retriever
        self.llm_factory = llm_factory
        self.top_k = top_k

    async def generate_answer(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate answer using RAG."""

        # Retrieve relevant documents
        retrieved_docs = await self.retriever.retrieve(
            query, k=self.top_k
        )

        # Build context from retrieved documents
        context = self._build_context(retrieved_docs)

        # Create prompt with context
        prompt = self._create_prompt(query, context, conversation_history)

        # Generate answer using LLM
        llm = await self.llm_factory.get_provider()
        response = await llm.generate(prompt)

        # Return answer with sources
        return {
            "answer": response,
            "sources": [
                {
                    "document": doc["metadata"]["filename"],
                    "page": doc["metadata"].get("page_number"),
                    "chunk": doc["metadata"]["chunk_index"],
                    "relevance_score": doc["score"]
                }
                for doc in retrieved_docs
            ],
            "context_used": len(retrieved_docs)
        }

    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[Document {i}] {doc['content']}"
            )
        return "\n\n".join(context_parts)

    def _create_prompt(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]] = None
    ) -> str:
        """Create RAG prompt with context."""
        prompt = f"""You are a helpful AI assistant. Answer the question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Answer based only on the provided context
- If the context doesn't contain relevant information, say so
- Cite document numbers when referencing information
- Be concise and accurate

Answer:"""
        return prompt
```

---

### 5. API Endpoints

#### 5.1 Document Upload API

**Endpoint**: `POST /api/v1/documents/upload`

**Request**:

```python
from fastapi import UploadFile, File
from typing import List

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks
):
    """Upload and process documents."""
    pass
```

**Response**:

```json
{
	"status": "success",
	"documents": [
		{
			"document_id": "doc_123",
			"filename": "report.pdf",
			"file_size": 1024000,
			"chunks_created": 45,
			"processing_time": 2.3
		}
	]
}
```

#### 5.2 Document List API

**Endpoint**: `GET /api/v1/documents`

**Response**:

```json
{
	"documents": [
		{
			"document_id": "doc_123",
			"filename": "report.pdf",
			"upload_date": "2026-06-23T08:00:00Z",
			"file_size": 1024000,
			"chunks": 45,
			"status": "indexed"
		}
	],
	"total": 1
}
```

#### 5.3 Chat API

**Endpoint**: `POST /api/v1/chat`

**Request**:

```json
{
	"message": "What are the key findings in the report?",
	"conversation_id": "conv_456",
	"top_k": 5
}
```

**Response**:

```json
{
	"answer": "Based on the documents, the key findings are...",
	"sources": [
		{
			"document": "report.pdf",
			"page": 5,
			"chunk": 12,
			"relevance_score": 0.89
		}
	],
	"conversation_id": "conv_456",
	"timestamp": "2026-06-23T08:30:00Z"
}
```

---

### 6. Frontend Components

#### 6.1 Document Upload Page

**File**: `frontend/streamlit/pages/1_📄_Documents.py`

**Features**:

- Multi-file upload (PDF, DOCX)
- Upload progress tracking
- Document list with metadata
- Delete document functionality
- Processing status indicators

**UI Layout**:

```
┌─────────────────────────────────────┐
│  📄 Document Management             │
├─────────────────────────────────────┤
│  Upload Documents                   │
│  [Choose Files] [Upload]            │
│                                     │
│  Uploaded Documents                 │
│  ┌───────────────────────────────┐ │
│  │ report.pdf    | 45 chunks     │ │
│  │ manual.docx   | 32 chunks     │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

#### 6.2 Chat Interface

**File**: `frontend/streamlit/pages/2_💬_Chat.py`

**Features**:

- Chat message input
- Conversation history display
- Source attribution display
- Clear conversation button
- Export conversation

**UI Layout**:

```
┌─────────────────────────────────────┐
│  💬 RAG Chat                        │
├─────────────────────────────────────┤
│  Conversation                       │
│  ┌───────────────────────────────┐ │
│  │ User: What are the findings?  │ │
│  │                               │ │
│  │ Assistant: Based on report... │ │
│  │ Sources: report.pdf (p.5)     │ │
│  └───────────────────────────────┘ │
│                                     │
│  [Type your message...]  [Send]     │
└─────────────────────────────────────┘
```

---

## Configuration Updates

### Settings Extension

Add to `backend/core/settings.py`:

```python
# RAG Configuration
embedding_model: str = "BAAI/bge-small-en-v1.5"
embedding_dimension: int = 384
chunk_size: int = 1000
chunk_overlap: int = 200
faiss_index_path: str = "data/vectorstore/faiss_index"
top_k_retrieval: int = 5

# Document Processing
max_file_size: int = 10485760  # 10MB
allowed_extensions: list[str] = [".pdf", ".docx"]
upload_dir: str = "data/raw"
processed_dir: str = "data/processed"
```

---

## Dependencies

### New Requirements

Add to `requirements.txt`:

```
# Document Processing
PyPDF2==3.0.1
python-docx==1.1.0
langchain-text-splitters==0.0.1

# Embeddings & Vector Store
sentence-transformers==2.3.1
faiss-cpu==1.7.4

# Additional Utilities
aiofiles==23.2.1
python-multipart==0.0.6
```

---

## Testing Strategy

### Unit Tests

1. **Document Loaders** (`tests/test_loaders.py`)
   - Test PDF extraction
   - Test DOCX extraction
   - Test metadata extraction
   - Test error handling

2. **Chunking** (`tests/test_chunking.py`)
   - Test chunk size limits
   - Test overlap functionality
   - Test separator handling
   - Test edge cases

3. **Embeddings** (`tests/test_embeddings.py`)
   - Test embedding generation
   - Test batch processing
   - Test dimension validation
   - Test model loading

### Integration Tests

1. **Ingestion Pipeline** (`tests/test_ingestion.py`)
   - Test end-to-end document processing
   - Test FAISS indexing
   - Test metadata persistence

2. **RAG Chain** (`tests/test_rag_chain.py`)
   - Test retrieval accuracy
   - Test answer generation
   - Test source attribution
   - Test conversation context

### End-to-End Tests

1. Upload sample documents
2. Verify chunking and indexing
3. Test retrieval with various queries
4. Validate answer quality
5. Check source attribution accuracy

---

## Performance Targets

### Document Processing

- PDF processing: < 2 seconds per page
- DOCX processing: < 1 second per page
- Chunking: < 0.5 seconds per document
- Embedding generation: < 1 second per 100 chunks

### Retrieval

- Query embedding: < 0.1 seconds
- FAISS search: < 0.05 seconds for 10k vectors
- Total retrieval time: < 0.2 seconds

### Answer Generation

- LLM response time: < 3 seconds (Ollama)
- Total RAG pipeline: < 5 seconds end-to-end

---

## Success Criteria

### Functional Requirements

- ✅ Can upload PDF and DOCX files
- ✅ Documents are chunked with proper overlap
- ✅ Metadata is preserved and accessible
- ✅ Embeddings are generated correctly
- ✅ FAISS index stores and retrieves vectors
- ✅ Retrieval returns relevant chunks
- ✅ LLM generates contextual answers
- ✅ Sources are attributed correctly
- ✅ UI is intuitive and responsive

### Quality Requirements

- ✅ Retrieval precision > 80% on test queries
- ✅ Answer relevance > 85% (human evaluation)
- ✅ Source attribution accuracy > 95%
- ✅ System handles 100+ documents
- ✅ No data loss during processing
- ✅ Error handling for all edge cases

---

## Risk Mitigation

### Technical Risks

1. **Large Document Processing**
   - Risk: Memory overflow with large PDFs
   - Mitigation: Stream processing, chunk-by-chunk

2. **Embedding Performance**
   - Risk: Slow embedding generation
   - Mitigation: Batch processing, GPU support

3. **FAISS Scalability**
   - Risk: Slow search with many vectors
   - Mitigation: Use IndexIVFFlat for large datasets

### Operational Risks

1. **File Upload Failures**
   - Risk: Network interruptions
   - Mitigation: Chunked uploads, retry logic

2. **Index Corruption**
   - Risk: System crash during indexing
   - Mitigation: Atomic writes, backup strategy

---

## Implementation Sequence

### Week 1: Core Components (Days 1-7)

**Days 1-2**: Document Processing

- Implement document loaders
- Create chunking module
- Add metadata extraction

**Days 3-4**: Embedding & Storage

- Set up embedding service
- Implement FAISS wrapper
- Create ingestion pipeline

**Days 5-7**: API Development

- Create document upload endpoint
- Implement document listing
- Add error handling

### Week 2: RAG & UI (Days 8-14)

**Days 8-10**: RAG Implementation

- Create retriever service
- Implement RAG chain
- Add chat endpoint

**Days 11-12**: Frontend

- Build document upload UI
- Create chat interface
- Add status tracking

**Days 13-14**: Testing & Documentation

- Write unit tests
- Perform integration testing
- Update documentation
- End-to-end validation

---

## Deliverables Checklist

### Code Deliverables

- [ ] Document loaders (PDF, DOCX)
- [ ] Text chunking module
- [ ] Embedding service
- [ ] FAISS vector store
- [ ] Ingestion pipeline
- [ ] Retriever service
- [ ] RAG chain
- [ ] Document API endpoints
- [ ] Chat API endpoint
- [ ] Document upload UI
- [ ] Chat interface UI

### Documentation Deliverables

- [ ] API documentation
- [ ] User guide
- [ ] Architecture documentation
- [ ] Testing documentation

### Testing Deliverables

- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance benchmarks

---

## Next Steps After Phase 1

Once Phase 1 is complete, the platform will have:

- Working document ingestion
- Functional RAG chatbot
- Basic retrieval capabilities
- Source attribution

**Phase 2** will add:

- BM25 retrieval
- Hybrid search
- Reciprocal Rank Fusion
- Improved retrieval accuracy

---

## Appendix: Sample Code Snippets

### Document Upload Handler

```python
@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks
):
    """Upload and process documents."""
    results = []

    for file in files:
        # Validate file
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(400, "Invalid file type")

        # Save file
        file_path = await save_upload_file(file)

        # Process in background
        background_tasks.add_task(
            process_document,
            file_path,
            file.filename
        )

        results.append({
            "filename": file.filename,
            "status": "processing"
        })

    return {"status": "success", "documents": results}
```

### RAG Query Handler

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat request with RAG."""

    # Initialize RAG chain
    rag_chain = RAGChain(
        retriever=retriever_service,
        llm_factory=llm_factory,
        top_k=request.top_k or 5
    )

    # Generate answer
    result = await rag_chain.generate_answer(
        query=request.message,
        conversation_history=request.history
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        conversation_id=request.conversation_id,
        timestamp=datetime.utcnow()
    )
```

---

**Document Version**: 1.0
**Last Updated**: 2026-06-23
**Author**: Bob (Planning Mode)
**Status**: Ready for Implementation
