import re
from config import llm
from state import AgentState, format_chat_history
from langchain_core.messages import AIMessage
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


def self_correct_response(question, initial_response, intent, history=""):
    """
    Review and improve the initial response for quality, accuracy, and historical context.
    """
    correction_prompt = """
    You are a quality assurance expert for the T3V chatbot.

    Conversation history:
    {history}

    Original question: {question}
    Intent classification: {intent}
    Current response: {response}

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

    3. Preserve all key details such as:
       - Original information sources (VectorDB, TMDB, etc.)
       - Accurate factual content
       - Any special formatting already present

    DO NOT change the meaning or core information of the original response.

    Return only the improved response (do not explain changes):
    """
    
    try:
        # Call the correction LLM with history context
        response = llm.invoke(correction_prompt.format(
            question=question,
            intent=intent,
            response=initial_response,
            history=history
        ))
        
        corrected = response if isinstance(response, str) else response.content
        corrected = corrected.strip()
        
        # Fallback if corrected response is too short or empty
        if not corrected or len(corrected) < 20:
            return initial_response
            
        return corrected
    except Exception as e:
        print(f"Self-correction error: {e}")
        return initial_response
    
# Node for FINAL ANSWER
def answer_synthesizer_node(state: AgentState) -> AgentState:
    query = state["query"]
    classification = state["classification"]["category"]
    
    # Convert message objects to proper format
    raw_history = state["chat_history"]
    chat_history = [convert_message_to_dict(msg) for msg in raw_history] if raw_history else []
    
    # Create detailed context from chat history
    history_context = ""
    if chat_history:
        # Format only the most recent exchanges (last 3-4 exchanges)
        recent_messages = chat_history[-8:]  # Last 4 exchanges
        history_context = "Recent conversation:\n"
        for msg in recent_messages:
            prefix = "User: " if msg['role'] == 'human' else "Assistant: "
            history_context += f"{prefix}{msg['content']}\n"
        history_context += "\n"

    # Enhanced synthesis prompts with history for all response types
    if classification == "SERVICE":
        rag_results = state["retrieved_documents"]
        synthesis_prompt = f"""
You are a customer support agent for the T3V streaming platform.

Conversation history:
{history_context}

Your task:
- Respond to the user's question clearly, politely, and directly
- Consider both the conversation history and the information provided below
- If this is a follow-up question, maintain context from the previous exchanges
- Base your answer on the information provided — do not make assumptions
- Reply in the same language as the user's question (English or Vietnamese)
- IF INFORMATION NOT CONTAIN OR NOT RELATE IN {rag_results} you must answer: "T3V don't have this information. Please contact T3V'admin to know more !"
Information from the documents:
{rag_results}

Current user question:
{query}

Your response:
"""

    elif classification == "MOVIE":
        movie_results = state["movie_results"]
        synthesis_prompt = f"""
You are a movie expert for the T3V streaming platform.

Conversation history:
{history_context}

Current user query: {query}
Search results: {movie_results}

Your task:
- Create a helpful response about these movies
- Consider the conversation history when generating your response
- If this is a follow-up question, maintain context from previous messages
- Present results in a clean, readable format
- If available, include movie title, genre, and release year
- Reply in the same language as the user's question

Append "Source: T3V DATABASE" at the end of your response and notice user should check infomation again.
"""
    else:  # OTHER
        web_results = state["retrieved_documents"]
        synthesis_prompt = f"""
You are a helpful assistant for the T3V streaming platform.

Conversation history:
{history_context}

Current user query: {query}
Web results: {web_results}

Your task:
- Create a helpful response based on the web results
- Consider the conversation history when generating your response
- If this is a follow-up question, maintain context from previous messages
- Highlight key points and answer concisely
- Reply in the same language as the user's question

Append "Source: Web" at the end of your response.
"""

    # Call LLM to synthesize the answer
    response = llm.invoke(synthesis_prompt)
    response_text = response if isinstance(response, str) else response.content
    
    # Apply self-correction with history context
    final_answer = self_correct_response(query, response_text, classification, history_context)

    # Save results to state
    state["final_answer"] = final_answer
    state["messages"].append(AIMessage(content=final_answer))
    
    return state

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

            


