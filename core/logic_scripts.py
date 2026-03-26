import os
import json
from datetime import datetime
import edge_tts

def get_lesson_scripts_dir(sub_path):
    """
    Trả về đường dẫn thư mục 'scripts' nằm trong bài học.
    sub_path: storage/Dự_án_A/Bài_1
    """
    path = os.path.join(sub_path, "scripts")
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def get_list_scripts_in_lesson(sub_path):
    """Lấy danh sách các file kịch bản của riêng bài học này"""
    folder = get_lesson_scripts_dir(sub_path)
    # Lấy các file .json và trả về tên file (không kèm đuôi)
    files = [f.replace(".json", "") for f in os.listdir(folder) if f.endswith(".json")]
    # Xếp mới nhất lên đầu dựa trên thời gian chỉnh sửa file
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x + ".json")), reverse=True)
    return files

def save_script_to_file(segments, sub_path, version_name):
    """
    Lưu kịch bản vào thư mục scripts của bài học.
    version_name: Tên phiên bản (vd: 'Ban_nhap_1', 'AI_Gen')
    """
    folder = get_lesson_scripts_dir(sub_path)
    
    # Làm sạch tên file để tránh ký tự đặc biệt
    safe_name = "".join([c for c in version_name if c.isalnum() or c in (' ', '_', '-')]).strip()
    if not safe_name: 
        safe_name = f"script_{datetime.now().strftime('%H%M%S')}"
    
    file_path = os.path.join(folder, f"{safe_name}.json")
    
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lesson_path": sub_path,
        "segments": segments
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path

def load_script_from_file(sub_path, version_name):
    """Load một phiên bản kịch bản cụ thể của bài học"""
    if not version_name or version_name == "-- Tạo mới --":
        return []
        
    folder = get_lesson_scripts_dir(sub_path)
    file_path = os.path.join(folder, f"{version_name}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('segments') or []
    return []

async def generate_voice(text, output_path, voice_id="vi-VN-HoaiMyNeural"):
    """Giữ nguyên hàm tạo giọng nói của mày"""
    try:
        communicate = edge_tts.Communicate(text, voice_id, rate="+0%")
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return False