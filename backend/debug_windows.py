# -*- coding: utf-8 -*-
"""Find ALL windows (including hidden) that match WeChat-related names."""
import ctypes
import ctypes.wintypes
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

results = []

def enum_callback(hwnd, _lparam):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        visible = bool(user32.IsWindowVisible(hwnd))
        results.append((hwnd, title, visible))
    return True

user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

# Search for WeChat related
keywords = ['微信', 'WeChat', 'wechat', 'WXWork']
matches = [(h, t, v) for h, t, v in results if any(k in t for k in keywords)]

print(f"Found {len(matches)} WeChat-related windows (out of {len(results)} total):")
for h, t, v in matches:
    print(f"  hwnd={h}  visible={v}  title={repr(t)}")

if not matches:
    print("\nNo WeChat windows found at all. Dumping ALL window titles for inspection:")
    for h, t, v in results:
        print(f"  hwnd={h}  vis={v}  title={repr(t)}")
