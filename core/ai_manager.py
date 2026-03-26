import os
import requests
import time
import re
import asyncio
import edge_tts
import unicodedata
import nest_asyncio
import uuid
from groq import Groq
from google import genai
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from core.knowledge_base import KnowledgeBase

# Xử lý tương thích MoviePy
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx.all as vfx
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
    import moviepy.video.fx as vfx

load_dotenv()

class AIManager:
    def __init__(self):
        self.provider = os.getenv("DEFAULT_PROVIDER", "Groq").strip()
        self.kb = KnowledgeBase() # Khởi tạo KnowledgeBase mới của Vũ
        self.whisper_model = None
        print(f"[DEBUG-AI] Khởi tạo hệ thống với KnowledgeBase & Provider: {self.provider}")

    def _clean_text(self, text):
        if not text: return ""
        text = unicodedata.normalize('NFKC', text)
        # Xóa ký tự Markdown rác AI hay tự thêm vào
        text = re.sub(r'[\*\#\_\[\]\(\)]', '', text)
        # Chỉ giữ lại Tiếng Việt, số và dấu câu
        text = re.sub(r'[^a-zA-Z0-9áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵĐđ.,!?;: ]', ' ', text)
        return " ".join(text.split()).strip()

    def transcribe_with_segments(self, input_path):
        """Bóc băng video thành các đoạn timeline thô"""
        path_to_process = input_path
        if input_path.endswith(".mp4"):
            wav_path = input_path.replace(".mp4", ".wav")
            if os.path.exists(wav_path): path_to_process = wav_path

        if not os.path.exists(path_to_process) or os.path.getsize(path_to_process) == 0:
            return []

        try:
            if self.whisper_model is None:
                print("[DEBUG-WHISPER] Loading Whisper model...")
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            
            segments_gen, _ = self.whisper_model.transcribe(
                path_to_process, beam_size=5, language="vi", vad_filter=True
            )
            
            results = []
            for s in list(segments_gen):
                if len(s.text.strip()) > 1:
                    results.append({
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": s.text.strip()
                    })
            return results
        except Exception as e:
            print(f"❌ Lỗi Whisper: {e}")
            return []

    def rewrite_segments(self, segments, scenario_key):
        """
        Dùng AI để viết lại lời thoại dựa trên KỊCH BẢN RIÊNG của từng clip
        Vũ truyền scenario_key (vd: 'nhap_kho_nu_trang') vào đây nhé.
        """
        if not segments: return []
        
        # 1. Lấy Prompt 'may đo' riêng cho clip này từ KnowledgeBase
        custom_prompt = self.kb.get_prompt_for_clip(scenario_key)
        
        # 2. Chuẩn bị dữ liệu thô cho AI
        raw_input = "\n".join([f"[{s['start']} - {s['end']}]: {s['text']}" for s in segments])
        
        full_prompt = f"""
        {custom_prompt}
        
        DÀNH RIÊNG CHO CÁC ĐOẠN SAU (Hãy sửa lỗi và làm mượt lời thoại):
        {raw_input}
        
        YÊU CẦU TRẢ VỀ: Trả về danh sách kịch bản theo đúng định dạng [start - end]: lời thoại.
        """

        print('------------Lời thoại trước thô:', full_prompt)

        print('----------------------------------------------------------')

        # 3. Gọi API AI
        res_content = self._call_ai_api(full_prompt)

        print('------------Lời thoại sau khi gọt dũa AI:', res_content)

        print('----------------------------------------------------------')

        
        # 4. Bóc tách dữ liệu từ câu trả lời của AI bằng Regex
        final_segments = []
        pattern = r"\[(\d+\.?\d*)\s*[-|]\s*(\d+\.?\d*)\s*\][:\s-]+(.*)"


        matches = re.findall(pattern, res_content)
        
        if matches:
            for start, end, text in matches:
                clean_txt = self._clean_text(text)
                if clean_txt:
                    final_segments.append({
                        "start": float(start),
                        "end": float(end),
                        "text": clean_txt
                    })
        
        # Backup nếu AI "ngáo" không trả về đúng định dạng
        if not final_segments:
            print("⚠️ Lỗi định dạng AI, đang trả về bản gốc...")
            return segments
        
        print('------------Lời thoại cuối cùng sau khi qua thư viện re:', segments)
        print('----------------------------------------------------------')


        return final_segments

    def _call_ai_api(self, prompt):
        """Hàm gọi API dùng chung cho Groq/Gemini/Ollama"""
        provider = self.provider.lower()
        try:
            if provider == "groq":
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.1
                )
                return completion.choices[0].message.content
            elif provider == "gemini":
                client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=prompt
                )
                return response.text
        except Exception as e:
            print(f"❌ API Error ({provider}): {e}")
        return ""

    async def _make_audio_clips(self, script_segments, voice_id=None):
        """Tạo file âm thanh từ lời thoại đã sửa"""
        nest_asyncio.apply()
        VOICE = voice_id if voice_id else "vi-VN-NamMinhNeural"
        audio_clips_list = []
        temp_files = []
        last_end_time = 0 

        # Tạo thư mục workspace nếu chưa có
        if not os.path.exists("workspace"): os.makedirs("workspace")

        for i, seg in enumerate(script_segments):
            text = self._clean_text(seg.get('text', ''))
            if not text: continue
            
            tmp_path = os.path.join("workspace", f"v_seg_{i}_{uuid.uuid4().hex[:4]}.mp3")
            try:
                communicate = edge_tts.Communicate(text, VOICE)
                await communicate.save(tmp_path)
                
                if os.path.exists(tmp_path):
                    a_clip = AudioFileClip(tmp_path)
                    start_time = max(float(seg['start']), last_end_time)
                    a_clip = a_clip.set_start(start_time)
                    
                    last_end_time = start_time + a_clip.duration
                    audio_clips_list.append(a_clip)
                    temp_files.append(tmp_path)
            except Exception as e:
                print(f"Lỗi TTS đoạn {i}: {e}")
        return audio_clips_list, temp_files

    def export_final_video(self, video_path, script_segments, output_path, voice_id=None):
        """Trộn video gốc và audio AI"""
        if not os.path.exists(video_path): return False

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_clips, temp_files = loop.run_until_complete(
                self._make_audio_clips(script_segments, voice_id)
            )
            
            if not audio_clips: return False

            with VideoFileClip(video_path) as video:
                final_audio = CompositeAudioClip(audio_clips)
                # Tắt tiếng gốc (Hoặc để 0.1 nếu muốn nghe tiếng click nhẹ của Vũ)
                final_video = video.set_audio(final_audio)
                
                final_video.write_videofile(
                    output_path, codec="libx264", audio_codec="aac",
                    preset="ultrafast", threads=4, logger=None
                )
                
                final_video.close()
                final_audio.close()
                for c in audio_clips: c.close()

            for f in temp_files:
                if os.path.exists(f): os.remove(f)
            return True
        except Exception as e:
            print(f"Export Error: {e}")
            return False
        finally:
            loop.close()