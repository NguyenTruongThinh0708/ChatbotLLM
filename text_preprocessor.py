import os
import logging
import warnings
import py_vncorenlp
from retry import retry
from config import VNCORENLP_SAVE_DIR

logger = logging.getLogger(__name__)

_vncorenlp_instance = None

class VnTextProcessor:
    """
    Wrapper cho VnCoreNLP, dùng Singleton.
    Luôn lấy model từ thư mục repo: models/vncorenlp
    """
    def __init__(self, annotators: list = None):
        global _vncorenlp_instance

        jar_file_name = "VnCoreNLP-1.2.jar"
        jar_path = os.path.join(VNCORENLP_SAVE_DIR, jar_file_name)

        # Log đường dẫn model
        logger.info(f"[VnTextProcessor] Expected model path: {jar_path}")

        annotators = annotators or ["wseg"]

        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            logger.info("[VnTextProcessor] Reusing existing VnCoreNLP instance.")
            return

        # Kiểm tra model có tồn tại không
        if not (os.path.exists(jar_path) and os.path.exists(os.path.join(VNCORENLP_SAVE_DIR, "models"))):
            raise RuntimeError(
                f"Không tìm thấy VnCoreNLP model tại {VNCORENLP_SAVE_DIR}. "
                f"Đảm bảo repo có thư mục 'models/vncorenlp' chứa {jar_file_name} và folder 'models'."
            )

        try:
            self.processor = py_vncorenlp.VnCoreNLP(
                save_dir=VNCORENLP_SAVE_DIR,
                annotators=",".join(annotators),
                max_heap_size='-Xmx2g'
            )
            _vncorenlp_instance = self.processor
            logger.info("[VnTextProcessor] VnCoreNLP khởi tạo thành công.")
        except ValueError as e:
            if "VM is already running" in str(e):
                warnings.warn("JVM đã khởi tạo, dùng DummyProcessor thay thế.")
                self.processor = DummyProcessor()
            else:
                logger.error(f"Lỗi khởi tạo VnCoreNLP: {str(e)}")
                raise

    def preprocess(self, text: str) -> dict:
        tokens = self.processor.word_segment(text)
        return {"word_segmented": tokens}


class DummyProcessor:
    def word_segment(self, text: str) -> list:
        return text.split()
