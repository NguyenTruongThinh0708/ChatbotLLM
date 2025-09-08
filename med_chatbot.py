import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from embedder import EmbeddingGenerator
from vector_db import VectorDB
from retriever import Retriever
from generator import Generator

# Hàm khởi tạo các đối tượng (cache để tránh lặp lại)
@st.cache_resource
def init_components():
    print("[LOG] Khởi tạo các module...")
    embedder = EmbeddingGenerator()
    print("[LOG] EmbeddingGenerator OK")

    vector_db = VectorDB()
    print("[LOG] VectorDB OK")

    # Cho phép chọn device động (nếu có GPU)
    device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    retriever = Retriever(vector_db, device=device)
    print(f"[LOG] Retriever OK (device={device})")

    generator = Generator(embedder, retriever)
    print("[LOG] Generator OK")

    print("[LOG] Khởi tạo hoàn tất.")
    return embedder, vector_db, retriever, generator


# Gọi hàm khởi tạo
embedder, vector_db, retriever, generator = init_components()

# Giao diện chat
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

    print("[LOG] Đang xử lý câu hỏi người dùng...")
    processed_query = embedder.preprocess_and_tokenize(query)

    print("[LOG] Đang tạo embedding cho câu hỏi...")
    query_embedding = embedder.embed_query(processed_query)

    print("[LOG] Đang truy xuất và rerank kết quả...")
    retrieve_results = retriever.retrieve(query_embedding)
    documents = [result.payload["content"] for result in retrieve_results]
    ranked_results = retriever.rerank(query, documents)

    context = "\n".join([f"{i+1}. {content}" for i, (_, content) in enumerate(ranked_results)])
    print("\nKết quả sau khi rerank (top 1):")
    print(context)
    print("\n")

    print("[LOG] Đang sinh câu trả lời...")
    response = generator.generate(query, context)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

    print("[LOG] Hoàn tất phản hồi.")
