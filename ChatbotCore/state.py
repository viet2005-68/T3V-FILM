from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    query: str
    classification: Dict[str, Any]
    retrieved_documents: List[str]
    movie_results: Dict[str, Any]
    final_answer: str
    chat_history: List[Dict[str, Any]]
    token: str

def convert_message_to_dict(message):
    """Convert LangChain message objects to dictionaries with role and content."""
    if hasattr(message, "content") and hasattr(message, "type"):
        # Convert HumanMessage/AIMessage to dict
        role = "human" if message.type == "human" else "ai"
        return {"role": role, "content": message.content}
    # If it's already in the right format, return as is
    elif isinstance(message, dict) and "role" in message and "content" in message:
        return message
    # Fallback for other formats
    else:
        content = str(message)
        return {"role": "unknown", "content": content}

def format_chat_history(messages, max_turns=4):
    """Format conversation turns for context with improved truncation and source tracking."""
    if not messages:
        return ""
    
    # Get the most recent conversations (limited to max_turns)
    recent_messages = messages[-2*max_turns:]  # Get pairs of messages
    
    # Format messages with roles and track sources for context
    formatted_history = []
    previous_sources = []
    
    for msg in recent_messages:
        if isinstance(msg, dict):
            # Already in dict format
            role = msg.get('role', 'Unknown')
            content = msg.get('content', '')
            
            # Track sources from assistant messages
            if role == 'ai' or role == 'assistant':
                if "source: vectordb" in content.lower():
                    previous_sources.append("SERVICE")
                elif "source: tmdb" in content.lower():
                    previous_sources.append("MOVIE")
                elif "source: web" in content.lower():
                    previous_sources.append("OTHER")
                    
            # Format the message
            role_label = "User" if role == 'human' else "Assistant"
            formatted_history.append(f"{role_label}: {content}")
        else:
            # Handle Message objects
            role = "User" if msg.type == "human" else "Assistant"
            content = msg.content
            
            # Track sources from assistant messages
            if role == "Assistant":
                if "source: vectordb" in content.lower():
                    previous_sources.append("SERVICE")
                elif "source: tmdb" in content.lower():
                    previous_sources.append("MOVIE")
                elif "source: web" in content.lower():
                    previous_sources.append("OTHER")
                    
            formatted_history.append(f"{role}: {content}")
    
    # Add source tracking information
    source_context = ""
    if previous_sources:
        most_recent_source = previous_sources[-1] if previous_sources else "UNKNOWN"
        source_context = f"\n[Previous topic category: {most_recent_source}]"
    
    # If history is too long, include the first exchanges and the most recent ones
    if len(formatted_history) > 2*max_turns:
        return "\n".join(formatted_history[:2] + ["..."] + formatted_history[-2*max_turns+2:]) + source_context
    
    return "\n".join(formatted_history) + source_context