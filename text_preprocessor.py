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
    Wrapper cho VnCoreNLP, dùng mô hình Singleton.
    Ưu tiên sử dụng model từ repo (models/vncorenlp), chỉ tải từ server nếu cần.
    """
    def __init__(self, save_dir: str = None, annotators: list = None):
        global _vncorenlp_instance

        # Đường dẫn gốc của repo trên Streamlit Cloud
        repo_base_dir = os.path.dirname(os.path.abspath(__file__))
        repo_vncorenlp_dir = os.path.join(repo_base_dir, "models", "vncorenlp")

        # Dùng thư mục từ repo nếu có file .jar và thư mục models, nếu không thì dùng save_dir hoặc thư mục tạm
        if save_dir is None:
            if (os.path.exists(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) and 
                os.path.exists(os.path.join(repo_vncorenlp_dir, "models")) and 
                os.path.getsize(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) > 0):
                save_dir = repo_vncorenlp_dir
                logger.info(f"Sử dụng model VnCoreNLP từ repo: {save_dir}")
            else:
                save_dir = os.path.join(os.getenv("TMPDIR", os.getenv("TEMP", "/tmp")), "vncorenlp")
                logger.info(f"Sử dụng thư mục tạm: {save_dir}")

        annotators = annotators or ["wseg"]
        logger.info(f"Khởi tạo VnTextProcessor với save_dir: {save_dir}")

        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            return

        model_jar_path = os.path.join(save_dir, "VnCoreNLP-1.2.jar")
        if not os.path.exists(model_jar_path):
            logger.info(f"Model chưa tồn tại tại {save_dir}. Đang kiểm tra và tải về...")
            try:
                # Kiểm tra kết nối mạng đến server VnCoreNLP
                response = requests.get("https://vncorenlp.vietnlp.ai", timeout=5)
                if response.status_code != 200:
                    logger.warning("Không thể kết nối đến server VnCoreNLP. Sử dụng repo nếu có.")
                    if (os.path.exists(repo_vncorenlp_dir) and 
                        os.path.exists(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) and 
                        os.path.getsize(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) > 0):
                        save_dir = repo_vncorenlp_dir
                        logger.info(f"Sử dụng fallback từ repo: {save_dir}")
                    else:
                        raise RuntimeError("Không thể tải model và không có fallback từ repo.")
                else:
                    # Xóa toàn bộ thư mục save_dir để tránh xung đột (nếu dùng thư mục tạm)
                    if save_dir.startswith(os.path.join(os.getenv("TMPDIR", os.getenv("TEMP", "/tmp")), "vncorenlp")):
                        if os.path.exists(save_dir):
                            logger.info(f"Xóa thư mục tạm xung đột: {save_dir}")
                            shutil.rmtree(save_dir, ignore_errors=True)
                        os.makedirs(save_dir, exist_ok=True)

                    # Tải model với retry
                    self._download_model_with_retry(save_dir)
                    logger.info("Tải model thành công.")
            except requests.RequestException as e:
                logger.error(f"Lỗi kết nối mạng: {str(e)}")
                if (os.path.exists(repo_vncorenlp_dir) and 
                    os.path.exists(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) and 
                    os.path.getsize(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) > 0):
                    save_dir = repo_vncorenlp_dir
                    logger.info(f"Sử dụng fallback từ repo: {save_dir}")
                else:
                    raise RuntimeError(f"Không thể tải model VnCoreNLP vào {save_dir}. Kiểm tra kết nối mạng. Error: {str(e)}")
            except Exception as e:
                logger.error(f"Lỗi khi tải model: {str(e)}")
                if (os.path.exists(repo_vncorenlp_dir) and 
                    os.path.exists(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) and 
                    os.path.getsize(os.path.join(repo_vncorenlp_dir, "VnCoreNLP-1.2.jar")) > 0):
                    save_dir = repo_vncorenlp_dir
                    logger.info(f"Sử dụng fallback từ repo: {save_dir}")
                else:
                    raise RuntimeError(f"Không thể tải model VnCoreNLP vào {save_dir}. Kiểm tra quyền write folder hoặc kết nối mạng. Error: {str(e)}")

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
