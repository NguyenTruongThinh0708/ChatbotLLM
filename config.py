import os
from dotenv import load_dotenv

# Load biến môi trường từ .env (local) hoặc Streamlit secrets (cloud)
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa config.py
PDF_PATH = os.path.join(BASE_DIR, "data", "Phần 11.pdf")
VNCORENLP_SAVE_DIR = os.getenv("VNCORENLP_SAVE_DIR", os.path.join(os.getenv("TMPDIR", os.getenv("TEMP", "/tmp")), "vncorenlp"))
OUTPUT_LOG = os.path.join(BASE_DIR, "logs", "logs.txt")
OUTPUT_JSON_CLEAN = os.path.join(BASE_DIR, "data", "pages_clean_mode.json")

# Models
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
RERANKER_MODEL_NAME = "namdp-ptit/ViRanker"
LLM_MODEL_NAME = "llama-3.1-8b-instant"

# Qdrant
QDRANT_URL = "https://72249cbf-3fe1-4881-b625-d4f1cb122aea.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = "test_llm"
VECTOR_SIZE = 1024  # Kích thước dense vector từ BGE-M3

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Kiểm tra API keys
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY không được cấu hình. Đặt trong .env (local) hoặc Streamlit secrets (cloud).")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY không được cấu hình. Đặt trong .env (local) hoặc Streamlit secrets (cloud).")
