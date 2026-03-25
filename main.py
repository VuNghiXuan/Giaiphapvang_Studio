import streamlit as st
import os
import time
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

# Import các cấu hình và Controller
from models.controller import StudioController
from config import Config
from core.ai_manager import AIManager

# Import các View (Đảm bảo mày đã tách các file này ra thư mục views/)
from views.dashboard_view import render_dashboard
from views.recorder_view import render_recorder
from views.editor_view import render_editor

# --- 0. KHỞI TẠO HỆ THỐNG ---
load_dotenv()
ctrl = StudioController()

@st.cache_resource
def get_ai_manager():
    return AIManager()

ai_studio = get_ai_manager()

def main():
    st.set_page_config(
        page_title="Giaiphapvang Studio", 
        layout="wide", 
        page_icon="🎬"
    )

    # --- 1. CSS CUSTOM: GIAO DIỆN CHUYÊN NGHIỆP ---
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #217346 !important; }
        
        /* Nút bấm Xanh Excel */
        .stButton > button {
            border-radius: 6px;
            background-color: #217346;
            color: white;
            transition: 0.3s all;
        }
        .stButton > button:hover {
            background-color: #d4af37;
            border-color: #d4af37;
        }

        /* Tinh chỉnh khoảng cách nhánh cây Dashboard */
        [data-testid="stVerticalBlock"] > div:has(div.stStatusWidget) {
            margin-left: 2rem;
            border-left: 2px dashed #ddd;
            padding-left: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
    if "view" not in st.session_state: 
        st.session_state.view = "dashboard"
    if "active_project" not in st.session_state: 
        st.session_state.active_project = None 
    if "active_sub" not in st.session_state: 
        st.session_state.active_sub = None 
    if 'active_tab' not in st.session_state: 
        st.session_state.active_tab = "Quay màn hình"

    # ==========================================
    # VIEW 1: DASHBOARD (TỔNG KHO DẠNG CÂY)
    # ==========================================
    if st.session_state.view == "dashboard":
        render_dashboard(ctrl)

    # ==========================================
    # VIEW 2: STUDIO (KHÔNG GIAN LÀM VIỆC CHUYÊN SÂU)
    # ==========================================
    elif st.session_state.view == "studio":
        p = st.session_state.active_project
        s = st.session_state.active_sub
        
        # Đường dẫn vật lý đến thư mục bài học hiện tại
        sub_path = os.path.join(Config.BASE_STORAGE, p['folder_name'], s['sub_folder'])

        # --- SIDEBAR: ĐIỀU KHIỂN BỘ NÃO & GIỌNG NÓI ---
        with st.sidebar:
            st.success(f"📁 Dự án: **{p['title']}**")
            st.info(f"📹 Bài: **{s['sub_title']}**")
            
            if st.button("⬅️ THOÁT STUDIO", use_container_width=True, type="primary"):
                st.session_state.view = "dashboard"
                st.rerun()
            
            st.divider()
            
            # CẤU HÌNH GIỌNG ĐỌC
            st.markdown("### 🎙️ Giọng đọc AI")
            VOICE_OPTIONS = {
                "Hoài My (Sang trọng)": "vi-VN-HoaiMyNeural",
                "Nam Minh (Trầm ấm)": "vi-VN-NamMinhNeural"
            }
            sel_voice = st.selectbox("Chọn giọng:", list(VOICE_OPTIONS.keys()))
            st.session_state.selected_voice_id = VOICE_OPTIONS[sel_voice]

            # CẤU HÌNH BỘ NÃO (LLM)
            st.markdown("### ⚙️ AI Brain")
            providers = ["Groq", "Gemini", "Ollama"]
            # Ép kiểu provider hiện tại để match với list chọn
            current_p = str(ai_studio.provider).capitalize()
            default_idx = providers.index(current_p) if current_p in providers else 1
            
            new_p = st.selectbox("Chọn não:", providers, index=default_idx)
            if new_p.lower() != str(ai_studio.provider).lower():
                ai_studio.provider = new_p.lower()
                st.rerun()

            st.divider()
            if st.button("🧹 Dọn dẹp Workspace", use_container_width=True):
                # Chỉ dọn dẹp folder workspace tạm, không xóa video đã quay
                st.toast("Đã làm sạch bộ nhớ tạm!")

        # --- STUDIO TABS: 3 BƯỚC QUY TRÌNH ---
        titles = ["Quay màn hình", "Biên tập AI", "Kho thành phẩm"]
        icons = ["camera-video", "magic", "archive"]
        
        # Xác định tab mặc định (để recorder có thể nhảy sang editor)
        try:
            curr_idx = titles.index(st.session_state.active_tab)
        except:
            curr_idx = 0

        selected = option_menu(
            menu_title=None,
            options=titles,
            icons=icons,
            orientation="horizontal",
            default_index=curr_idx,
            styles={
                "container": {"padding": "0px", "border-bottom": "2px solid #217346"},
                "nav-link-selected": {"background-color": "#217346"},
            }
        )
        st.session_state.active_tab = selected

        st.markdown("<br>", unsafe_allow_html=True)

        # --- NỘI DUNG TỪNG TAB ---
        if selected == titles[0]:
            # Tab 1: Gọi recorder và truyền path bài học
            render_recorder(sub_path)
            
        elif selected == titles[1]:
            # Tab 2: Gọi editor, truyền bộ não AI và path bài học
            render_editor(ai_studio, sub_path)
            
        elif selected == titles[2]:
            # Tab 3: Hiển thị các video đã render xong của bài học này
            st.subheader(f"📦 Thành phẩm của: {s['sub_title']}")
            output_dir = os.path.join(sub_path, "outputs")
            if not os.path.exists(output_dir): 
                os.makedirs(output_dir, exist_ok=True)
            
            files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
            
            if not files:
                st.info("Chưa có video hoàn chỉnh. Hãy sang tab Biên tập để xuất video!")
            else:
                cols = st.columns(2)
                for i, file in enumerate(files):
                    with cols[i % 2]:
                        st.video(os.path.join(output_dir, file))
                        st.caption(f"🔥 File: {file}")

if __name__ == "__main__":
    main()