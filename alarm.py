import pyautogui
import cv2
import numpy as np
import easyocr
import pygame
import time
import threading
import tkinter as tk
import keyboard

# easyocr Reader 객체 생성 (GPU 사용 시도)
reader = easyocr.Reader(['ko', 'en'], gpu=True)

# mp3 파일 경로
MP3_PATH = '1.mp3'

# 감지 상태 변수 및 감지 영역
is_detecting = False
thread_running = False
stop_thread = False
region = [0, 0, 1000, 1000]  # 기본값: 좌상단 1000x1000

# pygame 알람 함수
def play_mp3():
    pygame.mixer.init()
    pygame.mixer.music.load(MP3_PATH)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def is_green_text(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    green_part = cv2.bitwise_and(image, image, mask=mask)
    result = reader.readtext(green_part, detail=0)
    for text in result:
        if any('\uac00' <= ch <= '\ud7a3' for ch in text):
            return True
    return False

def detect_loop(status_label, btn):
    global is_detecting, stop_thread, region
    detected = False
    while not stop_thread:
        if is_detecting:
            screenshot = pyautogui.screenshot(region=tuple(region))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            if is_green_text(frame):
                if not detected:
                    status_label.config(text='감지됨! 알람 재생', fg='green')
                    play_mp3()
                    detected = True
            else:
                status_label.config(text='감지 중...', fg='blue')
                detected = False
        else:
            status_label.config(text='정지됨', fg='red')
        time.sleep(1)

def toggle_detection(status_label, btn):
    global is_detecting
    is_detecting = not is_detecting
    if is_detecting:
        btn.config(text='감지 정지')
        status_label.config(text='감지 중...', fg='blue')
    else:
        btn.config(text='감지 시작')
        status_label.config(text='정지됨', fg='red')

def on_f1(status_label, btn):
    toggle_detection(status_label, btn)

def select_area(root, area_label):
    global region
    # 전체 화면 오버레이 생성
    overlay = tk.Toplevel(root)
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-alpha', 0.3)
    overlay.config(bg='gray')
    overlay.lift()
    overlay.focus_set()
    start = [0, 0]
    rect = [None]
    canvas = tk.Canvas(overlay, cursor='cross', bg='gray', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    def on_mouse_down(event):
        start[0], start[1] = event.x, event.y
        rect[0] = canvas.create_rectangle(start[0], start[1], start[0], start[1], outline='red', width=2)

    def on_mouse_move(event):
        if rect[0]:
            canvas.coords(rect[0], start[0], start[1], event.x, event.y)

    def on_mouse_up(event):
        x1, y1 = start[0], start[1]
        x2, y2 = event.x, event.y
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        w, h = x2 - x1, y2 - y1
        if w > 10 and h > 10:
            region[:] = [x1, y1, w, h]
            area_label.config(text=f'영역: {region[0]}, {region[1]}, {region[2]}, {region[3]}')
        overlay.destroy()

    canvas.bind('<Button-1>', on_mouse_down)
    canvas.bind('<B1-Motion>', on_mouse_move)
    canvas.bind('<ButtonRelease-1>', on_mouse_up)


def gui():
    global thread_running, stop_thread, region
    root = tk.Tk()
    root.title('장사하자 응디')
    root.geometry('350x170')
    status_label = tk.Label(root, text='정지됨', fg='red', font=('맑은 고딕', 14))
    status_label.pack(pady=10)
    btn = tk.Button(root, text='감지 시작', font=('맑은 고딕', 12), command=lambda: toggle_detection(status_label, btn))
    btn.pack(pady=5)
    area_label = tk.Label(root, text=f'영역: {region[0]}, {region[1]}, {region[2]}, {region[3]}', font=('맑은 고딕', 10))
    area_label.pack(pady=5)
    area_btn = tk.Button(root, text='영역 선택', font=('맑은 고딕', 10), command=lambda: select_area(root, area_label))
    area_btn.pack(pady=5)
    # F1 키 이벤트 등록
    keyboard.add_hotkey('f1', lambda: on_f1(status_label, btn))
    # 감지 스레드 시작
    stop_thread = False
    if not thread_running:
        t = threading.Thread(target=detect_loop, args=(status_label, btn), daemon=True)
        t.start()
        thread_running = True
    root.protocol('WM_DELETE_WINDOW', lambda: (setattr(globals(), 'stop_thread', True), root.destroy()))
    root.mainloop()
    stop_thread = True

if __name__ == '__main__':
    gui()
