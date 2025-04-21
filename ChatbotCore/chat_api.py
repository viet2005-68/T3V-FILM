from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from chatbot import (
    process_pdf_from_path,
    process_csv_from_path,
    save_vectorstore,
    load_vectorstore,
    process_question
)

app = FastAPI()

# --- Cấu hình CORS ---
origins = [
    "http://localhost:5173",  # Địa chỉ React app của bạn (cổng 3000 thường là mặc định)
    "http://127.0.0.1:5173",
    # Bạn có thể thêm các origin khác nếu cần, hoặc dùng "*" để cho phép tất cả
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP
    allow_headers=["*"],  # Cho phép tất cả các headers
)

# --- Cấu hình đường dẫn ---
VECTORSTORE_DIR = "data/vectorstore"
PDF_DEFAULT = "data/T3V Chatbot Training Data.pdf"

# Tạo thư mục nếu chưa có
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(VECTORSTORE_DIR):
    os.makedirs(VECTORSTORE_DIR)

# --- Khởi tạo vectorstore ---
vectorstore = load_vectorstore(VECTORSTORE_DIR)
if vectorstore:
    print("✅ Đã tải vectorstore từ:", VECTORSTORE_DIR)
else:
    print("⚠️ Vectorstore không tồn tại hoặc lỗi, tạo mới từ file PDF mặc định...")
    if os.path.exists(PDF_DEFAULT):
        vs, msg = process_pdf_from_path(PDF_DEFAULT)
        if vs:
            vectorstore = vs
            print(save_vectorstore(vectorstore, VECTORSTORE_DIR))
        else:
            print("❌ Lỗi khi xử lý file PDF mặc định:", msg)
    else:
        print("🚫 Không tìm thấy file PDF mặc định:", PDF_DEFAULT)

# --- Schema cho request ---
class ChatMessage(BaseModel):
    role: str  # "user" hoặc "bot"
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []

class LoadDataRequest(BaseModel):
    data_type: str  # "pdf" hoặc "csv"
    path: str

# --- Endpoint trả lời câu hỏi ---
@app.post("/chat")
def chat(request: ChatRequest):
    global vectorstore
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    try:
        # Chuyển history sang mảng dict để hàm process_question sử dụng
        history_data = [msg.dict() for msg in request.history]
        response = process_question(request.question, history_data, vectorstore)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý câu hỏi: {str(e)}")

# --- Endpoint nạp dữ liệu từ PDF/CSV ---
@app.post("/load-data")
def load_data(request: LoadDataRequest):
    global vectorstore
    data_type = request.data_type.lower()
    if data_type == "pdf":
        vs, msg = process_pdf_from_path(request.path)
    elif data_type == "csv":
        vs, msg = process_csv_from_path(request.path)
    else:
        raise HTTPException(status_code=400, detail="data_type phải là 'pdf' hoặc 'csv'")
    
    if vs is None:
        raise HTTPException(status_code=500, detail=msg)
    
    # Nếu đã có vectorstore, merge; nếu không, gán mới
    if vectorstore:
        try:
            vectorstore.merge_from(vs)
        except Exception:
            vectorstore = vs
    else:
        vectorstore = vs

    save_msg = save_vectorstore(vectorstore, VECTORSTORE_DIR)
    return {"message": msg, "save_status": save_msg}
