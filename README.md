# 🎬 AI Video Tutorial Studio - Giải Pháp Vàng Edition

Hệ thống hỗ trợ tạo video hướng dẫn sử dụng phần mềm tự động, kết hợp giữa thao tác người dùng (Raw Video) và trí tuệ nhân tạo (Whisper, Groq/Gemini, Edge-TTS).

## 📌 1. Triết lý hệ thống (Phương án Hybrid)
Đây là phương án **Người quay - AI dựng**. Người dùng tập trung vào việc thao tác chuẩn xác trên màn hình, còn việc viết kịch bản, sửa lỗi chính tả chuyên môn và lồng tiếng sẽ do AI đảm nhận.

### ✅ Ưu điểm
- **Độ tự nhiên cao:** Thao tác chuột và nhịp độ video mang tính "người thật", dễ theo dõi hơn robot.
- **Linh hoạt:** Có thể quay mọi ngóc ngách của phần mềm mà không cần lo lắng về lỗi Code Automation (Playwright/Selenium).
- **Chất lượng âm thanh:** Sử dụng Neural Voice của Microsoft nên giọng đọc cực kỳ chuyên nghiệp, không bị vấp.
- **KnowledgeBase Thông minh:** Tự động sửa lỗi "ngáo" của Whisper (VD: "vàng bún số chín" -> "Vàng 9999").

### ❌ Nhược điểm
- **Tốn công quay:** Phải ngồi quay thủ công từng màn hình.
- **Phụ thuộc con người:** Nếu lúc quay Vũ bấm nhầm hoặc đứng hình quá lâu thì phải quay lại hoặc cắt ghép thủ công.

---

## 🛠 2. Quy trình 5 bước tạo Clip chuẩn "Giải Pháp Vàng"

Để có một clip hướng dẫn chuyên nghiệp, Vũ cần tuân thủ đúng quy trình này:

### Bước 1: Quay màn hình (Raw Material)
- Sử dụng phần mềm quay màn hình (OBS/CapCut/Camtasia).
- **Yêu cầu:** Thao tác chậm rãi, dứt khoát. 
- **Mẹo:** Vừa làm vừa nói nhỏ (thì thầm) vào mic về hành động đang làm. Việc này giúp Whisper ở bước sau bắt được "từ khóa" để AI hiểu ngữ cảnh tốt hơn.
- Lưu file vào: `lessons/[tên_bài]/raw/raw_video.mp4`.

### Bước 2: Bóc băng thô (Whisper Stage)
- Mở giao diện Editor, bấm nút **"🎙️ 1. WHISPER BÓC BĂNG"**.
- Hệ thống sẽ dùng model `faster-whisper` để chuyển giọng nói thì thầm của Vũ thành các mốc Timeline và văn bản thô.

### Bước 3: Chuốt lời thoại (AI Refine Stage)
- **CỰC KỲ QUAN TRỌNG:** Chọn đúng kịch bản (Scenario) trong ô "Chọn Form hướng dẫn".
- Bấm nút **"✨ 2. AI CHUỐT LỜI"**.
- AI (Groq/Gemini) sẽ đọc KnowledgeBase để:
    - Sửa thuật ngữ ngành vàng (tiền công, trọng lượng, mã đá...).
    - Thêm câu chào hỏi, dẫn dắt chuyên nghiệp theo đúng phong cách Giaiphapvang Studio.
    - Cân bằng lại độ dài câu nói cho khớp với Timeline.

### Bước 4: Kiểm tra và Tinh chỉnh (Manual Check)
- Xem lại danh sách lời thoại bên trái.
- Nếu đoạn nào AI đọc dài quá so với thao tác, hãy dùng Menu `📝 Chỉnh sửa` để rút gọn câu chữ hoặc điều chỉnh lại giây bắt đầu.

### Bước 5: Xuất bản (Final Render)
- Chọn giọng đọc (Nam Minh hoặc Hoài Mỹ).
- Bấm **"🎬 3. XUẤT VIDEO FINAL"**.
- Hệ thống sẽ tự động: Tạo file âm thanh MP3 -> Chèn vào đúng vị trí Timeline -> Trộn vào video gốc -> Xuất file `final_video.mp4`.

---

## 🏗 3. Cấu trúc thư mục dự án
- `/core`: Chứa "bộ não" xử lý (AI Manager, KnowledgeBase, Scripts).
- `/lessons`: Nơi lưu trữ các bài học. Mỗi thư mục con là một bài hướng dẫn.
- `/workspace`: Thư mục tạm chứa các file audio sinh ra trong quá trình render (tự động xóa sau khi xong).

## 📝 4. Lưu ý khi bảo trì
- **KnowledgeBase:** Nếu phần mềm có thêm tính năng mới, hãy cập nhật vào `core/knowledge_base.py` để AI không bị ngỡ ngàng khi chuốt lời.
- **API Keys:** Đảm bảo file `.env` luôn có đủ `GROQ_API_KEY` hoặc `GOOGLE_API_KEY`.

---
*Chúc Vũ tạo ra những bộ kịch bản "triệu view" cho Giải Pháp Vàng!*