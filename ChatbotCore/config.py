from langchain_ollama import OllamaLLM
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
# Ép Ollama chạy GPU 0
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# (tùy chọn) tăng tốc token gen
os.environ["OLLAMA_FLASH_ATTENTION"] = "1"
load_dotenv()

# API endpoints
API_BASE_MOVIES = "http://localhost:8080/api/movies/"

# LLM configuration
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))

# Global chat history as list
chat_history = []

# Memory for integration with chat_graphapi.py
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Session configuration
SESSION_EXPIRY_HOURS = 24  # Sessions expire after 24 hours

