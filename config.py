import os

class Config:
    # Thư mục gốc chứa toàn bộ dự án
    BASE_STORAGE = os.path.abspath("./storage")
    
    # Tên thư mục con trong mỗi bài học để chứa các bản thảo kịch bản
    SCRIPTS_DIR_NAME = "scripts"
    
    # Tên thư mục con chứa video gốc
    RAW_DIR_NAME = "raw"
    
    # File cơ sở dữ liệu
    DB_PATH = os.path.abspath("database.db")
    
    @classmethod
    def init_folders(cls):
        # Tạo thư mục storage gốc nếu chưa có
        if not os.path.exists(cls.BASE_STORAGE):
            os.makedirs(cls.BASE_STORAGE)

# Khởi tạo ngay khi import config
Config.init_folders()