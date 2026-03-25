import os
import shutil
import traceback
from config import Config
from .db_engine import DBEngine

class StudioController:
    def __init__(self):
        self.db = DBEngine()

    def create_tutorial(self, title):
        """Tạo dự án mới kèm thư mục vật lý"""
        folder_name = "".join([c if c.isalnum() else "_" for c in title])
        full_path = os.path.join(Config.BASE_STORAGE, folder_name)
        try:
            self.db.execute("INSERT INTO tutorials (title, folder_name) VALUES (?, ?)", (title, folder_name))
            os.makedirs(full_path, exist_ok=True)
            self.db.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi create_tutorial: {e}")
            traceback.print_exc()
            return False

    def get_all_tutorials(self):
        """Lấy danh sách dự án"""
        try:
            return self.db.execute("SELECT * FROM tutorials ORDER BY created_at DESC").fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_all_tutorials: {e}")
            return []

    def add_sub_content(self, t_id, sub_title, parent_folder):
        """Chèn thêm bài học mới vào cuối danh sách"""
        sub_folder_name = "".join([c if c.isalnum() else "_" for c in sub_title])
        full_sub_path = os.path.join(Config.BASE_STORAGE, parent_folder, sub_folder_name)
        
        try:
            # 1. Tính toán position tiếp theo (Lấy max position hiện tại + 1)
            res = self.db.execute("SELECT MAX(position) as max_pos FROM sub_contents WHERE tutorial_id = ?", (t_id,)).fetchone()
            next_pos = (res['max_pos'] + 1) if res and res['max_pos'] is not None else 0

            # 2. Chèn vào DB
            self.db.execute(
                "INSERT INTO sub_contents (tutorial_id, sub_title, sub_folder, position, status) VALUES (?, ?, ?, ?, ?)", 
                (t_id, sub_title, sub_folder_name, next_pos, "Chưa quay")
            )
            
            # 3. Tạo thư mục vật lý
            os.makedirs(full_sub_path, exist_ok=True)
            os.makedirs(os.path.join(full_sub_path, "raw"), exist_ok=True)
            os.makedirs(os.path.join(full_sub_path, "outputs"), exist_ok=True)
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi add_sub_content: {e}")
            traceback.print_exc()
            return False

    def get_sub_contents(self, tutorial_id):
        """Lấy danh sách bài học theo thứ tự position"""
        try:
            return self.db.execute(
                "SELECT * FROM sub_contents WHERE tutorial_id = ? ORDER BY position ASC", 
                (tutorial_id,)
            ).fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_sub_contents: {e}")
            return []

    def move_sub_content(self, sub_id, direction):
        """Di chuyển bài học Lên/Xuống bằng cách hoán đổi position"""
        try:
            # Lấy thông tin bài hiện tại
            curr = dict(self.db.execute("SELECT id, tutorial_id, position FROM sub_contents WHERE id = ?", (sub_id,)).fetchone())
            curr_pos = curr['position']
            t_id = curr['tutorial_id']

            if direction == "up":
                target = self.db.execute(
                    "SELECT id, position FROM sub_contents WHERE tutorial_id = ? AND position < ? ORDER BY position DESC LIMIT 1",
                    (t_id, curr_pos)
                ).fetchone()
            else:
                target = self.db.execute(
                    "SELECT id, position FROM sub_contents WHERE tutorial_id = ? AND position > ? ORDER BY position ASC LIMIT 1",
                    (t_id, curr_pos)
                ).fetchone()

            if target:
                target = dict(target)
                # Hoán đổi position trong DB
                self.db.execute("UPDATE sub_contents SET position = ? WHERE id = ?", (target['position'], sub_id))
                self.db.execute("UPDATE sub_contents SET position = ? WHERE id = ?", (curr_pos, target['id']))
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Lỗi move_sub_content: {e}")
            return False

    def update_sub_content(self, sub_id, title, status):
        """Cập nhật thông tin bài học"""
        try:
            self.db.execute(
                "UPDATE sub_contents SET sub_title = ?, status = ? WHERE id = ?", 
                (title, status, sub_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi update_sub_content: {e}")
            return False

    def delete_sub_content(self, sub_id, folder_name, sub_folder):
        """Xóa bài học: DB + Thư mục vật lý"""
        try:
            # Xóa DB
            self.db.execute("DELETE FROM sub_contents WHERE id = ?", (sub_id,))
            self.db.commit()
            
            # Xóa Folder
            full_path = os.path.join(Config.BASE_STORAGE, folder_name, sub_folder)
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            print(f"❌ Lỗi delete_sub_content: {e}")
            return False

    def update_tutorial_title(self, t_id, new_title):
        """Đổi tên dự án"""
        try:
            self.db.execute("UPDATE tutorials SET title = ? WHERE id = ?", (new_title, t_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi update_tutorial_title: {e}")
            return False

    def delete_tutorial(self, t_id, folder_name):
        """Xóa cả dự án: DB + Thư mục vật lý"""
        try:
            # 1. Xóa tất cả clip con trong DB
            self.db.execute("DELETE FROM sub_contents WHERE tutorial_id = ?", (t_id,))
            # 2. Xóa dự án trong DB
            self.db.execute("DELETE FROM tutorials WHERE id = ?", (t_id,))
            self.db.commit()
            
            # 3. Xóa thư mục gốc của dự án
            full_path = os.path.join(Config.BASE_STORAGE, folder_name)
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            print(f"❌ Lỗi delete_tutorial: {e}")
            return False
        
    def move_tutorial(self, t_id, direction):
        """Hoán đổi vị trí giữa 2 dự án lớn"""
        try:
            curr = dict(self.db.execute("SELECT id, created_at FROM tutorials WHERE id = ?", (t_id,)).fetchone())
            # Lưu ý: Nếu Vũ dùng created_at để sắp xếp thì việc hoán đổi sẽ phức tạp hơn chút.
            # Cách tốt nhất là thêm cột 'position' cho bảng tutorials giống như sub_contents.
            # Tao giả định mày đã thêm cột 'position' vào bảng tutorials nhé:
            curr_pos = self.db.execute("SELECT position FROM tutorials WHERE id = ?", (t_id,)).fetchone()['position']
            
            if direction == "up":
                target = self.db.execute("SELECT id, position FROM tutorials WHERE position < ? ORDER BY position DESC LIMIT 1", (curr_pos,)).fetchone()
            else:
                target = self.db.execute("SELECT id, position FROM tutorials WHERE position > ? ORDER BY position ASC LIMIT 1", (curr_pos,)).fetchone()

            if target:
                self.db.execute("UPDATE tutorials SET position = ? WHERE id = ?", (target['position'], t_id))
                self.db.execute("UPDATE tutorials SET position = ? WHERE id = ?", (curr_pos, target['id']))
                self.db.commit()
                return True
        except Exception as e:
            print(f"Lỗi move_tutorial: {e}")
            return False
    