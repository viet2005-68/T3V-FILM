import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.prompts.prompt import PromptTemplate

# Tải biến môi trường từ file .env
load_dotenv()

# Lấy API keys từ biến môi trường
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# Kiểm tra API keys
if not OPENAI_API_KEY:
    st.error("Không tìm thấy OPENAI_API_KEY trong file .env. Vui lòng thêm vào file .env.")
    st.stop()

if not TMDB_API_KEY:
    st.warning("Không tìm thấy TMDB_API_KEY trong file .env. Chức năng tìm kiếm phim sẽ không hoạt động.")

# Cấu hình OpenAI API Key cho LangChain
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Cấu hình trang Streamlit
st.set_page_config(page_title="Multi-Source ChatBot", layout="wide")
st.title("ChatBot với PDF, CSV và TMDB API")

# Thông báo về API keys
with st.sidebar:
    st.header("Thông tin API")
    if OPENAI_API_KEY:
        st.success("✅ Đã tải OpenAI API Key từ .env")
    else:
        st.error("❌ Chưa cấu hình OpenAI API Key")
    
    if TMDB_API_KEY:
        st.success("✅ Đã tải TMDB API Key từ .env")
    else:
        st.error("❌ Chưa cấu hình TMDB API Key")

# Khởi tạo session state variables
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "combined_vectorstore" not in st.session_state:
    st.session_state.combined_vectorstore = None

# Hàm xử lý tải file PDF từ đường dẫn
def process_pdf_from_path(pdf_path):
    try:
        # Kiểm tra nếu đường dẫn là thư mục thì xử lý tất cả các file pdf trong thư mục
        if os.path.isdir(pdf_path):
            loader = DirectoryLoader(pdf_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
            documents = loader.load()
        else:
            # Nếu là file cụ thể
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
        
        # Chia nhỏ tài liệu
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        # Tạo embeddings và lưu vào vectorstore
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, base_url= OPENAI_BASE_URL)
        vectorstore = FAISS.from_documents(docs, embeddings)
        
        return vectorstore, f"Đã xử lý PDF từ: {pdf_path}"
    except Exception as e:
        return None, f"Lỗi khi xử lý PDF: {str(e)}"

# Hàm xử lý tải file CSV từ đường dẫn
def process_csv_from_path(csv_path):
    try:
        # Kiểm tra nếu đường dẫn là thư mục thì xử lý tất cả các file csv trong thư mục
        if os.path.isdir(csv_path):
            all_docs = []
            for file in os.listdir(csv_path):
                if file.endswith('.csv'):
                    file_path = os.path.join(csv_path, file)
                    loader = CSVLoader(file_path=file_path)
                    all_docs.extend(loader.load())
            documents = all_docs
        else:
            # Nếu là file cụ thể
            loader = CSVLoader(file_path=csv_path)
            documents = loader.load()
        
        # Chia nhỏ tài liệu nếu cần
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        # Tạo embeddings và lưu vào vectorstore
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, base_url= os.getenv(OPENAI_BASE_URL))
        vectorstore = FAISS.from_documents(docs, embeddings)
        
        return vectorstore, f"Đã xử lý CSV từ: {csv_path}"
    except Exception as e:
        return None, f"Lỗi khi xử lý CSV: {str(e)}"

# Hàm gọi TMDB API
def call_tmdb_api(endpoint, params=None):
    base_url = "https://api.themoviedb.org/3"
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Content-Type": "application/json;charset=utf-8"
    }
    
    url = f"{base_url}/{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Tools TMDB API
def get_popular_movies(query=None):
    """Lấy danh sách phim phổ biến nhất hiện tại"""
    if not TMDB_API_KEY:
        return "Không thể sử dụng chức năng này. TMDB API Key chưa được cấu hình."
    
    response = call_tmdb_api("movie/popular", {"language": "vi-VN"})
    if "error" in response:
        return f"Lỗi khi lấy phim phổ biến: {response['error']}"
    
    results = response.get("results", [])
    if not results:
        return "Không tìm thấy phim phổ biến nào."
    
    formatted_results = "Các phim phổ biến nhất hiện tại:\n\n"
    for i, movie in enumerate(results[:10], 1):
        title = movie.get("title", "Không có tiêu đề")
        overview = movie.get("overview", "Không có mô tả")
        release_date = movie.get("release_date", "Không có ngày phát hành")
        vote_average = movie.get("vote_average", 0)
        
        formatted_results += f"{i}. {title}\n"
        formatted_results += f"   Ngày phát hành: {release_date}\n"
        formatted_results += f"   Đánh giá: {vote_average}/10\n"
        formatted_results += f"   Tóm tắt: {overview[:200]}...\n\n"
    
    return formatted_results

