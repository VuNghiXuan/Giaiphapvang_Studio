import streamlit as st
import os
from config import Config

def get_status_info(sub_path, manual_status=None):
    """Kiểm tra trạng thái bài học dựa trên DB hoặc file vật lý"""
    if manual_status:
        status_map = {
            "Chưa quay": ("🔴 Chưa quay", "#6c757d"),
            "Đã quay": ("🟡 Đã quay", "#d4af37"),
            "Hoàn chỉnh": ("🟢 Hoàn chỉnh", "#217346")
        }
        return status_map.get(manual_status, ("🔴 Chưa quay", "#6c757d"))

    raw_file = os.path.join(sub_path, "raw", "raw_video.mp4")
    output_dir = os.path.join(sub_path, "outputs")
    has_output = os.path.exists(output_dir) and any(f.endswith('.mp4') for f in os.listdir(output_dir))
    has_raw = os.path.exists(raw_file)

    if has_output: return "🟢 Hoàn chỉnh", "#217346"
    if has_raw: return "🟡 Đã quay", "#d4af37"
    return "🔴 Chưa quay", "#6c757d"

def render_dashboard(ctrl):
    # --- SIDEBAR: HỆ THỐNG & ĐIỀU HƯỚNG ---
    with st.sidebar:
        # Nút thoát Studio (Chỉ hiện khi đang ở view studio)
        if st.session_state.get('view') == "studio":
            if st.button("⬅️ THOÁT STUDIO", use_container_width=True, type="primary"):
                st.session_state.view = "dashboard"
                st.session_state.active_project = None
                st.session_state.active_sub = None
                st.rerun()
            st.divider()

        st.markdown("### 🛠️ Hệ thống")
        if st.button("🔄 LÀM MỚI DANH MỤC", use_container_width=True):
            st.rerun()

    # --- NỘI DUNG CHÍNH ---
    st.title("🚀 TỔNG KHO HƯỚNG DẪN")
    
    # 1. Tạo dự án mới
    with st.expander("➕ TẠO DỰ ÁN MỚI", expanded=False):
        c1, c2 = st.columns([3, 1])
        n = c1.text_input("Tên dự án:", placeholder="Nhập tên dự án...", key="new_proj_name")
        if c2.button("Tạo ngay", use_container_width=True):
            if n: 
                ctrl.create_tutorial(n)
                st.rerun()

    st.divider()

    # 2. Hiển thị danh sách dự án
    projects = ctrl.get_all_tutorials()
    total_projects = len(projects)

    for p_idx, p in enumerate(projects):
        with st.container(border=True):
            col_p_title, col_p_opt = st.columns([4.2, 0.8])
            col_p_title.markdown(f"### 📁 {p['title']}")
            
            # Popover quản lý dự án (Đổi tên, Di chuyển, Thêm bài, Xóa)
            with col_p_opt.popover("⚙️", use_container_width=True):
                st.subheader("Quản lý Dự án")
                
                # Di chuyển thứ tự dự án lớn
                st.write("Thứ tự dự án:")
                m_p1, m_p2 = st.columns(2)
                if m_p1.button("🔼 Lên", key=f"up_p_{p['id']}", disabled=(p_idx == 0)):
                    ctrl.move_tutorial(p['id'], "up")
                    st.rerun()
                if m_p2.button("🔽 Xuống", key=f"down_p_{p['id']}", disabled=(p_idx == total_projects - 1)):
                    ctrl.move_tutorial(p['id'], "down")
                    st.rerun()

                st.divider()

                # Sửa tên dự án
                new_p_title = st.text_input("Đổi tên dự án:", value=p['title'], key=f"edit_p_t_{p['id']}")
                if st.button("💾 LƯU TÊN MỚI", key=f"btn_p_upd_{p['id']}", use_container_width=True):
                    ctrl.update_tutorial_title(p['id'], new_p_title)
                    st.rerun()

                st.divider()

                # Thêm hướng dẫn con
                sub_n = st.text_input("Tên hướng dẫn mới:", key=f"add_in_{p['id']}")
                if st.button("➕ Thêm hướng dẫn", key=f"btn_add_{p['id']}", use_container_width=True):
                    if sub_n: 
                        ctrl.add_sub_content(p['id'], sub_n, p['folder_name'])
                        st.rerun()

                st.divider()

                # Xóa dự án
                if st.button("🗑️ XÓA DỰ ÁN", key=f"del_p_{p['id']}", type="primary", use_container_width=True):
                    ctrl.delete_tutorial(p['id'], p['folder_name'])
                    st.rerun()

            # --- HIỂN THỊ CÁC BÀI HỌC TRONG DỰ ÁN ---
            sub_contents = ctrl.get_sub_contents(p['id'])
            total_subs = len(sub_contents)
            
            for idx, s_row in enumerate(sub_contents):
                s = dict(s_row) 
                sub_path = os.path.join(Config.BASE_STORAGE, p['folder_name'], s['sub_folder'])
                label, color = get_status_info(sub_path, s.get('status'))
                
                st.markdown("---")
                c_icon, c_name, c_status, c_studio, c_opt = st.columns([0.2, 3, 1, 1.2, 0.6])
                
                c_icon.markdown("<div style='margin-top:5px'>└─ 📹</div>", unsafe_allow_html=True)
                c_name.markdown(f"<div style='margin-top:5px'><b>{s['sub_title']}</b></div>", unsafe_allow_html=True)
                
                c_status.markdown(f"""<div style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; text-align: center; width: 95px; margin-top:8px;">{label}</div>""", unsafe_allow_html=True)
                
                # Nút vào Studio quay phim
                if c_studio.button("🛠️ STUDIO", key=f"st_{s['id']}", use_container_width=True, type="primary"):
                    st.session_state.active_project = p
                    st.session_state.active_sub = s
                    st.session_state.view = "studio"
                    st.rerun()
                
                # Cài đặt bài học (Di chuyển, Sửa, Xóa)
                with c_opt.popover("⚙️", use_container_width=True):
                    st.subheader("Cài đặt bài")
                    m1, m2 = st.columns(2)
                    if m1.button("🔼 Lên", key=f"up_{s['id']}", disabled=(idx == 0)):
                        ctrl.move_sub_content(s['id'], "up")
                        st.rerun()
                    if m2.button("🔽 Xuống", key=f"down_{s['id']}", disabled=(idx == total_subs - 1)):
                        ctrl.move_sub_content(s['id'], "down")
                        st.rerun()
                    
                    st.divider()
                    status_list = ["Chưa quay", "Đã quay", "Hoàn chỉnh"]
                    curr_st = s.get('status', "Chưa quay")
                    new_st = st.selectbox("Trạng thái:", status_list, index=status_list.index(curr_st) if curr_st in status_list else 0, key=f"sel_st_{s['id']}")
                    new_sub_name = st.text_input("Tên bài:", value=s['sub_title'], key=f"txt_{s['id']}")
                    
                    if st.button("💾 LƯU", key=f"upd_{s['id']}", use_container_width=True):
                        ctrl.update_sub_content(s['id'], new_sub_name, new_st)
                        st.rerun()
                    
                    st.divider()
                    if st.button("🗑️ XÓA BÀI NÀY", key=f"del_s_{s['id']}", type="primary", use_container_width=True):
                        ctrl.delete_sub_content(s['id'], p['folder_name'], s['sub_folder'])
                        st.rerun()