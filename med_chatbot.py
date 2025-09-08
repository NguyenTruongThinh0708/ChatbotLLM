import sys
import os
import torch
import streamlit as st
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from embedder import EmbeddingGenerator
from vector_db import VectorDB
from retriever import Retriever
from generator import Generator

logger = logging.getLogger(__name__)

@st.cache_resource
def init_components():
    logger.info("[LOG] Khởi tạo các module...")

    logger.info("[LOG] -> Khởi tạo EmbeddingGenerator...")
    embedder = EmbeddingGenerator()
    logger.info("[LOG] ✅ EmbeddingGenerator OK")

    logger.info("[LOG] -> Khởi tạo VectorDB...")
    vector_db = VectorDB()
    logger.info("[LOG] ✅ VectorDB OK")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[LOG] -> Khởi tạo Retriever (device={device})...")
    retriever = Retriever(vector_db, device=device)
    logger.info("[LOG] ✅ Retriever OK")

    logger.info("[LOG] -> Khởi tạo Generator...")
    generator = Generator(embedder, retriever)
    logger.info("[LOG] ✅ Generator OK")

    logger.info("[LOG] 🎉 Tất cả module khởi tạo thành công.")

    return embedder, vector_db, retriever, generator

embedder, vector_db, retriever, generator = init_components()

# UI
st.title("Medical RAG Chatbot")
if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if query := st.chat_input("Nhập câu hỏi: "):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    st.write("[LOG] Đang xử lý câu hỏi...")
    processed_query = embedder.preprocess_and_tokenize(query)
    query_embedding = embedder.embed_query(processed_query)
    retrieve_results = retriever.retrieve(query_embedding)
    if not retrieve_results:
        response = "❌ Không tìm thấy dữ liệu liên quan."
    else:
        documents = [r.payload["content"] for r in retrieve_results]
        context = "\n".join([f"{i+1}. {content}" for i, content in enumerate(documents)])
        response = generator.generate(query, context)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