def search_movies(query):
    """Tìm kiếm phim theo từ khóa"""
    if not TMDB_API_KEY:
        return "Không thể sử dụng chức năng này. TMDB API Key chưa được cấu hình."
    
    if not query:
        return "Vui lòng cung cấp từ khóa tìm kiếm."
    
    response = call_tmdb_api("search/movie", {"query": query, "language": "vi-VN"})
    if "error" in response:
        return f"Lỗi khi tìm kiếm phim: {response['error']}"
    
    results = response.get("results", [])
    if not results:
        return f"Không tìm thấy phim nào với từ khóa '{query}'."
    
    formatted_results = f"Kết quả tìm kiếm cho '{query}':\n\n"
    for i, movie in enumerate(results[:5], 1):
        title = movie.get("title", "Không có tiêu đề")
        overview = movie.get("overview", "Không có mô tả")
        release_date = movie.get("release_date", "Không có ngày phát hành")
        vote_average = movie.get("vote_average", 0)
        
        formatted_results += f"{i}. {title}\n"
        formatted_results += f"   Ngày phát hành: {release_date}\n"
        formatted_results += f"   Đánh giá: {vote_average}/10\n"
        formatted_results += f"   Tóm tắt: {overview[:200]}...\n\n"
    
    return formatted_results

def get_movie_recommendations(query):
    """Lấy đề xuất phim tương tự dựa trên tên phim"""
    if not TMDB_API_KEY:
        return "Không thể sử dụng chức năng này. TMDB API Key chưa được cấu hình."
    
    if not query:
        return "Vui lòng cung cấp tên phim để tìm đề xuất."
    
    # Đầu tiên tìm phim theo tên
    search_response = call_tmdb_api("search/movie", {"query": query, "language": "vi-VN"})
    if "error" in search_response:
        return f"Lỗi khi tìm kiếm phim: {search_response['error']}"
    
    results = search_response.get("results", [])
    if not results:
        return f"Không tìm thấy phim nào với tên '{query}'."
    
    # Lấy ID của phim đầu tiên
    movie_id = results[0]["id"]
    movie_title = results[0]["title"]
    
    # Lấy các phim tương tự
    recommendations = call_tmdb_api(f"movie/{movie_id}/recommendations", {"language": "vi-VN"})
    if "error" in recommendations:
        return f"Lỗi khi lấy đề xuất phim: {recommendations['error']}"
    
    similar_movies = recommendations.get("results", [])
    if not similar_movies:
        return f"Không tìm thấy đề xuất nào cho phim '{movie_title}'."
    
    formatted_results = f"Các phim tương tự '{movie_title}':\n\n"
    for i, movie in enumerate(similar_movies[:5], 1):
        title = movie.get("title", "Không có tiêu đề")
        overview = movie.get("overview", "Không có mô tả")
        release_date = movie.get("release_date", "Không có ngày phát hành")
        vote_average = movie.get("vote_average", 0)
        
        formatted_results += f"{i}. {title}\n"
        formatted_results += f"   Ngày phát hành: {release_date}\n"
        formatted_results += f"   Đánh giá: {vote_average}/10\n"
        formatted_results += f"   Tóm tắt: {overview[:200]}...\n\n"
    
    return formatted_results

# Khởi tạo agent và tools
def create_agent():
    llm = ChatOpenAI(temperature=0.2, model_name="gpt-4o-mini", base_url= OPENAI_BASE_URL, api_key= OPENAI_API_KEY)
    
    tools = [
        Tool(
            name="PopularMovies",
            func=get_popular_movies,
            description="Lấy danh sách các phim phổ biến nhất hiện tại"
        ),
        Tool(
            name="SearchMovies",
            func=search_movies,
            description="Tìm kiếm phim theo từ khóa. Nhập tên phim bạn muốn tìm."
        ),
        Tool(
            name="MovieRecommendations",
            func=get_movie_recommendations,
            description="Lấy đề xuất các phim tương tự dựa trên tên phim. Nhập tên phim bạn muốn lấy đề xuất."
        )
    ]
    
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent

