import re
import requests
from typing import Dict, Any
from config import API_BASE_MOVIES
from state import AgentState
from search_tools import web_search
from document_tools import advanced_rag_tool
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
import json
from config import llm

def movie_search_by_title(title: str):
    # Full sanitation
    clean_title = (
        title.strip()
             .replace("```", "")
             .replace("\n", "")
             .replace("\r", "")
    )

    print(f"🔍 Searching for title: '{clean_title}'")

    try:
        response = requests.get(API_BASE_MOVIES, params={"title": clean_title})
        response.raise_for_status()
        result = response.json()
        
        # Format and limit results
        if isinstance(result, list) and result:
            return {
                "total_results": len(result),
                "movies": result[:5]
            }
        else:
            return {"message": "No movies found with that title.", "total_results": 0}
    except requests.RequestException as e:
        print(f"❌ Error during movie search: {e}")
        return {"error": f"Movie search failed: {str(e)}", "total_results": 0}

def movie_search_by_genre(genre: str):
    clean_genre = genre.strip().lower()
    print(f"🔍 Searching for genre: '{clean_genre}'")
    
    try:
        response = requests.get(API_BASE_MOVIES, params={"genre": clean_genre})
        response.raise_for_status()
        result = response.json()
        
        movies = result.get("movies", [])
        if movies:
            return {
                "total_results": len(movies),
                "movies": movies[:5]  # Limit to top 5 movies
            }
        else:
            return {"message": f"No movies found in the {genre} genre.", "total_results": 0}
    except requests.RequestException as e:
        return {"error": f"Genre search failed: {str(e)}", "total_results": 0}

def movie_search_by_year(year: str):
    try:
        year = year.strip()
        print(f"🔍 Searching for year: '{year}'")
        
        response = requests.get(API_BASE_MOVIES, params={"year": year})
        response.raise_for_status()
        result = response.json()
        
        movies = result.get("movies", [])
        if movies:
            return {
                "total_results": len(movies),
                "movies": movies[:5]  # Limit to top 5 movies
            }
        else:
            return {"message": f"No movies found from year {year}.", "total_results": 0}
    except requests.RequestException as e:
        return {"error": f"Year search failed: {str(e)}", "total_results": 0}

