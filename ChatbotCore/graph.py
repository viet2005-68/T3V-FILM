import json
from langgraph.graph import END, StateGraph
from typing import Dict, Any, List
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
    def router(state):
        # Preserve token in state
        token = state.get("token")
        print(f"🔑 Token in router: {token[:10] if token else 'None'}...")
        if token:
            state["token"] = token
            
        # Route based on classification
        if state["classification"].get("confidence", "medium") in ["low", "very low"]:
            return "react_node"
        return context_aware_router(state)

    workflow.add_conditional_edges(
        "classifier",
        router,
        {
            "service_node": "service_node",
            "movie_node": "movie_node",
            "web_node": "web_node",
            "react_node": "react_node"  # Route low confidence queries to ReAct
        }
    )
    
    # Add conditional edges from movie_node based on search results
    def movie_router(state):
        # Preserve token in state
        token = state.get("token")
        if token:
            state["token"] = token
            
        # Route based on search results
        if state["movie_results"].get("web_fallback", False):
            return "synthesizer"
        return "synthesizer"

    workflow.add_conditional_edges(
        "movie_node",
        movie_router,
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
def process_query_with_langgraph(query: str, history: List[Dict[str, Any]], token: str = None) -> str:
    """
    Process a user query with the LangGraph workflow.
    
    Args:
        query: The user's query text
        history: Chat history
        token: Authentication token
        
    Returns:
        The final answer from the agent
    """
    if not query or not isinstance(query, str):
        return "Vui lòng nhập câu hỏi hợp lệ."
    
    try:
        print(f"🔑 Token in process_query_with_langgraph: {token[:10] if token else 'None'}...")
        
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
        
        # Create initial state with the extracted chat history and token
        state_dict = {
            "messages": messages,
            "query": query,
            "classification": {},
            "retrieved_documents": [],
            "movie_results": {},
            "final_answer": "",
            "chat_history": messages,  # Use the extracted messages
        }
        
        # Add token if provided
        if token:
            state_dict["token"] = token
            
        # Create AgentState instance
        initial_state = AgentState(state_dict)
        
        print(f"🔑 Token in initial_state: {initial_state.get('token', '')[:10] if initial_state.get('token') else 'None'}...")
        
        # Get the graph
        graph = build_agent_graph()
        
        # Execute the graph with explicit state passing
        result = graph.invoke(initial_state)
        
        # Verify token in result
        print(f"🔑 Token in result: {result.get('token', '')[:10] if result.get('token') else 'None'}...")
        
        return result["final_answer"]
    
    except Exception as e:
        print(f"Error processing query: {e}")
        return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn: {str(e)}"

def execute_with_langgraph(query, token: str = None, memory=None):
    """Main execution loop for the chatbot with LangGraph."""
    global chat_history
    
    print(f"🔑 Token in execute_with_langgraph: {token[:10] if token else 'None'}...")
    
    if query.strip().lower() in ["exit", "quit", "thoát"]:
        print("👋 Tạm biệt!")
        return None
    
    if query.strip().lower() in ["reset", "clear", "xóa"]:
        chat_history = []
        if memory:
            memory.clear()
        print("🧹 Đã xóa lịch sử chat.")
        return "Đã xóa lịch sử chat."
    
    # Extract chat history from memory if it's being used
    if memory and hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
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
    
    # Process the query using chat_history and token
    response = process_query_with_langgraph(query, chat_history, token)
    
    # Update both chat_history and memory for consistency
    chat_history.append({"role": "human", "content": query})
    chat_history.append({"role": "ai", "content": response})
    
    # Update memory to stay in sync with chat_history
    if memory:
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(response)
    
    return response