# Tạo các panel ở sidebar
with st.sidebar:
    st.header("Cấu hình")
    
    # Xử lý PDF từ đường dẫn
    st.subheader("Xử lý PDF từ đường dẫn")
    pdf_path = st.text_input("Nhập đường dẫn đến file PDF hoặc thư mục chứa PDF")
    if pdf_path and st.button("Xử lý PDF"):
        with st.spinner("Đang xử lý file PDF..."):
            vectorstore, message = process_pdf_from_path(pdf_path)
            if vectorstore:
                st.session_state.vectorstore = vectorstore
                # Gộp với vectorstore hiện có nếu có
                if st.session_state.combined_vectorstore:
                    st.session_state.combined_vectorstore.merge_from(vectorstore)
                else:
                    st.session_state.combined_vectorstore = vectorstore
                st.success(message)
            else:
                st.error(message)
    
    # Xử lý CSV từ đường dẫn
    st.subheader("Xử lý CSV từ đường dẫn")
    csv_path = st.text_input("Nhập đường dẫn đến file CSV hoặc thư mục chứa CSV")
    if csv_path and st.button("Xử lý CSV"):
        with st.spinner("Đang xử lý file CSV..."):
            vectorstore, message = process_csv_from_path(csv_path)
            if vectorstore:
                # Gộp với vectorstore hiện có nếu có
                if st.session_state.combined_vectorstore:
                    st.session_state.combined_vectorstore.merge_from(vectorstore)
                else:
                    st.session_state.combined_vectorstore = vectorstore
                st.success(message)
            else:
                st.error(message)
    
    # Thông tin về tình trạng dữ liệu
    st.subheader("Trạng thái dữ liệu")
    if st.session_state.combined_vectorstore:
        st.success("✅ Đã tải dữ liệu từ các nguồn")
    else:
        st.warning("⚠️ Chưa tải dữ liệu từ bất kỳ nguồn nào")
    
    # Xóa dữ liệu
    if st.button("Xóa tất cả dữ liệu đã tải"):
        st.session_state.vectorstore = None
        st.session_state.combined_vectorstore = None
        st.success("Đã xóa tất cả dữ liệu")

# Main chat interface
st.header("Chat")

# Hàm phân tích câu hỏi để xác định nguồn dữ liệu
def analyze_query(query):
    # Các từ khóa liên quan đến phim
    movie_keywords = ["phim", "diễn viên", "đạo diễn", "chiếu rạp", "thể loại phim", 
                       "phổ biến", "đánh giá", "review", "trailer", "tìm phim", 
                       "gợi ý", "đề xuất", "tương tự", "tmdb", "imdb", "netflix",
                       "blockbuster", "oscar", "điện ảnh", "upcoming"]
    
    # Kiểm tra nếu có từ khóa nào trong câu hỏi
    for keyword in movie_keywords:
        if keyword.lower() in query.lower():
            return "movie"
    
    # Mặc định là tìm kiếm trong cơ sở kiến thức
    return "knowledge_base"

# Hiển thị lịch sử chat
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])

# Input chat
user_query = st.chat_input("Nhập câu hỏi của bạn...")

if user_query:
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.write(user_query)
    
    # Thêm vào lịch sử
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Xử lý câu hỏi
    with st.chat_message("assistant"):
        # Phân tích câu hỏi để quyết định xử lý bằng nguồn nào
        query_type = analyze_query(user_query)
        
        if query_type == "movie" and TMDB_API_KEY:
            # Sử dụng TMDB API cho câu hỏi liên quan đến phim
            with st.spinner("Đang tìm kiếm thông tin về phim..."):
                try:
                    agent = create_agent()
                    response = agent.invoke(user_query)
                    st.write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Lỗi khi xử lý yêu cầu về phim: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
        
        elif st.session_state.combined_vectorstore is not None:
            # Sử dụng vectorstore để trả lời từ dữ liệu đã nạp
            with st.spinner("Đang xử lý câu hỏi..."):
                # Khởi tạo LLM
                llm = ChatOpenAI(temperature=0.2, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, base_url= OPENAI_BASE_URL)
                
                # Tạo memory
                memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                
                # Custom prompt template để hướng dẫn AI trả lời dựa trên context
                qa_template = """
                Sử dụng thông tin sau đây để trả lời câu hỏi của người dùng.
                Nếu bạn không biết câu trả lời, hãy nói rằng bạn không biết. ĐỪNG bịa ra thông tin.
                
                Context: {context}
                
                Lịch sử trò chuyện: {chat_history}
                
                Câu hỏi: {question}
                
                Câu trả lời:
                """
                QA_PROMPT = PromptTemplate(
                    template=qa_template, 
                    input_variables=["context", "chat_history", "question"]
                )
                
                # Tạo conversation chain
                conversation_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=st.session_state.combined_vectorstore.as_retriever(),
                    memory=memory,
                    combine_docs_chain_kwargs={"prompt": QA_PROMPT}
                )
                
                # Lấy câu trả lời
                response = conversation_chain.invoke({"question": user_query})
                answer = response["answer"]
                
                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
        
        else:
            message = ""
            if query_type == "movie" and not TMDB_API_KEY:
                message = "TMDB API Key chưa được cấu hình nên không thể trả lời câu hỏi về phim. "
            
            message += "Vui lòng tải dữ liệu từ PDF hoặc CSV trước khi đặt câu hỏi về kiến thức cụ thể."
            
            st.warning(message)
            st.session_state.chat_history.append({"role": "assistant", "content": message})