"""
T3V Chatbot - Demo 8 Module

A modular implementation of the T3V chatbot with ReAct agent capabilities.
"""

__version__ = "1.0.0"

# No explicit imports in __init__.py to avoid circular dependencies
# Modules should be imported directly from their specific files

# Expose key modules and functions
from .config import llm, memory, chat_history
from .graph import execute_with_langgraph, build_agent_graph
from .state import AgentState
from .classifier import classify_node, context_aware_router
from .service_tools import service_rag_node
from .movie_tools import movie_search_node, extract_movie_title
from .document_tools import advanced_rag_tool
from .search_tools import enhanced_web_search_node, web_search
from .response_tools import unified_answer_synthesizer_node
from .react_agent import react_process_query 