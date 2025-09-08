import torch
from FlagEmbedding import FlagReranker
from vector_db import VectorDB  # Liên kết với vector_db.py
from embedder import EmbeddingGenerator  # Liên kết với embedder.py
from config import RERANKER_MODEL_NAME
from huggingface_hub import login
import os
import logging

logger = logging.getLogger(__name__)
HF_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")  # token lấy từ .env hoặc config

class Retriever:
    def __init__(self, vector_db: VectorDB, device=None):
        """
        Initialize Retriever with vector database and ViRanker.
        
        Args:
            vector_db: VectorDB instance for Qdrant access.
            device: Device to run ViRanker ('cpu' or 'cuda').
        """
        self.vector_db = vector_db
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = self._load_viranker()

    def _load_viranker(self):
        try:
            if HF_TOKEN:
                login(token=HF_TOKEN)
                logger.info("[Retriever] Đã login vào Hugging Face Hub")
            else:
                logger.warning("[Retriever] Không tìm thấy HUGGINGFACE_TOKEN, sẽ dùng anonymous (dễ bị 429)")
            
            logger.info(f"[Retriever] Đang load ViRanker trên device={self.device} ...")
            reranker = FlagReranker(
                RERANKER_MODEL_NAME,
                device=self.device
            )
            logger.info(f"[Retriever] ViRanker load thành công (device={self.device})")
            return reranker
        except Exception as e:
            logger.error(f"[Retriever] ViRanker load thất bại: {e}", exc_info=True)
            raise

    def retrieve(self, query_embedding, limit=5):
        """
        Retrieve relevant documents from Qdrant vector database.
        
        Args:
            query_embedding: Embedding vector of the query.
            limit: Maximum number of results.
            
        Returns:
            List of search results.
        """
        try:
            search_result = self.vector_db.search(query_vector=query_embedding, limit=limit)
            print("\nInitial search results (top 5):")
            for i, result in enumerate(search_result):
                print(f"ID: {result.id}, Score: {result.score:.4f}, Content: {result.payload['content'][:100]}...")
            return search_result
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

    def rerank(self, query, documents, top_k=1, normalize=True):
        """
        Rerank documents based on relevance to the query using ViRanker.
        
        Args:
            query: Query string.
            documents: List of document strings to rerank.
            top_k: Number of top documents to return.
            normalize: Whether to normalize scores.
            
        Returns:
            List of tuples (score, document) sorted by score.
        """
        try:
            pairs = [[query, doc] for doc in documents]
            scores = self.reranker.compute_score(pairs, normalize=normalize, batch_size=5)
            ranked_pairs = sorted(zip(scores, documents), reverse=True)
            return ranked_pairs[:top_k]
        except Exception as e:
            print(f"Error during reranking: {e}")

            return list(zip([0.0] * len(documents), documents))[:top_k]





