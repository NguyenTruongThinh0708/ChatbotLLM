import sys
import os
import torch
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embedder import EmbeddingGenerator
from vector_db import VectorDB
from retriever import Retriever
from generator import Generator

def init_components():
    st.write("[LOG] Khởi tạo các module...")

    st.write("[LOG] -> Khởi tạo EmbeddingGenerator...")
    embedder = EmbeddingGenerator()
    st.write("[LOG] ✅ EmbeddingGenerator OK")

    st.write("[LOG] -> Khởi tạo VectorDB...")
    vector_db = VectorDB()
    st.write("[LOG] ✅ VectorDB OK")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    st.write(f"[LOG] -> Khởi tạo Retriever (device={device})...")
    retriever = Retriever(vector_db, device=device)
    st.write("[LOG] ✅ Retriever OK")

    st.write("[LOG] -> Khởi tạo Generator...")
    generator = Generator(embedder, retriever)
    st.write("[LOG] ✅ Generator OK")

    st.write("[LOG] 🎉 Tất cả module khởi tạo thành công.")
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
        ranked_results = retriever.rerank(query, documents)
        context = "\n".join([f"{i+1}. {content}" for i, (_, content) in enumerate(ranked_results)])
        response = generator.generate(query, context)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