def unified_answer_synthesizer_node(state: AgentState) -> AgentState:
    query = state["query"]
    classification = state["classification"]["category"]
    confidence = state["classification"].get("confidence", "medium")
    chat_history = state["chat_history"]
    
    # Format chat history for context
    history_context = format_chat_history(chat_history) if chat_history else ""
    
    # Detect language (Vietnamese or English)
    is_vietnamese = any(c in query.lower() for c in "ăâêôơưđ") or "bố già" in query.lower() or "phim" in query.lower()
    
    # Base prompt structure with history included
    base_prompt = f"""
    LỊCH SỬ HỘI THOẠI:
    {history_context}

    CÂU HỎI HIỆN TẠI:
    {query}
    
    PHÂN LOẠI:
    {classification} (Độ tin cậy: {confidence})
    """
    
    # Add category-specific information
    if classification == "SERVICE":
        rag_results = state["retrieved_documents"]
        final_prompt = base_prompt + f"""
        THÔNG TIN CƠ SỞ DỮ LIỆU DỊCH VỤ T3V:
        {rag_results}

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
        movie_results = state["movie_results"]
        web_fallback = movie_results.get("web_fallback", False)
        
        if web_fallback:
            # Handle web fallbacks for movie searches
            web_results = state.get("retrieved_documents", "Không có kết quả tìm kiếm web")
            final_prompt = base_prompt + f"""
            KẾT QUẢ TÌM KIẾM PHIM:
            Không tìm thấy phim trong cơ sở dữ liệu.
            
            KẾT QUẢ TÌM KIẾM WEB:
            {web_results}

            HƯỚNG DẪN:
            1. Người dùng đang tìm kiếm thông tin phim, nhưng cơ sở dữ liệu của chúng tôi không có kết quả
            2. Sử dụng kết quả tìm kiếm web để cung cấp thông tin về phim
            3. Định dạng câu trả lời của bạn như thông tin phim nếu có thể
            4. Nếu đây là câu hỏi tiếp theo, đảm bảo tính liên tục với các câu trả lời trước đó
            5. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
            6. Thêm "Nguồn: Web" ở cuối cảnh báo người dùng chú ý với thông tin này
            """
        else:
            # Normal movie results
            final_prompt = base_prompt + f"""
            KẾT QUẢ TÌM KIẾM PHIM:
            {movie_results}

            HƯỚNG DẪN:
            1. Tham khảo bất kỳ cuộc thảo luận về phim liên quan nào từ lịch sử cuộc trò chuyện
            2. Trình bày kết quả theo định dạng rõ ràng, dễ đọc
            3. Nếu đây là câu hỏi tiếp theo, đảm bảo tính liên tục với các câu trả lời trước đó
            4. Nếu có, bao gồm tiêu đề phim, thể loại và năm phát hành
            5. Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Việt hoặc tiếng Anh)
            6. Thêm "Nguồn: T3V Database" ở cuối
            """
    else:  # OTHER
        web_results = state.get("retrieved_documents", "Không có kết quả tìm kiếm web")
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
        7. Thêm "Nguồn: Web + Kiến thức" ở cuối và chú thích cơ sở dữ liệu của T3V không có thông tin mà bạn đang tìm
            thông tin bạn đang tìm được tìm trên web và phụ thuộc vào bên thứ 3
        """

    # Call LLM to synthesize the answer
    try:
        response = llm.invoke(final_prompt)
        response_text = response if isinstance(response, str) else response.content
        
        # Apply self-correction with history context
        final_answer = self_correct_response(query, response_text, classification, history_context)
        
        # Add source tag in the appropriate language if missing
        if is_vietnamese:
            if "nguồn:" not in final_answer.lower() and "source:" not in final_answer.lower():
                if classification == "SERVICE":
                    final_answer += "\n\nNguồn: VectorDB"
                elif classification == "MOVIE" and not web_fallback:
                    final_answer += "\n\nNguồn: TMDB"
                else:
                    final_answer += "\n\nNguồn: Web + Kiến thức"
        else:
            if "source:" not in final_answer.lower() and "nguồn:" not in final_answer.lower():
                if classification == "SERVICE":
                    final_answer += "\n\nSource: VectorDB"
                elif classification == "MOVIE" and not web_fallback:
                    final_answer += "\n\nSource: TMDB"
                else:
                    final_answer += "\n\nSource: Web + Knowledge"
        
        # Save results to state
        state["final_answer"] = final_answer
        state["messages"].append(AIMessage(content=final_answer))
    except Exception as e:
        # Improved error handling - provide a more helpful response in the language of the query
        if is_vietnamese:
            error_msg = f"Tôi gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại hoặc diễn đạt câu hỏi của bạn theo cách khác."
        else:
            error_msg = f"I'm having trouble processing your request. Please try rephrasing your question."
        
        state["final_answer"] = error_msg
        state["messages"].append(AIMessage(content=error_msg))
    
    return state

