import sqlite3
from config import Config

class DBEngine:
    def __init__(self):
        # check_same_thread=False cực kỳ quan trọng khi dùng Streamlit
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Bảng Dự án lớn (Thêm cột position để di chuyển dự án)
        cursor.execute('''CREATE TABLE IF NOT EXISTS tutorials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            folder_name TEXT UNIQUE,
            position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 2. Bảng Bài học con (Thêm position để sắp xếp, status để lưu trạng thái tay)
        cursor.execute('''CREATE TABLE IF NOT EXISTS sub_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tutorial_id INTEGER,
            sub_title TEXT,
            sub_folder TEXT,
            position INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Chưa quay',
            FOREIGN KEY(tutorial_id) REFERENCES tutorials(id) ON DELETE CASCADE
        )''')
        
        self.conn.commit()

    def execute(self, query, params=()):
        """Thực thi câu lệnh SQL"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            # Không commit ở đây để Controller chủ động commit khi cần (như hoán đổi vị trí)
            return cursor
        except sqlite3.Error as e:
            print(f"❌ Lỗi SQL: {e}")
            raise e

    def commit(self):
        """Lưu thay đổi vào file .db"""
        self.conn.commit()

    def close(self):
        """Đóng kết nối khi cần"""
        self.conn.close()