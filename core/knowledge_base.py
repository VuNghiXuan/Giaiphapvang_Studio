class KnowledgeBase:
    def __init__(self):
        # 1. Thông tin chung toàn hệ thống (Dùng cho mọi clip)
        self.common_info = {
            "brand": "Phần mềm Giải Pháp Vàng (Giaiphapvang.net)",
            "whisper_fix": {
                "tạm/tào/tạo mạc": "Tạo mới",
                "giải phép phạm/phát vàng": "Phần mềm Giải Pháp Vàng",
                "clip/mắm": "Click / Bấm",
                "xích": "Hiển thị danh sách"
            }
        }

        # 2. Chi tiết từng Form/Tính năng (Mỗi clip sẽ chọn 1 cái này)
        self.scenarios = {
            "danh_muc_chi_nhanh": {
                "title": "Hướng dẫn quản lý Chi nhánh",
                "fields": ["Mã chi nhánh", "Tên chi nhánh", "Địa chỉ", "Số điện thoại", "Người quản lý"],
                "logic": "Mã chi nhánh không được trùng, Số điện thoại phải đủ 10 số",
                "actions": ["Bấm dấu cộng để thêm", "Nhấn Lưu để hoàn tất"],
                "keywords": ["tí nhắn", "tìm nắng", "địa trị", "sớm điện thoại"] # Lỗi đặc thù của clip này
            },
            "nhap_kho_nu_trang": {
                "title": "Hướng dẫn Nhập kho Nữ trang",
                "fields": ["Mã vạch", "Tên hàng", "Trọng lượng", "Tiền công", "Hàm lượng"],
                "logic": "Trọng lượng tính bằng chỉ, Tiền công nhập số dương",
                "keywords": ["trọng lượn", "tiền cộng", "hàm lượn", "mã vẹt"]
            }
        }

    def get_prompt_for_clip(self, scenario_key):
        """
        Hàm này sẽ tạo ra một Prompt 'May đo' riêng cho từng clip
        """
        common = self.common_info
        # Lấy dữ liệu của scenario cụ thể, nếu không có thì lấy rỗng
        scene = self.scenarios.get(scenario_key, {})
        
        if not scene:
            return "Cần cung cấp scenario_key hợp lệ."

        prompt = f"""
        Mày là chuyên gia biên tập kịch bản cho {common['brand']}.
        Nhiệm vụ: Chỉnh sửa bản bóc băng cho clip: '{scene['title']}'.
        
        SỬA LỖI WHISPER (Dựa trên từ điển):
        {self._format_dict(common['whisper_fix'])}
        
        NGỮ CẢNH RIÊNG CỦA CLIP NÀY (Các trường dữ liệu & Logic):
        - Các ô nhập liệu: {', '.join(scene['fields'])}
        - Logic cần nhớ: {scene['logic']}
        - Từ lỗi hay gặp trong clip này: {', '.join(scene['keywords'])}
        
        YÊU CẦU:
        1. Nếu thấy từ lỗi, phải sửa thành từ đúng trong danh sách ô nhập liệu.
        2. Văn phong chuyên nghiệp, dễ hiểu, phù hợp để AI Voice đọc.
        3. Giữ nguyên cấu trúc JSON và mốc thời gian.
        """
        return prompt

    def _format_dict(self, d):
        return "\n".join([f"- Nghe '{k}' -> Sửa thành '{v}'" for k, v in d.items()])