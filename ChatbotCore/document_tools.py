import json
from typing import List, Dict, Any
from state import AgentState
from config import llm
from embedding_manager import EmbeddingManager
from pathlib import Path
import re
from response_tools import convert_message_to_dict
# Initialize embedding manager
embedding_manager = EmbeddingManager(storage_path="embeddings")

# Process PDF data
file_path = Path(__file__).parent.parent / "data" / "T3V Chatbot Training Data.pdf"
embedding_manager.process_pdf(file_path)

# Get ChromaDB collection
chroma_collection = embedding_manager.get_collection()

def generate_multi_query(query):
    prompt_template = """
    You are an information search expert for the T3V streaming service.
    Given an initial question, generate different variations to expand the search scope. If question not relate about T3V service, stop and don't generate expand question

    INSTRUCTIONS:
    1. Generate 3-5 related questions, each with a different angle or phrasing
    2. Keep each question concise and focused (no more than 15 words)
    3. Include key terms from the original query
    4. Add synonyms or broaden the scope of the search
    5. Each question must be meaningful and standalone

    EXAMPLE:
    Original question: "How do I watch movies on T3V?"

    Expanded questions:
    How to register to watch T3V movies
    Guide to using the T3V app
    Devices supported by T3V streaming
    Movie viewing features on T3V
    Accessing T3V content

    Original question: {query}

    Expanded questions (list directly, no titles or numbering):
    """

    try:
        response = llm.invoke(prompt_template.format(query=query))
        content = response if isinstance(response, str) else response.content

        expanded_queries = []
        for line in content.split("\n"):
            cleaned_line = line.strip()
            if cleaned_line and not cleaned_line.startswith("-") and not cleaned_line.lower().startswith("expanded"):
                expanded_queries.append(cleaned_line)

        if not expanded_queries:
            return [query]

        if query not in expanded_queries:
            expanded_queries.insert(0, query)

        return expanded_queries[:5]
    except Exception as e:
        print(f"Error in query expansion: {e}")
        return [query]

# Document retrieval with deduplication
def get_unique_documents(query, chroma_collection, n_results=7):
    try:
        # Generate expanded queries
        aug_queries = generate_multi_query(query)
        
        # Debug information
        print("\nOriginal query:", query)
        print("\nExpanded queries:")
        for q in aug_queries:
            print(f"- {q}")
        
        # Combine original query with expanded queries, but prioritize the original
        joint_query = [query] + aug_queries
        
        # Set different n_results for original query vs. expanded queries
        original_results = 5  # More results from original query
        expanded_results = 3  # Fewer from each expanded query
        
        # Combined storage for results
        all_documents = []
        all_distances = []
        
        # Query with original query first (higher weight)
        original_result = chroma_collection.query(
            query_texts=[query], 
            n_results=original_results,
            include=["documents", "distances"]
        )
        
        all_documents.extend(original_result["documents"][0])
        all_distances.extend(original_result["distances"][0])
        
        # Query with expanded queries
        for expanded_q in aug_queries:
            expanded_result = chroma_collection.query(
                query_texts=[expanded_q], 
                n_results=expanded_results,
                include=["documents", "distances"]
            )
            
            if expanded_result["documents"]:
                all_documents.extend(expanded_result["documents"][0])
                all_distances.extend(expanded_result["distances"][0])
        
        # Create dictionary for deduplication
        unique_documents = {}
        for i, doc in enumerate(all_documents):
            # Only store the best score if document appears multiple times
            if doc not in unique_documents or all_distances[i] < unique_documents[doc]:
                unique_documents[doc] = all_distances[i]
        
        # Sort by relevance score (distance)
        sorted_docs = sorted(unique_documents.items(), key=lambda x: x[1])
        
        # Print number of documents retrieved
        print(f"\nRetrieved {len(sorted_docs)} unique documents")
        
        # Return just the documents (not the scores)
        return [doc for doc, _ in sorted_docs]
    except Exception as e:
        print(f"Error in document retrieval: {e}")
        # Fallback to direct query
        try:
            results = chroma_collection.query(
                query_texts=[query], 
                n_results=n_results,
            )
            return results["documents"][0]
        except Exception as fallback_error:
            print(f"Fallback query also failed: {fallback_error}")
            return ["No relevant documents found."]


