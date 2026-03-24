
import os
import edge_tts
import json
from datetime import datetime

VOICE_OPTIONS = {
    "Nam Minh (Trầm ấm)": "vi-VN-NamMinhNeural",
    "Hoài My (Sang trọng)": "vi-VN-HoaiMyNeural",
    "Thành Lung (Trẻ trung)": "vi-VN-ThanhLungNeural",
    "Duy Phan (Mạnh mẽ)": "vi-VN-DuyPhanNeural"
}

# --- HÀM HỖ TRỢ QUẢN LÝ FILE KỊCH BẢN ---
def save_script_to_file(text, version_name):
    """Lưu lời thoại vào thư mục workspace/scripts"""
    folder = "workspace/scripts"
    os.makedirs(folder, exist_ok=True)
    # Loại bỏ ký tự đặc biệt trong tên file
    safe_name = "".join([c for c in version_name if c.isalnum() or c in (' ', '_')]).strip()
    file_path = os.path.join(folder, f"{safe_name}.json")
    
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": text
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path

def get_list_scripts():
    """Lấy danh sách các bản lưu kịch bản"""
    folder = "workspace/scripts"
    if not os.path.exists(folder):
        return []
    files = [f.replace(".json", "") for f in os.listdir(folder) if f.endswith(".json")]
    return sorted(files, reverse=True)

async def generate_voice(text, output_path):
    voice = "vi-VN-HoaiMyNeural"
    # rate="+0%" để nghe thong thả, rõ ràng theo ý mày
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save(output_path)