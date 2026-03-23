import os
import requests
import time
from groq import Groq
from google import genai
from core.knowledge_base import KnowledgeBase
from faster_whisper import WhisperModel
# from moviepy.editor import VideoFileClip
from dotenv import load_dotenv
# from moviepy import VideoFileClip, AudioFileClip
# from gtts import gTTS # pip install gTTS

import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip


# Load ngay khi module được import vào hệ thống
load_dotenv()

class AIManager:
    def __init__(self):
        # Đồng bộ hóa tên provider về chữ thường để tránh lỗi so sánh
        self.provider = os.getenv("DEFAULT_PROVIDER", "Groq").strip()
        print(f"[DEBUG-AI] Khởi tạo AIManager với Provider: {self.provider}")
        self.kb = KnowledgeBase()

    def rewrite_script(self, segments):
        if not segments: return []
        
        # Biến list thành chuỗi có đánh số để AI dễ xử lý
        raw_input = "\n".join([f"[{s['start']:.1f}s - {s['end']:.1f}s]: {s['text']}" for s in segments])
        
        prompt = f"""
        Bạn là biên tập viên của Giaiphapvang Studio.
        Dưới đây là lời thoại gốc kèm mốc thời gian. 
        NHIỆM VỤ: Viết lại lời thoại cho HAY hơn, chuyên nghiệp hơn nhưng phải KHỚP với khoảng thời gian đã cho.
        
        YÊU CẦU:
        1. Giữ nguyên định dạng [start - end]: lời thoại mới.
        2. Lời thoại mới phải có độ dài tương đương lời thoại cũ để không bị nói quá nhanh hoặc quá chậm.
        3. Tuyệt đối không thêm bớt các mốc thời gian.

        DỮ LIỆU:
        {raw_input}
        """

        try:
            # 1. XỬ LÝ CHO GROQ
            if self.provider.lower() == "groq":
                api_key = os.getenv("GROQ_API_KEY")
                model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                print(f"[DEBUG-AI] Đang gọi Groq API (Model: {model_name})...")
                
                if not api_key:
                    print("[ERROR-AI] Thiếu GROQ_API_KEY!")
                    return "⚠️ LỖI: Vũ ơi, mày chưa nhập GROQ_API_KEY vào file .env kìa!"
                
                client = Groq(api_key=api_key)
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là biên tập viên kịch bản chuyên nghiệp."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model_name,
                    temperature=0.1
                )
                res = completion.choices[0].message.content.strip()
                print(f"[DEBUG-AI] Groq trả về thành công ({len(res)} ký tự).")
                return res

            # 2. XỬ LÝ CHO GEMINI
            elif self.provider.lower() == "gemini":
                api_key = os.getenv("GOOGLE_API_KEY")
                model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                print(f"[DEBUG-AI] Đang gọi Gemini API (Model: {model_name})...")
                
                if not api_key:
                    print("[ERROR-AI] Thiếu GOOGLE_API_KEY!")
                    return "⚠️ LỖI: Thiếu GOOGLE_API_KEY trong file .env rồi Vũ ơi!"
                
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                res = response.text.strip()
                print(f"[DEBUG-AI] Gemini trả về thành công ({len(res)} ký tự).")
                return res

            # 3. XỬ LÝ CHO OLLAMA (Local AI)
            elif self.provider.lower() == "ollama":
                base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
                model_name = os.getenv("OLLAMA_MODEL", "vinallama")
                print(f"[DEBUG-AI] Đang gọi Ollama Local ({base_url} - Model: {model_name})...")
                
                url = f"{base_url}/api/generate"
                payload = {"model": model_name, "prompt": prompt, "stream": False}
                
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status() # Kiểm tra lỗi HTTP (404, 500...)
                
                res = response.json().get('response', '').strip()
                print(f"[DEBUG-AI] Ollama trả về thành công.")
                return res

            else:
                print(f"[ERROR-AI] Provider '{self.provider}' không nằm trong danh sách hỗ trợ!")
                return f"⚠️ LỖI: Hệ thống chưa hỗ trợ AI Provider: {self.provider}"

        except Exception as e:
            print(f"❌ [CRITICAL-AI-ERROR]: {type(e).__name__} - {str(e)}")
            return f"❌ Lỗi hệ thống: {str(e)}"
        

    def transcribe_video(self, video_path):
        """Ưu tiên lấy file wav có sẵn, nếu không có mới trích xuất từ mp4"""
        # Đường dẫn file wav mà ScreenRecorder đã tạo ra
        audio_wav = "workspace/raw_video.wav"
        
        # BƯỚC 1: Nếu có file wav (thu từ mic), dùng nó luôn vì chất lượng tốt nhất
        if os.path.exists(audio_wav) and os.path.getsize(audio_wav) > 0:
            print(f"[DEBUG-AI] Phát hiện file WAV từ mic, đang bóc băng...")
            return self.transcribe_audio(audio_wav)

        # BƯỚC 2: Nếu không có wav, mới đi trích xuất từ mp4
        if not os.path.exists(video_path):
            return ""
        
        audio_temp = "workspace/temp_audio.mp3"
        try:
            print(f"[DEBUG-AI] Không thấy file WAV, đang tách âm thanh từ MP4: {video_path}")
            from moviepy import VideoFileClip
            with VideoFileClip(video_path) as video:
                if video.audio is None:
                    # Thay vì trả về câu xin lỗi, ta trả về rỗng để rewrite_script xử lý
                    return "" 
                video.audio.write_audiofile(audio_temp, logger=None)
            
            return self.transcribe_audio(audio_temp)
        except Exception as e:
            print(f"Lỗi trích xuất: {e}")
            return ""
        

    def transcribe_audio(self, input_path):
        if not os.path.exists(input_path): return []
        
        print(f"[DEBUG-WHISPER] Đang bóc băng kèm Timestamp: {input_path}")
        try:
            model = WhisperModel("base", device="cpu", compute_type="int8") 
            segments, info = model.transcribe(input_path, beam_size=5, language="vi")
            
            # Trả về list các dict có start, end và nội dung
            results = []
            for s in segments:
                results.append({
                    "start": s.start,
                    "end": s.end,
                    "text": s.text.strip()
                })
            return results # Giờ nó trả về List chứ không phải String nữa
        except Exception as e:
            print(f"Lỗi Whisper: {e}")
            return []

    def _clean_text(self, text):
        """Vệ sĩ dọn dẹp văn bản: Loại bỏ triệt để ký tự lạ gây lỗi API"""
        import re
        if not text: return ""
        # 1. Bỏ định dạng Markdown, xuống dòng rác
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'[\*#_~`>]', '', text)
        # 2. Bỏ các đoạn chú thích trong ngoặc
        text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        # 3. Chỉ giữ lại chữ, số, dấu câu cơ bản, dấu cách
        # Lọc cực kỹ để tránh lỗi 'No audio received'
        text = re.sub(r'[^a-zA-Z0-9áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵĐđ.,!?;: ]', ' ', text)
        # 4. Thu gọn khoảng trắng
        return " ".join(text.split()).strip()

    def export_final_video(self, video_path, script_segments, output_path):
        try:
            from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
            import edge_tts
            import asyncio

            VOICE = "vi-VN-Hoài MyNeural"
            audio_clips = []

            async def make_clips():
                for i, seg in enumerate(script_segments):
                    # seg là dict: {"start": 2.0, "end": 5.0, "text": "Chào các bạn"}
                    tmp = f"workspace/seg_{i}.mp3"
                    comm = edge_tts.Communicate(seg['text'], VOICE)
                    await comm.save(tmp)
                    
                    # Tạo clip audio và đặt mốc bắt đầu (start)
                    a_clip = AudioFileClip(tmp).with_start(seg['start'])
                    
                    # Nếu tiếng AI dài hơn khoảng thời gian mày nói, ta tăng tốc độ cho đoạn đó
                    duration_needed = seg['end'] - seg['start']
                    if a_clip.duration > duration_needed:
                        # Tăng tốc độ đoạn nhỏ này
                        a_clip = a_clip.with_effects([lambda clip: clip.with_speed_ex(a_clip.duration / duration_needed)])
                    
                    audio_clips.append(a_clip)

            asyncio.run(make_clips())

            with VideoFileClip(video_path) as video:
                # Trộn tất cả các đoạn audio nhỏ vào video
                final_audio = CompositeAudioClip(audio_clips)
                final_video = video.with_audio(final_audio)
                
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
            return True
        except Exception as e:
            print(f"Lỗi: {e}")
            return False