# Add Self-RAG and React Agent functionality
def evaluate_retrieval_quality(query: str, retrieved_docs: List[str], threshold: float = 0.7) -> Dict[str, Any]:
    """
    Evaluates the quality of retrieved documents against a query.
    
    Args:
        query: The user's original query
        retrieved_docs: A list of documents retrieved from the vector store
        threshold: Minimum required relevance score
        
    Returns:
        Dictionary with evaluation results and recommendations
    """
    
    if not retrieved_docs or (isinstance(retrieved_docs, list) and len(retrieved_docs) > 0 and retrieved_docs[0] == "No relevant documents found."):
        return {
            "quality_score": 0.0,
            "needs_additional_search": True,
            "query_suggestions": [f"more information about {query}", f"{query} explained", f"{query} features T3V"],
            "reasoning": "No documents were retrieved. Additional search is needed."
        }
    
    # Handle string vs list format
    docs_text = ""
    if isinstance(retrieved_docs, list):
        docs_text = "\n\n".join(retrieved_docs[:3])
    else:
        docs_text = retrieved_docs[:500]  # Limit string length
    
    # Create a prompt to evaluate document relevance
    evaluation_prompt = f"""
    Evaluate the relevance of these retrieved documents to the following query:
    
    QUERY: {query}
    
    DOCUMENTS:
    {docs_text}
    
    INSTRUCTIONS:
    1. Analyze how directly the documents address the query
    2. Check if key aspects of the query are covered in the documents
    3. Determine if crucial information is missing
    4. Evaluate overall relevance on a scale of 0.0 to 1.0
    
    Return your evaluation as a JSON object with these fields:
    - quality_score: float between 0 and 1
    - needs_additional_search: boolean
    - missing_aspects: list of aspects not covered
    - query_suggestions: list of 2-3 improved search queries (if needed)
    - reasoning: brief explanation
    
    JSON RESPONSE:
    """
    
    try:
        # Run evaluation through LLM
        response = llm.invoke(evaluation_prompt)
        content = response if isinstance(response, str) else response.content
        
        # Parse the JSON response
        try:
            evaluation = json.loads(content)
        except json.JSONDecodeError:
            # Fallback to regex extraction if JSON parsing fails
            quality_match = re.search(r'"quality_score":\s*([\d.]+)', content)
            needs_search_match = re.search(r'"needs_additional_search":\s*(true|false)', content, re.IGNORECASE) 
            reasoning_match = re.search(r'"reasoning":\s*"([^"]*)"', content)
            
            quality_score = float(quality_match.group(1)) if quality_match else 0.5
            needs_search = needs_search_match.group(1).lower() == "true" if needs_search_match else True
            reasoning = reasoning_match.group(1) if reasoning_match else "Evaluation parsing failed"
            
            # Extract query suggestions with regex
            suggestions_match = re.search(r'"query_suggestions":\s*\[(.*?)\]', content, re.DOTALL)
            suggestions = []
            if suggestions_match:
                suggestion_items = re.findall(r'"([^"]+)"', suggestions_match.group(1))
                suggestions = suggestion_items[:3]  # Limit to 3 suggestions
            
            evaluation = {
                "quality_score": quality_score,
                "needs_additional_search": needs_search,
                "query_suggestions": suggestions or [f"more about {query}", f"{query} details", f"{query} T3V specific"],
                "reasoning": reasoning
            }
        
        # Ensure minimum fields are present
        if "quality_score" not in evaluation:
            evaluation["quality_score"] = 0.5
        if "needs_additional_search" not in evaluation:
            evaluation["needs_additional_search"] = evaluation["quality_score"] < threshold
        if "query_suggestions" not in evaluation:
            evaluation["query_suggestions"] = [f"more about {query}", f"{query} details", f"{query} T3V specific"]
        if "reasoning" not in evaluation:
            evaluation["reasoning"] = "Basic quality evaluation"
            
        return evaluation
        
    except Exception as e:
        print(f"Error in retrieval evaluation: {e}")
        # Return default evaluation on error
        return {
            "quality_score": 0.5,
            "needs_additional_search": True,
            "query_suggestions": [f"more about {query}", f"{query} details", f"{query} T3V specific"],
            "reasoning": f"Evaluation error: {str(e)}"
        }