def movie_search_node(state: AgentState) -> AgentState:
    query = state["query"]
    chat_history = state["chat_history"]
    
    # Check for follow-up/contextual movie queries
    is_followup = False
    previous_movie_context = ""
    
    # Extract any previous movie context from history
    if chat_history:
        recent_messages = chat_history[-6:] if len(chat_history) >= 6 else chat_history
        
        # Check for follow-up indicators
        followup_indicators = ["what about", "how about", "tell me more", "and", "also", "another", 
                              "còn", "vậy còn", "thêm", "tiếp", "và", "nữa"]
        
        is_simple_followup = (
            len(query.split()) <= 4 or 
            any(indicator in query.lower() for indicator in followup_indicators) or
            query.strip().startswith("còn") or 
            query.strip().startswith("và") or
            query.strip().startswith("and")
        )
        
        # Extract relevant movie context from previous exchanges
        for i in range(len(recent_messages)-1, 0, -2):
            if i >= 1 and i < len(recent_messages):
                if isinstance(recent_messages[i], dict) and recent_messages[i].get('role') == 'ai':
                    ai_content = recent_messages[i].get('content', '').lower()
                    
                    # Check if previous response was movie-related
                    if "source: tmdb" in ai_content or "nguồn: tmdb" in ai_content:
                        if isinstance(recent_messages[i-1], dict) and recent_messages[i-1].get('role') == 'human':
                            previous_query = recent_messages[i-1].get('content', '')
                            previous_movie_context = previous_query
                            is_followup = is_simple_followup
                            break
    
    # Prompt to extract movie search info - enhanced with context
    movie_prompt = f"""
    Phân tích truy vấn để trích xuất thông tin tìm kiếm phim:
    
    {f"Truy vấn trước đó: {previous_movie_context}" if is_followup else ""}
    Truy vấn hiện tại: {query}
    
    {"Đây có vẻ là một câu hỏi tiếp theo cho truy vấn trước." if is_followup else ""}
    
    Trích xuất:
    1. Tên phim (nếu có)
    2. Thể loại (nếu có)
    3. Năm phát hành (nếu có)
    4. Diễn viên (nếu có)
    5. Đạo diễn (nếu có)
    
    Trả về định dạng JSON với các khóa: "title", "genre", "year", "actor", "director", "search_type".
    "search_type" nên là một trong: "title", "genre", "year", "actor", "director" dựa trên thông tin rõ ràng nhất có sẵn.
    """
    
    try:
        # Call LLM to analyze movie info
        response = llm.invoke(movie_prompt)
        response_text = response if isinstance(response, str) else response.content
        
        # Parse JSON from response
        try:
            movie_info = json.loads(response_text)
        except json.JSONDecodeError:
            # If response is not valid JSON, extract it with regex
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', response_text)
            genre_match = re.search(r'"genre"\s*:\s*"([^"]*)"', response_text)
            year_match = re.search(r'"year"\s*:\s*"([^"]*)"', response_text)
            actor_match = re.search(r'"actor"\s*:\s*"([^"]*)"', response_text)
            director_match = re.search(r'"director"\s*:\s*"([^"]*)"', response_text)
            search_type_match = re.search(r'"search_type"\s*:\s*"([^"]*)"', response_text)
            
            movie_info = {
                "title": title_match.group(1) if title_match else "",
                "genre": genre_match.group(1) if genre_match else "",
                "year": year_match.group(1) if year_match else "",
                "actor": actor_match.group(1) if actor_match else "",
                "director": director_match.group(1) if director_match else "",
                "search_type": search_type_match.group(1) if search_type_match else "title"
            }
        
        # Incorporate previous context for follow-up questions
        if is_followup and previous_movie_context and not movie_info.get("title"):
            # Try to extract movie title from previous context
            context_prompt = f"""
            Trích xuất tên phim từ cuộc hội thoại trước đó:
            
            Cuộc hội thoại trước đó: {previous_movie_context}
            Câu hỏi hiện tại: {query}
            
            Nếu tìm thấy tên phim, chỉ trả về tên đó. Nếu không, trả về "NONE".
            """
            
            context_response = llm.invoke(context_prompt)
            context_result = context_response if isinstance(context_response, str) else context_response.content
            
            if context_result.strip().upper() != "NONE":
                movie_info["title"] = context_result.strip()
                if not movie_info["search_type"] or movie_info["search_type"] == "title":
                    # If the follow-up specifies something else, prioritize that
                    if movie_info["actor"]:
                        movie_info["search_type"] = "actor"
                    elif movie_info["director"]:
                        movie_info["search_type"] = "director"
                    elif movie_info["genre"]:
                        movie_info["search_type"] = "genre"
                    elif movie_info["year"]:
                        movie_info["search_type"] = "year"
        
        # Select the proper search tool
        results = {"total_results": 0, "message": "No search criteria found"}
        
        if movie_info["search_type"] == "title" and movie_info["title"]:
            results = movie_search_by_title(movie_info["title"])
        elif movie_info["search_type"] == "genre" and movie_info["genre"]:
            results = movie_search_by_genre(movie_info["genre"])
        elif movie_info["search_type"] == "year" and movie_info["year"]:
            results = movie_search_by_year(movie_info["year"])
        elif movie_info["search_type"] == "actor" and movie_info["actor"]:
            # Implement actor search if API supports it
            # For now, fall back to web search
            web_results = web_search(f"{movie_info['actor']} actor movies")
            results = {"message": "Actor search is handled via web search", "total_results": 0, "web_fallback": True}
            state["retrieved_documents"] = web_results
        elif movie_info["search_type"] == "director" and movie_info["director"]:
            # Implement director search if API supports it
            # For now, fall back to web search
            web_results = web_search(f"{movie_info['director']} director movies")
            results = {"message": "Director search is handled via web search", "total_results": 0, "web_fallback": True}
            state["retrieved_documents"] = web_results
        else:
            # If no clear search criteria is found
            if is_followup and previous_movie_context:
                # Use the entire follow-up query + previous context
                search_term = f"{previous_movie_context} {query}"
                web_results = web_search(f"{search_term} movie information")
                results = {"message": "Using combined context for search", "total_results": 0, "web_fallback": True}
                state["retrieved_documents"] = web_results
            else:
                # Fallback to web search with the whole query
                web_results = web_search(f"{query} movie information")
                results = {"message": "No specific search criteria found", "total_results": 0, "web_fallback": True}
                state["retrieved_documents"] = web_results
        
        # Check if search failed or returned no results
        if results.get("error") or results.get("total_results", 0) == 0:
            # Fall back to web search if API call fails or no results
            search_criteria = []
            if movie_info.get("title"): search_criteria.append(movie_info["title"])
            if movie_info.get("actor"): search_criteria.append(movie_info["actor"])
            if movie_info.get("director"): search_criteria.append(movie_info["director"])
            if movie_info.get("genre"): search_criteria.append(movie_info["genre"])
            if movie_info.get("year"): search_criteria.append(movie_info["year"])
            
            # If we have search criteria, use them
            if search_criteria:
                search_term = " ".join(search_criteria) + " movie info"
            else:
                search_term = f"{query} movie information"
            
            web_results = web_search(search_term)
            state["retrieved_documents"] = web_results
            state["movie_results"] = {"total_results": 0, "web_fallback": True, "search_term": search_term}
            state["messages"].append(AIMessage(content=f"Falling back to web search for: {search_term}"))
        else:
            # Save successful results
            state["movie_results"] = results
            state["messages"].append(AIMessage(content=f"Found {results.get('total_results', 0)} movies."))
        
    except Exception as e:
        # Handle errors with web search fallback
        print(f"Error in movie search: {e}")
        web_results = web_search(f"{query} movie information")
        state["retrieved_documents"] = web_results
        state["movie_results"] = {"error": str(e), "total_results": 0, "web_fallback": True}
        state["messages"].append(AIMessage(content=f"Error during movie search. Using web search instead."))
    
    return state