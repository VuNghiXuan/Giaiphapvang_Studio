import os
import json
import glob
from datetime import datetime
import edge_tts

# --- QUẢN LÝ FILE KỊCH BẢN ---

def get_list_scripts():
    """Lấy danh sách các file json kịch bản, xếp mới nhất lên đầu"""
    folder = "workspace/scripts"
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        return []
    # Lấy file .json và bỏ đuôi file để hiển thị trên UI
    files = [f.replace(".json", "") for f in os.listdir(folder) if f.endswith(".json")]
    return sorted(files, reverse=True)

def save_script_to_file(segments, version_name):
    """Lưu danh sách segments vào file json"""
    folder = "workspace/scripts"
    os.makedirs(folder, exist_ok=True)
    
    # Làm sạch tên file
    safe_name = "".join([c for c in version_name if c.isalnum() or c in (' ', '_')]).strip()
    if not safe_name: safe_name = f"backup_{int(datetime.now().timestamp())}"
    
    file_path = os.path.join(folder, f"{safe_name}.json")
    
    # Cấu trúc đồng nhất: Luôn dùng key 'segments'
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "segments": segments  # Lưu nguyên list [{}, {}]
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path

def load_script_from_file(filename):
    path = f"workspace/scripts/{filename}.json"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Fix lỗi key mismatch: đọc cả 'content' hoặc 'segments'
            return data.get('content') or data.get('segments') or []
    return []

async def generate_voice(text, output_path, voice_id="vi-VN-HoaiMyNeural"):
    """
    Tạo file âm thanh từ văn bản.
    - text: Lời thoại
    - output_path: Đường dẫn lưu file (vd: workspace/temp_audio_1.mp3)
    - voice_id: ID giọng đọc (NamMinh, HoaiMy,...)
    """
    try:
        # Rate +0% là chuẩn, nếu muốn đọc nhanh hơn thì chỉnh +10%
        communicate = edge_tts.Communicate(text, voice_id, rate="+0%")
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return False