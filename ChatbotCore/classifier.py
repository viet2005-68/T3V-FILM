import json
import re
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
    
    try:
        # Call LLM for classification with reasoning
        response = llm.invoke(prompt.format(question=question))
        content = response if isinstance(response, str) else response.content
        
        # Extract category based on comprehensive analysis
        category = None
        confidence = "medium"
        
        # Look for clear category indicators in the response
        if "MOVIE" in content.upper() and ("Category: MOVIE" in content or "classification: MOVIE" in content or "MOVIE" in content.split()[-10:]):
            category = "MOVIE"
            if "high confidence" in content.lower() or "strong evidence" in content.lower():
                confidence = "high"
        elif "SERVICE" in content.upper() and ("Category: SERVICE" in content or "classification: SERVICE" in content or "SERVICE" in content.split()[-10:]):
            category = "SERVICE"
            if "high confidence" in content.lower() or "strong evidence" in content.lower():
                confidence = "high"
        elif "OTHER" in content.upper() and ("Category: OTHER" in content or "classification: OTHER" in content or "OTHER" in content.split()[-10:]):
            category = "OTHER"
            if "high confidence" in content.lower() or "strong evidence" in content.lower():
                confidence = "high"
        
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
        print(f"Error in classification: {e}")
        # More helpful error message with traceback
        import traceback
        trace = traceback.format_exc()
        print(f"Detailed error: {trace}")
        
        # Fallback to simple keyword matching
        movie_count = sum(1 for word in ["phim", "movie", "film", "actor", "actress", "director", "diễn viên", "đạo diễn"] if word in question)
        service_count = sum(1 for word in ["t3v", "account", "tài khoản", "subscription", "gói", "payment", "thanh toán", "đăng ký", "đăng nhập"] if word in question)
        
        if movie_count > service_count:
            return json.dumps({
                "category": "MOVIE", 
                "confidence": "low",
                "reasoning": f"Fallback classification based on keyword detection. Error: {str(e)}"
            })
        elif service_count > 0 or "t3v" in question:
            return json.dumps({
                "category": "SERVICE", 
                "confidence": "low",
                "reasoning": f"Fallback classification based on keyword detection. Error: {str(e)}"
            })
        else:
            return json.dumps({
                "category": "OTHER", 
                "confidence": "low",
                "reasoning": f"Classification error occurred. Defaulting to OTHER as fallback. Error: {str(e)}"
            })

def context_aware_router(state: AgentState) -> str:
    """
    Enhanced routing logic with better context awareness and follow-up detection.
    """
    classification = state["classification"]["category"]
    confidence = state["classification"].get("confidence", "medium")
    query = state["query"]
    chat_history = state["chat_history"]
    
    # Fast path for very high/high confidence classifications
    if confidence in ["very high", "high"]:
        print(f"High confidence classification: {classification} - proceeding directly")
        return classification.lower() + "_node"
    
    # Check for very short queries which are likely follow-ups
    is_short_query = len(query.split()) <= 3 and not any(char in "?.,!;" for char in query)
    
    # For medium/low confidence, analyze conversation flow
    if chat_history and len(chat_history) >= 2:
        # Properly format history for analysis
        history_context = format_chat_history(chat_history) if chat_history else ""
        
        # Extract the most recent AI response to check its category
        previous_categories = []
        for i in range(len(chat_history) - 1, 0, -1):
            msg = chat_history[i]
            if isinstance(msg, dict) and msg.get('role') == 'ai':
                content = msg.get('content', '').lower()
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
            result = response if isinstance(response, str) else response.content
            result = result.strip().upper()
            
            # Extract the classification
            if "SERVICE" in result:
                print("Context analysis rerouted to SERVICE")
                return "service_node"
            elif "MOVIE" in result:
                print("Context analysis rerouted to MOVIE")
                return "movie_node"
            elif "OTHER" in result:
                print("Context analysis confirmed OTHER category")
                return "web_node"
        except Exception as e:
            print(f"Context router analysis error: {e}")
            # If analysis fails, use original classification
    
    # Standard routing based on classification
    print(f"Standard routing based on classification: {classification}")
    if classification == "SERVICE":
        return "service_node"
    elif classification == "MOVIE":
        return "movie_node"
    else:  # OTHER
        return "web_node"


