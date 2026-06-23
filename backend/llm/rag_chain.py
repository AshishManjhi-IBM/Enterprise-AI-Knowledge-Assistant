"""
RAG (Retrieval-Augmented Generation) chain.
Combines document retrieval with LLM generation.
"""

from typing import List, Dict, Any, Optional
import time
from backend.retrievers.retriever import DocumentRetriever, RetrievalResult
from backend.llm.llm_service import LLMService
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RAGChain:
    """
    RAG chain that combines retrieval and generation.
    
    Retrieves relevant documents and uses them as context for LLM generation.
    """
    
    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        llm_service: Optional[LLMService] = None
    ):
        """
        Initialize RAG chain.
        
        Args:
            retriever: Document retriever
            llm_service: LLM service for generation
        """
        self.retriever = retriever or DocumentRetriever()
        self.llm_service = llm_service or LLMService()
        
        logger.info("Initialized RAGChain")
    
    async def generate_response(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            document_ids: Filter by document IDs
            conversation_history: Previous conversation messages
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant documents
            retrieval_start = time.time()
            
            retrieval_results = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                document_ids=document_ids
            )
            
            retrieval_time = time.time() - retrieval_start
            
            logger.info(
                f"Retrieved {len(retrieval_results)} documents "
                f"in {retrieval_time:.3f}s"
            )
            
            # Step 2: Format context from retrieved documents
            context = self.retriever.format_context(
                retrieval_results,
                max_length=3000,  # Limit context length
                include_metadata=True
            )
            
            # Step 3: Build prompt with context
            prompt = self._build_prompt(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            
            # Step 4: Generate response
            generation_start = time.time()
            
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            generation_time = time.time() - generation_start
            
            logger.info(f"Generated response in {generation_time:.3f}s")
            
            # Step 5: Format sources
            sources = self._format_sources(retrieval_results)
            
            # Calculate total time
            total_time = time.time() - start_time
            
            return {
                "response": response["text"],
                "sources": sources,
                "metadata": {
                    "model": response.get("model", "unknown"),
                    "tokens_used": response.get("tokens_used", 0),
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "total_time": total_time,
                    "documents_retrieved": len(retrieval_results)
                }
            }
            
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            raise
    
    async def generate_response_stream(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Generate a streaming response using RAG.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            document_ids: Filter by document IDs
            conversation_history: Previous conversation messages
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Yields:
            Response chunks
        """
        try:
            # Step 1: Retrieve relevant documents
            retrieval_results = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                document_ids=document_ids
            )
            
            # Step 2: Format context
            context = self.retriever.format_context(
                retrieval_results,
                max_length=3000,
                include_metadata=True
            )
            
            # Step 3: Build prompt
            prompt = self._build_prompt(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            
            # Step 4: Stream response
            async for chunk in self.llm_service.generate_stream(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield chunk
            
            # Step 5: Send sources at the end
            sources = self._format_sources(retrieval_results)
            yield {
                "type": "sources",
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"RAG streaming failed: {e}")
            raise
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build prompt with context and conversation history.
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous messages
            
        Returns:
            Formatted prompt
        """
        # System message
        system_message = (
            "You are a helpful AI assistant that answers questions based on the provided context. "
            "Always cite your sources by referring to the document names and page numbers when available. "
            "If the context doesn't contain enough information to answer the question, say so clearly. "
            "Be concise and accurate in your responses."
        )
        
        # Build prompt parts
        prompt_parts = [system_message, "\n\n"]
        
        # Add conversation history if provided
        if conversation_history:
            prompt_parts.append("Previous conversation:\n")
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.capitalize()}: {content}\n")
            prompt_parts.append("\n")
        
        # Add context
        if context:
            prompt_parts.append("Context from documents:\n")
            prompt_parts.append(context)
            prompt_parts.append("\n\n")
        
        # Add current query
        prompt_parts.append(f"Question: {query}\n\n")
        prompt_parts.append("Answer:")
        
        return "".join(prompt_parts)
    
    def _format_sources(
        self,
        retrieval_results: List[RetrievalResult]
    ) -> List[Dict[str, Any]]:
        """
        Format retrieval results as source references.
        
        Args:
            retrieval_results: List of retrieval results
            
        Returns:
            List of formatted sources
        """
        sources = []
        
        for result in retrieval_results:
            source = {
                "document_id": result.document_id,
                "filename": result.filename,
                "chunk_id": result.chunk_id,
                "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                "score": round(result.score, 3),
                "page_number": result.page_number
            }
            sources.append(source)
        
        return sources
    
    async def answer_question(
        self,
        question: str,
        use_rag: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Answer a question with or without RAG.
        
        Args:
            question: User question
            use_rag: Whether to use RAG (retrieval)
            **kwargs: Additional arguments for generation
            
        Returns:
            Response dictionary
        """
        if use_rag:
            return await self.generate_response(query=question, **kwargs)
        else:
            # Direct LLM generation without retrieval
            response = await self.llm_service.generate(
                prompt=question,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500)
            )
            
            return {
                "response": response["text"],
                "sources": [],
                "metadata": {
                    "model": response.get("model", "unknown"),
                    "tokens_used": response.get("tokens_used", 0),
                    "documents_retrieved": 0
                }
            }


# Made with Bob