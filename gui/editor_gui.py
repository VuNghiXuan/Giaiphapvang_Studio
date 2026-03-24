import streamlit as st
import os
import asyncio
import edge_tts
import subprocess
import time
import json
from datetime import datetime

# Import các hàm từ file scripts.py
from core.scripts import get_list_scripts, save_script_to_file

async def generate_voice(text, output_path, voice_id):
    # Fix giọng: Bỏ pitch -5Hz để hết uốn éo, nghe rõ ràng hơn
    communicate = edge_tts.Communicate(text, voice_id, rate="+0%")
    await communicate.save(output_path)

def render_editor(ai_studio):
    st.divider()
    st.header("🎬 TRẠM BIÊN TẬP & LỒNG TIẾNG AI")
    
    workspace = "workspace"
    video_raw = os.path.join(workspace, "raw_video.mp4")
    selected_voice_id = st.session_state.get('selected_voice_id', "vi-VN-NamMinhNeural")

    # --- KHU VỰC 1: CHỌN KỊCH BẢN ---
    with st.expander("📂 KHO KỊCH BẢN", expanded=True):
        saved_scripts = get_list_scripts()
        # Thêm biến session để quản lý tên file đang mở
        c1, c2 = st.columns([2, 1])
        with c1:
            selected_script = st.selectbox("Chọn kịch bản:", ["-- Tạo bản mới --"] + saved_scripts)
        
        if selected_script != "-- Tạo bản mới --":
            if st.session_state.get('last_selected_file') != selected_script:
                script_path = f"workspace/scripts/{selected_script}.json"
                if os.path.exists(script_path):
                    with open(script_path, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                        if 'segments' in saved_data:
                            st.session_state.script_segments = saved_data['segments']
                        st.session_state.last_selected_file = selected_script
                        st.session_state.current_script_name = selected_script
        else:
            if st.session_state.get('last_selected_file') != "-- Tạo bản mới --":
                st.session_state.script_segments = []
                st.session_state.last_selected_file = "-- Tạo bản mới --"
                st.session_state.current_script_name = ""

    # --- KHU VỰC 2: TIMELINE BIÊN TẬP ---
    if os.path.exists(video_raw) or st.session_state.get('script_segments'):
        col_v, col_e = st.columns([1, 1.2])
        
        with col_v:
            if os.path.exists(video_raw):
                st.video(video_raw)
            st.info(f"🎙️ Giọng: {selected_voice_id}")
            
            if st.button("🎙️ AI TỰ SOẠN TIMELINE MỚI", use_container_width=True):
                with st.spinner("AI đang nghe..."):
                    raw_segments = ai_studio.transcribe_with_segments(video_raw)
                    if raw_segments:
                        st.session_state.script_segments = ai_studio.rewrite_segments(raw_segments)
                        st.rerun()

        with col_e:
            if 'script_segments' in st.session_state and st.session_state.script_segments:
                st.subheader("📝 Hiệu chỉnh Timeline")
                
                # Hàm xử lý Ripple Edit (Cộng dồn thời gian)
                def adjust_timeline(index, offset):
                    for i in range(index, len(st.session_state.script_segments)):
                        st.session_state.script_segments[i]['start'] = round(st.session_state.script_segments[i]['start'] + offset, 2)
                        st.session_state.script_segments[i]['end'] = round(st.session_state.script_segments[i]['end'] + offset, 2)

                # Duyệt danh sách segments
                for i, seg in enumerate(st.session_state.script_segments):
                    with st.container(border=True):
                        # Dòng 1: Điều khiển thời gian
                        tc1, tc2, tc3, tc4 = st.columns([1.5, 1, 1, 2])
                        with tc1:
                            st.markdown(f"**Đoạn {i+1}: {seg['start']}s**")
                        with tc2:
                            if st.button("➕", key=f"plus_{i}"):
                                adjust_timeline(i, 0.5) # Tăng 0.5s từ đoạn này về sau
                                st.rerun()
                        with tc3:
                            if st.button("➖", key=f"minus_{i}"):
                                adjust_timeline(i, -0.5) # Giảm 0.5s từ đoạn này về sau
                                st.rerun()
                        with tc4:
                            # Cho phép sửa tay chính xác start/end
                            seg['start'] = st.number_input("Start", value=float(seg['start']), key=f"start_{i}", step=0.1, label_visibility="collapsed")

                        # Dòng 2: Sửa lời thoại
                        seg['text'] = st.text_area("Lời thoại", value=seg['text'], key=f"text_{i}", height=80, label_visibility="collapsed")

                st.divider()
                
                # NÚT LƯU THÔNG MINH
                c_s1, c_s2 = st.columns([2, 1])
                with c_s1:
                    save_name = st.text_input("Tên file lưu:", value=st.session_state.get('current_script_name', ""), placeholder="Ban_huong_dan_moi")
                with c_s2:
                    if st.button("💾 LƯU LẠI", use_container_width=True, type="secondary"):
                        if save_name:
                            save_script_to_file(st.session_state.script_segments, save_name)
                            st.success("Đã lưu!")
                            time.sleep(0.5)
                            st.rerun()
                
                # NÚT XUẤT VIDEO
                if st.button("🎬 XUẤT VIDEO THÀNH PHẨM", type="primary", use_container_width=True):
                    with st.spinner("⚡ Đang render..."):
                        out_file = f"outputs/Final_{int(time.time())}.mp4"
                        success = ai_studio.export_final_video(
                            video_path=video_raw,
                            script_segments=st.session_state.script_segments,
                            output_path=out_file,
                            voice_id=selected_voice_id
                        )
                        if success:
                            st.balloons()
                            st.video(out_file)
                            with open(out_file, "rb") as f:
                                st.download_button("📥 TẢI VỀ", f, file_name="Video_Thanh_Pham.mp4")
            else:
                st.info("Chưa có kịch bản. Hãy chọn kịch bản cũ hoặc bấm 'AI TỰ SOẠN' bên trái.")
    else:
        st.warning("Mày chưa có video thô. Hãy quay ở Tab 1.")