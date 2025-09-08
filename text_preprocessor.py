import os
import warnings
import py_vncorenlp
import logging
import shutil
from retry import retry
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_vncorenlp_instance = None

class VnTextProcessor:
    """
    Wrapper cho VnCoreNLP, dùng Singleton.
    Luôn nhận vào save_dir, từ đó tự xác định jar_path.
    """
    def __init__(self, save_dir: str, annotators: list = None):
        global _vncorenlp_instance

        jar_file_name = "VnCoreNLP-1.2.jar"
        jar_path = os.path.join(save_dir, jar_file_name)
        annotators = annotators or ["wseg"]

        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            return

        # Nếu jar chưa tồn tại → thử tải
        if not os.path.exists(jar_path):
            logger.info(f"Model chưa tồn tại tại {save_dir}. Đang kiểm tra và tải về...")
            self._ensure_model_exists(save_dir, jar_file_name)

        # Khởi tạo VnCoreNLP
        try:
            self.processor = py_vncorenlp.VnCoreNLP(
                jar_path=jar_path,
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
                raise e

    def _ensure_model_exists(self, save_dir, jar_file_name):
        """Đảm bảo model có sẵn hoặc tải về."""
        try:
            response = requests.get("https://vncorenlp.vietnlp.ai", timeout=5)
            if response.status_code == 200:
                if os.path.exists(save_dir):
                    shutil.rmtree(save_dir, ignore_errors=True)
                os.makedirs(save_dir, exist_ok=True)
                self._download_model_with_retry(save_dir)
                logger.info("Tải model thành công.")
            else:
                raise RuntimeError("Không thể kết nối đến server VnCoreNLP.")
        except Exception as e:
            logger.error(f"Lỗi khi tải model: {str(e)}")
            raise RuntimeError("Không thể tải model và không có fallback hợp lệ.")

    @retry(tries=3, delay=2, backoff=2, logger=logger)
    def _download_model_with_retry(self, save_dir):
        logger.info(f"Thử tải model VnCoreNLP vào {save_dir}")
        py_vncorenlp.download_model(save_dir=save_dir)

    def preprocess(self, text: str) -> dict:
        tokens = self.processor.word_segment(text)
        return {"word_segmented": tokens}


class DummyProcessor:
    def word_segment(self, text: str) -> list:
        return text.split()
