import streamlit as st
import os

def render_segment_editor(index, seg, video_raw, v):
    """Giao diện chi tiết khi bấm vào nút Chỉnh sửa một đoạn"""
    st.markdown(f"### 🛠️ BIÊN TẬP CHI TIẾT: ĐOẠN {index + 1}")
    st.divider()
    
    col_v, col_t = st.columns([1.2, 1])
    
    with col_v:
        # Xem trước đúng đoạn video đó để khớp lời
        if os.path.exists(video_raw):
            # Tính toán thời gian bắt đầu xem trước (lùi lại 0.5s cho dễ nhìn)
            preview_start = max(0, float(seg['start']) - 0.5)
            st.video(video_raw, start_time=int(preview_start))
            st.caption(f"📺 Đang xem trước tại giây thứ: {seg['start']}s")
        else:
            st.error("❌ Không tìm thấy video gốc workspace/raw_video.mp4")

    with col_t:
        with st.form(key=f"form_edit_{v}_{index}"):
            new_start = st.number_input(
                "⏱️ Giây bắt đầu trong Video", 
                value=float(seg['start']), 
                step=0.1
            )
            
            is_freeze = st.toggle(
                "❄️ Đóng băng hình (Freeze Frame)", 
                value=seg.get('freeze', False),
                help="Dừng video tại giây này để chờ AI nói xong mới chạy tiếp."
            )
            
            new_text = st.text_area(
                "🎙️ Nội dung lời thoại AI", 
                value=seg['text'], 
                height=200,
                placeholder="Nhập kịch bản cho đoạn này..."
            )
            
            st.divider()
            c1, c2 = st.columns(2)
            
            # Nút xác nhận trong Form
            submitted = c1.form_submit_button("✅ XÁC NHẬN LƯU", use_container_width=True)
            cancelled = c2.form_submit_button("❌ HỦY BỎ", use_container_width=True)
            
            if submitted:
                st.session_state.script_segments[index]['start'] = round(new_start, 2)
                st.session_state.script_segments[index]['text'] = new_text
                st.session_state.script_segments[index]['freeze'] = is_freeze
                st.session_state.editing_index = -1 # Quay lại mục lục
                st.rerun()
                
            if cancelled:
                st.session_state.editing_index = -1 # Tắt chế độ edit
                # Không cần reset script_segments vì mình dùng st.form, 
                # dữ liệu chưa xác nhận sẽ không được lưu vào session_state
                st.rerun()