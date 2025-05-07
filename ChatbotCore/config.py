from langchain_ollama import OllamaLLM
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
# Ép Ollama chạy GPU 0
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# (tùy chọn) tăng tốc token gen
os.environ["OLLAMA_FLASH_ATTENTION"] = "1"
load_dotenv()

# API endpoints
API_BASE_MOVIES = "http://localhost:8800/api/movies/"

# LLM configuration
#llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
# llm = OllamaLLM(
#         model="gemma:2b",
#         temperature=0.7,
#         top_p=0.9,
#         num_predict=512,
#     )
# Global chat history as list
llm = ChatGroq(model="gemma2-9b-it", temperature=0.7, api_key=os.getenv("GROQ_API_KEY"))
chat_history = []

# Memory for integration with chat_graphapi.py
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Session configuration
SESSION_EXPIRY_HOURS = 24  # Sessions expire after 24 hours

