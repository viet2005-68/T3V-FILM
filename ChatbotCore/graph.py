import json
from langgraph.graph import END, StateGraph
from typing import Dict, Any
from state import AgentState, convert_message_to_dict
from classifier import classify_node, context_aware_router
from service_tools import service_rag_node
from movie_tools import movie_search_node
from search_tools import enhanced_web_search_node
from react_agent import react_process_query
from response_tools import unified_answer_synthesizer_node
from config import chat_history, memory

def build_agent_graph():
    workflow = StateGraph(AgentState)

    # Add nodes with enhanced versions
    workflow.add_node("classifier", classify_node)
    workflow.add_node("service_node", service_rag_node)
    workflow.add_node("movie_node", movie_search_node)
    workflow.add_node("web_node", enhanced_web_search_node)
    workflow.add_node("react_node", react_process_query)  # Add ReAct node
    workflow.add_node("synthesizer", unified_answer_synthesizer_node)

    # Define initial routing from classifier with added ReAct support for low confidence
    workflow.add_conditional_edges(
        "classifier",
        lambda state: "react_node" if state["classification"].get("confidence", "medium") in ["low", "very low"] else context_aware_router(state),
        {
            "service_node": "service_node",
            "movie_node": "movie_node",
            "web_node": "web_node",
            "react_node": "react_node"  # Route low confidence queries to ReAct
        }
    )
    
    # Add conditional edges from movie_node based on search results
    # If the movie search required fallback to web search, route to the synthesizer directly
    workflow.add_conditional_edges(
        "movie_node",
        lambda state: "synthesizer" if state["movie_results"].get("web_fallback", False) else "synthesizer",
        {
            "synthesizer": "synthesizer"
        }
    )
    
    # Add edge from ReAct node to synthesizer
    workflow.add_edge("react_node", "synthesizer")
    
    # Standard routing for other nodes
    workflow.add_edge("service_node", "synthesizer")
    workflow.add_edge("web_node", "synthesizer")
    workflow.add_edge("synthesizer", END)

    # Set entry point
    workflow.set_entry_point("classifier")

    return workflow.compile()


# In graph.py
def process_query_with_langgraph(query: str) -> str:
    """
    Process a user query with the LangGraph workflow.
    
    Args:
        query: The user's query text
        
    Returns:
        The final answer from the agent
    """
    if not query or not isinstance(query, str):
        return "Vui lòng nhập câu hỏi hợp lệ."
    
    try:
        # Import memory directly to ensure we use the same object
        from config import memory
        
        # Format chat history from the memory object
        messages = []
        if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
            from langchain_core.messages import HumanMessage, AIMessage
            
            for msg in memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "human", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "ai", "content": msg.content})
        
        # Create initial state with the extracted chat history
        initial_state = {
            "messages": messages,
            "query": query,
            "classification": {},
            "retrieved_documents": [],
            "movie_results": {},
            "final_answer": "",
            "chat_history": messages  # Use the extracted messages
        }
        
        # Get the graph
        graph = build_agent_graph()
        
        # Execute the graph
        result = graph.invoke(initial_state)
        
        return result["final_answer"]
    
    except Exception as e:
        print(f"Error processing query: {e}")
        return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn: {str(e)}"

def execute_with_langgraph(query):
    """Main execution loop for the chatbot with LangGraph."""
    global chat_history, memory
    
    if query.strip().lower() in ["exit", "quit", "thoát"]:
        print("👋 Tạm biệt!")
        return None
    
    if query.strip().lower() in ["reset", "clear", "xóa"]:
        chat_history = []
        memory.clear()
        print("🧹 Đã xóa lịch sử chat.")
        return "Đã xóa lịch sử chat."
    
    # Extract chat history from memory if it's being used
    if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
        # Convert memory messages to chat_history format
        from langchain_core.messages import HumanMessage, AIMessage
        
        temp_history = []
        for msg in memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                temp_history.append({"role": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                temp_history.append({"role": "ai", "content": msg.content})
                
        # Use memory's chat history if available and more current
        if temp_history and len(temp_history) > len(chat_history):
            chat_history = temp_history
    
    # Process the query using chat_history
    response = process_query_with_langgraph(query, chat_history)
    
    # Update both chat_history and memory for consistency
    chat_history.append({"role": "human", "content": query})
    chat_history.append({"role": "ai", "content": response})
    
    # Update memory to stay in sync with chat_history
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)
    
    return response
