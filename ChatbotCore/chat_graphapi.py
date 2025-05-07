from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, TypedDict
import json
import uvicorn
import re
import uuid
from pathlib import Path
import os
import sys
import time

# Import core dependencies
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
import importlib.util

# Environment setup
load_dotenv()
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Optional: Accelerate token generation
os.environ["OLLAMA_FLASH_ATTENTION"] = "1"

# API endpoints configuration
API_BASE_MOVIES = "http://localhost:8000/api/movies/"

# Setup LLM - Use the same one defined in config to ensure consistency
# Get the LLM from config.py if available, otherwise create a new one
try:
    from config import llm, memory as global_memory
    print("✅ Successfully imported LLM and memory from config")
except ImportError:
    print("⚠️ Could not import from config, creating new LLM and memory")
    # Fallback LLM
    llm = OllamaLLM(
        model="gemma2:2b",
        temperature=0.7,
        top_p=0.9,
        num_predict=256
    )
    # Fallback memory
    global_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

# Define the state class for LangGraph
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    query: str
    classification: Dict[str, Any]
    retrieved_documents: List[str]
    movie_results: Dict[str, Any]
    final_answer: str
    chat_history: List[Dict[str, Any]]

# Try to import embedding manager
try:
    from embedding_manager import EmbeddingManager
    embedding_manager = EmbeddingManager(storage_path="embeddings")
    
    # Process PDF if not already done
    file_path = Path(__file__).parent / "data" / "T3V Chatbot Training Data.pdf"
    if not os.path.exists("embeddings"):
        embedding_manager.process_pdf(file_path)
    
    # Get ChromaDB collection
    chroma_collection = embedding_manager.get_collection()
    print("✅ Successfully set up embedding manager")
except ImportError:
    print("⚠️ Could not import embedding manager, RAG functionality may be limited")
    chroma_collection = None

# Import from graph module with error handling
try:
    # First try to import directly
    from graph import process_query_with_langgraph
    print("✅ Successfully imported process_query_with_langgraph")
