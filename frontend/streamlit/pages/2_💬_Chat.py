"""
RAG Chat Interface
Chat with your documents using RAG-powered responses.
"""

import streamlit as st
import requests
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Chat - RAG Platform",
    page_icon="💬",
    layout="wide"
)

st.title("💬 RAG Chat Assistant")
st.markdown("Ask questions about your uploaded documents")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Chat Settings")
    
    # RAG settings
    use_rag = st.toggle("Use RAG", value=True, help="Enable document retrieval")
    
    if use_rag:
        top_k = st.slider(
            "Documents to retrieve",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of relevant document chunks to retrieve"
        )
    else:
        top_k = 5
    
    # Generation settings
    st.subheader("🎛️ Generation")
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher = more creative, Lower = more focused"
    )
    
    max_tokens = st.slider(
        "Max tokens",
        min_value=100,
        max_value=2000,
        value=500,
        step=100,
        help="Maximum length of response"
    )
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()
    
    st.divider()
    
    # API Status
    st.subheader("🔌 Status")
    try:
        # Check API health
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
        
        # Check chat health
        chat_health = requests.get(f"{API_BASE_URL}/api/v1/chat/health", timeout=5)
        if chat_health.status_code == 200:
            health_data = chat_health.json()
            if health_data.get("llm_available"):
                st.success("✅ LLM Ready")
            else:
                st.warning("⚠️ LLM Not Available")
            
            # Show vector store info
            vector_info = health_data.get("vector_store", {})
            total_vectors = vector_info.get("total_vectors", 0)
            st.info(f"📊 {total_vectors} chunks indexed")
        
    except:
        st.error("❌ Disconnected")
    
    st.divider()
    
    # Info
    st.markdown("""
    ### 💡 Tips
    - Upload documents first in the Documents page
    - Enable RAG to use document context
    - Adjust temperature for creativity
    - Sources are shown with each response
    """)

# Main chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if message["role"] == "assistant" and "sources" in message:
                sources = message["sources"]
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)})"):
                        for idx, source in enumerate(sources, 1):
                            st.markdown(f"**{idx}. {source['filename']}**")
                            if source.get('page_number'):
                                st.caption(f"Page {source['page_number']}")
                            st.text(f"Score: {source['score']:.3f}")
                            st.markdown(f"> {source['content']}")
                            st.divider()

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        sources_placeholder = st.empty()
        
        try:
            # Prepare request
            request_data = {
                "message": prompt,
                "conversation_id": st.session_state.conversation_id,
                "use_rag": use_rag,
                "top_k": top_k,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Show loading
            with st.spinner("Thinking..."):
                # Call chat API
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/chat",
                    json=request_data,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response
                assistant_message = data["message"]["content"]
                sources = data.get("sources", [])
                conversation_id = data.get("conversation_id")
                
                # Update conversation ID
                if not st.session_state.conversation_id:
                    st.session_state.conversation_id = conversation_id
                
                # Display response
                message_placeholder.markdown(assistant_message)
                
                # Display sources
                if sources:
                    with sources_placeholder.expander(f"📚 Sources ({len(sources)})"):
                        for idx, source in enumerate(sources, 1):
                            st.markdown(f"**{idx}. {source['filename']}**")
                            if source.get('page_number'):
                                st.caption(f"Page {source['page_number']}")
                            st.text(f"Score: {source['score']:.3f}")
                            st.markdown(f"> {source['content']}")
                            st.divider()
                
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                    "sources": sources
                })
                
                # Show metadata
                metadata = data.get("metadata", {})
                st.caption(
                    f"⏱️ {metadata.get('processing_time', 0):.2f}s | "
                    f"🤖 {metadata.get('model', 'unknown')} | "
                    f"📊 {metadata.get('tokens_used', 0)} tokens"
                )
                
            else:
                error_msg = f"❌ Error: {response.text}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
        
        except requests.exceptions.ConnectionError:
            error_msg = "❌ Cannot connect to API. Make sure the backend is running."
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
        
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

# Welcome message if no messages
if len(st.session_state.messages) == 0:
    st.info("""
    👋 **Welcome to RAG Chat!**
    
    Ask questions about your uploaded documents and get AI-powered answers with source citations.
    
    **Example questions:**
    - "What is the main topic of the documents?"
    - "Summarize the key points from the report"
    - "What are the recommendations mentioned?"
    
    💡 Make sure you've uploaded documents in the Documents page first!
    """)

# Made with Bob