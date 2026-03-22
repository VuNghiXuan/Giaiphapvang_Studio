class KnowledgeBase:
    def __init__(self):
        self.software_info = {
            "name": "Giải Pháp Vàng (Giaiphapvang.net)",
            # 1. DANH MỤC CHUẨN (Để AI biết từ đúng)
            "menu_map": {
                "Sidebar": ["Hệ thống", "Danh mục", "Cấu hình", "Báo cáo"],
                "Hệ thống": ["Thông tin công ty", "Chi nhánh", "Nhân viên", "Phân quyền"],
                "Actions": ["Tạo mới", "Lưu", "Xóa", "Sửa", "Tìm kiếm", "Xuất file", "Dấu cộng (+)"]
            },
            # 2. BỘ GIẢI MÃ "TIẾNG NGÁO" (Gom hết đống lỗi vào đây)
            "whisper_decode": {
                "tạm/tào/tạo mạc/tê mắp": "Tạo mới / Thao tác",
                "chi nhắn/tí nhắn/tì nhân/tìm nắng": "Chi nhánh",
                "phòng mềm/giải phép phạm/phát vàng": "Phần mềm Giải Pháp Vàng",
                "spandersider/thanh công cụ": "Sidebar (Thanh menu bên trái)",
                "clip/tạo clip/mắm": "Click / Bấm / Nhấn",
                "giống cặng/dấu cặng": "Dấu cộng (+)",
                "tài mệ/tề nhập": "Trường dữ liệu / Ô nhập liệu",
                "mùa mùa/mùa mười": "10 ký tự (Validation)",
                "xích/hiện ra": "Hiển thị trên danh sách",
                "địa trị/sớm điện thoại": "Địa chỉ / Số điện thoại"
            }
        }

    def get_context(self):
        kb = self.software_info
        ctx = f"Tên phần mềm: {kb['name']}\n"
        ctx += "--- DANH MỤC TỪ ĐIỂN GIẢI MÃ LỖI WHISPER ---\n"
        for error, correct in kb['whisper_decode'].items():
            ctx += f"- Nếu nghe thấy '{error}' thì chắc chắn là: '{correct}'\n"
        
        ctx += "\n--- CẤU TRÚC MENU & TÍNH NĂNG ---\n"
        for menu, items in kb['menu_map'].items():
            ctx += f"- {menu}: {', '.join(items)}\n"
        return ctx