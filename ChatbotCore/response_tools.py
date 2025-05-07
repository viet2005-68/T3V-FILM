import re
from config import llm
from state import AgentState, format_chat_history
from langchain_core.messages import AIMessage
import json

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


def unified_answer_synthesizer_node(state: AgentState) -> AgentState:
    query = state["query"]
    classification = state["classification"]["category"]
    confidence = state["classification"].get("confidence", "medium")
    chat_history = state["chat_history"]
    
    # Format chat history for context
    history_context = format_chat_history(chat_history) if chat_history else ""
    
    # Detect language (Vietnamese or English)
    is_vietnamese = any(c in query.lower() for c in "ăâêôơưđ") or "bố già" in query.lower() or "phim" in query.lower()
    
    # Gather all possible sources of information
    service_info = state.get("retrieved_documents", "")
    movie_results = state.get("movie_results", {})
    web_results = state.get("retrieved_documents", "")  # Same as service_info but used differently
    
    # Check if we have multi-source information based on confidence level
    is_multi_source = confidence in ["low", "medium"] or (
        len(service_info) > 0 and (isinstance(movie_results, dict) and len(movie_results) > 0)
    )
    
    # Base prompt structure with history included
    base_prompt = f"""
    LỊCH SỬ HỘI THOẠI:
    {history_context}

    CÂU HỎI HIỆN TẠI:
    {query}
    
    PHÂN LOẠI:
    {classification} (Độ tin cậy: {confidence})
    """
    
    if is_multi_source:
        # Format movie_results for inclusion
        movie_info = ""
        if isinstance(movie_results, dict) and movie_results.get("movies"):
            movie_info = json.dumps(movie_results, ensure_ascii=False, indent=2)
        elif isinstance(movie_results, list) and len(movie_results) > 0:
            movie_info = json.dumps({"movies": movie_results, "total_results": len(movie_results)}, 
                                   ensure_ascii=False, indent=2)
        
        # Create a comprehensive prompt incorporating multiple data sources
        final_prompt = base_prompt + f"""
        THÔNG TIN TỪ NHIỀU NGUỒN:
        
        1. THÔNG TIN DỊCH VỤ T3V:
        {service_info}
        
        2. THÔNG TIN PHIM:
        {movie_info}
        
        3. THÔNG TIN WEB:
        {web_results}

        HƯỚNG DẪN:
        1. Phân tích đánh giá tất cả các nguồn thông tin trên để tạo câu trả lời tổng hợp đầy đủ nhất
        2. Ưu tiên thông tin từ nguồn T3V DATABASE cho tính chính xác cao nhất
        3. Bổ sung thông tin từ web khi cần thiết để làm phong phú câu trả lời
        4. Đảm bảo tính liên tục với các câu trả lời trước đó nếu đây là cuộc trò chuyện tiếp diễn
        5. Nếu các nguồn thông tin mâu thuẫn nhau, ưu tiên theo thứ tự: Dịch vụ T3V > Thông tin Phim > Thông tin Web
        6. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
        7. Nếu thông tin về phim được sử dụng, đảm bảo bao gồm liên kết chi tiết film với format: [Tên phim](http://localhost:5173/movie/ID_PHIM)
        8. Chỉ rõ nguồn gốc thông tin trong câu trả lời của bạn
        
        ĐỊNH DẠNG CÂU TRẢ LỜI:
        - Ngắn gọn, súc tích nhưng đầy đủ thông tin
        - Có cấu trúc rõ ràng, dễ đọc
        - Nếu là thông tin phim, tuân thủ cấu trúc yêu cầu với liên kết chi tiết
        - Kết thúc bằng nguồn thông tin phù hợp (T3V Database, Web, hoặc kết hợp)
        """
    else:
        # Use category-specific prompts as before for high-confidence single-source responses
        if classification == "SERVICE":
            final_prompt = base_prompt + f"""
            THÔNG TIN CƠ SỞ DỮ LIỆU DỊCH VỤ T3V:
            {service_info}

            HƯỚNG DẪN:
            1. Tham khảo bất kỳ thông tin liên quan nào từ lịch sử cuộc trò chuyện
            2. Sử dụng thông tin từ cơ sở dữ liệu để cung cấp chi tiết chính xác về dịch vụ T3V
            3. Đảm bảo tính liên tục với các câu trả lời trước đó nếu đây là câu hỏi tiếp theo
            4. Cung cấp câu trả lời rõ ràng, ngắn gọn và thân thiện
            5. Giữ nguyên thông tin nguồn nếu có
            6. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
            7. Nếu không tồn tại câu hỏi hoặc tài liệu có thông tin không khớp bạn có thể trả lời 
            "T3V SERVICE chưa có thông tin. Chúng tôi sẽ cố gắng cập nhật thông tin này sau"
            """
        elif classification == "MOVIE":
            # Xử lý trường hợp movie_results là một danh sách
            if isinstance(movie_results, list):
                movie_results = {"movies": movie_results, "total_results": len(movie_results)}
            
            web_fallback = movie_results.get("web_fallback", False) if isinstance(movie_results, dict) else False
            
            if web_fallback:
                # Handle web fallbacks for movie searches
                final_prompt = base_prompt + f"""
                KẾT QUẢ TÌM KIẾM PHIM:
                Không tìm thấy phim trong cơ sở dữ liệu.
                
                KẾT QUẢ TÌM KIẾM WEB:
                {web_results}

                HƯỚNG DẪN:
                1. Người dùng đang tìm kiếm thông tin phim, nhưng cơ sở dữ liệu của chúng tôi không có kết quả
                2. Sử dụng kết quả tìm kiếm web để cung cấp thông tin về phim
                3. Định dạng câu trả lời của bạn như thông tin phim nếu có thể kèm cảnh báo thông tin này hoàn toàn tìm kiếm từ web và phim không có trên T3V
                4. Nếu đây là câu hỏi tiếp theo, đảm bảo tính liên tục với các câu trả lời trước đó
                5. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
                6. Thêm "Nguồn: Web" ở cuối cảnh báo người dùng chú ý với thông tin này
                """
            else:
                # ENHANCED Movie results prompt with STRICT formatting instructions
                final_prompt = base_prompt + f"""
                KẾT QUẢ TÌM KIẾM PHIM:
                {movie_results}

                HƯỚNG DẪN:
                1. Tham khảo bất kỳ cuộc thảo luận về phim liên quan nào từ lịch sử cuộc trò chuyện
                2. Trình bày kết quả theo định dạng rõ ràng, dễ đọc
                3. Nếu đây là câu hỏi tiếp theo, đảm bảo tính liên tục với các câu trả lời trước đó
                4. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
                5. Thêm "Nguồn: T3V Database" ở cuối
                
                HƯỚNG DẪN ĐỊNH DẠNG CỤ THỂ (ĐÂY LÀ YÊU CẦU BẮT BUỘC):
                1. Đối với MỖI bộ phim, bạn PHẢI bao gồm các thông tin sau theo thứ tự:
                   - Tiêu đề phim (bắt buộc)
                   - Thể loại (nếu có)
                   - Năm phát hành (nếu có)
                   - Thời lượng (nếu có)
                   - Mô tả ngắn (nếu có)
                   - Nếu hiện ảnh thì ảnh chỉ có kích thước tối đa là 64x64 px
                   - LINK CHI TIẾT (BẮT BUỘC): Sử dụng định dạng chính xác [Tiêu đề phim](http://localhost:5173/movie/ID_PHIM)
                     trong đó ID_PHIM là giá trị _id từ dữ liệu phim
                
                2. Ví dụ định dạng PHẢI CÓ VÀ chuẩn cho MỖI bộ phim:
                   **Tên phim**
                   - Thể loại: [thể loại] (nếu có)
                   - Năm phát hành: [năm] (nếu có)
                   - Thời lượng: [thời lượng] (nếu có)
                   - Mô tả: [mô tả ngắn] (nếu có)
                   - Xem chi tiết: [Tên phim](http://localhost:5173/movie/ID_PHIM_THỰC_TẾ)
                
                3. LƯU Ý QUAN TRỌNG:
                   - PHẢI có đường link chi tiết cho MỖI bộ phim
                   - ID_PHIM phải là giá trị _id chính xác từ dữ liệu phim
                   - Đường link phải có định dạng [Tên phim](http://localhost:5173/movie/ID_PHIM) và người dùng có thể bấm được vào đường link đó
                   - Đây là yêu cầu BẮT BUỘC và QUAN TRỌNG NHẤT của người dùng
                """
        else:  # OTHER
            final_prompt = base_prompt + f"""
            KẾT QUẢ TÌM KIẾM WEB:
            {web_results}

            HƯỚNG DẪN:
            1. Xem xét lịch sử cuộc trò chuyện để hiểu ngữ cảnh
            2. Sử dụng kết quả tìm kiếm web cho thông tin thực tế khi liên quan
            3. Tận dụng kiến thức chung của bạn để cung cấp câu trả lời toàn diện
            4. Nếu đây là câu hỏi tiếp theo của các câu hỏi trước đó, duy trì tính liên tục
            5. Nêu bật các điểm chính và trả lời một cách ngắn gọn
            6. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
            7. Thêm cảnh báo sau đây vào đầu câu trả lời và điều này là BẮT BUỘC VỚI CÂU TRẢ LỜI:
               *CÂU HỎI CỦA BẠN DỰA VÀO WEB SEARCH CỦA BÊN THỨ BA CÂU TRẢ LỜI CÓ THỂ SAI*
            8. Thêm "Nguồn: Web + Kiến thức" ở cuối và chú thích cơ sở dữ liệu của T3V không có thông tin mà bạn đang tìm
               thông tin bạn đang tìm được tìm trên web và phụ thuộc vào bên thứ 3
            9. Từ chối trả lời câu hỏi liên quan đến phim khi câu hỏi không liên quan đến phim và các dịch vụ của web T3V
            """

    # Gọi LLM để tổng hợp câu trả lời
    try:
        response = llm.invoke(final_prompt)
        response_text = response if isinstance(response, str) else response.content
        
        # Áp dụng tự sửa lỗi với trọng tâm nâng cao vào liên kết phim
        if classification == "MOVIE" or is_multi_source:
            # Thêm hướng dẫn đặc biệt để xác minh liên kết trong quá trình tự sửa lỗi
            movie_correction_context = """
            CRITICAL REQUIREMENT: Check for movie links
            
            Every movie entry MUST have a link to its details page in the format:
            [Movie Title](http://localhost:5173/movie/MOVIE_ID)
            
            If ANY movie is missing its link, add it using the movie's _id from the data.
            This is the HIGHEST PRIORITY formatting requirement.
            """
            final_answer = self_correct_response(query, response_text, classification, 
                                           history_context + movie_correction_context)
        else:
            final_answer = self_correct_response(query, response_text, classification, history_context)
        
        # Thêm thẻ nguồn bằng ngôn ngữ thích hợp nếu thiếu
        if is_vietnamese:
            if "nguồn:" not in final_answer.lower() and "source:" not in final_answer.lower():
                if is_multi_source:
                    final_answer += "\n\nNguồn: Web + Kiến thức"
                elif classification == "SERVICE":
                    final_answer += "\n\nNguồn: T3V Database"
                elif classification == "MOVIE" and not web_fallback:
                    final_answer += "\n\nNguồn: T3V Database"
                else:
                    # Thêm cảnh báo cho web search
                    warning = "\n\n*CÂU HỎI CỦA BẠN DỰA VÀO WEB SEARCH CỦA BÊN THỨ BA CÂU TRẢ LỜI CÓ THỂ SAI*\n\n"
                    if warning not in final_answer:
                        final_answer = warning + final_answer
                    final_answer += "\n\nNguồn: Web + Kiến thức"
        else:
            if "source:" not in final_answer.lower() and "nguồn:" not in final_answer.lower():
                if is_multi_source:
                    final_answer += "\n\nSource: Web + Knowledge"
                elif classification == "SERVICE":
                    final_answer += "\n\nSource: T3V Database"
                elif classification == "MOVIE" and not web_fallback:
                    final_answer += "\n\nSource: T3V Database"
                else:
                    # Add warning for web search
                    warning = "\n\n*YOUR QUESTION IS BASED ON THIRD-PARTY WEB SEARCH RESULTS MAY BE INACCURATE*\n\n"
                    if warning not in final_answer:
                        final_answer = warning + final_answer
                    final_answer += "\n\nSource: Web + Knowledge"
        
        # Kiểm tra xác minh cuối cùng cho liên kết phim - sửa lỗi khẩn cấp nếu vẫn còn thiếu liên kết
        if (classification == "MOVIE" or is_multi_source) and "http://localhost:5173/movie/" not in final_answer:
            # Cố gắng trích xuất ID phim từ movie_results
            if isinstance(movie_results, dict) and "movies" in movie_results:
                movies = movie_results["movies"]
                if isinstance(movies, list) and len(movies) > 0:
                    # Thêm ghi chú về liên kết bị thiếu và nối chúng
                    final_answer += "\n\n Link chi tiết phim:\n"
                    for movie in movies:
                        if isinstance(movie, dict) and "_id" in movie and "title" in movie:
                            movie_id = movie["_id"]
                            movie_title = movie["title"]
                            final_answer += f"- [{movie_title}](http://localhost:5173/movie/{movie_id})\n"
        
        # Lưu kết quả vào trạng thái
        state["final_answer"] = final_answer
        state["messages"].append(AIMessage(content=final_answer))
    except Exception as e:
        # Xử lý lỗi cải tiến - cung cấp phản hồi hữu ích hơn bằng ngôn ngữ của truy vấn
        print(f"Error during answer synthesis: {e}")
        if is_vietnamese:
            error_msg = f"Tôi gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại hoặc diễn đạt câu hỏi của bạn theo cách khác."
        else:
            error_msg = f"I'm having trouble processing your request. Please try rephrasing your question."
        
        state["final_answer"] = error_msg
        state["messages"].append(AIMessage(content=error_msg))
    
    return state