def self_rag_search(query: str, initial_docs: List[str], state: AgentState) -> Dict[str, Any]:
    """
    Implements Self-RAG approach to improve retrieval quality through iterative refinement.
    
    Args:
        query: The original user query
        initial_docs: The initial set of retrieved documents
        state: The current agent state
        
    Returns:
        Updated state with improved document retrieval
    """
    # First, evaluate the quality of initial retrieval
    evaluation = evaluate_retrieval_quality(query, initial_docs)
    print(f"\nInitial retrieval quality: {evaluation['quality_score']:.2f}")
    print(f"Reasoning: {evaluation['reasoning']}")
    
    # If quality is sufficient, return the initial docs
    if not evaluation["needs_additional_search"] or evaluation["quality_score"] >= 0.8:
        print("Initial retrieval quality is sufficient.")
        return {
            "retrieved_documents": initial_docs,
            "final_quality_score": evaluation["quality_score"],
            "iterative_searches": 0
        }
    
    # Track documents and their quality
    best_docs = initial_docs
    best_quality = evaluation["quality_score"]
    
    # Maximum number of iterations
    max_iterations = 2
    
    # Modified queries for additional searches
    query_suggestions = evaluation.get("query_suggestions", [])
    if not query_suggestions:
        query_suggestions = [
            f"{query} T3V platform details",
            f"{query} specific information"
        ]
    
    all_docs = set()
    if isinstance(initial_docs, list):
        all_docs.update(initial_docs)
    else:
        all_docs.add(initial_docs)
        
    iteration_results = []
    
    # Perform iterative search refinement
    for i, suggested_query in enumerate(query_suggestions[:max_iterations]):
        print(f"\nTrying refined query: '{suggested_query}'")
        
        try:
            # Get documents for the refined query
            refined_docs = get_unique_documents(suggested_query, chroma_collection)
            
            # Add new docs to the combined set
            if isinstance(refined_docs, list):
                for doc in refined_docs:
                    if doc not in all_docs and doc != "No relevant documents found.":
                        all_docs.add(doc)
            else:
                if refined_docs not in all_docs and refined_docs != "No relevant documents found.":
                    all_docs.add(refined_docs)
            
            # Evaluate this retrieval
            refined_evaluation = evaluate_retrieval_quality(query, refined_docs)
            print(f"Refined query quality: {refined_evaluation['quality_score']:.2f}")
            
            # Store iteration results
            if isinstance(refined_docs, list):
                docs_sample = refined_docs[:3]  # Top 3 docs
            else:
                docs_sample = refined_docs[:300]  # Sample of string
                
            iteration_results.append({
                "query": suggested_query,
                "quality": refined_evaluation["quality_score"],
                "docs": docs_sample
            })
            
            # Update best docs if quality improved
            if refined_evaluation["quality_score"] > best_quality:
                best_quality = refined_evaluation["quality_score"]
                best_docs = refined_docs
                
        except Exception as e:
            print(f"Error in iteration {i+1}: {e}")
    
    # Create a combined set of the best documents
    combined_docs = list(all_docs)[:7] if all_docs else initial_docs  # Limit to top 7 docs
    
    # Final combined evaluation
    combined_evaluation = evaluate_retrieval_quality(query, combined_docs)
    
    print(f"\nFinal retrieval quality after {len(iteration_results)} iterations: {combined_evaluation['quality_score']:.2f}")
    
    # Return the better set of documents
    if combined_evaluation["quality_score"] >= best_quality:
        return {
            "retrieved_documents": combined_docs,
            "final_quality_score": combined_evaluation["quality_score"],
            "iterative_searches": len(iteration_results),
            "iterations": iteration_results
        }
    else:
        return {
            "retrieved_documents": best_docs,
            "final_quality_score": best_quality,
            "iterative_searches": len(iteration_results),
            "iterations": iteration_results
        }

