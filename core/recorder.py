import cv2
import numpy as np
import mss
import pyaudio
import wave
import threading
import os
import time
import tkinter as tk
from threading import Thread

class ScreenRecorder:
    def __init__(self):
        self.recording = False
        self.paused = False
        self.finished = False  # Trạng thái để Streamlit biết khi nào cần nhảy Tab
        self.video_thread = None
        self.audio_thread = None
        self.root_control = None 
        self.fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        os.makedirs("workspace", exist_ok=True)
        print("[DEBUG-CORE] 🛠️ Đã khởi tạo ScreenRecorder Engine.")

    def start_recording(self, output_path, fps=20.0, resolution=(1920, 1080), stop_hotkey="ctrl+q"):
        if self.recording: 
            print("[DEBUG-CORE] ⚠️ Cảnh báo: Lệnh quay bị bỏ qua vì đang trong quá trình ghi.")
            return
        
        self.recording = True
        self.paused = False
        self.finished = False # Reset trạng thái kết thúc
        self.fps = float(fps)
        self.resolution = resolution
        self.audio_path = output_path.replace(".mp4", ".wav")
        self.video_path = output_path

        print(f"[DEBUG-CORE] 🎬 Bắt đầu luồng ghi hình: {self.video_path} | FPS: {self.fps}")
        
        self.video_thread = threading.Thread(target=self._record_video, args=(self.video_path,), daemon=True)
        self.audio_thread = threading.Thread(target=self._record_audio, args=(self.audio_path,), daemon=True)
        
        self.video_thread.start()
        self.audio_thread.start()
        print("[DEBUG-CORE] ✅ Cả 2 luồng Video & Audio đã kích hoạt thành công.")

    def _record_video(self, path):
        print(f"[DEBUG-VIDEO] 📽️ Luồng Video bắt đầu ghi vào file...")
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                out = cv2.VideoWriter(path, self.fourcc, self.fps, self.resolution)
                last_time = time.time()
                frame_count = 0
                
                while self.recording:
                    if self.paused:
                        time.sleep(0.1)
                        continue
                        
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    if (frame.shape[1], frame.shape[0]) != self.resolution:
                        frame = cv2.resize(frame, self.resolution)
                    
                    out.write(frame)
                    frame_count += 1
                    
                    if frame_count % 100 == 0:
                        print(f"[DEBUG-VIDEO] 🎞️ Đã ghi {frame_count} frames...")

                    wait_time = (1.0 / self.fps) - (time.time() - last_time)
                    if wait_time > 0: time.sleep(wait_time)
                    last_time = time.time()
                
                out.release()
                print(f"[DEBUG-VIDEO] 💾 Đã đóng file Video. Tổng số frame: {frame_count}")
        except Exception as e: 
            print(f"[DEBUG-VIDEO] ❌ Lỗi Video: {e}")

    def _record_audio(self, path):
        print(f"[DEBUG-AUDIO] 🎙️ Luồng Audio bắt đầu thu âm...")
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            frames = []
            while self.recording:
                if self.paused:
                    time.sleep(0.1)
                    continue
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
            print(f"[DEBUG-AUDIO] 💾 Đã lưu file Audio thành công: {path}")
        except Exception as e: 
            print(f"[DEBUG-AUDIO] ❌ Lỗi Audio: {e}")
        finally: 
            p.terminate()

    def stop_recording(self):
        print("[DEBUG-CORE] 🛑 Nhận lệnh STOP ghi hình.")
        self.recording = False
        self.paused = False
        self.finished = True # Đánh dấu hoàn tất để GUI bắt được tín hiệu nhảy Tab
        
        if self.root_control:
            try:
                print("[DEBUG-TK] 🧹 Đang đóng cửa sổ điều khiển Tkinter...")
                # Sử dụng after để đảm bảo lệnh destroy chạy trong main thread của Tkinter
                self.root_control.after(0, self.root_control.destroy)
                self.root_control = None
            except Exception as e:
                print(f"[DEBUG-TK] ⚠️ Lỗi khi đóng Tkinter: {e}")

    def toggle_pause(self):
        self.paused = not self.paused
        state = "TẠM DỪNG" if self.paused else "TIẾP TỤC QUAY"
        print(f"[DEBUG-CORE] ⏸️ Trạng thái: {state}")
        return self.paused

    def show_floating_control(self, output_path, fps, resolution, hotkey):
        def create_window():
            print("[DEBUG-TK] 🖥️ Khởi tạo cửa sổ điều khiển nổi...")
            root = tk.Tk()
            self.root_control = root
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            root.attributes("-alpha", 0.95)
            
            w, h = 220, 70
            root.geometry(f"{w}x{h}+{root.winfo_screenwidth()-(w+20)}+{root.winfo_screenheight()-(h+70)}")

            main_frame = tk.Frame(root, bg="#1E1E1E", bd=2, relief="raised")
            main_frame.pack(fill=tk.BOTH, expand=True)

            status_label = tk.Label(main_frame, text="SẴN SÀNG", fg="#00FF00", bg="#1E1E1E", font=("Arial", 8, "bold"))
            status_label.pack(pady=2)

            btn_frame = tk.Frame(main_frame, bg="#1E1E1E")
            btn_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

            def start_action():
                print("[DEBUG-TK] 🖱️ Click START.")
                self.start_recording(output_path, fps, resolution, hotkey)
                btn_start.pack_forget()
                btn_pause.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                btn_stop.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
                status_label.config(text="● ĐANG QUAY...", fg="#FF4B4B")

            def pause_action():
                print("[DEBUG-TK] 🖱️ Click PAUSE/RESUME.")
                is_paused = self.toggle_pause()
                if is_paused:
                    btn_pause.config(text="▶ TIẾP TỤC", bg="#E69400")
                    status_label.config(text="⏸ ĐANG TẠM DỪNG", fg="#E69400")
                else:
                    btn_pause.config(text="⏸ TẠM DỪNG", bg="#262730")
                    status_label.config(text="● ĐANG QUAY...", fg="#FF4B4B")

            def stop_action():
                print("[DEBUG-TK] 🖱️ Click STOP.")
                self.stop_recording()

            btn_start = tk.Button(btn_frame, text="🔴 BẮT ĐẦU QUAY", bg="#4CAF50", fg="white", 
                                 font=("Arial", 9, "bold"), command=start_action, bd=0)
            btn_start.pack(fill=tk.BOTH, expand=True)

            btn_pause = tk.Button(btn_frame, text="⏸ TẠM DỪNG", bg="#262730", fg="white", 
                                 font=("Arial", 8, "bold"), command=pause_action, bd=0)
            btn_stop = tk.Button(btn_frame, text="⏹ STOP", bg="#FF4B4B", fg="white", 
                                font=("Arial", 8, "bold"), command=stop_action, bd=0)

            # Logic kéo thả
            def start_move(event): root.x, root.y = event.x, event.y
            def stop_move(event): root.geometry(f"+{event.x_root - root.x}+{event.y_root - root.y}")
            main_frame.bind("<Button-1>", start_move)
            main_frame.bind("<B1-Motion>", stop_move)

            print("[DEBUG-TK] 🚀 Cửa sổ Tkinter chính thức chạy mainloop.")
            root.mainloop()

        Thread(target=create_window, daemon=True).start()