def self_correct_response(question, initial_response, intent, history=""):
    """
    Enhanced self-correction function with special handling for movie links
    """
    # Add specific instructions for movie links if this is a movie response
    movie_link_instructions = ""
    if intent == "MOVIE":
        movie_link_instructions = """
        SPECIAL VERIFICATION FOR MOVIE RESPONSES:
        - Every movie MUST have a clickable link to its details page
        - Every movie MUST have description and you MUST add description to the response
        - Each link MUST be formatted exactly as IF film has id: [Movie Title](http://localhost:5173/movie/MOVIE_ID)
        - If ANY movie is missing its link, this is a CRITICAL ERROR that must be fixed
        - If you don't see movie IDs in the response, add a note that links are missing
        
        This is the HIGHEST PRIORITY requirement for movie responses!
        """
    
    correction_prompt = f"""
    You are a quality assurance expert for the T3V chatbot.

    Conversation history:
    {history}

    Original question: {question}
    Intent classification: {intent}
    Current response: {initial_response}
    
    {movie_link_instructions}

    YOUR TASK:
    1. Evaluate the quality of the response based on:
       - Accuracy and completeness
       - Relevance to the question
       - Consistency with conversation history
       - Clarity and formatting
       - Professionalism and tone

    2. Improve the response if needed:
       - Ensure it maintains context from the conversation history
       - Resolve any references to previous messages (e.g., "as I mentioned earlier...")
       - Remove irrelevant information
       - Clarify unclear parts
       - Improve formatting for readability
       - Ensure the language matches the original question (Vietnamese or English)
       
    3. FOR MOVIE RESPONSES:
       - EVERY movie MUST have a clickable details link in format if film has id: [Title](http://localhost:5173/movie/ID)
       - The ID must be the actual movie ID from the database
       - This is the MOST IMPORTANT requirement for movie responses
       - If links are missing, add them or add a note about missing links

    4. Preserve all key details such as:
       - Original information sources (VectorDB, TMDB, etc.)
       - Accurate factual content
       - Any special formatting already present

    DO NOT change the meaning or core information of the original response.

    Return only the improved response (do not explain changes):
    """
    
    try:
        # Call the correction LLM with history context
        response = llm.invoke(correction_prompt)
        
        corrected = response if isinstance(response, str) else response.content
        corrected = corrected.strip()
        
        # Fallback if corrected response is too short or empty
        if not corrected or len(corrected) < 20:
            return initial_response
            
        return corrected
    except Exception as e:
        print(f"Self-correction error: {e}")
        return initial_response
    

# Router function based on classification
def router(state: AgentState) -> str:
    classification = state["classification"]["category"]
    
    if classification == "SERVICE":
        return "service_node"
    elif classification == "MOVIE":
        return "movie_node"
    else:  # OTHER
        return "web_node"
    
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
    source_context = ""
    if previous_sources:
        most_recent_source = previous_sources[-1] if previous_sources else "UNKNOWN"
        source_context = f"\n[Previous topic category: {most_recent_source}]"
    
    # If history is too long, include the first exchanges and the most recent ones
    if len(formatted_history) > 2*max_turns:
        return "\n".join(formatted_history[:2] + ["..."] + formatted_history[-2*max_turns+2:]) + source_context
    
    return "\n".join(formatted_history) + source_context

            