#define advanced_rag_tool function
def advanced_rag_tool(query_text: str, raw_history=None) -> str:
    try:
        # Convert message objects to proper format
        chat_history = [convert_message_to_dict(msg) for msg in raw_history] if raw_history else []
        
        # Extract relevant context from chat history
        context_from_history = ""
        previous_queries = []
        previous_topics = []
        
        if chat_history:
            # Find the most recent relevant exchanges
            recent_messages = chat_history[-6:]  # Last 3 exchanges
            for i, msg in enumerate(recent_messages):
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                # Collect previous user queries for context enhancement
                if role == 'human':
                    previous_queries.append(content)
                    
                # Track the topic categories from assistant responses
                if role == 'ai' or role == 'assistant':
                    if "source: vectordb" in content.lower():
                        previous_topics.append("SERVICE")
                    elif "source: tmdb" in content.lower():
                        previous_topics.append("MOVIE")
                        
                # Format for context
                role_prefix = "User: " if role == 'human' else "Assistant: "
                context_from_history += f"{role_prefix}{content}\n"
        
        # Check if this is a follow-up question
        is_followup = False
        if previous_queries and previous_topics:
            followup_indicators = ["what about", "how about", "tell me more", "and", "also", "another", "more",
                                  "còn", "vậy còn", "thêm", "tiếp", "và", "nữa", "có gì khác"]
            
            is_followup = (
                len(query_text.split()) <= 4 or
                any(indicator in query_text.lower() for indicator in followup_indicators) or
                query_text.strip().startswith("còn") or
                query_text.strip().startswith("và") or
                query_text.strip().startswith("and")
            )
        
        # Create an enhanced query that incorporates conversation context
        enhanced_query = query_text
        
        # For follow-up questions, combine with previous query for better context
        if is_followup and previous_queries:
            most_recent_query = previous_queries[-1]
            enhanced_query = f"{most_recent_query} và {query_text}"
            print(f"Enhanced query for follow-up: {enhanced_query}")
        
        # Retrieve unique documents based on the enhanced query
        unique_documents = get_unique_documents(enhanced_query, chroma_collection, n_results=5)

        if not unique_documents or unique_documents[0] == "No relevant documents found.":
            return "Tôi không tìm thấy thông tin cụ thể cho câu hỏi này trong cơ sở kiến thức T3V. Vui lòng liên hệ bộ phận hỗ trợ để được trợ giúp thêm.\n\nNguồn: VectorDB"

        # Enhanced RAG system prompt with conversational context
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

        # Prepare the context
        context = "\n\n".join([f"Tài liệu {i+1}:\n{doc}" for i, doc in enumerate(unique_documents[:5])])
        
        # Run the RAG chain with history
        response = llm.invoke(system_prompt.format(
            context=context, 
            query=query_text,
            history=context_from_history if chat_history else "Không có cuộc trò chuyện trước đó"
        ))
        
        # Handle different response types
        final_answer = response if isinstance(response, str) else response.content

        # Clean up the final answer
        response_text = final_answer.strip()

        if len(response_text) < 20:
            return "Không có đủ thông tin để trả lời câu hỏi của bạn. Vui lòng liên hệ bộ phận hỗ trợ khách hàng T3V để được hỗ trợ thêm.\n\nNguồn: VectorDB"

        return response_text + "\n\nNguồn: VectorDB"

    except Exception as e:
        print(f"Error in RAG tool: {e}")
        return f"Đã xảy ra lỗi khi truy xuất thông tin: {str(e)}. Vui lòng thử lại sau hoặc liên hệ bộ phận hỗ trợ khách hàng T3V.\n\nNguồn: VectorDB Error"