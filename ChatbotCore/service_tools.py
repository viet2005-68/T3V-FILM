from state import AgentState
from document_tools import get_unique_documents, advanced_rag_tool, chroma_collection
from config import llm
from response_tools import format_chat_history
from response_tools import self_correct_response
from langchain_core.messages import AIMessage
from document_tools import self_rag_search

# Node RAG for SERVICE
def service_rag_node(state: AgentState) -> AgentState:
    """
    Enhanced service RAG node that incorporates Self-RAG for improved document retrieval and response quality.
    """
    query = state["query"]
    chat_history = state["chat_history"]
    
    print(f"Processing SERVICE query with Self-RAG: {query}")
    
    try:
        # Initial document retrieval
        initial_docs = get_unique_documents(query, chroma_collection)
        
        # Apply Self-RAG for improved document retrieval
        self_rag_results = self_rag_search(query, initial_docs, state)
        
        # Get enhanced documents and quality metrics
        enhanced_docs = self_rag_results["retrieved_documents"]
        quality_score = self_rag_results["final_quality_score"]
        iterations = self_rag_results["iterative_searches"]
        
        print(f"Self-RAG completed with {iterations} iterations. Final quality: {quality_score:.2f}")
        
        # Format the retrieved documents for the prompt
        if isinstance(enhanced_docs, list):
            context = "\n\n".join(enhanced_docs[:5])  # Use top 5 documents
        else:
            context = enhanced_docs
        
        # Enhanced RAG system prompt with conversation context
        system_prompt = """
        Bạn là trợ lý hỗ trợ khách hàng chuyên nghiệp cho dịch vụ xem phim trực tuyến T3V.

        NGỮ CẢNH HỘI THOẠI:
        {history}
        
        NHIỆM VỤ:
        Sử dụng thông tin từ các tài liệu được cung cấp và ngữ cảnh cuộc trò chuyện để trả lời câu hỏi của người dùng một cách chính xác.

        HƯỚNG DẪN:
        1. Xem xét lịch sử cuộc trò chuyện để nắm bắt ngữ cảnh
        2. Đọc kỹ các tài liệu được cung cấp
        3. Nhận ra các câu hỏi tiếp theo và duy trì sự liên tục về ngữ cảnh
        4. Tổng hợp thông tin từ nhiều tài liệu nếu cần
        5. Viết câu trả lời rõ ràng, súc tích, thân thiện và chuyên nghiệp
        6. CHỈ cung cấp thông tin có trong tài liệu, KHÔNG tự tạo câu trả lời
        7. Nếu thông tin không đầy đủ hoặc thiếu, hãy thừa nhận điều đó

        RẤT QUAN TRỌNG:
        - Trả lời bằng cùng ngôn ngữ với câu hỏi của người dùng (tiếng Anh hoặc tiếng Việt)
        - Luôn đại diện cho T3V một cách chuyên nghiệp
        - Sử dụng định dạng rõ ràng như dấu đầu dòng hoặc danh sách đánh số khi thích hợp
        - Nếu không tìm thấy thông tin cụ thể, hãy đề xuất liên hệ với bộ phận hỗ trợ khách hàng

        TÀI LIỆU THAM KHẢO:
        {context}
        
        CÂU HỎI NGƯỜI DÙNG:
        {query}
        """
        
        # Format history context
        history_context = format_chat_history(chat_history) if chat_history else "Không có cuộc trò chuyện trước đó"
        
        # Run the enhanced RAG chain
        response = llm.invoke(system_prompt.format(
            context=context, 
            query=query,
            history=history_context
        ))
        
        # Process response
        rag_result = response if isinstance(response, str) else response.content
        
        # Apply self-correction to improve response quality
        corrected_response = self_correct_response(
            question=query,
            initial_response=rag_result,
            intent="SERVICE",
            history=history_context
        )
        
        # Save results to state
        state["retrieved_documents"] = corrected_response
        state["search_quality"] = quality_score
        state["messages"].append(AIMessage(content=corrected_response))
        
        # Store the documents for optional display
        state["raw_documents"] = enhanced_docs
        
        return state
        
    except Exception as e:
        print(f"Error in service_rag_node: {e}")
        # Fallback to standard RAG approach
        rag_results = advanced_rag_tool(query, chat_history)
        state["retrieved_documents"] = rag_results
        state["messages"].append(AIMessage(content=rag_results))
        return state