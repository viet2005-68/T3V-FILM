import json
import re
from typing import Dict, Any, List
from state import AgentState, format_chat_history
from config import llm
from document_tools import get_unique_documents, self_rag_search
from search_tools import web_search
from movie_tools import movie_search_by_title
from response_tools import self_correct_response
from document_tools import chroma_collection
def react_agent_step(state: AgentState, observation: str = None) -> Dict[str, Any]:
    """
    Implements ReAct agent logic for reasoning, action, and reflection.
    
    Args:
        state: Current agent state
        observation: Optional observation from previous action
        
    Returns:
        Updated state with next action
    """
    query = state.get("query", "")
    classification = state.get("classification", {})
    chat_history = state.get("chat_history", [])
    
    # Format history for context
    history_context = format_chat_history(chat_history) if chat_history else ""
    
    # Initialize reasoning tracker
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    
    # Build ReAct prompt
    react_prompt = f"""
    You are an intelligent problem-solving agent for the T3V streaming platform.
    
    USER QUERY: {query}
    
    CONVERSATION HISTORY:
    {history_context}
    
    CURRENT STATE:
    - Classification: {classification.get("category", "Unknown")} (Confidence: {classification.get("confidence", "Unknown")})
    - Retrieved Information: {state.get("retrieved_documents", "None yet")}
    
    PREVIOUS OBSERVATIONS:
    {observation if observation else "No previous observations."}
    
    TASK:
    Follow the ReAct (Reasoning + Acting) approach:
    1. Think through the current state and user query
    2. Decide what action to take next
    3. Provide the reasoning behind your decision
    
    AVAILABLE ACTIONS:
    - SEARCH_DOCUMENTS: Search T3V knowledge base documents
    - SEARCH_WEB: Search the web for information
    - SEARCH_MOVIES: Search for movie information
    - REFINE_QUERY: Refine the search query for better results
    - ANSWER: Generate a final answer based on information collected
    
    Your response should be in this JSON format:
    {{
        "thought": "Your reasoning about the current state and what to do next",
        "action": "One of the AVAILABLE ACTIONS",
        "action_input": "Parameters for the selected action",
        "reflection": "Brief reflection on your choice and expectations"
    }}
    """
    
    try:
        # Call LLM for agent reasoning
        response = llm.invoke(react_prompt)
        content = response if isinstance(response, str) else response.content
        
        # Try to parse JSON from response
        try:
            react_step = json.loads(content)
        except json.JSONDecodeError:
            # Fall back to regex extraction
            thought_match = re.search(r'"thought":\s*"([^"]*)"', content)
            action_match = re.search(r'"action":\s*"([^"]*)"', content)
            action_input_match = re.search(r'"action_input":\s*"([^"]*)"', content)
            reflection_match = re.search(r'"reflection":\s*"([^"]*)"', content)
            
            react_step = {
                "thought": thought_match.group(1) if thought_match else "Need to process the user query",
                "action": action_match.group(1) if action_match else "ANSWER",
                "action_input": action_input_match.group(1) if action_input_match else query,
                "reflection": reflection_match.group(1) if reflection_match else "Default reasoning path"
            }
        
        # Store this reasoning step
        state["reasoning_steps"].append(react_step)
        
        # Execute the selected action
        action = react_step.get("action", "ANSWER")
        action_input = react_step.get("action_input", "")
        
        if action == "SEARCH_DOCUMENTS":
            # Enhanced document search with Self-RAG
            initial_docs = get_unique_documents(action_input, chroma_collection)
            self_rag_results = self_rag_search(action_input, initial_docs, state)
            state["retrieved_documents"] = self_rag_results["retrieved_documents"]
            state["search_quality"] = self_rag_results["final_quality_score"]
            
        elif action == "SEARCH_WEB":
            web_results = web_search(action_input)
            state["web_results"] = web_results
            
        elif action == "SEARCH_MOVIES":
            # Call movie search with refined input
            movie_info = {}
            # Parse movie search criteria from action_input
            title_match = re.search(r'title:\s*"([^"]*)"', action_input)
            if title_match:
                movie_info["title"] = title_match.group(1)
                movie_results = movie_search_by_title(movie_info["title"])
                state["movie_results"] = movie_results
            else:
                # Generic movie search
                movie_results = movie_search_by_title(action_input)
                state["movie_results"] = movie_results
            
        elif action == "REFINE_QUERY":
            # Update the query with a refined version
            state["refined_query"] = action_input
            
        elif action == "ANSWER":
            # Generate a final answer
            category = classification.get("category", "OTHER")
            
            answer_prompt = f"""
            Based on all the information gathered, create a comprehensive answer to the user's query.
            
            ORIGINAL QUERY: {query}
            CATEGORY: {category}
            
            AVAILABLE INFORMATION:
            - Documents: {state.get("retrieved_documents", "None")}
            - Web Results: {state.get("web_results", "None")}
            - Movie Results: {state.get("movie_results", "None")}
            
            CHAT HISTORY:
            {history_context}
            
            REASONING STEPS:
            {json.dumps(state["reasoning_steps"], indent=2)}
            
            Create a clear, helpful response in the language of the original query.
            For SERVICE questions, prioritize information from our documents.
            For MOVIE questions, include specific movie details if available.
            For OTHER questions, combine web results with general knowledge.
            
            Add source attribution at the end.
            """
            
            final_response = llm.invoke(answer_prompt)
            content = final_response if isinstance(final_response, str) else final_response.content
            
            # Apply self-correction
            final_answer = self_correct_response(query, content, category, history_context)
            state["final_answer"] = final_answer
        
        return state
        
    except Exception as e:
        print(f"Error in ReAct agent: {e}")
        # Default action on error
        return {
            "thought": f"Error occurred: {str(e)}. Falling back to default handling.",
            "action": "ANSWER",
            "action_input": query,
            "reflection": "Error recovery path"
        }


