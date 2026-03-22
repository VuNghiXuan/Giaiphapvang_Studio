import streamlit as st
import os
import time 

def render_recorder():
    if 'recorder' not in st.session_state:
        from core.recorder import ScreenRecorder # Kiểm tra lại tên file core cho đúng
        st.session_state.recorder = ScreenRecorder()
        st.session_state.is_recording = False

    st.subheader("⏺️ Trạm quay màn hình (Camtasia Mini)")

    # 1. KHỞI TẠO ĐƯỜNG DẪN
    workspace = "workspace"
    os.makedirs(workspace, exist_ok=True)
    video_raw = os.path.join(workspace, "raw_video.mp4") # Khuyên dùng .mp4 luôn cho nhẹ và chuẩn web
    audio_raw = os.path.join(workspace, "raw_audio.wav")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        if not st.session_state.is_recording:
            if st.button("🔴 BẮT ĐẦU QUAY", type="primary", use_container_width=True):
                try:
                    os.makedirs("workspace", exist_ok=True)
                    
                    # CÁCH FIX AN TOÀN: Thử xóa, nếu không được thì thôi (không làm sập App)
                    if os.path.exists(video_raw):
                        try:
                            os.remove(video_raw)
                        except OSError:
                            # Nếu file bị khóa, mình đổi tên file mới luôn để né lỗi
                            video_raw = os.path.join("workspace", f"raw_video_{int(time.time())}.mp4")
                    
                    # Gọi quay phim
                    st.session_state.recorder.start_recording(
                        output_path=video_raw, 
                        fps=20.0, 
                        resolution=(1920, 1080)
                    )
                    
                    st.session_state.is_recording = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khởi động: {e}")
        else:
            if st.button("⏹️ DỪNG QUAY", use_container_width=True):
                # Lưu ý: Nếu mày dùng phím Pause để dừng thì code recorder đã tự dừng rồi
                # Nút này chỉ để cập nhật trạng thái UI thôi
                st.session_state.is_recording = False
                st.success("Đã dừng quay. Đang xử lý dữ liệu...")
                st.rerun()

    # 2. HIỂN THỊ TRẠNG THÁI & KẾT QUẢ
    if st.session_state.is_recording:
        st.warning("⚠️ ĐANG GHI HÌNH... Nhấn phím **'Pause'** trên bàn phím để Kết thúc.")
    else:
        if os.path.exists(video_raw) and os.path.getsize(video_raw) > 1024:
            st.success(f"✅ Đã ghi thành công: {os.path.basename(video_raw)}")
            
            if st.button("📂 Mở thư mục chứa Video"):
                os.startfile(os.path.abspath(workspace))
            
            with st.expander("📺 Xem lại clip vừa quay", expanded=True):
                st.video(video_raw)