def classify_node(state: AgentState) -> AgentState:
    """
    Enhanced classification node with better context handling and query analysis.
    """
    query = state["query"]
    raw_history = state["chat_history"]
    
    # Better history processing with proper error handling
    try:
        chat_history = [convert_message_to_dict(msg) for msg in raw_history] if raw_history else []
    except Exception as e:
        print(f"Error processing chat history: {e}")
        chat_history = []  # Fallback to empty history on error
    
    # Enhanced context extraction from history
    context_from_history = ""
    recent_query_context = ""
    if chat_history:
        # Analyze recent messages for better context
        recent_messages = chat_history[-6:] if len(chat_history) >= 6 else chat_history
        
        # Format full context for reference
        context_from_history = "Previous conversation:\n"
        for msg in recent_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            prefix = "User: " if role == 'human' else "Assistant: "
            context_from_history += f"{prefix}{content.strip()}\n"
        
        # Extract the most recent user query and assistant response specifically
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and i < len(chat_history):
                user_msg = chat_history[i-1] if chat_history[i-1].get('role') == 'human' else None
                ai_msg = chat_history[i] if chat_history[i].get('role') == 'ai' else None
                
                if user_msg and ai_msg:
                    recent_query_context = f"Last query: {user_msg.get('content')}\nLast response: {ai_msg.get('content')[:100]}..."
                    break
    
    # Check for follow-up patterns in the query
    followup_indicators = [
        "what about", "how about", "tell me more", "additionally", "and", "also", "another", "more",
        "còn", "vậy còn", "cho tôi biết thêm", "thêm", "tiếp", "và", "cụ thể hơn", "nữa", 
        "có gì khác", "những cái khác", "tiếp theo"
    ]
    
    is_likely_followup = (
        len(query.split()) <= 4 or 
        any(indicator in query.lower() for indicator in followup_indicators) or
        not any(char in "?.,!;" for char in query) or  # No punctuation often indicates follow-up
        query.strip().startswith("còn") or
        query.strip().startswith("và") or
        query.strip().startswith("and")
    )
    
    try:
        # If this appears to be a follow-up and we have history, use context-aware classification
        if is_likely_followup and chat_history and len(chat_history) >= 2:
            # Create contextual query for classification
            contextual_classification_prompt = f"""
            CÂU HỎI GẦN ĐÂY:
            {recent_query_context}
            
            CÂU HỎI HIỆN TẠI:
            {query}
            
            Dựa vào ngữ cảnh trên, câu hỏi hiện tại có phải là câu hỏi tiếp theo về cùng chủ đề không?
            Nếu đúng là câu hỏi tiếp theo, chủ đề chính là gì?
            1. Về dịch vụ T3V (đăng ký, tài khoản, thanh toán, v.v) - trả lời "SERVICE"
            2. Về phim (phim cụ thể, diễn viên, đề xuất, v.v) - trả lời "MOVIE"
            3. Về chủ đề khác - trả lời "OTHER"
            
            Chỉ trả lời một từ: "SERVICE", "MOVIE", hoặc "OTHER"
            """
            
            # Check if it's a follow-up
            response = llm.invoke(contextual_classification_prompt)
            content = response if isinstance(response, str) else response.content
            
            if "SERVICE" in content.upper():
                classification_result = json.dumps({
                    "category": "SERVICE",
                    "confidence": "medium",
                    "reasoning": "Follow-up question continuing about T3V services from previous conversation."
                })
            elif "MOVIE" in content.upper():
                classification_result = json.dumps({
                    "category": "MOVIE",
                    "confidence": "medium",
                    "reasoning": "Follow-up question continuing about movies from previous conversation."
                })
            else:
                # Standard classification for new topics
                classification_result = classify_query_tool(query)
        else:
            # Standard classification for new topics
            classification_result = classify_query_tool(query)
        
        # Parse and store classification
        classification_data = json.loads(classification_result)
        state["classification"] = classification_data
        
        # Add detailed classification info to messages for debugging (can be removed in production)
        state["messages"].append(AIMessage(
            content=f"Query classified as: {classification_data['category']} (Confidence: {classification_data['confidence']})"
        ))
        
    except Exception as e:
        # Improved error handling with useful diagnostics
        print(f"Classification error: {e}")
        print(f"Query that caused error: '{query}'")
        
        # Extract fallback category using most basic keyword detection
        fallback_category = "OTHER"
        if any(word in query.lower() for word in ["t3v", "account", "tài khoản", "đăng ký", "thanh toán", "subscription"]):
            fallback_category = "SERVICE"
        elif any(word in query.lower() for word in ["phim", "movie", "film", "diễn viên", "actor", "thể loại", "genre"]):
            fallback_category = "MOVIE"
        
        # Default with diagnostics info
        state["classification"] = {
            "category": fallback_category,
            "confidence": "low",
            "reasoning": f"Classification failed. Using {fallback_category} as fallback. Error: {str(e)}"
        }
        state["messages"].append(AIMessage(
            content=f"Classification system encountered an issue. Proceeding with {fallback_category} handling."
        ))

    return state