def react_process_query(state: AgentState) -> AgentState:
    """
    Process a query using the ReAct agent approach with iterative steps.
    
    Args:
        state: Initial agent state with query
        
    Returns:
        Final state with answer
    """
    # Maximum number of reasoning steps
    max_steps = 5
    query = state["query"]
    
    # Initialize state if empty
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    
    # Execute agent steps iteratively
    step = 0
    observation = None
    
    while step < max_steps:
        print(f"\nExecuting ReAct step {step+1}...")
        
        # Execute a single agent step
        updated_state = react_agent_step(state, observation)
        
        # Update full state
        for key, value in updated_state.items():
            if key != "reasoning_steps":  # Avoid duplicating steps
                state[key] = value
        
        # Check if we have a final answer
        if "final_answer" in updated_state:
            print("Final answer reached, ending ReAct process.")
            return state
        
        # Get the last reasoning step
        last_step = state["reasoning_steps"][-1] if state["reasoning_steps"] else None
        
        if not last_step:
            print("No reasoning step produced, ending ReAct process.")
            break
            
        # Create observation for next step
        action = last_step.get("action", "")
        if action == "SEARCH_DOCUMENTS":
            observation = f"Retrieved {len(state.get('retrieved_documents', [])) if isinstance(state.get('retrieved_documents', []), list) else 1} documents with quality score: {state.get('search_quality', 0):.2f}"
        elif action == "SEARCH_WEB":
            observation = f"Web search completed, found information: {state.get('web_results', '')[:200]}..."
        elif action == "SEARCH_MOVIES":
            movie_results = state.get("movie_results", {})
            total = movie_results.get("total_results", 0)
            observation = f"Found {total} movies matching the criteria."
        elif action == "REFINE_QUERY":
            observation = f"Query refined to: {state.get('refined_query', query)}"
        else:
            observation = "Action completed, ready for next step."
        
        step += 1
    
    # If we reach max steps without an answer, generate a final answer
    if "final_answer" not in state:
        print("Reached maximum ReAct steps, generating final answer.")
        
        try:
            category = state.get("classification", {}).get("category", "OTHER")
            
            # For SERVICE questions, use retrieved documents
            if category == "SERVICE" and state.get("retrieved_documents"):
                documents = state.get("retrieved_documents", [])
                if isinstance(documents, list):
                    context = "\n\n".join(documents[:5])
                else:
                    context = documents
                
                answer_prompt = f"""
                Create a comprehensive answer based on these documents:
                
                QUERY: {query}
                
                DOCUMENTS:
                {context}
                
                Answer the query directly and professionally, focusing on T3V service information.
                """
                
                response = llm.invoke(answer_prompt)
                content = response if isinstance(response, str) else response.content
                state["final_answer"] = content + "\n\nSource: VectorDB"
                
            # For MOVIE questions, use movie results
            elif category == "MOVIE" and state.get("movie_results"):
                movie_data = state.get("movie_results", {})
                
                answer_prompt = f"""
                Create a helpful movie information response:
                
                QUERY: {query}
                
                MOVIE DATA:
                {json.dumps(movie_data, indent=2)}
                
                Provide a well-formatted response about these movies.
                """
                
                response = llm.invoke(answer_prompt)
                content = response if isinstance(response, str) else response.content
                state["final_answer"] = content + "\n\nSource: TMDB"
                
            # For OTHER questions or fallbacks, use web results
            else:
                web_results = state.get("web_results", "No web results found.")
                
                answer_prompt = f"""
                Create an informative answer based on web results:
                
                QUERY: {query}
                
                WEB INFORMATION:
                {web_results[:1500]}
                
                Provide a clear, helpful response based on this information.
                """
                
                response = llm.invoke(answer_prompt)
                content = response if isinstance(response, str) else response.content
                state["final_answer"] = content + "\n\nSource: Web"
                
        except Exception as e:
            print(f"Error generating final answer: {e}")
            # Fallback response
            state["final_answer"] = f"I encountered an issue while processing your question. Please try rephrasing your query or contact T3V support for assistance.\n\nError: {str(e)}"
    
    return state