import streamlit as st
import os
import time
from streamlit_autorefresh import st_autorefresh # Đảm bảo đã: pip install streamlit-autorefresh

def render_recorder():
    # --- 0. KHỞI TẠO TRẠNG THÁI ---
    if 'recorder' not in st.session_state:
        from core.recorder import ScreenRecorder
        st.session_state.recorder = ScreenRecorder()
        st.session_state.is_active = False 
    
    # Tên Tab phải khớp 100% với list titles trong app.py
    TAB_EDITOR = "Biên tập AI"

    # --- 1. CƠ CHẾ "ĐÁNH THỨC" STREAMLIT (QUAN TRỌNG) ---
    # Khi đang mở bảng điều khiển nổi, cứ 1 giây Streamlit sẽ tự kiểm tra recorder.finished 1 lần
    if st.session_state.get('is_active', False):
        st_autorefresh(interval=1000, key="recorder_sync_heartbeat")

    # --- 2. LOGIC TỰ ĐỘNG NHẬN DIỆN KHI NHẤN STOP TRÊN WIDGET ---
    if st.session_state.recorder.finished:
        # Reset trạng thái ngay lập tức để tránh loop
        st.session_state.recorder.finished = False 
        st.session_state.is_active = False
        
        # Thông báo cho người dùng
        st.toast("✅ Đã lưu video thành công!", icon="🎬")
        
        # Tự động nhảy sang tab Biên tập
        st.session_state.active_tab = TAB_EDITOR
        
        # Nghỉ một chút để người dùng kịp nhìn thấy Toast rồi mới load tab mới
        time.sleep(0.5) 
        st.rerun()

    # Kiểm tra nếu Widget bị đóng bất ngờ (không nhấn stop mà tắt hẳn cửa sổ Tkinter)
    if st.session_state.is_active:
        if not st.session_state.recorder.recording and st.session_state.recorder.root_control is None:
            st.session_state.is_active = False
            st.rerun()

    # --- 3. GIAO DIỆN KHI ĐANG QUAY (MÀN HÌNH CHỜ) ---
    if st.session_state.is_active:
        st.info("💡 **Hệ thống đang hoạt động...**")
        st.warning("Vui lòng thực hiện thao tác trên **Bảng điều khiển nổi** vừa xuất hiện.")
        
        # Nút cứu cánh nếu người dùng muốn hủy quay ngay từ web
        if st.button("❌ Hủy bỏ và Quay lại cấu hình", use_container_width=True):
            st.session_state.recorder.stop_recording()
            st.session_state.is_active = False
            st.rerun()
        return 

    # --- 4. GIAO DIỆN CẤU HÌNH (KHI CHƯA QUAY) ---
    with st.expander("🛠️ Cấu hình kỹ thuật", expanded=True):
        col_fps, col_res = st.columns(2)
        with col_fps:
            fps_option = st.select_slider("Tốc độ khung hình (FPS):", options=[10, 15, 20, 24, 30, 60], value=20)
        with col_res:
            res_map = {"4K": (3840, 2160), "Full HD": (1920, 1080), "HD": (1280, 720)}
            res_label = st.selectbox("Độ phân giải video:", list(res_map.keys()), index=1)
            selected_res = res_map[res_label]

    workspace = "workspace"
    os.makedirs(workspace, exist_ok=True)
    video_raw = os.path.join(workspace, "raw_video.mp4")

    # --- 5. NÚT KÍCH HOẠT QUAY ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 MỞ BẢNG ĐIỀU KHIỂN NỔI", type="primary", use_container_width=True):
        # Dọn dẹp file cũ nếu có
        if os.path.exists(video_raw):
            try: os.remove(video_raw)
            except: pass
        
        # Gọi engine quay hình
        st.session_state.recorder.finished = False
        st.session_state.recorder.show_floating_control(
            output_path=video_raw, 
            fps=float(fps_option), 
            resolution=selected_res,
            hotkey=None 
        )
        
        # Kích hoạt trạng thái hoạt động
        st.session_state.is_active = True
        st.rerun()

    # --- 6. XEM TRƯỚC (NẾU CÓ FILE TRONG BỘ NHỚ TẠM) ---
    if os.path.exists(video_raw) and os.path.getsize(video_raw) > 5000:
        st.divider()
        st.success("🎥 Bản ghi gần nhất đã sẵn sàng!")
        st.video(video_raw)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✨ Tiến hành Biên tập AI", type="primary", use_container_width=True):
                st.session_state.active_tab = TAB_EDITOR
                st.rerun()
        with col_btn2:
            if st.button("🗑️ Xóa bản quay này", use_container_width=True):
                os.remove(video_raw)
                st.rerun()