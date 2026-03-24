import streamlit as st
import os
import asyncio
import edge_tts
import subprocess
import time

from core.scripts import *

# async def generate_voice(text, output_path):
#     # Giọng Hoài My cực kỳ sang và rõ cho ngành vàng bạc
#     voice = "vi-VN-HoaiMyNeural"
#     # Tăng tốc độ nói lên một chút (10%) để nghe chuyên nghiệp hơn
#     communicate = edge_tts.Communicate(text, voice, rate="+10%")
#     await communicate.save(output_path)

# def render_editor(ai_studio):
#     st.divider()
#     st.header("🎬 TRẠM BIÊN TẬP & LỒNG TIẾNG AI")
    
#     # 1. KHỞI TẠO ĐƯỜNG DẪN (Đồng bộ với Tab Recorder)
#     workspace = "workspace"
#     outputs = "outputs"
#     os.makedirs(workspace, exist_ok=True)
#     os.makedirs(outputs, exist_ok=True)

#     # Kiểm tra cả 2 định dạng file quay màn hình có thể có
#     video_raw_mp4 = os.path.join(workspace, "raw_video.mp4")
#     video_raw_avi = os.path.join(workspace, "raw_video.avi")
    
#     upload_path = os.path.join(workspace, "input_video.mp4")
#     audio_ai_path = os.path.abspath(os.path.join(workspace, "voice_ai.mp3"))
#     output_video = os.path.abspath(os.path.join(outputs, "Giaiphapvang_Tutorial.mp4"))

#     col1, col2 = st.columns(2)
#     video_input = None

#     # --- CỘT 1: QUẢN LÝ VIDEO ---
#     with col1:
#         st.subheader("📺 Bước 1: Chọn Video")
#         uploaded_file = st.file_uploader("Hoặc Upload video mới (.mp4)", type=["mp4"])
        
#         if uploaded_file:
#             video_input = upload_path
#             with open(video_input, "wb") as f:
#                 f.write(uploaded_file.read())
#         elif os.path.exists(video_raw_mp4):
#             video_input = video_raw_mp4
#             st.success("✅ Đang dùng bản quay màn hình (.mp4)")
#         elif os.path.exists(video_raw_avi):
#             video_input = video_raw_avi
#             st.info("✅ Đang dùng bản quay màn hình (.avi)")

#         if video_input:
#             # Hiển thị preview (Chỉ hiển thị được MP4 trên web)
#             if video_input.endswith('.avi'):
#                 st.warning("⚠️ File AVI không xem trước được. AI sẽ tự chuyển sang MP4 khi Render.")
#             else:
#                 st.video(video_input)

#     # --- CỘT 2: QUẢN LÝ LỜI THOẠI ---
#     with col2:
#         st.subheader("✍️ Bước 2: Chuốt lời thoại")
#         default_raw = st.session_state.get('raw_voice_input', "")
#         raw_voice = st.text_area("Lời thoại nháp (Bạn nói lúc quay):", value=default_raw, height=150)
        
#         if st.button("🪄 AI BIÊN SOẠN CHUYÊN NGHIỆP", use_container_width=True):
#             if raw_voice:
#                 with st.spinner("AI đang mông má kịch bản..."):
#                     # Gọi hàm rewrite từ AIManager (nhớ truyền context nếu cần)
#                     st.session_state['refined_text'] = ai_studio.rewrite_script(raw_voice)
#                     st.rerun()
#             else:
#                 st.error("Mày chưa nhập lời thoại nháp kìa Vũ!")

