import cv2
import numpy as np
import mss
import pyaudio
import wave
# import threading
# import os
import time
import keyboard
import time
import streamlit as st
import os
import pyautogui



class ScreenRecorder:
    def __init__(self):
        # Đảm bảo thư mục lưu video tồn tại
        if not os.path.exists("exports/videos"):
            os.makedirs("exports/videos")

    def start_recording(self, output_path, fps=20.0, resolution=(1920, 1080)):
        """
        Quay màn hình: Dùng phím Pause để Start/Stop.
        Đã gia cố để tránh lỗi truyền nhầm tham số.
        """
        out = None
        try:
            # 1. BẢO VỆ ÉP KIỂU FPS (Chống lỗi 'could not convert string to float')
            try:
                fps_float = float(fps)
            except (ValueError, TypeError):
                # Nếu Vũ truyền nhầm path file vào đây, mặc định lấy 20.0
                print(f"⚠️ Cảnh báo: FPS truyền vào không phải số ({fps}). Tự động dùng 20.0")
                fps_float = 20.0
            
            # 2. XỬ LÝ ĐỘ PHÂN GIẢI
            if resolution is None or isinstance(resolution, str):
                w, h = pyautogui.size()
            else:
                w, h = int(resolution[0]), int(resolution[1])
            
            screen_size = (w, h)

            # 3. KHỞI TẠO VIDEOWRITER
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps_float, screen_size)

            if not out.isOpened():
                st.error("❌ Không thể khởi tạo VideoWriter. Kiểm tra đường dẫn file hoặc quyền Admin.")
                return

            st.info("🎯 **SẴN SÀNG!**\n1. Mở phần mềm Tiệm Vàng lên.\n2. Nhấn phím **'Pause'** (trên bàn phím) để BẮT ĐẦU.")
            
            # Chờ nhấn Pause lần 1
            keyboard.wait('pause')
            time.sleep(0.5) # Chống dính phím
            
            is_recording = True
            print(f"🔴 ĐANG QUAY MÀN HÌNH: {output_path}")
            
            # 4. VÒNG LẶP GHI HÌNH
            while is_recording:
                # Chụp màn hình
                img = pyautogui.screenshot()
                
                # Chuyển đổi định dạng ảnh cho OpenCV
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Ép đúng kích cỡ để không bị lỗi 'Bad argument'
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, screen_size)

                # Ghi frame
                out.write(frame)

                # Kiểm tra nhấn Pause lần 2 để dừng
                if keyboard.is_pressed('pause'):
                    is_recording = False
                    time.sleep(0.5)
                    break
                    
        except Exception as e:
            st.error(f"❌ Lỗi Recording: {e}")
            print(f"❌ Lỗi Recording: {e}")
        
        finally:
            # Giải phóng tài nguyên
            if out is not None:
                out.release()
            cv2.destroyAllWindows()
            print("⬜ ĐÃ DỪNG VÀ LƯU VIDEO THÀNH CÔNG.")
            
        st.success(f"✅ Video đã lưu tại: {output_path}")

    def stop_recording(self):
        print(f"\n--- [STOP] Đang yêu cầu dừng quay... ---")
        self.recording = False
        if hasattr(self, 'video_thread'): self.video_thread.join()
        if hasattr(self, 'audio_thread'): self.audio_thread.join()
        print("--- [SUCCESS] Đã dừng và lưu tất cả các file thành công ---\n")

    def _record_video(self, path):
        print(f"--- [VIDEO] Luồng Video bắt đầu chạy ---")
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1] 
                width = monitor["width"]
                height = monitor["height"]
                print(f"--- [VIDEO] Nhận diện màn hình: {width}x{height} ---")
                
                path_avi = path.replace(".mp4", ".avi")
                out = cv2.VideoWriter(path_avi, self.fourcc, self.fps, (width, height))
                
                if not out.isOpened():
                    print("--- [ERROR] Không thể mở VideoWriter (XVID). Kiểm tra đường dẫn hoặc quyền ghi file! ---")
                    return

                count = 0
                last_time = time.time()
                while self.recording:
                    # Chụp hình
                    img = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Ghi hình
                    out.write(frame)
                    
                    count += 1
                    if count % 20 == 0:
                        print(f"--- [VIDEO] Đang ghi hình... Frame: {count} ---")
                    
                    # Giữ nhịp FPS
                    time_to_wait = (1.0 / self.fps) - (time.time() - last_time)
                    if time_to_wait > 0:
                        time.sleep(time_to_wait)
                    last_time = time.time()
                
                out.release()
                print(f"--- [VIDEO] Đã đóng file Video: {path_avi} ---")
        except Exception as e:
            print(f"--- [VIDEO ERROR] Lỗi trong lúc ghi hình: {e} ---")

    def _record_audio(self, path):
        print(f"--- [AUDIO] Luồng Audio bắt đầu chạy ---")
        p = pyaudio.PyAudio()
        try:
            # Kiểm tra xem có thiết bị input không
            try:
                device_info = p.get_default_input_device_info()
                print(f"--- [AUDIO] Đang dùng Mic: {device_info['name']} ---")
            except:
                print("--- [AUDIO ERROR] Không tìm thấy Micro! ---")
                return

            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            frames = []
            
            while self.recording:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            wf = wave.open(path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
            wf.close()
            print(f"--- [AUDIO] Đã đóng file Audio: {path} ---")
        except Exception as e:
            print(f"--- [AUDIO ERROR] Lỗi Mic: {e} ---")
        finally:
            p.terminate()