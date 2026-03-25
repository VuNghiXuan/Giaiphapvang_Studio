import streamlit as st
import os
import time
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from models.controller import StudioController
from config import Config

from views.recorder_view import render_recorder
from views.editor_view import render_editor

# 0. KHỞI TẠO HỆ THỐNG & AI
load_dotenv()
ctrl = StudioController()

from core.ai_manager import AIManager
@st.cache_resource
def get_ai_manager():
    return AIManager()
ai_studio = get_ai_manager()

def main():
    st.set_page_config(page_title="Giaiphapvang Studio", layout="wide", page_icon="🎬")

    # --- CSS CUSTOM (GIỮ NGUYÊN CỦA MÀY) ---
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #217346 !important; }
        .stButton > button { background-color: #217346; color: white; border-radius: 6px; }
        .stButton > button:hover { background-color: #d4af37; color: white; }
        </style>
        """, unsafe_allow_html=True)

    # --- QUẢN LÝ ĐIỀU HƯỚNG ---
    if "view" not in st.session_state: st.session_state.view = "dashboard"
    if "active_project" not in st.session_state: st.session_state.active_project = None 
    if "active_sub" not in st.session_state: st.session_state.active_sub = None 
    if 'active_tab' not in st.session_state: st.session_state.active_tab = "Quay màn hình"

    # ==========================================
    # VIEW 1: DASHBOARD (TỔNG KHO)
    # ==========================================
    if st.session_state.view == "dashboard":
        st.title("🚀 TỔNG KHO HƯỚNG DẪN")
        with st.expander("➕ TẠO DỰ ÁN MỚI"):
            c1, c2 = st.columns([3, 1])
            n = c1.text_input("Tên dự án:")
            if c2.button("Tạo ngay", use_container_width=True):
                if n: ctrl.create_tutorial(n); st.rerun()

        st.divider()
        projects = ctrl.get_all_tutorials()
        for p in projects:
            with st.container(border=True):
                col_txt, col_btn = st.columns([3, 2])
                col_txt.subheader(f"📁 {p['title']}")
                
                b1, b2, b3 = col_btn.columns(3)
                if b1.button("📖 Xem", key=f"v_{p['id']}", use_container_width=True):
                    st.session_state.active_project = p
                    st.session_state.view = "sub_category"
                    st.rerun()
                
                with b2.popover("📝 Sửa"):
                    new_t = st.text_input("Tên mới:", value=p['title'], key=f"ren_{p['id']}")
                    if st.button("Lưu", key=f"s_{p['id']}"):
                        ctrl.update_tutorial_title(p['id'], new_t); st.rerun()
                
                with b3.popover("🗑️ Xóa"):
                    if st.button("Xác nhận XÓA", key=f"d_{p['id']}", type="primary"):
                        ctrl.delete_tutorial(p['id'], p['folder_name']); st.rerun()

    # ==========================================
    # VIEW 2: SUB-CATEGORY (BÀI HỌC)
    # ==========================================
    elif st.session_state.view == "sub_category":
        p = st.session_state.active_project
        st.title(f"📚 Dự án: {p['title']}")
        if st.button("⬅️ Quay lại Tổng kho"): st.session_state.view = "dashboard"; st.rerun()

        with st.expander("➕ THÊM BÀI HỌC MỚI"):
            sub_n = st.text_input("Tên bài học:")
            if st.button("Thêm ngay"):
                if sub_n: ctrl.add_sub_content(p['id'], sub_n, p['folder_name']); st.rerun()

        st.divider()
        for s in ctrl.get_sub_contents(p['id']):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"### 📹 {s['sub_title']}")
                if c2.button("🛠️ MỞ STUDIO", key=f"sub_{s['id']}", type="primary"):
                    st.session_state.active_sub = s
                    st.session_state.view = "studio"
                    st.rerun()

    # ==========================================
    # VIEW 3: STUDIO (NƠI CÓ CẤU HÌNH CỦA MÀY)
    # ==========================================
    elif st.session_state.view == "studio":
        p = st.session_state.active_project
        s = st.session_state.active_sub
        sub_path = os.path.join(Config.BASE_STORAGE, p['folder_name'], s['sub_folder'])

        # --- SIDEBAR CẤU HÌNH AI & GIỌNG ĐỌC ---
        with st.sidebar:
            st.markdown(f"### 🎯 Studio: \n**{s['sub_title']}**")
            if st.button("⬅️ THOÁT STUDIO", use_container_width=True):
                st.session_state.view = "sub_category"; st.rerun()
            
            st.divider()
            st.markdown("### 🎙️ Cấu hình Giọng đọc")
            VOICE_OPTIONS = {"Hoài My (Sang trọng)": "vi-VN-HoaiMyNeural", "Nam Minh (Trầm ấm)": "vi-VN-NamMinhNeural"}
            sel_voice = st.selectbox("Giọng AI:", list(VOICE_OPTIONS.keys()))
            st.session_state.selected_voice_id = VOICE_OPTIONS[sel_voice]

            st.markdown("### ⚙️ Cấu hình AI Brain")
            providers = ["Groq", "Gemini", "Ollama"]
            current_p = str(ai_studio.provider).capitalize()
            default_idx = providers.index(current_p) if current_p in providers else 1
            new_p = st.selectbox("Bộ não:", providers, index=default_idx)
            if new_p != ai_studio.provider:
                ai_studio.provider = new_p; st.rerun()

            if st.button("🧹 Dọn dẹp bộ nhớ bài này"):
                # Logic dọn dẹp folder bài học...
                st.success("Đã dọn dẹp!"); st.rerun()

        # --- MENU 3 TAB ---
        titles = ["Quay màn hình", "Biên tập AI", "Kho thành phẩm"]
        curr_index = titles.index(st.session_state.active_tab) if st.session_state.active_tab in titles else 0
        
        selected = option_menu(None, titles, icons=["camera-video", "magic", "archive"], 
                               orientation="horizontal", default_index=curr_index)
        st.session_state.active_tab = selected

        if selected == titles[0]:            
            render_recorder(sub_path)
        elif selected == titles[1]:            
            render_editor(ai_studio, sub_path)
        elif selected == titles[2]:
            out = os.path.join(sub_path, "outputs")
            files = [f for f in os.listdir(out) if f.endswith('.mp4')] if os.path.exists(out) else []
            if not files: st.info("Chưa có video render.")
            for f in files: st.video(os.path.join(out, f))

if __name__ == "__main__":
    main()