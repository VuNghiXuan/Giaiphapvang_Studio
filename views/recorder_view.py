import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh

def render_recorder(sub_path): # Nhận đường dẫn thư mục bài học con
    # --- 0. KHỞI TẠO TRẠNG THÁI ---
    if 'recorder' not in st.session_state:
        from core.recorder import ScreenRecorder
        st.session_state.recorder = ScreenRecorder()
        st.session_state.is_active = False 
    
    # Tên Tab để điều hướng (Phải khớp với main.py)
    TAB_EDITOR = "Biên tập AI"

    # --- FIX LỖI Ở ĐÂY: Đồng bộ tên biến đường dẫn ---
    raw_path = os.path.join(sub_path, "raw") 
    if not os.path.exists(raw_path):
        os.makedirs(raw_path, exist_ok=True)
    
    # File video gốc của bài học này
    video_raw_file = os.path.join(raw_path, "raw_video.mp4")

    # --- 1. CƠ CHẾ SYNC (HEARTBEAT) ---
    if st.session_state.get('is_active', False):
        st_autorefresh(interval=1000, key="recorder_sync_heartbeat")

    # --- 2. KIỂM TRA TRẠNG THÁI KẾT THÚC TỪ WIDGET ---
    if st.session_state.recorder.finished:
        st.session_state.recorder.finished = False 
        st.session_state.is_active = False
        st.toast("✅ Đã lưu video vào thư mục bài học!", icon="🎬")
        
        # Chuyển sang tab biên tập
        st.session_state.active_tab = TAB_EDITOR
        time.sleep(0.5) 
        st.rerun()

    # Xử lý nếu đóng cửa sổ quay bất ngờ
    if st.session_state.is_active:
        if not st.session_state.recorder.recording and st.session_state.recorder.root_control is None:
            st.session_state.is_active = False
            st.rerun()

    # --- 3. GIAO DIỆN KHI ĐANG QUAY ---
    if st.session_state.is_active:
        st.info("💡 **Hệ thống đang chờ lệnh từ Bảng điều khiển nổi...**")
        st.warning("Vui lòng không đóng trình duyệt khi đang quay.")
        st.caption(f"📁 Lưu tại: `{video_raw_file}`")
        
        if st.button("❌ Hủy bỏ và Quay lại", use_container_width=True):
            st.session_state.recorder.stop_recording()
            st.session_state.is_active = False
            st.rerun()
        return 

    # --- 4. CẤU HÌNH TRƯỚC KHI QUAY ---
    with st.expander("🛠️ Cấu hình thông số video", expanded=True):
        c1, c2 = st.columns(2)
        fps = c1.select_slider("Tốc độ (FPS):", options=[15, 20, 24, 30], value=20)
        res_map = {"Full HD (1080p)": (1920, 1080), "HD (720p)": (1280, 720)}
        res_label = c2.selectbox("Độ phân giải:", list(res_map.keys()))
        selected_res = res_map[res_label]

    # --- 5. NÚT MỞ MÁY QUAY ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 MỞ BẢNG ĐIỀU KHIỂN NỔI", type="primary", use_container_width=True):
        # Xóa clip cũ của bài học này để quay mới
        if os.path.exists(video_raw_file):
            try: os.remove(video_raw_file)
            except: pass
        
        st.session_state.recorder.finished = False
        # Kích hoạt Widget nổi với đường dẫn chuẩn của bài học
        st.session_state.recorder.show_floating_control(
            output_path=video_raw_file, 
            fps=float(fps), 
            resolution=selected_res,
            hotkey=None
        )
        
        st.session_state.is_active = True
        st.rerun()

    # --- 6. XEM LẠI CLIP ĐÃ QUAY ---
    if os.path.exists(video_raw_file) and os.path.getsize(video_raw_file) > 1000:
        st.divider()
        st.success("🎥 Clip gốc của bài học đã sẵn sàng!")
        st.video(video_raw_file)
        
        col1, col2 = st.columns(2)
        if col1.button("✨ Tiến hành Biên tập AI", type="primary", use_container_width=True):
            st.session_state.active_tab = TAB_EDITOR
            st.rerun()
        if col2.button("🗑️ Xóa bản quay này", use_container_width=True):
            os.remove(video_raw_file)
            st.rerun()