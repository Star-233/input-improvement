from pynput import keyboard
import time
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image
import threading
from pynput.keyboard import Controller, Key
import chat_model_request
import win_tool

# 记录空格按下的时间戳列表
space_presses = []
# 定义短时间阈值（单位：秒）
SHORT_TIME_THRESHOLD = 0.5
# 用于控制监听器的停止
stop_listener = False
# 用于记录当前运行的字符输入线程
char_input_thread = None

# 定义按键按下时的回调函数
def on_press(key):
    global space_presses, char_input_thread, stop_listener
    if stop_listener:
        return False
    
    # 检查是否有线程正在运行
    if char_input_thread and char_input_thread.is_alive():
        return

    
    if key == keyboard.Key.space:
        current_time = time.time()
        space_presses.append(current_time)
        # 移除超过阈值时间的记录
        space_presses = [
            t for t in space_presses if current_time - t <= SHORT_TIME_THRESHOLD
        ]
        if len(space_presses) >= 3:
            time_used = space_presses[-1] - space_presses[-3]
            print("短时间内快速按下了三次空格！耗时 {:.4f} 秒".format(time_used))
            # 获取输入框nei'ron
            key_controller = Controller()
            key_controller.press(Key.ctrl)
            key_controller.press("a")
            key_controller.release("a")
            key_controller.press("c")
            key_controller.release("c")
            key_controller.release(Key.ctrl)
            key_controller.press(Key.right)
            key_controller.release(Key.right)
            time.sleep(0.1)
            # 获取剪贴板内容
            clipboard_content = win_tool.get_clipboard_text()
            if clipboard_content is not None:
                clipboard_content = clipboard_content.strip()
            else:
                clipboard_content = ''
            print("剪贴板内容：", clipboard_content)

            # 执行ai调用
            def handle_response(clipboard_content):
                # pyperclip.copy(res)
                key_controller = Controller()
                key_controller.press(Key.ctrl)
                key_controller.press("a")
                key_controller.release("a")
                # key_controller.press("v")
                # key_controller.release("v")
                key_controller.release(Key.ctrl)

                for chunk in chat_model_request.chat_with_model(clipboard_content):
                    # time.sleep(0.2)
                    print(chunk, end='')
                    win_tool.send_string(chunk)
                    # key_controller.type(chunk)

            char_input_thread = threading.Thread(target=handle_response, args=(clipboard_content,))
            char_input_thread.start()
            space_presses = []


# 定义按键释放时的回调函数
def on_release(key):
    if stop_listener:
        return False


# 键盘监听函数
def start_keyboard_listener():
    global stop_listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# 退出函数
def quit_action(icon, item):
    global stop_listener
    stop_listener = True
    icon.stop()


# 创建系统托盘图标
def create_tray_icon():
    # 请替换为实际的图标路径，若没有图标，可使用透明图标
    try:
        image = Image.open("icon.png")
    except FileNotFoundError:
        # 如果没有图标文件，创建一个 16x16 红色的图标
        image = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
    # 修改变量名避免冲突
    tray_menu = menu(item("退出输入框加强", quit_action))
    tray_icon = icon("space_detector", image, menu=tray_menu)
    tray_icon.run()


if __name__ == "__main__":
    # 启动键盘监听线程
    listener_thread = threading.Thread(target=start_keyboard_listener)
    listener_thread.start()
    # 启动系统托盘图标
    create_tray_icon()
