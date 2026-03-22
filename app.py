import streamlit as st
import os
from core.ai_manager import AIManager
from gui.recorder import render_recorder
from gui.editor import render_editor

# 1. Khởi tạo môi trường thư mục
for p in ["workspace", "outputs", "assets"]:
    os.makedirs(p, exist_ok=True)

st.set_page_config(
    page_title="Giaiphapvang Studio", 
    layout="wide", 
    page_icon="🎬"
)

# 2. Khởi tạo bộ não AI (Dùng cache để không load lại mỗi khi chuyển tab)
@st.cache_resource
def get_ai_manager():
    return AIManager()

ai_studio = get_ai_manager()

# 3. Giao diện chính
st.title("🎥 Giaiphapvang AI Video Studio")
st.caption("Quy trình chuẩn: Quay màn hình ➡️ Biên soạn AI ➡️ Lồng tiếng & Render")

# 4. CHIA TAB Ở ĐÂY
tab1, tab2, tab3 = st.tabs(["⏺️ BƯỚC 1: QUAY MÀN HÌNH", "✍️ BƯỚC 2: BIÊN TẬP AI", "📁 BƯỚC 3: QUẢN LÝ THÀNH PHẨM"])

with tab1:
    st.info("Mẹo: Hãy chạy Terminal quyền Admin để quay được phần mềm Giaiphapvang.net")
    render_recorder()

with tab2:
    # Truyền ai_studio vào để xử lý kịch bản
    render_editor(ai_studio)

with tab3:
    st.subheader("📦 Kho lưu trữ Video đã Render")
    output_dir = "outputs"
    files = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.avi'))]
    
    if not files:
        st.write("Chưa có video thành phẩm nào. Hãy hoàn thành Bước 2 nhé!")
    else:
        for file in files:
            with st.expander(f"🎬 {file}"):
                st.video(os.path.join(output_dir, file))
                # Nút tải về cho tiện
                with open(os.path.join(output_dir, file), "rb") as v_file:
                    st.download_button(
                        label="📥 Tải video về máy",
                        data=v_file,
                        file_name=file,
                        mime="video/mp4"
                    )

# 5. Thanh Sidebar cấu hình
st.sidebar.markdown("### ⚙️ Cấu hình hệ thống")
st.sidebar.divider()
st.sidebar.success(f"🤖 AI: {os.getenv('DEFAULT_PROVIDER')}")
st.sidebar.warning(f"📚 Data: {os.getenv('KNOWLEDGE_MODE')}")

if st.sidebar.button("🧹 Dọn dẹp Workspace"):
    # Xóa các file nháp trong workspace để làm lại từ đầu
    for f in os.listdir("workspace"):
        os.remove(os.path.join("workspace", f))
    st.sidebar.write("Đã dọn dẹp sạch sẽ!")