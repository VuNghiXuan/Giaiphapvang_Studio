import os
from groq import Groq
from google import genai
import requests
from core.knowledge_base import KnowledgeBase
from faster_whisper import WhisperModel

class AIManager:
    def __init__(self):
        self.provider = os.getenv("DEFAULT_PROVIDER", "Groq")
        self.kb = KnowledgeBase()

    def rewrite_script(self, raw_text):
        context = self.kb.get_context()
        
        # PROMPT TỰ ĐỘNG HÓA - Dùng ngữ cảnh để giải mã "tiếng ngáo"
        prompt = f"""
        Bạn là chuyên gia biên tập của phần mềm Giải Pháp Vàng (Giaiphapvang).
        
        NGỮ CẢNH HỆ THỐNG (Dùng để đối chiếu):
        {context}

        NHIỆM VỤ:
        Dưới đây là lời thoại bị lỗi bóc băng (Whisper lỗi). Hãy dựa vào 'Ngữ cảnh hệ thống' 
        để đoán ý người dùng và viết lại kịch bản lồng tiếng chuyên nghiệp.

        QUY TẮC DỊCH THÔNG MINH:
        1. Tự động khớp các từ phát âm sai vào Menu/Nút bấm đúng (Ví dụ: 'tì nhân/tí nhắn' -> 'Chi nhánh', 'tạm/tào' -> 'Tạo mới/Thao tác').
        2. Nếu có chuỗi ký tự lạ (phê đe, i doctor...), hãy thay bằng ví dụ thực tế phù hợp với trường dữ liệu (ví dụ: tên chi nhánh hoặc email).
        3. Văn phong: Mượt mà, lịch sự, bắt đầu bằng 'Chào các bạn...'.

        VĂN BẢN GỐC ĐANG LỖI: "{raw_text}"

        KỊCH BẢN CHUẨN ĐỂ LỒNG TIẾNG:
        """

        try:
            # --- KIỂM TRA KEY CHO GROQ ---
            if self.provider == "Groq":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    return "⚠️ LỖI: Vũ ơi, mày chưa nhập GROQ_API_KEY vào file .env kìa!"
                
                client = Groq(api_key=api_key)
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là biên tập viên kịch bản chuyên nghiệp, giỏi suy luận từ ngữ cảnh phần mềm."},
                        {"role": "user", "content": prompt}
                    ],
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.1
                )
                return completion.choices[0].message.content.strip()

            # --- KIỂM TRA KEY CHO GEMINI ---
            elif self.provider == "Gemini":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    return "⚠️ LỖI: Thiếu GOOGLE_API_KEY trong file .env rồi Vũ ơi!"
                
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=prompt
                )
                return response.text.strip()

            elif self.provider == "Ollama":
                url = f"{os.getenv('OLLAMA_BASE_URL')}/api/generate"
                payload = {"model": os.getenv("OLLAMA_MODEL"), "prompt": prompt, "stream": False}
                response = requests.post(url, json=payload)
                return response.json()['response'].strip()
                
        except Exception as e:
            # In lỗi chi tiết ra Terminal để mày dễ debug
            print(f"⚠️ Lỗi AI Manager: {e}")
            return f"❌ Lỗi hệ thống: {str(e)}"

    def transcribe_audio(self, audio_path):
        if not os.path.exists(audio_path): return ""
        try:
            # Chuyển sang model 'small' cho chuẩn tiếng Việt
            model = WhisperModel("small", device="cpu", compute_type="int8") 
            segments, _ = model.transcribe(audio_path, beam_size=5, language="vi")
            return " ".join([s.text for s in segments]).strip()
        except Exception as e:
            print(f"Lỗi Whisper: {e}")
            return ""