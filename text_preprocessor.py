import os
import warnings
import py_vncorenlp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_vncorenlp_instance = None


class VnTextProcessor:
    """
    Wrapper cho VnCoreNLP, dùng Singleton.
    Ưu tiên sử dụng model trong repo (models/vncorenlp).
    Nếu không tìm thấy thì fallback DummyProcessor.
    """
    def __init__(self, save_dir: str = None, annotators: list = None):
        global _vncorenlp_instance

        repo_base_dir = os.path.dirname(os.path.abspath(__file__))
        repo_vncorenlp_dir = os.path.join(repo_base_dir, "models", "vncorenlp")
        jar_file_name = "VnCoreNLP-1.2.jar"
        jar_path = os.path.join(repo_vncorenlp_dir, jar_file_name)

        # Nếu chưa có save_dir → thử lấy từ repo
        if save_dir is None:
            if os.path.exists(jar_path) and os.path.exists(os.path.join(repo_vncorenlp_dir, "models")):
                save_dir = repo_vncorenlp_dir
                logger.info(f"Sử dụng model VnCoreNLP từ repo: {save_dir}")
            else:
                logger.warning("Không tìm thấy model VnCoreNLP trong repo, dùng DummyProcessor.")
                self.processor = DummyProcessor()
                return

        annotators = annotators or ["wseg"]

        # Nếu đã có instance rồi thì tái sử dụng
        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            return

        # Khởi tạo VnCoreNLP
        try:
            self.processor = py_vncorenlp.VnCoreNLP(
                jar_path=os.path.join(save_dir, jar_file_name),
                annotators=",".join(annotators),
                max_heap_size='-Xmx2g'
            )
            _vncorenlp_instance = self.processor
        except ValueError as e:
            if "VM is already running" in str(e):
                warnings.warn("JVM đã khởi tạo, dùng DummyProcessor thay thế.")
                self.processor = DummyProcessor()
            else:
                logger.error(f"Lỗi khởi tạo VnCoreNLP: {str(e)}")
                self.processor = DummyProcessor()

    def preprocess(self, text: str) -> dict:
        tokens = self.processor.word_segment(text)
        return {"word_segmented": tokens}


class DummyProcessor:
    def word_segment(self, text: str) -> list:
        return text.split()