except ImportError:
    print("⚠️ Could not import process_query_with_langgraph directly, attempting dynamic import")
    
    # Try dynamic import - look for graph.py in the current directory
    graph_path = Path(__file__).parent / "graph.py"
    if graph_path.exists():
        try:
            spec = importlib.util.spec_from_file_location("graph_module", graph_path)
            graph_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(graph_module)
            process_query_with_langgraph = graph_module.process_query_with_langgraph
            print("✅ Successfully imported process_query_with_langgraph via dynamic import")
        except Exception as e:
            print(f"⚠️ Failed to dynamically import graph module: {e}")
            
            # Define fallback implementation
            def process_query_with_langgraph(query):
                # Fallback implementation for when the graph module isn't available
                from document_tools import advanced_rag_tool
                print("⚠️ Using fallback RAG implementation")
                return advanced_rag_tool(query)
    else:
        print("⚠️ graph.py not found, will use fallback implementation")
        
        # Define fallback implementation
        def process_query_with_langgraph(query):
            # Simple RAG implementation using chroma
            if chroma_collection:
                docs = chroma_collection.similarity_search(query, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                prompt = f"""Based on the following context, answer the user's question:
                
                Context:
                {context}
                
                User Question: {query}
                
                Answer:"""
                
                response = llm.invoke(prompt)
                return response if isinstance(response, str) else response.content
            else:
                return "I'm sorry, but I'm currently operating with limited functionality and can't access the knowledge base."

# Create FastAPI app
app = FastAPI(
    title="T3V Movie Chatbot API",
    description="API for Vietnamese Movie Recommendation and Information Chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = []

# Response model
class ChatResponse(BaseModel):
    response: str
    source: Optional[str] = None
    suggested_questions: Optional[List[str]] = []
    session_id: str

# Store for conversation memories (session management)
conversation_memories = {}
session_timestamps = {}  # For expiration tracking

# Session expiration time in seconds (24 hours)
SESSION_EXPIRY = 24 * 60 * 60

# Helper functions
def format_response_for_display(response: str) -> Dict[str, Any]:
    """Format the response for better display in React"""
    
    # Extract source if included in the response
    source = None
    if "\n\nSource:" in response:
        main_text, source_text = response.split("\n\nSource:", 1)
        source = f"Source: {source_text.strip()}"
        response = main_text.strip()
    
    # Generate suggested follow-up questions
    suggested_questions = generate_follow_up_questions(response)
    
    return {
        "response": add_markdown_formatting(response),
        "source": source,
        "suggested_questions": suggested_questions
    }

def add_markdown_formatting(text: str) -> str:
    """Add markdown formatting to enhance the display in React"""
    
    # Replace simple patterns with markdown equivalents
    formatted = text
    
    # Format movie titles with bold
    formatted = re.sub(r'"([^"]+)"', r'**"\1"**', formatted)
    
    # Handle Vietnamese movie titles
    formatted = re.sub(r'"([^"]+)"', r'**"\1"**', formatted)
    
    # Format bullet lists properly
    formatted = re.sub(r'(?m)^- ', r'\n• ', formatted)
    
    # Format numbered lists
    formatted = re.sub(r'(?m)^(\d+)\. ', r'\n\1. ', formatted)
    
    # Highlight important information
    formatted = re.sub(r'(?i)(Note|Important|Lưu ý|Quan trọng):', r'**\1:**', formatted)
    
    # Format actor names
    formatted = re.sub(r'(?<=diễn viên )([A-Za-zÀ-ỹ\s]+)(?=[,\.]|$)', r'*\1*', formatted)
    
    # Format ratings and years
    formatted = re.sub(r'(\d+\.\d+/10)', r'**\1**', formatted)
    formatted = re.sub(r'(\(\d{4}\))', r'*\1*', formatted)
    
    return formatted

def generate_follow_up_questions(response: str) -> List[str]:
    """Generate suggested follow-up questions based on the response"""
    
    # Detect language (simple approach)
    is_vietnamese = any(c in response for c in "ăâêôơưđ")
    
    # Prompt to generate follow-up questions in the appropriate language
    if is_vietnamese:
        prompt = f"""
        Dựa trên câu trả lời này của chatbot:
        
        "{response}"
        
        Tạo 2-3 câu hỏi tiếp theo tự nhiên mà người dùng có thể hỏi. 
        Câu hỏi nên:
        - Liên quan trực tiếp đến nội dung phản hồi
        - Ngắn gọn (tối đa 10 từ)
        - Bằng tiếng Việt
        - Định dạng dưới dạng danh sách đơn giản không có số hoặc dấu đầu dòng
        
        Chỉ trả về các câu hỏi, mỗi câu một dòng, không có văn bản bổ sung:
        """
    else:
        prompt = f"""
        Based on this chatbot response:
        
        "{response}"
        
        Generate 2-3 natural follow-up questions a user might ask next. 
        The questions should be:
        - Directly related to the response content
        - Short (max 10 words)
        - In English
        - Formatted as a simple list without numbers or bullet points
        
        Return only the questions, one per line, with no additional text:
        """
    
    try:
        result = llm.invoke(prompt)
        content = result if isinstance(result, str) else result.content
        
        # Extract questions (one per line)
        questions = [q.strip() for q in content.split('\n') if q.strip() and '?' in q]
        
        # Keep only 3 max, remove any numbering or bullets
        clean_questions = []
        for q in questions[:3]:
            # Remove any leading numbers, dashes, etc.
            clean_q = re.sub(r'^[\d\-\*\•\.\s]+', '', q).strip()
            clean_questions.append(clean_q)
            
        return clean_questions
    except Exception as e:
        print(f"Error generating follow-up questions: {e}")
        return []

def get_session_memory(session_id):
    """Get or create a memory instance for the given session ID"""
    # Clean expired sessions
    clean_expired_sessions()
    
    # Create new session if needed
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Create or get session memory
    if session_id not in conversation_memories:
        conversation_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        # Set timestamp for new session
        session_timestamps[session_id] = time.time()
    else:
        # Update timestamp for existing session
        session_timestamps[session_id] = time.time()
    
    return session_id, conversation_memories[session_id]

def clean_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, timestamp in session_timestamps.items():
        if current_time - timestamp > SESSION_EXPIRY:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        if session_id in conversation_memories:
            del conversation_memories[session_id]
        if session_id in session_timestamps:
            del session_timestamps[session_id]
    
    if expired_sessions:
        print(f"Cleaned {len(expired_sessions)} expired sessions")

def convert_messages_to_memory_format(messages):
    """Convert message dict objects to LangChain message objects"""
    memory_messages = []
    for msg in messages:
        if msg["role"].lower() in ["user", "human"]:
            memory_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"].lower() in ["assistant", "ai", "system"]:
            memory_messages.append(AIMessage(content=msg["content"]))
    return memory_messages

def sync_memories(session_memory):
    """Sync the session memory with the global memory"""
    # Clear global memory to avoid duplication
    global_memory.clear()
    
    # Copy all messages from session memory to global memory
    for msg in session_memory.chat_memory.messages:
        if isinstance(msg, HumanMessage):
            global_memory.chat_memory.add_user_message(msg.content)
        elif isinstance(msg, AIMessage):
            global_memory.chat_memory.add_ai_message(msg.content)
    
    return global_memory

# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get or create session memory
        session_id, session_memory = get_session_memory(request.session_id)
        
        # Clear session memory if history is provided
        if request.history:
            session_memory.clear()
            
            # Load history into session memory
            for msg in request.history:
                if msg["role"].lower() in ["user", "human"]:
                    session_memory.chat_memory.add_user_message(msg["content"])
                elif msg["role"].lower() in ["assistant", "ai", "system"]:
                    session_memory.chat_memory.add_ai_message(msg["content"])
        
        # Sync session memory with global memory to ensure consistency
        sync_memories(session_memory)
        
        # Log the messages in memory for debugging
        print(f"Memory contains {len(global_memory.chat_memory.messages)} messages before processing")
        
        # Process query using langgraph with synced memory
        response = process_query_with_langgraph(request.question)
        
        # Update both memories with the new exchange
        session_memory.chat_memory.add_user_message(request.question)
        session_memory.chat_memory.add_ai_message(response)
        
        # Also update global memory to keep them in sync
        global_memory.chat_memory.add_user_message(request.question)
        global_memory.chat_memory.add_ai_message(response)
        
        # Format the response
        formatted_response = format_response_for_display(response)
        
        return ChatResponse(session_id=session_id, **formatted_response)
        
    except Exception as e:
        print(f"Error processing chat: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple response
        try:
            session_id = request.session_id or str(uuid.uuid4())
            fallback_response = "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
            
            # Try RAG as fallback if available
            if chroma_collection:
                try:
                    docs = chroma_collection.similarity_search(request.question, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    
                    prompt = f"""Based on the following context, answer the user's question:
                    
                    Context:
                    {context}
                    
                    User Question: {request.question}
                    
                    Answer:"""
                    
                    fallback_response = llm.invoke(prompt)
                    if not isinstance(fallback_response, str):
                        fallback_response = fallback_response.content
                except Exception as inner_e:
                    print(f"RAG fallback failed: {inner_e}")
            
            formatted_fallback = format_response_for_display(fallback_response)
            return ChatResponse(session_id=session_id, **formatted_fallback)
        except Exception as inner_e:
            print(f"Fallback also failed: {inner_e}")
            raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    # Clean expired sessions first
    clean_expired_sessions()
    
    if session_id not in conversation_memories:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_memory = conversation_memories[session_id]
    history = []
    
    for message in session_memory.chat_memory.messages:
        if isinstance(message, HumanMessage):
            history.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            history.append({"role": "assistant", "content": message.content})
    
    return {"session_id": session_id, "history": history}

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_memories:
        # Clear the session memory
        conversation_memories[session_id].clear()
        
        # Also clear global memory if it matches this session
        global_memory.clear()
        
        return {"status": "success", "message": "Conversation history cleared"}
    
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions and their last activity time"""
    # Clean expired sessions first
    clean_expired_sessions()
    
    sessions = []
    for session_id, timestamp in session_timestamps.items():
        if session_id in conversation_memories:
            # Calculate message count
            message_count = len(conversation_memories[session_id].chat_memory.messages)
            # Format last activity time
            last_activity = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            
            sessions.append({
                "session_id": session_id,
                "last_activity": last_activity,
                "message_count": message_count
            })
    
    return {"sessions": sessions, "total": len(sessions)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Clean expired sessions first
    clean_expired_sessions()
    
    return {
        "status": "ok", 
        "message": "T3V Chatbot API is running",
        "active_sessions": len(conversation_memories),
        "memory_type": type(global_memory).__name__,
        "llm_type": type(llm).__name__
    }

# Run the server if this file is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting T3V Chatbot API on port {port}")
    print(f"📊 Memory type: {type(global_memory).__name__}")
    print(f"🤖 LLM type: {type(llm).__name__}")
    
    uvicorn.run("app:app", host="localhost", port=port, reload=True)