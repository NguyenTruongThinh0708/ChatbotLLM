import os
import warnings
import py_vncorenlp
import logging  # Thêm logging để debug dễ hơn

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Biến toàn cục để lưu instance duy nhất
_vncorenlp_instance = None

class VnTextProcessor:
    """
    Wrapper cho VnCoreNLP, dùng mô hình Singleton.
    Mục đích: tránh khởi tạo JVM nhiều lần gây lỗi "VM is already running".
    Tự động tải model nếu chưa tồn tại.
    """
    def __init__(self, 
                 save_dir: str = "./models/vncorenlp", 
                 annotators: list = None):
        global _vncorenlp_instance

        annotators = annotators or ["wseg"]
        os.makedirs(save_dir, exist_ok=True)  # Tạo folder nếu chưa có

        # Nếu đã có instance, dùng lại
        if _vncorenlp_instance is not None:
            self.processor = _vncorenlp_instance
            return

        # Kiểm tra xem model đã tồn tại chưa (kiểm tra file .jar chính)
        model_jar_path = os.path.join(save_dir, "VnCoreNLP-1.2.jar")  # Tên file .jar mặc định của py_vncorenlp
        if not os.path.exists(model_jar_path):
            logger.info(f"Model chưa tồn tại tại {save_dir}. Đang tải về...")
            try:
                py_vncorenlp.download_model(save_dir=save_dir)
                logger.info("Tải model thành công.")
            except Exception as e:
                logger.error(f"Lỗi khi tải model: {str(e)}")
                raise RuntimeError("Không thể tải model VnCoreNLP. Kiểm tra kết nối mạng hoặc quyền write folder.")

        try:
            # Khởi tạo VnCoreNLP
            self.processor = py_vncorenlp.VnCoreNLP(
                annotators=annotators,
                save_dir=save_dir
            )

            # Lưu instance để tái sử dụng
            _vncorenlp_instance = self.processor

        except ValueError as e:
            # Bắt lỗi JVM đã chạy
            if "VM is already running" in str(e):
                warnings.warn("JVM đã khởi tạo, dùng DummyProcessor thay thế.")
                self.processor = DummyProcessor()
            else:
                raise e

    def preprocess(self, text: str) -> dict:
        """
        Tiền xử lý văn bản: tách từ
        """
        tokens = self.processor.word_segment(text)
        return {"word_segmented": tokens}


class DummyProcessor:
    """
    Processor giả phòng trường hợp JVM đã chạy trước đó.
    """
    def word_segment(self, text: str) -> list:
        return text.split()