def render_editor(ai_studio):
    st.divider()
    st.header("🎬 TRẠM BIÊN TẬP & LỒNG TIẾNG AI")
    
    workspace = "workspace"
    outputs = "outputs"
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(outputs, exist_ok=True)

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
            if video_input.endswith('.avi'):
                st.warning("⚠️ File AVI không xem trước được.")
            else:
                st.video(video_input)

    # --- CỘT 2: QUẢN LÝ LỜI THOẠI ---
    with col2:
        st.subheader("✍️ Bước 2: Chuốt lời thoại")
        
        # 1. LẤY DANH SÁCH FILE CŨ (Hiện luôn không cần đợi AI)
        saved_scripts = get_list_scripts()
        selected_script = st.selectbox("📂 Chọn kịch bản đã lưu:", ["-- Tạo bản mới --"] + saved_scripts)

        # Nếu mày chọn một bản cũ trong danh sách
        if selected_script != "-- Tạo bản mới --":
            if st.session_state.get('last_selected') != selected_script:
                with open(f"workspace/scripts/{selected_script}.json", 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    st.session_state['refined_text'] = saved_data['content']
                    st.session_state['last_selected'] = selected_script

        # 2. Ô NHẬP LIỆU NHÁP (Để AI soạn)
        default_raw = st.session_state.get('raw_voice_input', "")
        raw_voice = st.text_area("Lời thoại nháp (Bạn nói lúc quay):", value=default_raw, height=100)
        
        if st.button("🪄 AI BIÊN SOẠN KỊCH BẢN", use_container_width=True):
            if raw_voice:
                with st.spinner("AI đang soạn..."):
                    refined = ai_studio.rewrite_script(raw_voice)
                    st.session_state['refined_text'] = refined
                    st.rerun()
            else:
                st.error("Mày chưa nhập lời thoại nháp kìa Vũ!")

    # --- HỆ THỐNG HIỆN THỊ, SỬA VÀ LƯU (Xuất hiện khi có dữ liệu) ---
    if 'refined_text' in st.session_state:
        st.divider()
        st.subheader("📝 Hiệu chỉnh & Lưu phiên bản")
        
        # Ô này cho phép mày sửa cho "chậm và rõ"
        final_text = st.text_area("Nội dung kịch bản cuối cùng:", 
                                  value=st.session_state['refined_text'], height=150)
        
        c_ver1, c_ver2 = st.columns([3, 1])
        with c_ver1:
            ver_name = st.text_input("Tên phiên bản mới:", placeholder="Ví dụ: Kịch bản chốt lần 1")
        with c_ver2:
            if st.button("💾 LƯU FILE", use_container_width=True):
                if ver_name:
                    save_script_to_file(final_text, ver_name)
                    st.success(f"Đã lưu file {ver_name}.json")
                    time.sleep(0.5)
                    st.rerun() # Refresh để cập nhật vào selectbox
                else:
                    st.warning("Nhập tên file đã!")

        # Cập nhật lại session_state khi mày sửa tay
        st.session_state['refined_text'] = final_text

    # --- HỆ THỐNG LƯU & SỬA KỊCH BẢN ---
    if 'refined_text' in st.session_state:
        st.divider()
        st.subheader("📝 Hiệu chỉnh & Lưu phiên bản")
        
        final_text = st.text_area("Nội dung kịch bản (Có thể sửa trực tiếp ở đây):", 
                                  value=st.session_state['refined_text'], height=150)
        
        c_ver1, c_ver2 = st.columns([3, 1])
        with c_ver1:
            ver_name = st.text_input("Đặt tên phiên bản để lưu:", placeholder="Ví dụ: Kịch bản chốt lần 1")
        with c_ver2:
            if st.button("💾 LƯU PHIÊN BẢN", use_container_width=True):
                if ver_name:
                    save_script_to_file(final_text, ver_name)
                    st.success(f"Đã lưu: {ver_name}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nhập cái tên để lưu chứ Vũ!")

        # Cập nhật text cuối cùng vào session_state để Render
        st.session_state['refined_text'] = final_text

        # --- BƯỚC 3: RENDER ---
        st.subheader("🚀 Bước 3: Xuất Video Thành Phẩm")
        if st.button("🔥 BẮT ĐẦU RENDER VIDEO", type="primary", use_container_width=True):
            if not video_input:
                st.error("Thiếu video đầu vào!")
            else:
                with st.spinner("⚡ Đang lồng tiếng (Hoài My) và trộn video..."):
                    # Render logic giống file cũ của mày...
                    asyncio.run(generate_voice(final_text, audio_ai_path))
                    
                    v_in = os.path.abspath(video_input)
                    a_in = os.path.abspath(audio_ai_path)
                    v_out = os.path.abspath(output_video)

                    cmd = ['ffmpeg', '-y', '-i', v_in, '-i', a_in, '-c:v', 'libx264', '-preset', 'ultrafast', '-map', '0:v:0', '-map', '1:a:0', '-shortest', v_out]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        st.balloons()
                        st.video(v_out)
                        with open(v_out, "rb") as file:
                            st.download_button("📥 TẢI VIDEO", file, file_name=f"Giaiphapvang_{int(time.time())}.mp4")

    