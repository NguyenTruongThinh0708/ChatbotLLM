import os
import warnings
import py_vncorenlp
import logging
import shutil
from retry import retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_vncorenlp_instance = None

class VnTextProcessor:
    """
    Wrapper cho VnCoreNLP, dùng mô hình Singleton.
    Tự động tải model nếu chưa tồn tại, tối ưu cho Windows và Streamlit Cloud (Linux).
    """
    def __init__(self, save_dir: str = None, annotators: list = None):
        global _vncorenlp_instance

        # Dùng thư mục tạm tương thích với Windows và Linux
        if save_dir is None:
            save_dir = os.path.join(os.getenv("TMPDIR", os.getenv("TEMP", "/tmp")), "vncorenlp")
        
        annotators = annotators or ["wseg"]
        logger.info(f"Khởi tạo VnTextProcessor với save_dir: {save_dir}")

        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            return

        model_jar_path = os.path.join(save_dir, "VnCoreNLP-1.2.jar")
        if not os.path.exists(model_jar_path):
            logger.info(f"Model chưa tồn tại tại {save_dir}. Đang tải về...")
            try:
                # Xóa toàn bộ thư mục save_dir để tránh xung đột
                if os.path.exists(save_dir):
                    logger.info(f"Xóa thư mục xung đột: {save_dir}")
                    shutil.rmtree(save_dir, ignore_errors=True)  # Xóa toàn bộ save_dir
                os.makedirs(save_dir, exist_ok=True)  # Tạo lại save_dir
                self._download_model_with_retry(save_dir)
                logger.info("Tải model thành công.")
            except Exception as e:
                logger.error(f"Lỗi khi tải model: {str(e)}")
                raise RuntimeError(f"Không thể tải model VnCoreNLP vào {save_dir}. Kiểm tra kết nối mạng hoặc quyền write folder. Error: {str(e)}")

        try:
            self.processor = py_vncorenlp.VnCoreNLP(
                annotators=annotators,
                save_dir=save_dir
            )
            _vncorenlp_instance = self.processor
        except ValueError as e:
            if "VM is already running" in str(e):
                warnings.warn("JVM đã khởi tạo, dùng DummyProcessor thay thế.")
                self.processor = DummyProcessor()
            else:
                logger.error(f"Lỗi khởi tạo VnCoreNLP: {str(e)}")
                raise e

    @retry(tries=3, delay=2, backoff=2, logger=logger)
    def _download_model_with_retry(self, save_dir):
        """Tải model với retry nếu thất bại."""
        logger.info(f"Thử tải model VnCoreNLP vào {save_dir}")
        py_vncorenlp.download_model(save_dir=save_dir)

    def preprocess(self, text: str) -> dict:
        tokens = self.processor.word_segment(text)
        return {"word_segmented": tokens}

class DummyProcessor:
    def word_segment(self, text: str) -> list:
        return text.split()
