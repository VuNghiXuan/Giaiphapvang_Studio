import os
import requests
import time
import re
import asyncio
import edge_tts
from groq import Groq
from google import genai
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx
# import moviepy.video.fx.all as vfx
from core.knowledge_base import KnowledgeBase
import unicodedata

# Load biến môi trường
load_dotenv()

class AIManager:
    def __init__(self):
        self.provider = os.getenv("DEFAULT_PROVIDER", "Groq").strip()
        self.kb = KnowledgeBase()
        print(f"[DEBUG-AI] Khởi tạo hệ thống khớp lệnh với Provider: {self.provider}")

    def _clean_text(self, text):
        if not text: return ""
                
        # 1. Chuẩn hóa về dạng chuẩn nhất
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Xóa các ký tự Markdown AI hay dùng: dấu sao, dấu thăng, dấu gạch dưới
        text = re.sub(r'[\*\#\_\[\]\(\)]', '', text)
        
        # 3. Chỉ giữ lại chữ Tiếng Việt, số và dấu câu cơ bản nhất
        text = re.sub(r'[^a-zA-Z0-9áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵĐđ.,!?;: ]', ' ', text)
        
        # 4. Thu gọn khoảng trắng
        text = " ".join(text.split()).strip()
        return text

    def transcribe_with_segments(self, input_path):
        """Bóc băng kèm mốc thời gian (Timestamp)"""
        if not os.path.exists(input_path):
            print(f"❌ Không tìm thấy file để bóc băng: {input_path}")
            return []
        
        print(f"[DEBUG-WHISPER] Đang phân tích Timeline: {input_path}")
        try:
            # Dùng model base để tốc độ xử lý nhanh trên CPU
            model = WhisperModel("base", device="cpu", compute_type="int8") 
            segments, _ = model.transcribe(input_path, beam_size=5, language="vi")
            
            results = []
            for s in segments:
                if len(s.text.strip()) > 1: # Bỏ qua âm thanh rác
                    results.append({
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": s.text.strip()
                    })
            return results
        except Exception as e:
            print(f"❌ Lỗi Whisper: {e}")
            return []

    def _call_ai_api(self, prompt):
        """Hàm dùng chung để gọi các Provider AI khác nhau"""
        provider = self.provider.lower()
        try:
            # 1. XỬ LÝ CHO GROQ
            if provider == "groq":
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.1
                )
                return completion.choices[0].message.content

            # 2. XỬ LÝ CHO GEMINI (Khuyên dùng bản 2.0 Flash)
            elif provider == "gemini":
                client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=prompt
                )
                return response.text

            # 3. XỬ LÝ CHO OLLAMA (Dành cho chạy Local)
            elif provider == "ollama":
                url = f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate"
                payload = {"model": os.getenv("OLLAMA_MODEL", "vinallama"), "prompt": prompt, "stream": False}
                res = requests.post(url, json=payload, timeout=60)
                return res.json().get('response', '')

        except Exception as e:
            print(f"❌ Lỗi khi gọi API {provider}: {e}")
        return ""

    def rewrite_segments(self, segments):
        if not segments: return []
        
        system_context = self.kb.get_context()
        # Gom dữ liệu để AI hiểu ngữ cảnh
        raw_input = "\n".join([f"SEGMENT_{i} [{s['start']} - {s['end']}]: {s['text']}" for i, s in enumerate(segments)])
        
        prompt = f"""
        Bạn là biên tập viên cao cấp của Giaiphapvang Studio.
        Dựa trên kiến thức: {system_context}
        
        Nhiệm vụ: Viết lại lời thoại chuyên nghiệp, sửa lỗi chính tả nặng (VD: 'chi nhấm' -> 'Chi nhánh', 'tàu' -> 'Tạo').
        
        QUY TẮC:
        1. Giữ nguyên mốc thời gian.
        2. Trả về đúng định dạng: [start - end]: lời thoại
        
        DỮ LIỆU:
        {raw_input}
        """

        res_content = self._call_ai_api(prompt)
        
        final_segments = []
        # Regex này cực khôn: Nó tìm mọi thứ có dạng [Số - Số] rồi lấy phần chữ phía sau
        # Nó sẽ tự bỏ qua mấy câu "Dưới đây là..." của AI
        pattern = r"\[(\d+\.?\d*)\s*[-|]\s*(\d+\.?\d*)\s*\][:\s-]+(.*)"
        
        # Tìm tất cả các khớp (matches) trong toàn bộ văn bản AI trả về
        matches = re.findall(pattern, res_content)
        
        if matches:
            for start, end, text in matches:
                # Ép sạch rác một lần nữa
                clean_txt = self._clean_text(text)
                if clean_txt and len(clean_txt) > 1:
                    final_segments.append({
                        "start": float(start),
                        "end": float(end),
                        "text": clean_txt
                    })
        
        if not final_segments:
            print("⚠️ Regex không bắt được gì, AI nói quá nhiều lời dẫn. Đang dùng lời thoại gốc...")
            for s in segments:
                s['text'] = self._clean_text(s['text'])
            return segments

        print(f"✅ Đã bóc tách thành công {len(final_segments)} đoạn thoại sạch!")
        return final_segments

    async def _make_audio_clips(self, script_segments):
        """Tạo các đoạn audio từ kịch bản và khớp vào Timeline với logic Tăng tốc & Debug"""
        # --- Import local để đảm bảo không lỗi thư viện ---       

        VOICE = "vi-VN-Hoài MyNeural"
        clips = []
        temp_files = []
        
        print(f"\n🚀 [DEBUG-TTS] BẮT ĐẦU TIẾN TRÌNH: {len(script_segments)} đoạn.")

        for i, seg in enumerate(script_segments):
            # 1. Làm sạch văn bản tuyệt đối bằng hàm đã tối ưu
            text_to_read = self._clean_text(seg.get('text', ''))
            
            print(f"\n--- Đoạn {i} ---")
            print(f"📝 Nội dung gửi đi: '{text_to_read}'")
            print(f"⏱️ Khung giờ: {seg['start']}s -> {seg['end']}s")

            # Bỏ qua nếu văn bản rỗng hoặc quá ngắn (tránh lỗi API)
            if not text_to_read or len(text_to_read) < 2:
                print(f"⏩ [SKIP] Bỏ qua đoạn {i} do văn bản không hợp lệ.")
                continue
                
            start_time = float(seg['start'])
            end_time = float(seg['end'])
            duration_limit = end_time - start_time
            
            # Tạo file tạm trong thư mục workspace
            tmp_path = os.path.join("workspace", f"seg_{i}_{int(time.time())}.mp3")
            
            try:
                # 2. VỆ SĨ: Nghỉ 0.6s để tránh bị Microsoft chặn (Rate Limit)
                print(f"⏳ Đang chờ phản hồi từ Microsoft...")
                await asyncio.sleep(0.6) 
                
                # 3. Gọi Edge-TTS tạo file audio
                communicate = edge_tts.Communicate(text_to_read, VOICE)
                await communicate.save(tmp_path)
                
                # Kiểm tra kết quả lưu file
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    f_size = os.path.getsize(tmp_path)
                    print(f"📊 Đã nhận Audio: {f_size} bytes")
                    
                    # 4. Nạp vào MoviePy để xử lý timeline
                    a_clip = AudioFileClip(tmp_path)
                    original_duration = a_clip.duration
                    print(f"🎵 Độ dài thực tế: {original_duration:.2f}s | Giới hạn clip: {duration_limit:.2f}s")
                    
                    # 5. LOGIC KHỚP LỆNH: Nếu nói quá dài -> Tăng tốc giọng đọc
                    if original_duration > duration_limit and duration_limit > 0:
                        # Tính toán hệ số tốc độ (Ví dụ: cần 5s mà nói 7s -> tăng tốc x1.4)
                        speed_factor = original_duration / duration_limit
                        # Giới hạn tối đa x2.0 để nghe vẫn ra tiếng người
                        speed_factor = min(speed_factor, 2.0) 
                        
                        # Sử dụng vfx để thay đổi tốc độ
                        a_clip = a_clip.fx(vfx.speedx, speed_factor)
                        print(f"⚡ [SPEEDUP] Đã ép tốc độ x{speed_factor:.2f} để kịp Timeline.")
                    
                    # 6. Đặt mốc thời gian bắt đầu
                    a_clip = a_clip.set_start(start_time)
                    
                    clips.append(a_clip)
                    temp_files.append(tmp_path)
                    print(f"✅ Đoạn {i}: XỬ LÝ HOÀN TẤT.")
                else:
                    print(f"❌ [ERROR] Đoạn {i}: Microsoft trả về file rỗng hoặc không lưu được.")

            except Exception as e:
                # Bẫy lỗi chi tiết
                error_msg = str(e)
                print(f"🧨 [FATAL] Lỗi xử lý đoạn {i}: {type(e).__name__}")
                if "NoAudioReceived" in error_msg:
                    print("🚨 CẢNH BÁO: Không nhận được âm thanh. Hãy kiểm tra kết nối Internet!")
                else:
                    print(f"🔍 Chi tiết: {error_msg}")
                continue

        print(f"\n🎯 [DEBUG-TTS] TỔNG KẾT: Thành công {len(clips)}/{len(script_segments)} đoạn.")
        
        if not clips:
            print("💀 [CRITICAL] Không tạo được bất kỳ đoạn audio nào. Vui lòng kiểm tra lại kịch bản hoặc mạng.")
            
        return clips, temp_files
    

    def export_final_video(self, video_path, script_segments, output_path):
        """Hợp nhất Video + Audio (Bản sửa lỗi No Audio Received)"""
        try:
            # Tạo event loop mới để chạy async trong thread của Streamlit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_clips, temp_files = loop.run_until_complete(self._make_audio_clips(script_segments))
            loop.close()

            if not audio_clips:
                print("❌ Không có đoạn audio hợp lệ để lồng tiếng. Kiểm tra lại kịch bản!")
                return False

            print(f"[DEBUG-RENDER] Đang trộn {len(audio_clips)} đoạn thoại...")
            with VideoFileClip(video_path) as video:
                final_audio = CompositeAudioClip(audio_clips)
                
                # Fix lỗi thuộc tính tùy phiên bản MoviePy
                if hasattr(video, "set_audio"):
                    final_video = video.set_audio(final_audio)
                else:
                    final_video = video.with_audio(final_audio)
                
                # Giới hạn thời gian video bằng đúng thời gian video gốc (tránh bị dài ra vô tận)
                final_video = final_video.set_duration(video.duration)

                final_video.write_videofile(
                    output_path, 
                    codec="libx264", 
                    audio_codec="aac", 
                    fps=24, 
                    logger=None,
                    temp_audiofile="workspace/temp-audio.m4a", # Tránh xung đột file audio
                    remove_temp=True
                )
            
            # Dọn dẹp
            for f in temp_files:
                if os.path.exists(f): os.remove(f)
            return True
        except Exception as e:
            print(f"❌ Lỗi Render: {str(e)}")
            return False