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
# from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx
# import moviepy.video.fx.all as vfx
from core.knowledge_base import KnowledgeBase
import unicodedata
import nest_asyncio
import uuid

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx.all as vfx
except ImportError:
    # Nếu bản 2.0+ hoặc lỗi đường dẫn editor
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx as vfx

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
        """
        Bóc băng kèm mốc thời gian (Timestamp)
        Fix lỗi: tuple index out of range bằng cách ưu tiên file .wav và ép kiểu list.
        """
        # 1. KIỂM TRA FILE VÀ ƯU TIÊN FILE .WAV (Để tránh lỗi codec trong MP4)
        # Nếu đầu vào là .mp4, thử tìm file .wav cùng tên trong thư mục
        path_to_process = input_path
        if input_path.endswith(".mp4"):
            wav_path = input_path.replace(".mp4", ".wav")
            if os.path.exists(wav_path):
                path_to_process = wav_path
                print(f"[DEBUG-WHISPER] Phát hiện file WAV, ưu tiên dùng: {path_to_process}")

        if not os.path.exists(path_to_process):
            print(f"❌ Không tìm thấy file để bóc băng: {path_to_process}")
            return []
        
        # Kiểm tra size file, nếu 0 byte thì nghỉ khỏe
        if os.path.getsize(path_to_process) == 0:
            print(f"⚠️ File bị rỗng (0 bytes): {path_to_process}")
            return []

        print(f"[DEBUG-WHISPER] Đang phân tích Timeline: {path_to_process}")
        
        try:
            # 2. KHỞI TẠO MODEL (Nên để model này làm biến static của class để tránh load đi load lại)
            # Nếu đã có self.model thì dùng, không thì mới khởi tạo
            if not hasattr(self, 'whisper_model') or self.whisper_model is None:
                print("[DEBUG-WHISPER] Đang load model Whisper base (CPU)...")
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            
            # 3. THỰC HIỆN TRANSCRIBE
            # beam_size=5 là chuẩn, vad_filter=True giúp lọc bớt đoạn im lặng/nhiễu
            segments_gen, info = self.whisper_model.transcribe(
                path_to_process, 
                beam_size=5, 
                language="vi",
                vad_filter=True, # Lọc tiếng ồn/khoảng lặng
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # QUAN TRỌNG: Ép kiểu generator về list ngay lập tức để tránh lỗi index khi duyệt
            segments = list(segments_gen)
            
            results = []
            for s in segments:
                # Làm sạch text
                clean_text = s.text.strip()
                
                # Chỉ lấy các đoạn có nội dung thực sự (dài hơn 1 ký tự)
                if len(clean_text) > 1:
                    results.append({
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": clean_text
                    })
            
            print(f"✅ Đã trích xuất thành công {len(results)} đoạn timeline.")
            return results

        except Exception as e:
            # Nếu lỗi liên quan đến file, có thể do ffmpeg không đọc được codec
            print(f"❌ Lỗi Whisper tại {path_to_process}: {str(e)}")
            import traceback
            traceback.print_exc() # In chi tiết lỗi ra console để debug
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

    
    async def _make_audio_clips(self, script_segments, voice_id=None):
        nest_asyncio.apply()
        
        # Lấy giọng từ tham số, ưu tiên giọng người dùng chọn từ GUI
        VOICE = voice_id if voice_id else "vi-VN-NamMinhNeural"
        
        audio_clips_list = []
        temp_files = []
        last_end_time = 0 

        print(f"\n🚀 [DEBUG-TTS] ĐANG DÙNG GIỌNG: {VOICE}")

        for i, seg in enumerate(script_segments):
            text_to_read = self._clean_text(seg.get('text', '')).replace("e mail", "email")
            if not text_to_read: continue
            
            unique_name = f"seg_{i}_{uuid.uuid4().hex[:6]}.mp3"
            tmp_path = os.path.join("workspace", unique_name)
            
            try:
                # FIX TẠI ĐÂY: Bỏ pitch="-5Hz" để giọng không bị uốn éo
                communicate = edge_tts.Communicate(text_to_read, VOICE, rate="+0%")
                await communicate.save(tmp_path)
                
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    a_clip = AudioFileClip(tmp_path)
                    
                    original_start = float(seg['start'])
                    original_end = float(seg['end'])
                    
                    # Logic chống đè
                    actual_start = max(original_start, last_end_time)
                    drift = actual_start - original_start
                    
                    # Ép tốc độ nhẹ nếu bị lệch quá nhiều
                    if drift > 0.5:
                        duration_limit = original_end - original_start
                        if duration_limit > 0:
                            factor = a_clip.duration / duration_limit
                            a_clip = a_clip.fx(vfx.speedx, min(factor, 1.1))
                    
                    a_clip = a_clip.set_start(actual_start)
                    last_end_time = actual_start + a_clip.duration
                    
                    audio_clips_list.append(a_clip)
                    temp_files.append(tmp_path)
            
            except Exception as e:
                print(f"🧨 Lỗi đoạn {i}: {e}")
                continue
        return audio_clips_list, temp_files
    
    def export_final_video(self, video_path, script_segments, output_path, voice_id=None):
        """
        Hàm trộn Video gốc + Audio AI theo đúng Timeline.
        Vũ chú ý: voice_id truyền từ st.session_state.selected_voice_id vào đây.
        """
        temp_audio_files = []
        audio_clips = []
        
        try:
            # 1. KIỂM TRA FILE GỐC (Tránh lỗi FileNotFoundError nãy mày gặp)
            if not os.path.exists(video_path):
                print(f"❌ Lỗi: File gốc '{video_path}' không tồn tại!")
                return False

            # 2. TẠO AUDIO CLIPS (CHẠY ASYNC)
            # Tao giả định mày đã có hàm _make_audio_clips trả về (clips, paths)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_clips_raw, temp_audio_files = loop.run_until_complete(
                    self._make_audio_clips(script_segments, voice_id=voice_id)
                )
            finally:
                loop.close()

            if not audio_clips_raw:
                print("⚠️ Không có audio nào được tạo ra.")
                return False

            print(f"🎬 [RENDER] Bắt đầu trộn {len(audio_clips_raw)} đoạn thoại vào video...")

            # 3. XỬ LÝ VIDEO & AUDIO CHÍNH
            with VideoFileClip(video_path) as video:
                # Lấy FPS gốc của video để tránh lệch hình/tiếng
                original_fps = video.fps if video.fps else 30
                
                # Gán thời điểm bắt đầu (start) cho từng đoạn audio theo kịch bản
                # Đây là bước quan trọng nhất để KHỚP LỜI
                final_clips_to_composite = []
                for i, clip in enumerate(audio_clips_raw):
                    start_time = script_segments[i].get('start', 0)
                    # Ép audio bắt đầu đúng tại giây start_time trong timeline video
                    positioned_clip = clip.set_start(start_time)
                    final_clips_to_composite.append(positioned_clip)

                # Trộn các đoạn audio thành một track duy nhất
                final_audio = CompositeAudioClip(final_clips_to_composite)
                
                # Gắn audio vào video (Tương thích cả MoviePy cũ và mới)
                if hasattr(video, "with_audio"):
                    final_video = video.with_audio(final_audio)
                else:
                    final_video = video.set_audio(final_audio)

                # Cắt video đúng bằng độ dài gốc (tránh audio dài hơn làm video bị đen đoạn cuối)
                final_video = final_video.subclip(0, video.duration)

                # 4. XUẤT FILE THÀNH PHẨM
                # preset='ultrafast' giúp render nhanh gấp 5 lần
                # threads=4 tận dụng đa nhân CPU máy Vũ
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    fps=original_fps,
                    preset="ultrafast",
                    threads=4,
                    logger=None # Tắt log rác của MoviePy cho sạch terminal
                )

                # 5. GIẢI PHÓNG TÀI NGUYÊN (Bắt buộc)
                final_video.close()
                final_audio.close()
                for c in audio_clips_raw:
                    c.close()

            # 6. DỌN RÁC (Xóa file MP3 tạm)
            for f in temp_audio_files:
                if os.path.exists(f):
                    try: os.remove(f)
                    except: pass

            print(f"✅ Đã xuất video thành công: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng khi Export: {e}")
            # Đảm bảo dọn rác kể cả khi crash
            for f in temp_audio_files:
                try: os.remove(f)
                except: pass
            return False