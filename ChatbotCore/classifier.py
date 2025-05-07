import json
import re
import traceback
from state import AgentState
from config import llm
from response_tools import format_chat_history
from response_tools import convert_message_to_dict
from langchain_core.messages import AIMessage

def classify_query_tool(question: str) -> str:
    """
    Enhanced classification tool with better context handling and robust fallback mechanisms.
    """
    # Preprocess the question
    question = question.strip().lower()
    
    try:
        # Quick check for obvious greetings with high confidence
        greeting_phrases = ["chào", "xin chào", "hello", "hi", "hola", "bonjour", "hey", "good morning", "good afternoon"]
        if any(question.startswith(greet) for greet in greeting_phrases) and len(question.split()) <= 5:
            return json.dumps({
                "category": "SERVICE",
                "confidence": "high",
                "reasoning": "Simple greeting detected, treating as a general service inquiry."
            })
        
        # Strong indicators for SERVICE queries (high confidence)
        service_indicators = [
            "t3v là gì", "what is t3v", "dịch vụ t3v", "t3v service", "đăng ký t3v", "register t3v",
            "tài khoản", "account", "đăng nhập", "login", "mật khẩu", "password", "subscription",
            "thanh toán", "payment", "giá", "price", "cost", "gói dịch vụ", "bao nhiêu tiền",
            "how to use t3v", "cách sử dụng t3v", "hướng dẫn", "guide", "cách đăng ký", "hỗ trợ", 
            "support", "vấn đề", "issue", "lỗi", "error", "không xem được", "cannot watch",
            "không đăng nhập được", "cannot login", "subscription", "đăng ký gói", "gia hạn",
            "renew", "extend", "nâng cấp", "upgrade", "downgrade", "hạ cấp", "hủy gói", "cancel"
        ]
        
        # Check for complete service phrases (highest priority)
        complete_service_phrases = [
            "đăng ký tài khoản t3v", "register t3v account", 
            "cách thanh toán", "payment method",
            "quên mật khẩu", "forgot password",
            "gói dịch vụ t3v", "t3v subscription plans",
            "hướng dẫn sử dụng t3v", "how to use t3v",
            "vấn đề kỹ thuật", "technical issues",
            "không đăng nhập được", "cannot login",
            "không xem được phim", "cannot watch movies",
            "hỗ trợ khách hàng", "customer support"
        ]
        
        if any(phrase in question for phrase in complete_service_phrases):
            return json.dumps({
                "category": "SERVICE",
                "confidence": "very high",
                "reasoning": "Complete service-related phrase detected in query."
            })
        
        if sum(1 for indicator in service_indicators if indicator in question) >= 2:
            return json.dumps({
                "category": "SERVICE",
                "confidence": "high",
                "reasoning": "Multiple service-related indicators detected in query."
            })
        elif any(indicator in question for indicator in service_indicators):
            if "t3v" in question:
                return json.dumps({
                    "category": "SERVICE",
                    "confidence": "high",
                    "reasoning": "Service indicator with T3V mention detected in query."
                })
            return json.dumps({
                "category": "SERVICE", 
                "confidence": "medium",
                "reasoning": "Service-related indicator detected in query."
            })
        
        # Strong indicators for MOVIE queries (high confidence)
        movie_indicators = [
            "phim", "movie", "film", "xem phim", "watch", "diễn viên", "actor", "actress", 
            "đạo diễn", "director", "thể loại", "genre", "năm", "year", "recommend", "gợi ý",
            "review", "rating", "đánh giá", "series", "tập", "episode", "season", "imdb",
            "trailer", "preview", "teaser", "plot", "storyline", "cốt truyện", "nội dung",
            "thông tin phim", "movie info", "cast", "dàn diễn viên", "nhân vật", "character",
            "giải thưởng", "award", "oscar", "box office", "doanh thu", "phòng vé", "phim mới",
            "new release", "phim hay", "best movies", "hành động", "action", "kinh dị", "horror",
            "hài", "comedy", "tình cảm", "romance", "khoa học viễn tưởng", "sci-fi"
        ]
        
        # Check for complete movie phrases (highest priority for MOVIE)
        complete_movie_phrases = [
            "phim hay nhất", "best movies", 
            "đánh giá phim", "movie review",
            "thông tin phim", "movie information",
            "diễn viên trong phim", "actors in movie",
            "đạo diễn phim", "movie director",
            "nội dung phim", "movie plot",
            "phim mới ra mắt", "new movie releases",
            "gợi ý phim hay", "movie recommendations",
            "phim thuộc thể loại", "movies in the genre"
        ]
        
        if any(phrase in question for phrase in complete_movie_phrases):
            return json.dumps({
                "category": "MOVIE",
                "confidence": "very high",
                "reasoning": "Complete movie-related phrase detected in query."
            })
        
        # Check if it's explicitly a movie query by counting multiple indicators
        movie_indicator_count = sum(1 for indicator in movie_indicators if indicator in question)
        
        if movie_indicator_count >= 2:
            # Further check if it's about watching ON T3V (service) or ABOUT movies (content)
            if any(phrase in question for phrase in ["on t3v", "trên t3v", "t3v platform", "nền tảng t3v", "app t3v", "t3v app"]):
                if any(action in question for action in ["how to", "cách", "làm sao", "làm thế nào"]):
                    return json.dumps({
                        "category": "SERVICE",
                        "confidence": "high",
                        "reasoning": "Query about how to watch movies ON the T3V platform (service-related)."
                    })
            
            return json.dumps({
                "category": "MOVIE",
                "confidence": "high",
                "reasoning": "Multiple movie-related indicators detected in query."
            })
        elif movie_indicator_count == 1:
            # Single movie indicator - medium confidence
            return json.dumps({
                "category": "MOVIE",
                "confidence": "medium",
                "reasoning": "Single movie-related indicator detected in query."
            })
        
        # Enhanced classification prompt with chain-of-thought
        prompt = """
        Bạn là chuyên gia phân loại ý định người dùng cho nền tảng xem phim T3V.
        
        INSTRUCTIONS:
        Analyze the user's question step by step to determine the correct category:
        1. First, identify the main topic or focus of the question
        2. Consider what information or action the user is seeking
        3. Match this to the most appropriate category
        4. Provide your detailed reasoning process
        5. Return your final classification
        
        CÁC DANH MỤC:
        - "MOVIE" — Câu hỏi về phim cụ thể, diễn viên, đề xuất, thể loại hoặc nội dung liên quan đến phim
        - "SERVICE" — Câu hỏi về chính nền tảng T3V, tài khoản, hỗ trợ kỹ thuật, giá cả, tính năng hoặc cách sử dụng T3V
        - "OTHER" — Câu hỏi không liên quan đến phim hoặc dịch vụ T3V
        
        PHÂN BIỆT QUAN TRỌNG:
        - Câu hỏi về "xem phim trên T3V" là SERVICE nếu chúng hỏi CÁCH SỬ DỤNG nền tảng
        - Câu hỏi về NỘI DUNG phim, đề xuất hoặc thông tin là MOVIE
        - Câu hỏi về tính năng T3V, tài khoản, giá cả là SERVICE
        - Các câu hỏi chung không liên quan đến phim hoặc T3V là OTHER
        
        Câu hỏi: "{question}"
        
        Lý luận từng bước:
        """
        
        # Call LLM for classification with reasoning
        response = llm.invoke(prompt.format(question=question))
        content = get_llm_content(response)
        
        # Extract category based on comprehensive analysis
        category = None
        confidence = "medium"
        
        # Extract category using regex patterns for more accurate detection
        category_match = re.search(r"Category:[\s]*(MOVIE|SERVICE|OTHER)", content, re.IGNORECASE)
        if not category_match:
            category_match = re.search(r"classification:[\s]*(MOVIE|SERVICE|OTHER)", content, re.IGNORECASE)
        
        if category_match:
            category = category_match.group(1).upper()
            if "high confidence" in content.lower() or "strong evidence" in content.lower():
                confidence = "high"
        else:
            # Fallback to analyzing last few words
            last_words = ' '.join(content.split()[-10:]).upper()
            if "MOVIE" in last_words.split():
                category = "MOVIE"
            elif "SERVICE" in last_words.split():
                category = "SERVICE"
            elif "OTHER" in last_words.split():
                category = "OTHER"
        
        # If still no category found, use improved keyword detection as fallback
        if not category:
            # More comprehensive keyword lists with scoring
            movie_keywords = {
                "phim": 3, "movie": 3, "film": 3, "actor": 2, "actress": 2, "director": 2, 
                "genre": 2, "recommendation": 2, "watch": 1, "series": 2, "episode": 2, 
                "diễn viên": 3, "đạo diễn": 3, "thể loại": 3, "imdb": 3, "trailer": 3, 
                "plot": 2, "story": 2, "character": 2, "nhân vật": 2, "review": 2, 
                "đánh giá": 3, "nội dung": 3, "gợi ý": 2
            }
            
            service_keywords = {
                "t3v": 3, "account": 2, "tài khoản": 3, "password": 3, "mật khẩu": 3, 
                "subscription": 3, "gói": 2, "payment": 3, "thanh toán": 3, "platform": 2, 
                "nền tảng": 2, "stream": 2, "phát": 1, "app": 2, "application": 2, 
                "ứng dụng": 3, "download": 2, "tải": 1, "price": 3, "giá": 3, 
                "support": 3, "hỗ trợ": 3, "đăng ký": 3, "đăng nhập": 3, "login": 3,
                "register": 3, "vấn đề": 3, "issue": 3, "lỗi": 3, "error": 3,
                "không xem được": 3, "cannot watch": 3
            }
            
            # Calculate weighted scores
            movie_score = sum(score for word, score in movie_keywords.items() if word in question)
            service_score = sum(score for word, score in service_keywords.items() if word in question)
            
            # Special case: "t3v" mention has higher weight for SERVICE classification
            if "t3v" in question:
                service_score += 3
            
            # Apply thresholds for better confidence levels
            if movie_score > service_score:
                category = "MOVIE"
                if movie_score >= 6:
                    confidence = "high"
                elif movie_score >= 3:
                    confidence = "medium"
                else:
                    confidence = "low"
            elif service_score > 0:
                category = "SERVICE"
                if service_score >= 6:
                    confidence = "high"
                elif service_score >= 3:
                    confidence = "medium"
                else:
                    confidence = "low"
            else:
                category = "OTHER"
                confidence = "medium"
        
        # Extract reasoning if possible
        reasoning_match = re.search(r"Step-by-step reasoning:(.*?)(?=Category:|classification:|$)", content, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        else:
            # Look for any reasoning pattern
            reasoning_match = re.search(r"Reasoning:(.*?)(?=Category:|classification:|$)", content, re.DOTALL | re.IGNORECASE)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Classification based on content analysis"
        
        return json.dumps({
            "category": category or "SERVICE",  # Default to SERVICE if all else fails
            "confidence": confidence,
            "reasoning": reasoning
        })
        
    except Exception as e:
        # Log the error with minimal detail
        print(f"Error in classification: {str(e)}")
        # Don't print full traceback in production, but log the exception type
        error_type = type(e).__name__
        
        # Fallback to simple keyword matching
        movie_count = sum(1 for word in ["phim", "movie", "film", "actor", "actress", "director", "diễn viên", "đạo diễn"] if word in question)
        service_count = sum(1 for word in ["t3v", "account", "tài khoản", "subscription", "gói", "payment", "thanh toán", "đăng ký", "đăng nhập"] if word in question)
        
        if movie_count > service_count:
            return json.dumps({
                "category": "MOVIE", 
                "confidence": "low",
                "reasoning": f"Fallback classification based on keyword detection. Error type: {error_type}"
            })
        elif service_count > 0 or "t3v" in question:
            return json.dumps({
                "category": "SERVICE", 
                "confidence": "low",
                "reasoning": f"Fallback classification based on keyword detection. Error type: {error_type}"
            })
        else:
            return json.dumps({
                "category": "OTHER", 
                "confidence": "low",
                "reasoning": f"Classification error occurred. Defaulting to OTHER as fallback. Error type: {error_type}"
            })

def get_llm_content(response):
    """Helper function to safely extract content from LLM response."""
    if isinstance(response, str):
        return response
    # Try to get content attribute
    if hasattr(response, 'content'):
        return response.content
    # Try to convert to string if all else fails
    return str(response)

def context_aware_router(state: AgentState) -> str:
    """
    Enhanced routing logic with better context awareness and follow-up detection.
    """
    classification = state.get("classification", {}).get("category", "OTHER")
    confidence = state.get("classification", {}).get("confidence", "medium")
    query = state.get("query", "")
    chat_history = state.get("chat_history", [])
    
    # Log our inputs for debugging
    print(f"Routing for category: {classification}, confidence: {confidence}")
    
    # Fast path for very high/high confidence classifications
    if confidence in ["very high", "high"]:
        print(f"High confidence classification: {classification} - proceeding directly")
        return classification.lower() + "_node"
    
    # Check for very short queries which are likely follow-ups
    is_short_query = len(query.split()) <= 3 and not any(char in "?.,!;" for char in query)
    
    # For medium/low confidence, analyze conversation flow
    if chat_history and len(chat_history) >= 2:
        # Extract the most recent AI response to check its category
        previous_categories = []
        for i in range(len(chat_history) - 1, 0, -1):
            msg = chat_history[i]
            # Handle both dictionary and object formats
            if isinstance(msg, dict):
                content = msg.get('content', '').lower()
                is_ai = msg.get('role') == 'ai'
            else:
                try:
                    # Try to access as object attributes
                    content = getattr(msg, 'content', '').lower()
                    is_ai = getattr(msg, 'type', '') == 'ai'
                except AttributeError:
                    continue
                    
            if is_ai:
                if "source: vectordb" in content:
                    previous_categories.append("SERVICE")
                elif "source: tmdb" in content:
                    previous_categories.append("MOVIE")
                elif "source: web" in content:
                    previous_categories.append("OTHER")
                break
        
        # Strong indicators for follow-up questions
        followup_indicators = [
            "what about", "how about", "tell me more", "and", "also", "another", "more",
            "còn", "vậy còn", "thêm", "tiếp", "và", "nữa", "có gì khác", "những cái khác"
        ]
        
        # Check if this is likely a follow-up
        is_followup = (
            is_short_query or
            any(indicator in query.lower() for indicator in followup_indicators) or
            query.strip().startswith("còn") or
            query.strip().startswith("và") or
            query.strip().startswith("and")
        )
        
        # If likely follow-up and we have a previous category, maintain conversational context
        if is_followup and previous_categories:
            most_recent_category = previous_categories[0]
            print(f"Likely follow-up detected. Previous category: {most_recent_category}")
            
            # If current classification is different or low confidence, use previous context
            if classification != most_recent_category or confidence == "low":
                print(f"Rerouting to {most_recent_category} based on conversation flow")
                return most_recent_category.lower() + "_node"
    
    # For uncertain cases, perform deeper context analysis
    if confidence == "low" or classification == "OTHER":
        try:
            # Create a more detailed context analysis prompt
            context_analysis_prompt = f"""
            Phân tích cuộc hội thoại và câu hỏi hiện tại:
            
            LỊCH SỬ HỘI THOẠI:
            {format_chat_history(chat_history) if chat_history else "Không có lịch sử trò chuyện"}
            
            CÂU HỎI HIỆN TẠI:
            {query}
            
            Xác định chủ đề chính của câu hỏi:
            1. Nếu về dịch vụ, tính năng, nền tảng T3V - trả lời "SERVICE"
            2. Nếu về phim cụ thể, diễn viên, đề xuất phim - trả lời "MOVIE"
            3. Nếu không liên quan đến cả hai - trả lời "OTHER"
            
            CHỈ TRẢ LỜI BẰNG MỘT TỪ: SERVICE, MOVIE, hoặc OTHER
            """
            
            # Call LLM for context analysis
            response = llm.invoke(context_analysis_prompt)
            result = get_llm_content(response).strip().upper()
            
            # Use more precise matching to extract classification
            if re.search(r'\bSERVICE\b', result):
                print("Context analysis rerouted to SERVICE")
                return "service_node"
            elif re.search(r'\bMOVIE\b', result):
                print("Context analysis rerouted to MOVIE")
                return "movie_node"
            elif re.search(r'\bOTHER\b', result):
                print("Context analysis confirmed OTHER category")
                return "web_node"
            else:
                print(f"Context analysis returned unclear result: '{result}', falling back to original classification")
        except Exception as e:
            print(f"Context router analysis error: {type(e).__name__}")
            # Don't log the full exception details
    
    # Standard routing based on classification
    print(f"Using standard routing based on classification: {classification}")
    if classification == "SERVICE":
        return "service_node"
    elif classification == "MOVIE":
        return "movie_node"
    else:  # OTHER
        return "web_node"


def classify_node(state: AgentState) -> AgentState:
    """Classify the query and update state with classification results."""
    try:
        query = state["query"]
        token = state.get("token")  # Get token from state
        
        print(f"🔑 Token in classify_node: {token[:10] if token else 'None'}...")
        
        # Get classification
        classification_result = classify_query_tool(query)
        classification = json.loads(classification_result)
        
        # Update state directly instead of creating a new one
        state["classification"] = classification
        
        print(f"Classification complete: {classification['category']} with {classification['confidence']} confidence")
        return state
        
    except Exception as e:
        print(f"Error in classify_node: {type(e).__name__}")
        
        # Update state directly with error classification
        state["classification"] = {
            "category": "SERVICE",  # Default to SERVICE as the safest option
            "confidence": "low",
            "reasoning": "Error occurred during classification"
        }
        return state