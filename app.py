import streamlit as st
import os
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import time

# 0. Cấu hình hệ thống
load_dotenv()
for p in ["workspace", "outputs", "assets"]:
    os.makedirs(p, exist_ok=True)

st.set_page_config(
    page_title="Giaiphapvang Studio", 
    layout="wide", 
    page_icon="🎬"
)

# --- CSS CUSTOM: FIX GIẬT & ĐẸP ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Khử hiệu ứng fade khi chuyển tab của Streamlit */
    .stApp [data-testid="stVerticalBlock"] {
        animation: none !important;
    }

    /* Khối nội dung chính */
    div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #eef0f2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    /* Nút bấm Xanh Excel */
    .stButton > button {
        border-radius: 6px;
        border: none;
        height: 3em;
        background-color: #217346;
        color: white;
        font-weight: 500;
        transition: 0.2s all;
    }
    .stButton > button:hover {
        background-color: #d4af37;
        color: white;
    }

    /* Tiêu đề */
    h1, h2, h3 { color: #217346 !important; }
    
    /* Tinh chỉnh thanh Menu để không bị nháy */
    .nav-link { 
        font-weight: 400 !important; 
        border-radius: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo AI Manager
from core.ai_manager import AIManager
@st.cache_resource
def get_ai_manager():
    return AIManager()
ai_studio = get_ai_manager()

# --- 1. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")
    providers = ["Groq", "Gemini", "Ollama"]
    
    # --- CHỖ SỬA QUAN TRỌNG: Tự động khớp provider ---
    # Lấy provider từ máy, ép về kiểu chữ viết hoa đầu (VD: gemini -> Gemini)
    current_p_raw = str(ai_studio.provider).strip().capitalize()
    
    # Nếu provider trong .env là 'gemini-2.5-flash' thì vẫn coi là 'Gemini'
    if "Groq" in current_p_raw:
        current_p = "Groq"
    elif "Gemini" in current_p_raw:
        current_p = "Gemini"
    
    elif "Ollama" in current_p_raw:
        current_p = "Ollama"
    else:
        current_p = providers[0]

    # Tìm index an toàn
    try:
        default_idx = providers.index(current_p)
    except ValueError:
        default_idx = 0 # Mặc định chọn Gemini nếu có lỗi
        
    new_provider = st.selectbox("AI Brain:", providers, index=default_idx)
    
    if new_provider != ai_studio.provider:
        ai_studio.provider = new_provider
        st.rerun()
    # ----------------------------------------------
    
    st.divider()
    if st.button("🧹 Xóa bộ nhớ tạm", use_container_width=True):
        # Dọn dẹp file trong workspace
        for f in os.listdir("workspace"):
            try: 
                file_path = os.path.join("workspace", f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except: pass
        # Xóa kịch bản cũ trong session để tránh lỗi render cũ
        if 'script_segments' in st.session_state:
            del st.session_state.script_segments
        st.success("Đã dọn dẹp!")
        st.rerun()

# --- 2. THANH TAB (ĐÃ BỔ SUNG LOGIC NHẢY TAB) ---
titles = ["Quay màn hình", "Biên tập AI", "Kho thành phẩm"]
icons = ["camera-video", "magic", "archive"]

# BỔ SUNG: Tính toán index hiện tại từ session_state (do recorder_gui.py thay đổi)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = titles[0]

try:
    curr_index = titles.index(st.session_state.active_tab)
except ValueError:
    curr_index = 0

# CẬP NHẬT: Thêm default_index vào option_menu
selected = option_menu(
    menu_title=None,
    options=titles,
    icons=icons,
    menu_icon="cast",
    orientation="horizontal",
    default_index=curr_index, # <-- Chỗ bổ sung quan trọng nhất
    styles={
        "container": {"padding": "0px", "background-color": "white", "border-radius": "0px", "border-bottom": "2px solid #217346"},
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#f1f3f4", "color": "#495057"},
        "nav-link-selected": {"background-color": "#217346", "color": "white", "border-radius": "0px"},
    },
    key="main_menu_key" 
)

# Luôn đồng bộ lại session_state khi người dùng click thủ công
st.session_state.active_tab = selected

st.markdown("<br>", unsafe_allow_html=True)

# --- 3. NỘI DUNG TỪNG TAB ---
from gui.recorder_gui import render_recorder

if selected == titles[0]:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("⏺️ Ghi hình màn hình")
        render_recorder()
    with col2:
        st.subheader("📝 Hướng dẫn")
        st.info("""
        1. Click **Mở bảng điều khiển**.
        2. Thực hiện quay trên Widget nổi.
        3. Sau khi STOP, hệ thống sẽ tự nhảy sang tab **Biên tập AI**.
        """)

elif selected == titles[1]:
    st.subheader("✍️ Trình biên tập nội dung AI (Theo Timeline)")
    video_raw = "workspace/raw_video.mp4"
    audio_raw = "workspace/raw_video.wav" # Ưu tiên file wav thu từ mic
    
    if os.path.exists(video_raw):
        col_v, col_e = st.columns([1, 1])
        with col_v:
            st.video(video_raw)
            st.caption("Bản quay màn hình thô")
        
        with col_e:
            st.markdown("#### 🚀 Quy trình xử lý khớp lệnh")
            
            # --- BƯỚC 1: TRÍCH XUẤT THEO TIMELINE ---
            if st.button("🎙️ 1. Phân tích Timeline & Biên tập", use_container_width=True):
                with st.spinner("🤖 AI đang phân tích từng giây mày nói..."):
                    # 1. Gọi Whisper lấy segments (mốc thời gian)
                    # Nếu có file wav thì dùng wav, không thì dùng mp4
                    path_to_listen = audio_raw if os.path.exists(audio_raw) else video_raw
                    raw_segments = ai_studio.transcribe_with_segments(path_to_listen)
                    
                    if raw_segments:
                        # 2. Gọi AI Rewrite dựa trên kiến thức hệ thống và mốc thời gian
                        refined_segments = ai_studio.rewrite_segments(raw_segments)
                        st.session_state.script_segments = refined_segments
                        st.success("Đã phân tích xong Timeline!")
                    else:
                        st.error("Không nghe thấy lời thoại nào trong video!")

            # --- BƯỚC 2: HIỂN THỊ Ô CHỈNH SỬA THEO ĐOẠN ---
            if 'script_segments' in st.session_state and st.session_state.script_segments:
                st.markdown("---")
                st.write("📝 **Hiệu chỉnh lời thoại (Khớp theo giây):**")
                
                updated_segments = []
                # Hiển thị từng đoạn để user sửa
                for i, seg in enumerate(st.session_state.script_segments):
                    with st.expander(f"Đoạn {i+1}: {seg['start']}s -> {seg['end']}s", expanded=True):
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            # Cho phép sửa nhẹ mốc thời gian nếu muốn
                            new_start = st.number_input("Bắt đầu", value=float(seg['start']), key=f"s_{i}", step=0.1)
                            new_end = st.number_input("Kết thúc", value=float(seg['end']), key=f"e_{i}", step=0.1)
                        with c2:
                            new_text = st.text_area("Lời thoại AI đề xuất", value=seg['text'], key=f"t_{i}", height=100)
                        
                        updated_segments.append({"start": new_start, "end": new_end, "text": new_text})
                
                # Lưu lại dữ liệu đã sửa vào session_state
                st.session_state.script_segments = updated_segments

                st.markdown("---")
                # --- BƯỚC 3: RENDER VIDEO CUỐI CÙNG ---
                if st.button("🎬 2. Xuất video thành phẩm", type="primary", use_container_width=True):
                    with st.spinner("🎬 Đang lồng ghép audio vào đúng Timeline..."):
                        output_path = f"outputs/final_{int(time.time())}.mp4"
                        
                        # Gọi hàm render theo từng segment
                        success = ai_studio.export_final_video(
                            video_path=video_raw, 
                            script_segments=st.session_state.script_segments, 
                            output_path=output_path
                        )
                        
                        if success:
                            st.balloons()
                            st.success(f"Đã xuất bản: {output_path}")
                            st.video(output_path)
                        else:
                            st.error("Lỗi trong quá trình trộn audio vào Timeline!")
    else:
        st.warning("Chưa có video thô. Hãy quay phim ở tab đầu tiên.")

elif selected == titles[2]:
    st.subheader("📦 Kho thành phẩm")
    output_dir = "outputs"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    files = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.avi'))]
    
    if not files:
        st.info("Chưa có video nào được lưu.")
    else:
        cols = st.columns(3)
        for i, file in enumerate(files):
            with cols[i % 3]:
                st.video(os.path.join(output_dir, file))
                st.caption(file)