import ctypes
from ctypes import wintypes

# 定义必要的常量和结构体
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0

CF_UNICODETEXT = 13

# 定义结构体
class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_void_p)),
    )

class KEYBDINPUT(ctypes.Structure):
    _fields_ = ( 
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_void_p)),
    )

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD),
    )

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (
            ('mi', MOUSEINPUT),
            ('ki', KEYBDINPUT),
            ('hi', HARDWAREINPUT),
        )

    _anonymous_ = ('_input',)
    _fields_ = (
        ('type', wintypes.DWORD),
        ('_input', _INPUT),
    )

LPINPUT = ctypes.POINTER(INPUT)

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return result

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (
    wintypes.UINT,  # nInputs
    LPINPUT,       # pInputs
    ctypes.c_int,  # cbSize
)

# 模拟输入字符串的函数
def send_string(text):
    inputs = []
    for char in text:
        code_point = ord(char)
        if code_point > 0xFFFF:
            # 处理代理对字符
            high_surrogate = 0xD800 + ((code_point - 0x10000) >> 10)
            low_surrogate = 0xDC00 + ((code_point - 0x10000) & 0x3FF)
            # 发送高位代理字符
            key_down = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=high_surrogate,
                    dwFlags=KEYEVENTF_UNICODE,
                )
            )
            key_up = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=high_surrogate,
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                )
            )
            inputs.extend((key_down, key_up))
            
            # 发送低位代理字符
            key_down = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=low_surrogate,
                    dwFlags=KEYEVENTF_UNICODE,
                )
            )
            key_up = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=low_surrogate,
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                )
            )
            inputs.extend((key_down, key_up))
        else:
            # 按下按键
            key_down = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=ord(char),
                    dwFlags=KEYEVENTF_UNICODE,
                )
            )
            # 释放按键
            key_up = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=ord(char),
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                )
            )
            inputs.extend((key_down, key_up))

    # 转换为 ctypes 数组
    nInputs = len(inputs)
    LPINPUT = ctypes.POINTER(INPUT)
    pInputs = (INPUT * nInputs)(*inputs)
    cbSize = ctypes.sizeof(INPUT)

    # 调用 SendInput 函数
    user32.SendInput(nInputs, pInputs, cbSize)

def get_clipboard_text():
    """使用 Windows API 获取剪贴板中的文本内容。"""
    if not user32.OpenClipboard(None):
        return None
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        h_clipboard = user32.GetClipboardData(CF_UNICODETEXT)
        if not h_clipboard:
            return None
        data = kernel32.GlobalLock(h_clipboard)
        if not data:
            return None
        try:
            text = ctypes.wstring_at(data)
        finally:
            kernel32.GlobalUnlock(h_clipboard)
        return text
    finally:
        user32.CloseClipboard()

if __name__ == '__main__':
    send_string('😡')