import streamlit as st
import os
import asyncio
import edge_tts
import subprocess
import time

async def generate_voice(text, output_path):
    # Giọng Hoài My cực kỳ sang và rõ cho ngành vàng bạc
    voice = "vi-VN-HoaiMyNeural"
    # Tăng tốc độ nói lên một chút (10%) để nghe chuyên nghiệp hơn
    communicate = edge_tts.Communicate(text, voice, rate="+10%")
    await communicate.save(output_path)

def render_editor(ai_studio):
    st.divider()
    st.header("🎬 TRẠM BIÊN TẬP & LỒNG TIẾNG AI")
    
    # 1. KHỞI TẠO ĐƯỜNG DẪN (Đồng bộ với Tab Recorder)
    workspace = "workspace"
    outputs = "outputs"
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(outputs, exist_ok=True)

    # Kiểm tra cả 2 định dạng file quay màn hình có thể có
    video_raw_mp4 = os.path.join(workspace, "raw_video.mp4")
    video_raw_avi = os.path.join(workspace, "raw_video.avi")
    
    upload_path = os.path.join(workspace, "input_video.mp4")
    audio_ai_path = os.path.abspath(os.path.join(workspace, "voice_ai.mp3"))
    output_video = os.path.abspath(os.path.join(outputs, "Giaiphapvang_Tutorial.mp4"))

    col1, col2 = st.columns(2)
    video_input = None

    # --- CỘT 1: QUẢN LÝ VIDEO ---
    with col1:
        st.subheader("📺 Bước 1: Chọn Video")
        uploaded_file = st.file_uploader("Hoặc Upload video mới (.mp4)", type=["mp4"])
        
        if uploaded_file:
            video_input = upload_path
            with open(video_input, "wb") as f:
                f.write(uploaded_file.read())
        elif os.path.exists(video_raw_mp4):
            video_input = video_raw_mp4
            st.success("✅ Đang dùng bản quay màn hình (.mp4)")
        elif os.path.exists(video_raw_avi):
            video_input = video_raw_avi
            st.info("✅ Đang dùng bản quay màn hình (.avi)")

        if video_input:
            # Hiển thị preview (Chỉ hiển thị được MP4 trên web)
            if video_input.endswith('.avi'):
                st.warning("⚠️ File AVI không xem trước được. AI sẽ tự chuyển sang MP4 khi Render.")
            else:
                st.video(video_input)

    # --- CỘT 2: QUẢN LÝ LỜI THOẠI ---
    with col2:
        st.subheader("✍️ Bước 2: Chuốt lời thoại")
        default_raw = st.session_state.get('raw_voice_input', "")
        raw_voice = st.text_area("Lời thoại nháp (Bạn nói lúc quay):", value=default_raw, height=150)
        
        if st.button("🪄 AI BIÊN SOẠN CHUYÊN NGHIỆP", use_container_width=True):
            if raw_voice:
                with st.spinner("AI đang mông má kịch bản..."):
                    # Gọi hàm rewrite từ AIManager (nhớ truyền context nếu cần)
                    st.session_state['refined_text'] = ai_studio.rewrite_script(raw_voice)
                    st.rerun()
            else:
                st.error("Mày chưa nhập lời thoại nháp kìa Vũ!")

    # --- BƯỚC 3: RENDER THÀNH PHẨM ---
    if 'refined_text' in st.session_state:
        st.divider()
        st.subheader("🚀 Bước 3: Xuất Video Thành Phẩm")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            edited_text = st.text_area("Kịch bản cuối cùng (Hoài My sẽ đọc):", 
                                      value=st.session_state['refined_text'], height=150)
        with c2:
            st.info("💡 Mẹo: Giọng AI sẽ đè lên toàn bộ âm thanh cũ của video.")
            
            if st.button("🔥 BẮT ĐẦU RENDER", type="primary", use_container_width=True):
                if not video_input:
                    st.error("Thiếu video đầu vào!")
                else:
                    with st.spinner("⚡ Đang lồng tiếng và nén video..."):
                        # Xử lý file cũ
                        if os.path.exists(output_video):
                            try: os.remove(output_video)
                            except: pass

                        # 1. Tạo voice AI (Chạy async trong sync)
                        asyncio.run(generate_voice(edited_text, audio_ai_path))

                        # 2. Lệnh FFMPEG (Dùng đường dẫn tuyệt đối để tránh lỗi Windows)
                        v_in = os.path.abspath(video_input)
                        a_in = os.path.abspath(audio_ai_path)
                        v_out = os.path.abspath(output_video)

                        cmd = [
                            'ffmpeg', '-y', 
                            '-i', v_in,
                            '-i', a_in,
                            '-c:v', 'libx264', 
                            '-preset', 'ultrafast',
                            '-crf', '23',
                            '-pix_fmt', 'yuv420p',
                            '-map', '0:v:0', # Lấy hình video gốc
                            '-map', '1:a:0', # Lấy tiếng AI
                            '-shortest',     # Kết thúc khi 1 trong 2 hết
                            v_out
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            st.balloons()
                            st.success("🎉 XONG RỒI VŨ ƠI!")
                            st.video(v_out)
                            with open(v_out, "rb") as file:
                                st.download_button("📥 TẢI VIDEO VỀ MÁY", file, file_name="Giaiphapvang_Final.mp4")
                        else:
                            st.error(f"Lỗi FFmpeg: {result.stderr}")