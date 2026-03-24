# pip uninstall moviepy -y
# pip install moviepy==1.0.3

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
import nest_asyncio
import uuid

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


    # async def _make_audio_clips(self, script_segments):
       
    #     nest_asyncio.apply()
    #     VOICE = "vi-VN-NamMinhNeural" 
    #     clips = []
    #     temp_files = []
        
    #     print(f"\n🚀 [DEBUG-TTS] ĐANG KHỚP AUDIO VÀO TIMELINE...")

    #     for i, seg in enumerate(script_segments):
    #         text_to_read = self._clean_text(seg.get('text', '')).replace("e mail", "email")
    #         if not text_to_read: continue
                
    #         tmp_path = os.path.join("workspace", f"seg_{i}_{int(time.time())}.mp3")
            
    #         try:
    #             # 1. Gọi Microsoft tạo file
    #             communicate = edge_tts.Communicate(text_to_read, VOICE)
    #             await communicate.save(tmp_path)
                
    #             if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
    #                 # 2. Nạp Clip
    #                 a_clip = AudioFileClip(tmp_path)
                    
    #                 # 3. Tính toán Speed (Tăng tốc)
    #                 duration_limit = float(seg['end']) - float(seg['start'])
    #                 if a_clip.duration > duration_limit and duration_limit > 0:
    #                     factor = min(a_clip.duration / duration_limit, 2.0)
    #                     # SỬA LỖI .fx: Dùng cách gọi an toàn nhất
    #                     a_clip = vfx.speedx(a_clip, factor) 
    #                     print(f"⚡ Đoạn {i}: Tăng tốc x{factor:.2f}")
                    
    #                 # 4. SỬA LỖI .set_start: Dùng thuộc tính start trực tiếp hoặc set_start cũ
    #                 # Cách này bao thầu mọi phiên bản MoviePy
    #                 try:
    #                     a_clip = a_clip.set_start(float(seg['start']))
    #                 except AttributeError:
    #                     a_clip.start = float(seg['start'])
                        
    #                 clips.append(a_clip)
    #                 temp_files.append(tmp_path)
    #                 print(f"✅ Đoạn {i}: ĐÃ KHỚP ({a_clip.duration:.2f}s)")
    #             else:
    #                 print(f"❌ Đoạn {i}: Lỗi file mp3.")
    #         except Exception as e:
    #             print(f"🧨 Lỗi xử lý MoviePy ở đoạn {i}: {e}")
    #             continue

        # return clips, temp_files
    
    async def _make_audio_clips(self, script_segments):
        
        nest_asyncio.apply()
        VOICE = "vi-VN-NamMinhNeural" 
        audio_clips_list = []
        temp_files = []
        
        print(f"\n🚀 [DEBUG-TTS] ĐANG TẠO {len(script_segments)} FILE RIÊNG BIỆT...")

        for i, seg in enumerate(script_segments):
            text_to_read = self._clean_text(seg.get('text', '')).replace("e mail", "email")
            if not text_to_read: continue
            
            # Tên file cực kỳ dị để không bao giờ trùng
            unique_name = f"seg_{i}_{uuid.uuid4().hex[:6]}.mp3"
            tmp_path = os.path.join("workspace", unique_name)
            
            try:
                communicate = edge_tts.Communicate(text_to_read, VOICE)
                await communicate.save(tmp_path)
                
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    a_clip = AudioFileClip(tmp_path)
                    
                    # Khớp Timeline
                    start_t = float(seg['start'])
                    duration_limit = float(seg['end']) - start_t
                    
                    if a_clip.duration > duration_limit and duration_limit > 0:
                        a_clip = vfx.speedx(a_clip, min(a_clip.duration / duration_limit, 2.0))
                    
                    # QUAN TRỌNG: Gán vị trí bắt đầu
                    if hasattr(a_clip, "set_start"):
                        a_clip = a_clip.set_start(start_t)
                    else:
                        a_clip.start = start_t
                        
                    audio_clips_list.append(a_clip)
                    temp_files.append(tmp_path)
                    print(f"✅ Đã nạp đoạn {i} vào danh sách chờ trộn (Start: {start_t}s)")
                
            except Exception as e:
                print(f"🧨 Lỗi đoạn {i}: {e}")
                continue

        return audio_clips_list, temp_files
    
    # def export_final_video(self, video_path, script_segments, output_path):
    #     """Hợp nhất Video + Audio (Bản sửa lỗi triệt để mọi phiên bản MoviePy)"""
        
    #     try:
    #         # 1. Tạo event loop mới để chạy async TTS trong thread của Streamlit
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         audio_clips, temp_files = loop.run_until_complete(self._make_audio_clips(script_segments))
    #         loop.close()

    #         if not audio_clips:
    #             print("❌ Không có đoạn audio hợp lệ để lồng tiếng. Kiểm tra lại kịch bản!")
    #             return False

    #         print(f"[DEBUG-RENDER] Đang trộn {len(audio_clips)} đoạn thoại vào video...")
            
    #         with VideoFileClip(video_path) as video:
    #             # Tạo bản phối âm thanh từ các đoạn nhỏ
    #             final_audio = CompositeAudioClip(audio_clips)
                
    #             # 2. Gán Audio (Hỗ trợ cả MoviePy v1 và v2)
    #             if hasattr(video, "set_audio"):
    #                 final_video = video.set_audio(final_audio)
    #             else:
    #                 final_video = video.with_audio(final_audio)
                
    #             # 3. Giới hạn thời gian theo video gốc
    #             if hasattr(final_video, "set_duration"):
    #                 final_video = final_video.set_duration(video.duration)
    #             else:
    #                 final_video = final_video.with_duration(video.duration)

    #             # 4. Xuất file video cuối cùng
    #             final_video.write_videofile(
    #                 output_path, 
    #                 codec="libx264", 
    #                 audio_codec="aac", 
    #                 fps=24, 
    #                 logger="bar", # Hiện thanh % chạy cho đẹp
    #                 temp_audiofile="workspace/temp-audio.m4a",
    #                 remove_temp=True
    #             )
                
    #             # 5. Giải phóng tài nguyên ngay lập tức
    #             final_video.close()
    #             final_audio.close()
    #             for clip in audio_clips:
    #                 clip.close()
            
    #         # 6. Dọn dẹp file tạm (.mp3) một cách an toàn
    #         print("[DEBUG-CLEAN] Đang dọn dẹp các mảnh audio tạm...")
    #         time.sleep(1.5) # Chờ Windows nhả file hoàn toàn
            
    #         for f in temp_files:
    #             try:
    #                 if os.path.exists(f):
    #                     os.remove(f)
    #                     print(f"🗑️ Đã xóa: {f}")
    #             except Exception as e:
    #                 # Nếu vẫn không xóa được thì kệ nó, không làm sập tiến trình
    #                 print(f"⚠️ File {f} đang bận, sẽ xóa sau!")
            
    #         print(f"✨ CHÚC MỪNG VŨ! Video đã sẵn sàng tại: {output_path}")
    #         return True

    #     except Exception as e:
    #         print(f"❌ Lỗi Render cực nặng: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
    #         return False

    def export_final_video(self, video_path, script_segments, output_path):
       
        
        try:
            # Chạy async lấy danh sách 5 clips
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_clips, temp_files = loop.run_until_complete(self._make_audio_clips(script_segments))
            loop.close()

            if not audio_clips: return False

            print(f"🎬 [RENDER] Bắt đầu trộn tổng cộng {len(audio_clips)} đoạn thoại...")
            
            with VideoFileClip(video_path) as video:
                # GỘP TẤT CẢ AUDIO VÀO MỘT BẢN PHỐI
                final_audio = CompositeAudioClip(audio_clips)
                
                # Gán vào video
                if hasattr(video, "set_audio"):
                    final_video = video.set_audio(final_audio)
                else:
                    final_video = video.with_audio(final_audio)
                
                # Ép thời gian video
                if hasattr(final_video, "set_duration"):
                    final_video = final_video.set_duration(video.duration)
                else:
                    final_video = final_video.with_duration(video.duration)

                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                
                # Giải phóng bộ nhớ
                final_video.close()
                final_audio.close()
                for c in audio_clips: c.close()

            return True
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False