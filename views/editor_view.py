import streamlit as st
import os
import time
from core.logic_scripts import (
    get_list_scripts_in_lesson, 
    save_script_to_file, 
    load_script_from_file
)
from .components.editor_components import render_segment_editor

def render_editor(ai_studio, sub_path):
    # --- CSS HACK: Giao diện chia đôi màn hình và nút bấm ---
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; height: 3em; }
        .main-col { border-right: 1px solid #ddd; padding-right: 20px; }
        .sticky-video { position: -webkit-sticky; position: sticky; top: 10px; }
        div[data-testid="stExpander"] { border: 1px solid #217346; background: #f9f9f9; }
        </style>
    """, unsafe_allow_html=True)

    # --- 1. KHỞI TẠO STATE ---
    if 'editing_index' not in st.session_state:
        st.session_state.editing_index = -1
    if 'script_segments' not in st.session_state:
        st.session_state.script_segments = []
    
    video_raw = os.path.join(sub_path, "raw", "raw_video.mp4")
    video_final = os.path.join(sub_path, "final_video.mp4")

    # --- 2. LOGIC XỬ LÝ LỆNH ---
    def handle_action(action, index):
        if action == "📝 Chỉnh sửa":
            st.session_state.editing_index = index
        elif action == "🗑️ Xóa đoạn":
            st.session_state.script_segments.pop(index)
        elif "➕ Chèn" in action:
            offset = 2.0
            insert_pos = index if "phía trước" in action else index + 1
            new_start = st.session_state.script_segments[index]['start']
            if "phía sau" in action: new_start += offset
            for i in range(insert_pos, len(st.session_state.script_segments)):
                st.session_state.script_segments[i]['start'] = round(st.session_state.script_segments[i]['start'] + offset, 2)
            st.session_state.script_segments.insert(insert_pos, {"start": new_start, "end": new_start + offset, "text": "", "freeze": False})
            st.session_state.editing_index = insert_pos
        st.rerun()

    # --- 3. GIAO DIỆN BIÊN TẬP CHI TIẾT (FULL SCREEN KHI EDIT) ---
    if st.session_state.editing_index != -1:
        idx = st.session_state.editing_index
        render_segment_editor(idx, st.session_state.script_segments[idx], video_raw, 0)
        if st.button("⬅️ Quay lại danh sách", use_container_width=True):
            st.session_state.editing_index = -1
            st.rerun()
        return 

    # --- 4. THANH CÔNG CỤ (TOOLBAR) ---
    with st.expander("🛠️ QUẢN LÝ KỊCH BẢN & AI", expanded=True):
        # Chọn Scenario từ KnowledgeBase
        all_scenarios = list(ai_studio.kb.scenarios.keys())
        selected_key = st.selectbox(
            "🎯 Chọn Form hướng dẫn (Ngữ cảnh AI):", 
            all_scenarios, 
            format_func=lambda x: ai_studio.kb.scenarios[x]['title']
        )

        col_file, col_name, col_save = st.columns([2, 2, 1])
        saved_scripts = get_list_scripts_in_lesson(sub_path)
        current_name = st.session_state.get('current_script_name', "-- Tạo mới --")
        
        with col_file:
            selection = st.selectbox("Bản thảo đã lưu:", ["-- Tạo mới --"] + saved_scripts, 
                                   index=(["-- Tạo mới --"] + saved_scripts).index(current_name) if current_name in (["-- Tạo mới --"] + saved_scripts) else 0)
            if selection != st.session_state.get('last_selection'):
                st.session_state.script_segments = load_script_from_file(sub_path, selection) if selection != "-- Tạo mới --" else []
                st.session_state.current_script_name = selection
                st.session_state.last_selection = selection
                st.rerun()

        with col_name:
            new_name = st.text_input("Lưu tên phiên bản:", value=selection if selection != "-- Tạo mới --" else "", placeholder="VD: Ban_nhap_1")

        with col_save:
            st.write(" ") # Padding top
            if st.button("💾 LƯU", use_container_width=True):
                if new_name:
                    save_script_to_file(st.session_state.script_segments, sub_path, new_name)
                    st.session_state.current_script_name = new_name
                    st.toast(f"Đã lưu: {new_name}")
                    st.rerun()

        st.divider()
        
        # 3 NÚT AI NẰM CÙNG MỘT DÒNG
        c1, c2, c3 = st.columns(3)
        
        if c1.button("🎙️ 1. WHISPER BÓC BĂNG", use_container_width=True):
            if os.path.exists(video_raw):
                with st.spinner("Whisper đang nghe..."):
                    raw = ai_studio.transcribe_with_segments(video_raw)
                    if raw:
                        st.session_state.script_segments = [{"start": s['start'], "end": s.get('end', s['start']+2), "text": s.get('text',''), "freeze": False} for s in raw]
                        st.rerun()
            else: st.error("Thiếu video gốc!")

        if c2.button("✨ 2. AI CHUỐT LỜI", use_container_width=True):
            if st.session_state.script_segments:
                with st.spinner("AI đang sửa lỗi theo KnowledgeBase..."):
                    refined = ai_studio.rewrite_segments(st.session_state.script_segments, selected_key)
                    if refined:
                        st.session_state.script_segments = refined
                        st.success("Đã tối ưu lời thoại!")
                        st.rerun()
            else: st.error("Chưa có kịch bản!")

        if c3.button("🎬 3. XUẤT VIDEO FINAL", type="primary", use_container_width=True):
            if st.session_state.script_segments:
                msg = st.empty()
                msg.info("🚀 Đang Render...")
                save_script_to_file(st.session_state.script_segments, sub_path, "Backup_Before_Render")
                success = ai_studio.export_final_video(
                    video_path=video_raw,
                    script_segments=st.session_state.script_segments,
                    output_path=video_final,
                    voice_id=st.session_state.get("selected_voice_id", "vi-VN-HoaiMyNeural")
                )
                if success:
                    msg.empty()
                    st.success("🎉 Xong!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()

    st.divider()

    # --- 5. BỐ CỤC CHÍNH: LỜI THOẠI TRÁI - VIDEO PHẢI ---
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("📝 Lời thoại chi tiết")
        if not st.session_state.script_segments:
            st.info("Chưa có dữ liệu. Hãy chọn bản thảo hoặc bấm bóc băng AI.")
        else:
            for i, seg in enumerate(st.session_state.script_segments):
                with st.container():
                    # Layout dòng segment: Time | Text | Menu
                    s1, s2, s3 = st.columns([0.7, 3, 1.3])
                    s1.markdown(f"**{seg['start']}s**")
                    
                    # Hiển thị text ngắn gọn
                    display_text = seg['text'] if seg['text'] else "..."
                    s2.write(f"{'❄️' if seg.get('freeze') else '▶️'} {display_text}")
                    
                    choice = s3.selectbox(f"M_{i}", ["⚙️", "📝 Chỉnh sửa", "🗑️ Xóa đoạn"], key=f"menu_{i}", label_visibility="collapsed")
                    if choice != "⚙️":
                        handle_action(choice, i)
                    st.divider()

    with col_right:
        st.markdown('<div class="sticky-video">', unsafe_allow_html=True)
        st.subheader("📺 Preview")
        if os.path.exists(video_final):
            st.video(video_final)
            st.success("Video Final đã sẵn sàng")
            if st.button("🗑️ Xóa Video Final để làm lại"):
                os.remove(video_final)
                st.rerun()
        elif os.path.exists(video_raw):
            st.video(video_raw)
            st.caption("📽️ Đang hiển thị Video Gốc (Raw)")
        else:
            st.warning("Không tìm thấy video nào!")
        st.markdown('</div>', unsafe_allow_html=True)