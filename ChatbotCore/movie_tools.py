import re
import requests
from typing import Dict, Any
from config import API_BASE_MOVIES
from state import AgentState
from search_tools import web_search
from document_tools import advanced_rag_tool
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage, HumanMessage
import json
from config import llm

def movie_search_by_title(title: str, token: str = None):
    # Full sanitation
    clean_title = (
        title.strip()
             .replace("```", "")
             .replace("\n", "")
             .replace("\r", "")
    )

    try:
        
        print(f"🔍 Searching for title: '{clean_title}'")
        
        # Xác thực token
        headers = {"token": f"Bearer {token}"} if token else {}
        
        # Thêm xử lý lỗi chi tiết hơn
        try:
            response = requests.get(API_BASE_MOVIES, params={"title": clean_title}, headers=headers, timeout=10)
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response content: {response.text[:200]}...")  # Print first 200 chars of response
            
            # Xử lý các mã trạng thái phổ biến
            if response.status_code == 401:
                return {"error": "Authentication failed. Invalid token.", "total_results": 0}
            elif response.status_code == 404:
                return {"message": f"No movies found for this title {clean_title}.", "total_results": 0}
            
            response.raise_for_status()
            result = response.json()
            for film in result:
                episodes = len(film['episodes'])
                del film["episodes"]
                film['episodes'] = episodes
                
            # Đảm bảo định dạng kết quả nhất quán
            if isinstance(result, list):
                print(f"List format response with {len(result)} movies")
                if result:
                    # Luôn trả về định dạng chuẩn với trường movies 
                    formatted_result = {
                        "total_results": len(result),
                        "movies": result  # Giới hạn 3 bộ phim đầu tiên
                    }
                    return formatted_result
                else:
                    return {"message": f"No movies found for this title {clean_title}.", "total_results": 0, "movies": []}
            else:
                # Xử lý định dạng phản hồi từ điển
                movies = result.get("movies", [])
                print(f"Dictionary format response with {len(movies)} movies")
                if movies:
                    return {
                        "total_results": len(movies),
                        "movies": movies # Giới hạn 3 bộ phim đầu tiên
                    }
                else:
                    return {"message": f"No movies found for this title {clean_title}.", "total_results": 0, "movies": []}
                    
        except requests.Timeout:
            print(f"Request timed out for find film: {clean_title}")
            return {"error": f"Request timed out while searching for movies for this title {clean_title}.", "total_results": 0, "movies": []}
            
    except requests.RequestException as e:
        print(f"Error during title search: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return {"error": f"Title search failed: {str(e)}", "total_results": 0, "movies": []}
    except Exception as e:
        print(f"Unexpected error in title search: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "total_results": 0, "movies": []}


def movie_search_by_genre(genre: str, token: str = None):
    clean_genre = genre.strip().lower()
    try:
        
        print(f"🔍 Searching for title: '{clean_genre}'")
        
        # Xác thực token
        headers = {"token": f"Bearer {token}"} if token else {}
        
        # Thêm xử lý lỗi chi tiết hơn
        try:
            response = requests.get(API_BASE_MOVIES, params={"genre": clean_genre}, headers=headers, timeout=10)
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response content: {response.text[:200]}...")  # Print first 200 chars of response
            
            # Xử lý các mã trạng thái phổ biến
            if response.status_code == 401:
                return {"error": "Authentication failed. Invalid token.", "total_results": 0}
            elif response.status_code == 404:
                return {"message": f"No movies found for this genre {clean_genre}.", "total_results": 0}
            
            response.raise_for_status()
            result = response.json()
            
            for film in result:
                episodes = len(film['episodes'])
                del film["episodes"]
                film['episodes'] = episodes
                
            
            # Đảm bảo định dạng kết quả nhất quán
            if isinstance(result, list):
                print(f"List format response with {len(result)} movies")
                if result:
                    # Luôn trả về định dạng chuẩn với trường movies 
                    formatted_result = {
                        "total_results": len(result),
                        "movies": result  # Giới hạn 3 bộ phim đầu tiên
                    }
                    return formatted_result
                else:
                    return {"message": f"No movies found for this genre {clean_genre}.", "total_results": 0, "movies": []}
            else:
                # Xử lý định dạng phản hồi từ điển
                movies = result.get("movies", [])
                print(f"Dictionary format response with {len(movies)} movies")
                if movies:
                    return {
                        "total_results": len(movies),
                        "movies": movies  # Giới hạn 3 bộ phim đầu tiên
                    }
                else:
                    return {"message": f"No movies found for this genre {clean_genre}.", "total_results": 0, "movies": []}
                    
        except requests.Timeout:
            print(f"Request timed out for find by genre film: {clean_genre}")
            return {"error": f"Request timed out while searching for movies for this genre {clean_genre}.", "total_results": 0, "movies": []}
            
    except requests.RequestException as e:
        print(f"Error during title search: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return {"error": f"Title search failed: {str(e)}", "total_results": 0, "movies": []}
    except Exception as e:
        print(f"Unexpected error in title search: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "total_results": 0, "movies": []}

def movie_search_top(token: str = None):
    try:
        headers = {"token": f"Bearer {token}"} if token else {}
        print("🔍 Searching for top movies")
        
        try:
            # Sử dụng endpoint chính xác cho top movies
            response = requests.get(API_BASE_MOVIES, params={"type": "top"}, headers=headers, timeout=10)
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response content: {response.text[:200]}...")  # Print first 200 chars of response
            
            # Xử lý các mã trạng thái phổ biến
            if response.status_code == 401:
                return {"error": "Authentication failed. Invalid token.", "total_results": 0}
            elif response.status_code == 404:
                return {"message": "No top movies found.", "total_results": 0}
            
            response.raise_for_status()
            result = response.json()
            
            # Xử lý episodes cho mỗi phim
            for film in result:
                episodes = len(film['episodes'])
                del film["episodes"]
                film['episodes'] = episodes
            
            # Đảm bảo định dạng kết quả nhất quán
            if isinstance(result, list):
                print(f"List format response with {len(result)} movies")
                if result:
                    # Giới hạn 5 phim đầu tiên
                    top_movies = result[:5]
                    formatted_result = {
                        "total_results": len(top_movies),
                        "movies": top_movies
                    }
                    return formatted_result
                else:
                    return {"message": "No top movies found.", "total_results": 0, "movies": []}
            else:
                # Xử lý định dạng phản hồi từ điển
                movies = result.get("movies", [])
                print(f"Dictionary format response with {len(movies)} movies")
                if movies:
                    # Giới hạn 5 phim đầu tiên
                    top_movies = movies[:5]
                    return {
                        "total_results": len(top_movies),
                        "movies": top_movies
                    }
                else:
                    return {"message": "No top movies found.", "total_results": 0, "movies": []}
                    
        except requests.Timeout:
            print("Request timed out while searching for top movies")
            return {"error": "Request timed out while searching for top movies.", "total_results": 0, "movies": []}
            
    except requests.RequestException as e:
        print(f"Error during top movies search: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return {"error": f"Top movies search failed: {str(e)}", "total_results": 0, "movies": []}
    except Exception as e:
        print(f"Unexpected error in top movies search: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "total_results": 0, "movies": []}

def movie_search_by_year(year: str, token: str = None):
    try:
        year = year.strip()
        print(f"🔍 Searching for year: '{year}'")
        
        # Xác thực token
        headers = {"token": f"Bearer {token}"} if token else {}
        
        # Thêm kiểm tra xem year có phải là số không
        if not year.isdigit():
            return {"message": f"Invalid year format: {year}. Please provide a valid year.", "total_results": 0}
        
        # Thêm xử lý lỗi chi tiết hơn
        try:
            response = requests.get(API_BASE_MOVIES, params={"year": year}, headers=headers, timeout=10)
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response content: {response.text[:200]}...")  # Print first 200 chars of response
            
            # Xử lý các mã trạng thái phổ biến
            if response.status_code == 401:
                return {"error": "Authentication failed. Invalid token.", "total_results": 0}
            elif response.status_code == 404:
                return {"message": f"No movies found from year {year}.", "total_results": 0}
            
            response.raise_for_status()
            result = response.json()
            for film in result:
                episodes = len(film['episodes'])
                del film["episodes"]
                film['episodes'] = episodes
                
            
            # Đảm bảo định dạng kết quả nhất quán
            if isinstance(result, list):
                print(f"List format response with {len(result)} movies")
                if result:
                    # Luôn trả về định dạng chuẩn với trường movies 
                    formatted_result = {
                        "total_results": len(result),
                        "movies": result  # Giới hạn 5 bộ phim đầu tiên
                    }
                    return formatted_result
                else:
                    return {"message": f"No movies found from year {year}.", "total_results": 0, "movies": []}
            else:
                # Xử lý định dạng phản hồi từ điển
                movies = result.get("movies", [])
                print(f"Dictionary format response with {len(movies)} movies")
                if movies:
                    return {
                        "total_results": len(movies),
                        "movies": movies # Giới hạn 5 bộ phim đầu tiên
                    }
                else:
                    return {"message": f"No movies found from year {year}.", "total_results": 0, "movies": []}
                    
        except requests.Timeout:
            print(f"Request timed out for year: {year}")
            return {"error": f"Request timed out while searching for movies from year {year}.", "total_results": 0, "movies": []}
            
    except requests.RequestException as e:
        print(f"Error during year search: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return {"error": f"Year search failed: {str(e)}", "total_results": 0, "movies": []}
    except Exception as e:
        print(f"Unexpected error in year search: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "total_results": 0, "movies": []}

def analyze_movie_details(query, previous_context=None):
    """
    Extract specific details being asked about a movie
    """
    detail_prompt = f"""
    Phân tích truy vấn để xác định người dùng đang hỏi chi tiết gì về phim:
    
    {f"Cuộc hội thoại trước đó: {previous_context}" if previous_context else ""}
    Truy vấn hiện tại: {query}
    
    Xác định:
    1. Người dùng đang hỏi về:
       - Diễn viên (actors)
       - Đạo diễn (director)
       - Nội dung phim (plot)
       - Đánh giá (rating)
       - Chiếu rạp/phát hành (release)
       - Chi tiết khác (other)
    
    Trả về JSON với khóa "detail_type" và "search_term" nếu có.
    Ví dụ:
    {{"detail_type": "actors", "search_term": "tên phim"}}
    """
    
    try:
        response = llm.invoke(detail_prompt)
        response_text = response if isinstance(response, str) else response.content
        
        # Parse JSON from response
        try:
            detail_info = json.loads(response_text)
            return detail_info
        except json.JSONDecodeError:
            # Extract with regex if JSON parsing fails
            detail_type_match = re.search(r'"detail_type"\s*:\s*"([^"]*)"', response_text)
            search_term_match = re.search(r'"search_term"\s*:\s*"([^"]*)"', response_text)
            
            return {
                "detail_type": detail_type_match.group(1) if detail_type_match else "other",
                "search_term": search_term_match.group(1) if search_term_match else ""
            }
    except Exception as e:
        print(f"Error analyzing movie details: {e}")
        return {"detail_type": "other", "search_term": ""}

def extract_movie_from_previous_response(message_content):
    """
    Extract movie title, year, and other details from a previous response
    """
    movie_data = {}
    
    # Extract title
    title_match = re.search(r"\*\*Tiêu đề:\*\* ([^\*]+)", message_content) or \
                 re.search(r"\*\*Title:\*\* ([^\*]+)", message_content)
    if title_match:
        movie_data["title"] = title_match.group(1).strip()
    
    # Extract year
    year_match = re.search(r"\*\*Năm phát hành:\*\* (\d{4})", message_content) or \
                re.search(r"\*\*Release Year:\*\* (\d{4})", message_content)
    if year_match:
        movie_data["year"] = year_match.group(1)
    
    # Extract genre
    genre_match = re.search(r"\*\*Thể loại:\*\* ([^\*]+)", message_content) or \
                 re.search(r"\*\*Genre:\*\* ([^\*]+)", message_content)
    if genre_match:
        movie_data["genre"] = genre_match.group(1).strip()
    
    # Extract actors if present
    actors_match = re.search(r"\*\*Diễn viên:\*\* ([^\*]+)", message_content) or \
                  re.search(r"\*\*Actors:\*\* ([^\*]+)", message_content)
    if actors_match:
        movie_data["actors"] = actors_match.group(1).strip()
    
    # Extract director if present
    director_match = re.search(r"\*\*Đạo diễn:\*\* ([^\*]+)", message_content) or \
                    re.search(r"\*\*Director:\*\* ([^\*]+)", message_content)
    if director_match:
        movie_data["director"] = director_match.group(1).strip()
    
    return movie_data

def search_for_movie_detail(movie_data, detail_type):
    """
    Search for specific details about a movie
    """
    title = movie_data.get("title", "")
    year = movie_data.get("year", "")
    
    search_query = f"{title} "
    
    if detail_type == "actors":
        search_query += "actors cast"
    elif detail_type == "director":
        search_query += "director"
    elif detail_type == "release":
        search_query += f"release date {year}"
    elif detail_type == "rating":
        search_query += "movie rating reviews"
    elif detail_type == "plot":
        search_query += "plot summary"
    else:
        search_query += f"{detail_type} {year}"
    
    # Perform web search for the details
    return web_search(search_query)

def movie_search_node(state: AgentState) -> AgentState:
    query = state["query"]
    chat_history = state["chat_history"]
    token = state.get("token")
    
    print(f"🔑 Token in movie_search_node: {token[:10] if token else 'None'}...")
    
    if not token:
        print("⚠️ Warning: No token provided for movie search")
    
    # Check for follow-up/contextual movie queries
    is_followup = False
    previous_movie_context = ""
    previous_response_content = ""
    
    # Extract any previous movie context from history
    if chat_history:
        recent_messages = chat_history[-6:] if len(chat_history) >= 6 else chat_history
        
        # Check for follow-up indicators
        followup_indicators = ["what about", "how about", "tell me more", "and", "also", "another", 
                              "còn", "vậy còn", "thêm", "tiếp", "và", "nữa", "ai", "who"]
        
        is_simple_followup = (
            len(query.split()) <= 6 or 
            any(indicator in query.lower() for indicator in followup_indicators) or
            query.strip().startswith("còn") or 
            query.strip().startswith("và") or
            query.strip().startswith("and") or
            "?" in query
        )
        
        # Extract relevant movie context from previous exchanges
        for i in range(len(recent_messages)-1, 0, -2):
            if i >= 1 and i < len(recent_messages):
                if isinstance(recent_messages[i], dict) and recent_messages[i].get('role') == 'ai':
                    ai_content = recent_messages[i].get('content', '').lower()
                    
                    # Check if previous response was movie-related
                    if "source: tv3database" in ai_content or "nguồn: t3vdatabase" in ai_content or "nguồn: t3v database" in ai_content:
                        previous_response_content = recent_messages[i].get('content', '')
                        if isinstance(recent_messages[i-1], dict) and recent_messages[i-1].get('role') == 'human':
                            previous_query = recent_messages[i-1].get('content', '')
                            previous_movie_context = previous_query
                            is_followup = is_simple_followup
                            break
                elif hasattr(recent_messages[i], 'type') and recent_messages[i].type == 'ai':
                    ai_content = recent_messages[i].content.lower()
                    
                    # Check if previous response was movie-related
                    if "source: t3vdatabase" in ai_content or "nguồn: t3vdatabase" in ai_content or "nguồn: t3v database" in ai_content:
                        previous_response_content = recent_messages[i].content
                        if i > 0 and hasattr(recent_messages[i-1], 'type') and recent_messages[i-1].type == 'human':
                            previous_query = recent_messages[i-1].content
                            previous_movie_context = previous_query
                            is_followup = is_simple_followup
                            break
    
    # Handle follow-up questions about specific movie details
    if is_followup and previous_response_content:
        # Extract movie data from previous response
        movie_data = extract_movie_from_previous_response(previous_response_content)
        
        if movie_data.get("title"):
            # Analyze what specific detail the user is asking about
            detail_info = analyze_movie_details(query, previous_movie_context)
            detail_type = detail_info.get("detail_type", "other")
            
            # First try to check if the detail exists in our movie data
            if detail_type == "actors" and movie_data.get("actors"):
                state["movie_results"] = {
                    "movie": movie_data,
                    "requested_detail": detail_type,
                    "detail_value": movie_data.get("actors")
                }
                return state
            
            if detail_type == "director" and movie_data.get("director"):
                state["movie_results"] = {
                    "movie": movie_data,
                    "requested_detail": detail_type,
                    "detail_value": movie_data.get("director")
                }
                return state
            
            # Otherwise search for the specific detail
            web_results = search_for_movie_detail(movie_data, detail_type)
            state["retrieved_documents"] = web_results
            state["movie_results"] = {
                "movie": movie_data,
                "requested_detail": detail_type,
                "web_fallback": True
            }
            return state
    
    # Prompt to extract movie search info - enhanced with context and year detection
    movie_prompt = f"""
    Phân tích truy vấn để trích xuất thông tin tìm kiếm phim:
    
    {f"Truy vấn trước đó: {previous_movie_context}" if is_followup else ""}
    Truy vấn hiện tại: {query}
    
    {"Đây có vẻ là một câu hỏi tiếp theo cho truy vấn trước." if is_followup else ""}
    
    Trích xuất:
    1. Tên phim (nếu có)
    2. Thể loại (nếu có)
    3. Năm phát hành (nếu có) - chú ý các cụm từ như "phim năm X", "phim ra mắt X", "phim X", "năm X"
    4. Diễn viên (nếu có)
    5. Đạo diễn (nếu có)
    6. URL của phim (nếu có)
    7. Top phim - chú ý các cụm từ như "top phim", "phim hot", "phim trending", "phim hay nhất"
    
    Trả về định dạng JSON với các khóa: "title", "genre", "year", "actor", "director", "search_type".
    "search_type" nên là một trong: "title", "genre", "year", "actor", "director", "top" dựa trên thông tin rõ ràng nhất có sẵn.
    
    Ví dụ cho tìm kiếm theo năm:
    - "phim năm 2023" -> search_type: "year", year: "2023"
    - "phim ra mắt 2020" -> search_type: "year", year: "2020"
    - "phim 2019" -> search_type: "year", year: "2019"
    - "năm 2021 có phim gì hay" -> search_type: "year", year: "2021"
    
    Ví dụ cho tìm kiếm top phim:
    - "top phim hay nhất" -> search_type: "top"
    - "phim hot hiện nay" -> search_type: "top"
    - "phim trending" -> search_type: "top"
    - "top 10 phim" -> search_type: "top"
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
                    elif "top" in query.lower() or "hot" in query.lower() or "trending" in query.lower():
                        movie_info["search_type"] = "top"
        
        # Select the proper search tool
        results = {"total_results": 0, "message": "No search criteria found"}
        
        if movie_info["search_type"] == "title" and movie_info["title"]:
            print("Search by title")
            results = movie_search_by_title(movie_info["title"], token)
            print(results)
        elif movie_info["search_type"] == "genre" and movie_info["genre"]:
            print("Search by genre")
            results = movie_search_by_genre(movie_info["genre"], token)
            print(results)
        elif movie_info["search_type"] == "year" and movie_info["year"]:
            print("Search by year")
            results = movie_search_by_year(movie_info["year"], token)
            print(results)
        elif movie_info["search_type"] == "top":
            print("Search top movies")
            results = movie_search_top(token)
            print(results)
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
        if results.get("error"):
            # Only fall back to web search if there was an error
            search_criteria = []
            if movie_info.get("title"): search_criteria.append(movie_info["title"])
            if movie_info.get("actor"): search_criteria.append(movie_info["actor"])
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
            # If we have results, use them directly
            state["movie_results"] = results
        
        return state
        
    except Exception as e:
        # Handle errors with web search fallback
        print(f"Error in movie search: {e}")
        web_results = web_search(f"{query} movie information")
        state["retrieved_documents"] = web_results
        state["movie_results"] = {"error": str(e), "total_results": 0, "web_fallback": True}
        state["messages"].append(AIMessage(content=f"Error during movie search. Using web search instead."))
    
    return state