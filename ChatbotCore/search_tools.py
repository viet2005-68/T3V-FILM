import re
from typing import Dict, Any
from state import AgentState
from config import llm
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage
from response_tools import format_chat_history
from response_tools import self_correct_response
def web_search(query: str) -> str:
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        return results
    except Exception as e:
        return f"Web search failed: {str(e)}"


def web_search(query: str) -> str:
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        return results
    except Exception as e:
        return f"Web search failed: {str(e)}"

def enhanced_web_search_node(state: AgentState) -> AgentState:
    query = state["query"]
    chat_history = state["chat_history"]
    classification = state["classification"]["category"]
    
    # Format chat history for context
    history_context = format_chat_history(chat_history) if chat_history else ""
    
    # Enhance query for movie searches
    if classification == "MOVIE" and state["movie_results"].get("web_fallback", False):
        # Extract movie info from state if available
        if "movie_results" in state and state["movie_results"].get("search_term"):
            search_query = state["movie_results"]["search_term"]
        else:
            # Analyze query to extract better search terms
            try:
                analysis_prompt = f"""
                Extract key search terms from this movie-related query:
                "{query}"
                
                Return ONLY the essential search terms, no explanation needed.
                """
                response = llm.invoke(analysis_prompt)
                search_terms = response if isinstance(response, str) else response.content
                search_query = f"{search_terms.strip()} movie information"
            except:
                search_query = f"{query} movie information"
    else:
        search_query = query
    
    # Get web search results
    web_results = web_search(search_query)
    
    # Create a prompt that combines web results and chat history
    hybrid_prompt = f"""
    You are the T3V virtual assistant, helping a user with their question.
    
    CONVERSATION HISTORY:
    {history_context}
    
    CURRENT QUESTION:
    {query}
    
    WEB SEARCH RESULTS:
    {web_results}
    
    INSTRUCTIONS:
    1. Look at the conversation history to understand any context from previous messages
    2. Consider the web search results for factual information
    3. Use your general knowledge to fill gaps or provide additional context
    4. Synthesize a comprehensive answer that addresses the user's question directly
    5. If the web results don't provide useful information, rely more on your knowledge
    6. If the conversation history contains relevant information, refer back to it
    7. Respond in the same language as the user's question
    8. If you find on web (INFORMATION YOU GET IN WEB SEARCH RESULTS), you must contain detail and specific information detail contain this text "T3VDATABASE don't have information about it"
    Create a helpful, informative response that combines all available information:
    """
    
    # Call LLM for synthesis
    try:
        response = llm.invoke(hybrid_prompt)
        response_text = response if isinstance(response, str) else response.content
        
        # Apply self-correction with awareness of history
        final_answer = self_correct_response(query, response_text, classification, history_context)
        
        # Save both web results and synthesized answer
        state["retrieved_documents"] = web_results
        state["final_answer"] = final_answer + "\n\nSource: Web + Knowledge + T3V DON'T CONTAIN THIS INFORMATION"
        state["messages"].append(AIMessage(content=final_answer))
    except Exception as e:
        # Improved error handling with language detection
        is_vietnamese = any(c in query for c in "ăâêôơưđ") or "bố già" in query.lower()
        
        if is_vietnamese:
            fallback_response = f"Tôi gặp sự cố khi xử lý yêu cầu của bạn. Đây là những gì tôi tìm được:\n\n{web_results[:500]}... (Nguồn: Web)"
        else:
            fallback_response = f"I'm having trouble processing your request. Here's what I found:\n\n{web_results[:500]}... (Source: Web)"
            
        state["final_answer"] = fallback_response
        state["messages"].append(AIMessage(content=fallback_response))
    
    return state