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
    # --- CSS HACK: Giao diện chuyên nghiệp ---
    st.markdown("""
        <style>
        div[data-testid="column"] { display: flex; align-items: center; }
        .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; }
        .render-box { border: 2px solid #217346; padding: 15px; border-radius: 10px; background: #f0fdf4; }
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

    # --- 3. GIAO DIỆN BIÊN TẬP CHI TIẾT ---
    if st.session_state.editing_index != -1:
        idx = st.session_state.editing_index
        render_segment_editor(idx, st.session_state.script_segments[idx], video_raw, 0)
        if st.button("⬅️ Quay lại danh sách", use_container_width=True):
            st.session_state.editing_index = -1
            st.rerun()
        return 

    # --- 4. THANH CÔNG CỤ (TOOLBAR) ---
    with st.expander("🛠️ QUẢN LÝ KỊCH BẢN & AI", expanded=True):
        # --- THÊM PHẦN CHỌN KỊCH BẢN TỪ KNOWLEDGE BASE ---
        all_scenarios = list(ai_studio.kb.scenarios.keys())
        selected_key = st.selectbox(
            "🎯 Chọn kịch bản hướng dẫn (Form):", 
            all_scenarios, 
            format_func=lambda x: ai_studio.kb.scenarios[x]['title'],
            help="AI sẽ dựa vào kịch bản này để sửa lỗi chính tả và thuật ngữ chuyên môn."
        )

        col_file, col_name, col_btn = st.columns([2, 2, 1])
        # ... (giữ nguyên phần chọn bản thảo và tên phiên bản của mày) ...

        # --- CÁC NÚT BẤM AI ---
        c1, c2, c3 = st.columns(3) # Chia làm 3 cột
        
        if c1.button("🎙️ 1. BÓC BĂNG THÔ", use_container_width=True):
            if os.path.exists(video_raw):
                with st.spinner("Whisper đang nghe..."):
                    raw = ai_studio.transcribe_with_segments(video_raw)
                    if raw:
                        st.session_state.script_segments = [{"start": s['start'], "end": s.get('end', s['start']+2), "text": s.get('text',''), "freeze": False} for s in raw]
                        st.rerun()
            else: st.error("Thiếu video gốc!")

        if c2.button("✨ 2. AI CHUỐT LỜI", type="secondary", use_container_width=True):
            if st.session_state.script_segments:
                with st.spinner(f"AI ({ai_studio.provider}) đang sửa lỗi theo kịch bản..."):
                    # ĐÂY LÀ CHỖ GỌI HÀM THÔNG MINH ĐÂY VŨ!
                    refined = ai_studio.rewrite_segments(
                        segments=st.session_state.script_segments, 
                        scenario_key=selected_key
                    )
                    if refined:
                        st.session_state.script_segments = refined
                        st.success("Đã chuốt lại lời thoại xong!")
                        st.rerun()
            else: st.error("Chưa có kịch bản thô để sửa!")
        
        if c2.button("🎬 XUẤT VIDEO FINAL", type="primary", use_container_width=True):
            if st.session_state.script_segments:
                msg = st.empty()
                msg.info("🚀 Đang Render... Vũ đợi tí!")
                save_script_to_file(st.session_state.script_segments, sub_path, "Auto_Backup_Before_Render")
                
                success = ai_studio.export_final_video(
                    video_path=video_raw,
                    script_segments=st.session_state.script_segments,
                    output_path=video_final,
                    voice_id=st.session_state.get("selected_voice_id", "vi-VN-HoaiMyNeural")
                )
                if success:
                    msg.empty()
                    st.success("🎉 Render xong rồi Vũ ơi!")
                    st.balloons()
                    time.sleep(1) # Chờ file kịp ổn định trên ổ đĩa
                    st.rerun() # Refresh để hiện video mới
            else: st.error("Kịch bản trống!")

    # --- 5. HIỂN THỊ VIDEO THÀNH PHẨM (NẾU CÓ) ---
    if os.path.exists(video_final):
        with st.container():
            st.markdown("### 📺 Video Thành Phẩm")
            st.video(video_final)
            st.caption(f"📍 Vị trí: {video_final}")
    
    st.divider()

    # --- 6. DANH SÁCH PHÂN ĐOẠN ---
    st.subheader("📝 Nội dung chi tiết")
    if st.session_state.script_segments:
        for i, seg in enumerate(st.session_state.script_segments):
            with st.container():
                c1, c2, c3 = st.columns([0.8, 4, 1.2])
                c1.markdown(f"**{seg['start']}s**")
                txt = seg['text'][:70] + "..." if len(seg['text']) > 70 else (seg['text'] or "---")
                c2.write(f"{'❄️' if seg.get('freeze') else '▶️'} {txt}")
                
                choice = c3.selectbox(f"Menu {i}", ["⚙️...", "📝 Chỉnh sửa", "🗑️ Xóa"], key=f"m_{i}", label_visibility="collapsed")
                if choice != "⚙️...": handle_action(choice, i)
                st.divider()