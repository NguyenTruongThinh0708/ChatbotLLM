import torch
import re
from FlagEmbedding import BGEM3FlagModel
from text_preprocessor import VnTextProcessor, DummyProcessor
from config import EMBEDDING_MODEL_NAME, VNCORENLP_SAVE_DIR
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name=EMBEDDING_MODEL_NAME, device=None, max_length=512):
        """
        Khởi tạo EmbeddingGenerator với mô hình BGE-M3.
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model_name = model_name
        self.max_length = max_length

        # Khởi tạo VnTextProcessor
        try:
            self.vncorenlp = VnTextProcessor(
                save_dir=VNCORENLP_SAVE_DIR,
                annotators=["wseg"]
            )
        except Exception as e:
            logger.error(f"Không thể khởi tạo VnTextProcessor: {str(e)}")
            raise RuntimeError(f"Khởi tạo VnTextProcessor thất bại: {str(e)}")

        if isinstance(self.vncorenlp.processor, DummyProcessor):
            logger.warning("Dùng DummyProcessor, tách từ sẽ không chính xác.")

        # Khởi tạo mô hình embedding
        self.model = BGEM3FlagModel(model_name, device=device)

    def embed_query(self, processed_text):
        try:
            if not processed_text or not isinstance(processed_text, str):
                raise ValueError("Processed text phải là một chuỗi không rỗng.")
            embedding = self.model.encode(processed_text)
            if isinstance(embedding, dict) and 'dense_vecs' in embedding:
                return embedding['dense_vecs'].tolist()
            else:
                raise ValueError("Embedding không chứa 'dense_vecs'.")
        except Exception as e:
            logger.error(f"Lỗi khi tính embedding cho query: {str(e)}")
            return [0.0] * self.get_dense_size()

    def embed_documents(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts)
        if isinstance(embeddings, dict) and 'dense_vecs' in embeddings:
            return [v.tolist() for v in embeddings['dense_vecs']]
        return [v.tolist() for v in embeddings]

    def preprocess_and_tokenize(self, text):
        try:
            if self.vncorenlp is None or isinstance(self.vncorenlp.processor, DummyProcessor):
                logger.warning("VnCoreNLP không khả dụng, trả về text gốc.")
                return text.strip().lower()
            # Chuẩn hóa
            text = text.strip().lower()
            # Tách từ
            processed = self.vncorenlp.preprocess(text)
            tokens = processed["word_segmented"]
            tokens = [re.sub(r'\s+', ' ', word).strip() for word in tokens]
            return " ".join(tokens)
        except Exception as e:
            logger.error(f"Lỗi khi tiền xử lý và tokenize: {str(e)}")
            return text.strip().lower()

    def get_dense_size(self):
        sample_text = "This is a test sentence."
        sample_embedding = self.model.encode(sample_text)
        if isinstance(sample_embedding, dict) and 'dense_vecs' in sample_embedding:
            return len(sample_embedding['dense_vecs'][0])
        return len(sample_embedding[0])
