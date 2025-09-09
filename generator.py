from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
from config import GROQ_API_KEY
from embedder import EmbeddingGenerator
from retriever import Retriever

class Generator:
    def __init__(self, embedder: EmbeddingGenerator, retriever: Retriever):
        """
        Initialize Generator with embedder, retriever, and LLM.
        
        Args:
            embedder: EmbeddingGenerator instance.
            retriever: Retriever instance.
        """
        self.embedder = embedder
        self.retriever = retriever
        self.llm = self._load_llm()

    def _load_llm(self):
        """
        Load Groq LLM model.
        
        Returns:
            Initialized ChatGroq model.
        """
        try:
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=400,
                api_key=GROQ_API_KEY,
                stop=["<END_OF_ANSWER>"]
            )
            return llm
        except Exception as e:
            print(f"Error loading LLM: {e}")
            raise

    def generate(self, query, context):
        """
        Process query, retrieve documents, rerank, and generate response.
        
        Args:
            query: User query string.
            
        Returns:
            Tuple of (response, embedding_time, generate_time, total_time).
        """
        try:
            # Generate response with LLM
            # Prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                    "Bạn là một bác sĩ AI chuyên phân tích triệu chứng để đưa ra lời khuyên sức khỏe.\n"
                    "Hãy trả lời một cách ngắn gọn, đầy đủ và chuyên nghiệp, theo yêu cầu sau:\n"
                    "1. Mở đầu: Tóm tắt lại triệu chứng người dùng mô tả.\n"
                    "2. Liệt kê tối đa 3 bệnh phổ biến có thể liên quan, mỗi bệnh kèm lý do ngắn gọn.\n"
                    "3. Kết thúc bằng lời khuyên: đây chỉ là gợi ý tham khảo, không thay thế chẩn đoán y khoa, "
                    "và nên đến gặp bác sĩ để kiểm tra chính xác.\n"
                    "4. Nếu không đủ thông tin để xác định bệnh, hãy trả lời đúng câu sau: "
                    "'Dựa trên thông tin bạn cung cấp, chưa đủ để xác định bệnh cụ thể. "
                    "Bạn nên đến gặp bác sĩ để được khám và chẩn đoán chính xác.'\n"
                    "5. Giữ giọng điệu lịch sự, an ủi và chuyên nghiệp.\n"
                    "6. Trả lời không quá 250 từ và luôn kết thúc bằng <END_OF_ANSWER>."
                ),
                ("user",
                    f"Dựa trên thông tin sau:\n{context}\n"
                    f"Hãy trả lời câu hỏi: {query}\n\n"
                    "Trả lời theo đúng hướng dẫn trên, kết thúc bằng <END_OF_ANSWER>."
                )
            ])
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({})
            return response
        except Exception as e:

            return f"Error: {e}", 0, 0, 0



