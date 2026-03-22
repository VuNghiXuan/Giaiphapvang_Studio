import pyautogui
print("Toạ độ chuột hiện tại:", pyautogui.position())
# Thử chụp 1 tấm ảnh màn hình xem có lỗi không
pyautogui.screenshot("test_screen.png")
print("Đã chụp thử màn hình thành công!")