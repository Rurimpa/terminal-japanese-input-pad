# input_pad.pyw — 日本語入力パッド（常設の入力窓）
# 作者    ：Rurimpa（https://github.com/Rurimpa）・MIT License。使うとき・直して使うときは、作者名とこの置き場のアドレスを残してください
# 何のため：Claude Code など黒い画面（Windows Terminal）の入力欄に、日本語入力の予測候補の窓が重なって読めない問題をよけるため。
#           Windows Terminal の窓のすぐ下に、普通の Windows の入力窓をいつも出しておき、そこで打った文を元の窓へ貼り付けて送る。
# 動き    ：Windows Terminal の窓の下に同じ横幅でくっつき、窓を動かす・幅を変えるとついてくる。最小化すると一緒に隠れる。
#           下に場所が無いときは、Windows Terminal の窓の高さを入力窓の分だけ自動で縮める（v0.3.0）
# キー    ：入力窓の中＝Enter 貼り付けて送信／Ctrl+Enter 貼り付けだけ／Shift+Enter 改行／Esc 元の窓へ戻る（書きかけは残る）
#           Ctrl+Shift+J（config.json で変えられる）＝入力窓と元の窓を行き来する
#           Windows Terminal が前にあるときの Tab＝入力窓へ飛ぶ（v0.5.0・config.json の tab_jump で切れる）
#           入力窓を出しているときに Windows Terminal を選ぶと、自動で入力窓へ移る（v0.6.0・Esc で戻ったときは移らない・config.json の auto_focus で切れる）
#           入力窓の中の Ctrl+C（文字を選んでいないとき）＝元の窓へ Ctrl+C を送って止める（v0.7.0）
#           Windows Terminal の窓ごとに入力窓を1つずつ出す（v0.8.0・Codex の窓など。書きかけは入力窓ごとに別々）
#           入力窓が空のときの ↑・↓・Enter＝元の窓へ送る（v0.10.0。Claude Code の選ぶ画面を入力窓のまま選べる）
#           入力窓が選ばれているときの Win＋矢印＝Windows Terminal の窓を寄せる（v0.9.0。↑全画面／←→左右半分／↓元に戻す。
#           左右半分から↑↓で上下4分の1・v0.9.1）
#           「メモ：」で始まる文は、config.json の memo_file にファイルの場所を書いたときだけ、元の窓へ送らずにそのファイルへ1行足す（v0.11.0・既定は切）
# 起動    ：pythonw input_pad.pyw（二重起動しない）
# ログ    ：logs\input_pad_YYYYMMDD.log（打った文の中身は書かない。文字数だけ。送り先の窓の題名は残る）

import ctypes
import ctypes.wintypes as wt
import json
import os
import logging
import queue
import re
import threading
import time
import tkinter as tk
import tkinter.font as tkfont

try:   # ファイルを落とす機能の部品（無ければ、その機能だけ使えない）
    from tkinterdnd2 import TkinterDnD, DND_FILES
except Exception:
    TkinterDnD = None
    DND_FILES = None
from datetime import datetime
from pathlib import Path

APP_NAME = "日本語入力パッド"
VERSION = "0.11.0"
ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / "logs"
CONFIG_PATH = ROOT_DIR / "config.json"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi")
imm32 = ctypes.WinDLL("imm32")
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_void_p]
user32.SetWindowLongPtrW.restype = ctypes.c_void_p
user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.CallWindowProcW.restype = ctypes.c_ssize_t
imm32.ImmGetContext.argtypes = [wt.HWND]
imm32.ImmGetContext.restype = ctypes.c_void_p
imm32.ImmReleaseContext.argtypes = [wt.HWND, ctypes.c_void_p]
imm32.ImmGetCompositionStringW.argtypes = [ctypes.c_void_p, wt.DWORD, ctypes.c_void_p, wt.DWORD]
imm32.ImmGetCompositionStringW.restype = ctypes.c_long
WM_IME_COMPOSITION = 0x010F
GCS_RESULTSTR = 0x0800
GCS_COMPSTR = 0x0008
GWLP_WNDPROC = -4
# 入れる窓の値に -1（いつも手前）などを渡すので、64ビットでも正しく渡るよう型を決めておく
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wt.BOOL

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HOTKEY_ID = 1
VK_LBUTTON, VK_CONTROL, VK_SHIFT, VK_MENU, VK_RETURN, VK_V = 0x01, 0x11, 0x10, 0x12, 0x0D, 0x56
VK_LWIN, VK_RWIN = 0x5B, 0x5C
VK_TAB = 0x09
VK_C = 0x43
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 0x25, 0x26, 0x27, 0x28
VK_MENU_MASK = 0xE8     # どのキーにも割り当てられていない番号。Win を離したときにスタートメニューが開かないよう挟む
SNAP_KEYS = {VK_LEFT: "left", VK_UP: "up", VK_RIGHT: "right", VK_DOWN: "down"}
SNAP_TOLERANCE = 8      # 寄せた位置と「同じ」とみなす誤差（px）
KEYEVENTF_KEYUP = 0x2
# キーが押された瞬間を見張る仕組み（Tab で入力窓へ飛ぶため・v0.5.0）
WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0104, 0x0105
LLKHF_INJECTED = 0x10    # プログラムが送ったキー（入力窓が送る Ctrl+V など）の印


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wt.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
kernel32.GetModuleHandleW.restype = ctypes.c_void_p
SW_RESTORE = 9
SW_MINIMIZE = 6
SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_NOACTIVATE = 0x1, 0x2, 0x4, 0x10
HWND_TOP = 0
HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_CLOAKED = 14
MONITOR_DEFAULTTONULL, MONITOR_DEFAULTTONEAREST = 0, 2
TERMINAL_CLASS = "CASCADIA_HOSTING_WINDOW_CLASS"   # Windows Terminal の窓
MIN_TERMINAL_HEIGHT = 240                          # これより縮めない（縮められないときは窓の一番下に重ねて出す）
DOCK_INTERVAL_MS = 200
ACCENT_LINE = 2          # 上の線の太さ（v0.3.4。旧 4px）
GRIP_H = 6               # 上の線のつかめる幅（見た目の線は ACCENT_LINE）
MAX_PAD_RATIO = 0.6      # 入力窓の高さの上限（画面の高さに対する割合）
MIN_FONT, MAX_FONT = 8, 32   # 文字の大きさの範囲
TEXT_TOP = 8             # 入力窓の上の線から、字の始まりまでの余白
PLACEHOLDER_TEXT = "ここに日本語を入力（Enter で送信）"   # 打てない状態で空のときに出す薄い案内
PAD_BG = "#1c2433"       # 入力窓の背景（Claude Code の黒より少し青い）
ACCENT_ON = "#e8833a"    # 打てるとき（Claude のオレンジ）
ACCENT_OFF = "#4a5262"   # 元の窓にいるとき

DEFAULT_CONFIG = {
    "hotkey_modifiers": ["ctrl", "shift"],
    "hotkey_key": "J",
    "font_family": "BIZ UDゴシック",
    "font_size": 14,
    "pad_lines": 3,
    "tab_jump": True,    # Windows Terminal が前にあるとき Tab で入力窓へ飛ぶ（false で切る）
    "auto_focus": True,  # Windows Terminal を選ぶと自動で入力窓へ移る（false で切る）
    "memo_file": "",     # 「メモ：」で始まる文を、元の窓へ送らずにこのファイルへ1行足す（v0.11.0。空なら切＝今までどおり送る）
}

# 「メモ：」「メモ:」「メモ；」「メモ;」「めも：」で始まる文（前の空白は無視）。
# Claude Code の UserPromptSubmit フックで同じ「メモ：」を受け取る仕組みと並べて使えるよう、見分け方をそろえてある
MEMO_HEAD = re.compile(r"^\s*(メモ|めも)\s*[:：;；]\s*")


def memo_body(text):
    """「メモ：」で始まる文なら、頭を除いた本文を返す（本文が空なら ""）。メモでなければ None。"""
    m = MEMO_HEAD.match(text)
    return text[m.end():].strip() if m else None


def write_memo(path, text, window=""):
    """受け取りファイルへ1行足す（JSON Lines）。1行の形は Claude Code のフックが書く行（at・seat_dir・session_id・text）にそろえ、
    入力パッドからは分からない席のフォルダと session_id は空にし、来た所（source）と送り先の窓の題名（window）を足す。
    書けなければ例外をそのまま上げる（呼ぶ側が欄に文を残す）。"""
    rec = {"at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "seat_dir": "", "session_id": "",
           "text": text, "source": "input_pad", "window": window}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return rec


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


# ---------------- 下回り ----------------

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / f"input_pad_{datetime.now():%Y%m%d}.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception as e:  # 設定が壊れていても既定で動く
            logging.warning("config.json を読めませんでした（既定で動きます）: %s", e)
    return cfg


def save_config_value(key, value):
    """config.json の1項目だけを書き換える（ほかの項目は残す）。"""
    try:
        cur = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
        cur[key] = value
        CONFIG_PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logging.warning("config.json を書けませんでした: %s", e)


def single_instance():
    """二重起動を防ぐ。すでに動いていれば False。"""
    kernel32.CreateMutexW(None, False, "Local\\terminal_japanese_input_pad")
    return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS


def set_dpi_aware():
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def class_name(hwnd):
    buf = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value


def window_title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def is_terminal(hwnd):
    return bool(hwnd) and class_name(hwnd) == TERMINAL_CLASS and bool(user32.IsWindowVisible(hwnd))


def same_process(a, b):
    """2つの窓が同じプログラムのものか。"""
    pa, pb = wt.DWORD(), wt.DWORD()
    user32.GetWindowThreadProcessId(a, ctypes.byref(pa))
    user32.GetWindowThreadProcessId(b, ctypes.byref(pb))
    return pa.value != 0 and pa.value == pb.value


def list_terminals():
    """開いている Windows Terminal の窓をすべて返す（v0.8.0。窓ごとに入力窓を作るため。v0.7.0 までは一番手前の1つだけを選んでいた）。"""
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(h, _):
        if is_terminal(h):
            found.append(h)
        return True

    user32.EnumWindows(cb, 0)
    return found


def is_cloaked(hwnd):
    """別の仮想デスクトップへ移した窓など、Windows が画面に描いていない窓か。"""
    v = wt.DWORD()
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(v), ctypes.sizeof(v)) == 0:
        return v.value != 0
    return False


def window_rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def visible_rect(hwnd):
    """見えている枠の位置（Windows 11 の透明な縁を除いた位置）。"""
    r = wt.RECT()
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r), ctypes.sizeof(r)) == 0:
        return r.left, r.top, r.right, r.bottom
    return window_rect(hwnd)


def work_area(hwnd):
    """その窓がある画面の、タスクバーを除いた広さ。"""
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST), ctypes.byref(mi))
    w = mi.rcWork
    return w.left, w.top, w.right, w.bottom


def work_area_at(x, y):
    """その点がある画面の、タスクバーを除いた広さ。そこに画面が無ければ None。"""
    mon = user32.MonitorFromPoint(wt.POINT(x, y), MONITOR_DEFAULTTONULL)
    if not mon:
        return None
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(mon, ctypes.byref(mi))
    w = mi.rcWork
    return w.left, w.top, w.right, w.bottom


def set_visible_rect(hwnd, left, top, right, bottom):
    """見えている枠がこの位置になるよう、透明な縁の分を足して動かす。"""
    wl, wt_, wr, wb = window_rect(hwnd)
    vl, vt, vr, vb = visible_rect(hwnd)
    left -= vl - wl
    top -= vt - wt_
    right += wr - vr
    bottom += wb - vb
    user32.SetWindowPos(hwnd, None, left, top, right - left, bottom - top, SWP_NOZORDER | SWP_NOACTIVATE)


def force_foreground(hwnd):
    """窓を前に出す。普通に頼んで通らないときは入力スレッドをつないで頼み直す。"""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    if user32.SetForegroundWindow(hwnd):
        return True
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    user32.AttachThreadInput(cur, fg_tid, True)
    try:
        return bool(user32.SetForegroundWindow(hwnd))
    finally:
        user32.AttachThreadInput(cur, fg_tid, False)


def wait_modifiers_released(timeout=1.5):
    """Ctrl+Enter の Ctrl を押したまま貼り付けると Ctrl+Enter が相手へ届くので、離すまで待つ。"""
    end = time.time() + timeout
    keys = (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN)
    while time.time() < end:
        if not any(user32.GetAsyncKeyState(k) & 0x8000 for k in keys):
            return True
        time.sleep(0.02)
    for k in keys:  # 離されないままなら、押されていないことにして進む
        if user32.GetAsyncKeyState(k) & 0x8000:
            user32.keybd_event(k, 0, KEYEVENTF_KEYUP, 0)
    return False


def tap(vk, with_ctrl=False):
    if with_ctrl:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    if with_ctrl:
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


class HotkeyThread(threading.Thread):
    """RegisterHotKey は登録したスレッドのメッセージループに届くので、専用スレッドで待つ。"""

    def __init__(self, modifiers, vk, events, tab_allowed=None, snap_target=None):
        super().__init__(daemon=True)
        self.modifiers, self.vk, self.events = modifiers, vk, events
        self.tab_allowed = tab_allowed   # Tab で飛んでよいかを答える関数（None なら Tab は見張らない）
        self.snap_target = snap_target   # 入力窓 → 受け持ちの Windows Terminal の窓を答える関数（v0.9.0）
        self.snap_eaten = set()          # 横取りした矢印キー（離したときの知らせも相手へ渡さない・押しっぱなしの繰り返しは1回と数える）
        self.thread_id = None
        self.ok = threading.Event()
        self.error = None
        self.tab_hook = None
        self.tab_eaten = False           # 横取りした Tab の、離したときの知らせも相手へ渡さないため

    def on_key(self, code, wparam, lparam):
        """Tab で入力窓へ飛ぶ（v0.5.0）。
        横取りするのは、Windows Terminal が前にあり、Tab だけが押され、人が押したキーのときだけ。
        Claude Code の入力欄の Tab は候補が出ているときだけ働くので、ふだんは失うものが無い（2026-10-01 説明書と実機で確認）。
        ここは Windows がキーを止めて待っている途中なので、手早く済ませ、入力窓の操作は置き場（events）に入れて Tk 側でやる。"""
        try:
            if code == 0:
                k = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if k.vkCode in SNAP_KEYS and self.snap_target:
                    if self.on_snap_key(k, wparam):
                        return 1
                if k.vkCode == VK_TAB and self.tab_allowed:
                    if wparam == WM_KEYUP and self.tab_eaten:
                        self.tab_eaten = False
                        return 1
                    if (wparam == WM_KEYDOWN and not (k.flags & LLKHF_INJECTED)
                            and not any(user32.GetAsyncKeyState(m) & 0x8000
                                        for m in (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN))):
                        fg = user32.GetForegroundWindow()
                        if is_terminal(fg) and self.tab_allowed(fg):
                            self.tab_eaten = True
                            self.events.put(("hotkey", fg))
                            return 1
        except Exception:
            logging.exception("tab hook failed")
        return user32.CallNextHookEx(None, code, wparam, lparam)

    def on_snap_key(self, k, wparam):
        """入力窓が選ばれているときの Win＋矢印を受け取り、受け持ちの Windows Terminal の窓を寄せる（v0.9.0）。
        Windows は Win＋矢印を「いま選ばれている窓」にかける。入力窓へ自動で移る働き（v0.6.0）があるので、選ばれているのはほぼいつも入力窓で、
        入力窓は枠なしの窓のため Windows は何もしなかった。横取りしたら True を返す。"""
        if wparam in (WM_KEYUP, WM_SYSKEYUP):
            if k.vkCode in self.snap_eaten:
                self.snap_eaten.discard(k.vkCode)
                return True
            return False
        if wparam not in (WM_KEYDOWN, WM_SYSKEYDOWN) or k.flags & LLKHF_INJECTED:
            return False
        if not any(user32.GetAsyncKeyState(m) & 0x8000 for m in (VK_LWIN, VK_RWIN)):
            return False
        if any(user32.GetAsyncKeyState(m) & 0x8000 for m in (VK_CONTROL, VK_SHIFT, VK_MENU)):
            return False   # Win＋Shift＋矢印などは今までどおり Windows に任せる
        if k.vkCode in self.snap_eaten:
            return True    # 押しっぱなしの繰り返しは寄せ直さない
        target = self.snap_target(user32.GetForegroundWindow())
        if not target:
            return False
        self.snap_eaten.add(k.vkCode)
        # Windows は「Win を押して何も押さずに離した」ときにスタートメニューを開く。矢印をここで止めたので、
        # 割り当ての無いキーを1回挟み、Win だけを押したのではないと Windows に伝える
        user32.keybd_event(VK_MENU_MASK, 0, 0, 0)
        user32.keybd_event(VK_MENU_MASK, 0, KEYEVENTF_KEYUP, 0)
        self.events.put(("snap", (target, SNAP_KEYS[k.vkCode])))
        return True

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, HOTKEY_ID, self.modifiers | MOD_NOREPEAT, self.vk):
            self.error = ctypes.get_last_error()
            self.ok.set()
            return
        if self.tab_allowed or self.snap_target:
            # 見張りの知らせは、見張りを付けたこのスレッドのメッセージループの中で届く
            self.tab_proc = HOOKPROC(self.on_key)   # 消えないよう持っておく
            self.tab_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.tab_proc, kernel32.GetModuleHandleW(None), 0)
            if self.tab_hook:
                logging.info("key watch on (tab jump=%s, win+arrow=%s)", bool(self.tab_allowed), bool(self.snap_target))
            else:
                logging.error("tab hook failed to install (error %s)", ctypes.get_last_error())
        self.ok.set()
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.events.put(("hotkey", user32.GetForegroundWindow()))
        if self.tab_hook:
            user32.UnhookWindowsHookEx(self.tab_hook)
        user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)


# ---------------- 入力窓 ----------------

class Pad:
    """Windows Terminal の窓1つを受け持つ入力窓（v0.8.0〜。窓ごとに1つ作る）。"""

    def __init__(self, root, cfg, manager, target):
        self.root = root
        self.cfg = cfg
        self.manager = manager
        self.target = target          # 受け持ちの Windows Terminal の窓（変わらない）
        self.alive = True
        self.last_layout = None
        self.shown = False
        self.sending = False
        self.saved_rect = None        # Win＋矢印で寄せる前の位置（Win＋↓ で戻すため・v0.9.0）

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)   # 枠なし。Windows Terminal の窓の続きに見えるようにする
        # 入力窓だと一目で分かるように（v0.3.1）：
        #   上の太い線＝打てるときはオレンジ・元の窓にいるときは灰色／青みのある背景／左の見出し／空のときの薄い案内
        self.win.configure(bg=PAD_BG)
        # 上の線は、つかんで上下に動かすと入力窓の高さが変わる仕切りを兼ねる（v0.3.5）。
        # 見た目の線は ACCENT_LINE の太さのまま、つかめる幅は GRIP_H まで広げる
        self.grip = tk.Frame(self.win, height=GRIP_H, bg=PAD_BG, cursor="sb_v_double_arrow")
        self.grip.pack(fill="x", side="top")
        self.grip.pack_propagate(False)
        self.line = tk.Frame(self.grip, height=ACCENT_LINE, bg=ACCENT_OFF, cursor="sb_v_double_arrow")
        self.line.pack(fill="x", side="top")
        for w in (self.grip, self.line):
            w.bind("<ButtonPress-1>", self.on_grip_press)
            w.bind("<B1-Motion>", self.on_grip_drag)
            w.bind("<ButtonRelease-1>", self.on_grip_release)

        # 文字の大きさを後から変えられるよう、名前つきの字体にする（v0.4.0）。
        # 字体はすべての入力窓で1つを分け合う（v0.8.0。1つの入力窓で大きさを変えると、ほかの入力窓も同じ大きさになる）
        self.font, self.font_bold = manager.font, manager.font_bold
        font = self.font
        body = tk.Frame(self.win, bg=PAD_BG)
        body.pack(fill="both", expand=True)
        row = tk.Frame(body, bg=PAD_BG)
        row.pack(fill="both", expand=True)
        # 見出し・案内・打つところの3つで、字の始まる高さをそろえる（v0.3.2）。
        # それぞれの部品に付いていた余白（Label の既定 pady=1・bd 等）を 0 にし、上の余白は TEXT_TOP だけにする
        self.label = tk.Label(row, text="入力 ›", bg=PAD_BG, fg=ACCENT_OFF, padx=0, pady=0, bd=0,
                              highlightthickness=0, font=self.font_bold)
        self.label.pack(side="left", anchor="n", padx=(12, 8), pady=(TEXT_TOP, 0))
        self.text = tk.Text(row, font=font, wrap="char", height=int(cfg["pad_lines"]),
                            undo=True, bd=0, padx=0, pady=TEXT_TOP, highlightthickness=0, spacing1=0,
                            bg=PAD_BG, fg="#f0f0f0", insertbackground="#ffffff", insertwidth=2)
        self.text.pack(side="left", fill="both", expand=True)
        self.text.tag_configure("placeholder", foreground="#6c7686")
        self.ph_on = False        # いま入力欄に薄い案内が入っているか
        self.status = tk.Label(body, anchor="e", padx=10, pady=2, bg=PAD_BG, fg="#8a93a3",
                               font=(cfg["font_family"], 9),
                               text="Enter＝送信　Ctrl+Enter＝貼り付けだけ　Shift+Enter＝改行　Ctrl+C＝止める　Esc＝元の窓へ　Ctrl+Shift+J＝行き来"
                                    + ("　黒い画面で Tab＝ここへ" if cfg.get("tab_jump", True) else ""))
        self.status.pack(fill="x")
        self.text.bind("<FocusIn>", lambda e: (self.set_focus_look(True), self.update_placeholder()), add="+")
        self.text.bind("<FocusOut>", lambda e: (self.set_focus_look(False), self.update_placeholder()), add="+")
        self.text.bind("<KeyRelease>", lambda e: self.update_placeholder(), add="+")
        self.hook_ime()

        self.text.bind("<Return>", self.on_return)
        # 入力窓が空のときの ↑↓ は元の窓へ送る（v0.10.0＝Claude Code の選ぶ画面）
        self.text.bind("<Up>", lambda e: self.on_nav_key(e, VK_UP))
        self.text.bind("<Down>", lambda e: self.on_nav_key(e, VK_DOWN))
        self.text.bind("<Control-Return>", lambda e: (self.send(submit=False), "break")[1])
        self.text.bind("<Shift-Return>", self.on_shift_enter)
        self.text.bind("<Escape>", lambda e: (self.focus_target(), "break")[1])
        self.text.bind("<Control-c>", self.on_ctrl_c)
        self.text.bind("<Control-C>", self.on_ctrl_c)   # Caps Lock が入っているとき
        self.text.bind("<Button-1>", lambda e: self.activate(), add="+")

        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(label="書きかけを消す", command=lambda: (self.text.delete("1.0", "end"), setattr(self, "ph_on", False), self.update_placeholder()))
        menu.add_separator()
        menu.add_command(label="文字を大きく（Ctrl＋ホイール上）", command=lambda: self.change_font_size(+1))
        menu.add_command(label="文字を小さく（Ctrl＋ホイール下）", command=lambda: self.change_font_size(-1))
        menu.add_separator()
        menu.add_command(label="入力窓をしまう（Ctrl＋Shift＋J で戻す）", command=self.turn_off)
        menu.add_separator()
        menu.add_command(label=f"{APP_NAME}を終了する", command=self.quit_app)
        self.text.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.text.bind("<Control-MouseWheel>", lambda e: (self.change_font_size(+1 if e.delta > 0 else -1), "break")[1])

        # ファイルや画像を落とすと、その場所（フルパス）が入る（v0.4.0）
        if DND_FILES:
            self.text.drop_target_register(DND_FILES)
            self.text.dnd_bind("<<Drop>>", self.on_drop)

        self.off = False          # 入力窓をしまっているか（v0.4.0）
        self.pad_h = cfg.get("pad_height")   # オレンジの線で決めた高さ（config.json に覚える）
        self.grip_dragging = False
        self.drag_pad_bottom = None
        self.topmost = False
        self.prev_fg = None           # 前の回に前にあった窓（Windows Terminal が新しく選ばれたかを見るため）
        self.focus_pending = False    # Windows Terminal が選ばれ、入力窓へ移る順番を待っている
        self.stay_in_target = False   # Esc などで自分から元の窓へ戻った（自動で入力窓へ移さない）

        self.win.update_idletasks()
        self.min_height = self.win.winfo_reqheight()   # これより低くはしない（3行＋案内の高さ）
        self.update_placeholder()

    def set_focus_look(self, focused):
        color = ACCENT_ON if focused else ACCENT_OFF
        self.line.configure(bg=color)
        self.label.configure(fg=color)

    def update_placeholder(self):
        """薄い案内は、打てない状態（元の窓に戻っている）で空のときだけ、入力欄の中に薄い色の文字として入れる（v0.4.0）。
        別の部品として重ねると、文字の大きさを変えたあとに打った文字が欠けて見えた（2026-10-01 試し窓で3回確認）ので、部品は重ねない。
        打てる状態になったら案内は消す（そのときはカーソルとオレンジの線で入力窓だと分かる）。"""
        focused = self.root.focus_get() is self.text
        if self.ph_on and (focused or self.text.get("1.0", "end-1c") != PLACEHOLDER_TEXT):
            self.text.delete("1.0", "end")
            self.ph_on = False
        if not self.ph_on and not focused and not self.text.get("1.0", "end-1c"):
            self.text.insert("1.0", PLACEHOLDER_TEXT, "placeholder")
            self.text.mark_set("insert", "1.0")
            self.ph_on = True

    def hook_ime(self):
        """日本語入力で確定した文字を、Tk を通さず入力窓が直接受け取る（v0.4.4〜）。
        Tk は確定した文字のうちハイフンなどを落とす（2026-10-01）。
        v0.4.4 は入力欄の窓だけに付けたが効かず、どの窓に知らせが届くか分からないので、v0.4.5 で入力窓を作る3つの窓すべてに付ける。
        確定文字列（GCS_RESULTSTR）だけを自分で入れ、その知らせは Tk に渡さない。変換中の表示などはそのまま Tk に渡す。"""
        self.win.update_idletasks()
        targets = {"text": self.text.winfo_id(), "inner": self.win.winfo_id(), "frame": self.hwnd()}
        self.ime_procs = {}
        self.ime_queue = queue.Queue()
        self.root.after(30, self.drain_ime)

        def make(role, old):
            def proc(hwnd, msg, wparam, lparam):
                if msg == WM_IME_COMPOSITION and (lparam & GCS_RESULTSTR):
                    try:
                        himc = imm32.ImmGetContext(hwnd)
                        size = imm32.ImmGetCompositionStringW(himc, GCS_RESULTSTR, None, 0)
                        result = ""
                        if size > 0:
                            buf = ctypes.create_unicode_buffer(size // 2 + 1)
                            imm32.ImmGetCompositionStringW(himc, GCS_RESULTSTR, buf, size)
                            result = buf.value[: size // 2]
                        imm32.ImmReleaseContext(hwnd, himc)
                        # 記録には文字数だけ残す（v0.4.7。打った文の中身は英数字も含めて残さない）
                        logging.info("ime result at %s: len=%d", role, len(result))
                        if result:
                            # ここ（Windows の知らせの途中）で Tk を呼ぶと、Tk が止まって入力窓ごと落ちる
                            # （2026-10-01 11:15:35 実際に落ちた・0xc0000409）。置き場に入れておき、Tk の順番の中で入れる
                            self.ime_queue.put(result)
                            return 0
                    except Exception:
                        logging.exception("ime hook failed")
                return user32.CallWindowProcW(old[0], hwnd, msg, wparam, lparam)
            return proc

        for role, hwnd in targets.items():
            if not hwnd or hwnd in [h for h, _ in self.ime_procs.values()]:
                continue
            old = [None]
            fn = WNDPROC(make(role, old))
            old[0] = user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(fn, ctypes.c_void_p))
            self.ime_procs[role] = (hwnd, fn)   # 消えないよう持っておく
        logging.info("ime hook installed %s", {r: h for r, (h, _) in self.ime_procs.items()})

    def drain_ime(self):
        try:
            while True:
                self.insert_ime_result(self.ime_queue.get_nowait())
        except queue.Empty:
            pass
        except Exception:
            logging.exception("ime insert failed")
        if self.alive:
            self.root.after(30, self.drain_ime)

    def insert_ime_result(self, result):
        if self.ph_on:
            self.text.delete("1.0", "end")
            self.ph_on = False
        self.text.insert("insert", result)
        self.text.see("insert")

    def current_text(self):
        """打った文（薄い案内は数えない）。"""
        return "" if self.ph_on else self.text.get("1.0", "end-1c")

    # --- ファイルを落とす ---
    def on_drop(self, event):
        paths = [os.path.normpath(p) for p in self.root.tk.splitlist(event.data)]   # 区切りの / を Windows の形へ直す
        if self.ph_on:
            self.text.delete("1.0", "end")
            self.ph_on = False
        text = " ".join(f'"{p}"' if " " in p else p for p in paths)
        if self.text.index("insert") != "1.0" and not self.text.get("insert-1c").isspace():
            text = " " + text
        self.text.insert("insert", text + " ")
        self.update_placeholder()
        self.activate()
        logging.info("dropped %d file(s)", len(paths))
        return event.action

    # --- 文字の大きさ ---
    def change_font_size(self, step):
        size = max(MIN_FONT, min(MAX_FONT, int(self.font.cget("size")) + step))
        self.font.configure(size=size)
        self.font_bold.configure(size=size)
        for pad in self.manager.pads.values():   # 字体は分け合っているので、すべての入力窓を測り直す（v0.8.0）
            pad.refit_font()
        save_config_value("font_size", size)
        logging.info("font size -> %d (min_h=%d)", size, self.min_height)

    def refit_font(self):
        self.win.update_idletasks()
        self.min_height = self.win.winfo_reqheight()   # 3行＋案内に要る高さ（文字の大きさに合わせて測り直す）
        self.last_layout = None
        # 文字の大きさを変えたあと、入力欄の中の表示が少しずれて文字の上が欠けることがある（2026-10-01 試し窓で確認）。
        # 字体を付け直して、表示を一番上から並べ直す
        self.text.configure(font=self.font)
        self.text.yview_moveto(0)
        self.text.see("insert")

    # --- 入力窓を出す・しまう ---
    def turn_off(self):
        h = self.last_layout[3] if self.last_layout else 0
        self.off = True
        self.hide("off by user")
        if self.target and user32.IsWindow(self.target):
            wl, wt_, wr, wb = work_area(self.target)
            vl, vt, vr, vb = visible_rect(self.target)
            if h and vb + h <= wb + 2:   # 入力窓があった場所まで、Windows Terminal の窓を伸ばして返す
                set_visible_rect(self.target, vl, vt, vr, min(vb + h, wb))
            force_foreground(self.target)
        logging.info("pad off (h=%s)", h)

    def turn_on(self):
        self.off = False
        self.last_layout = None   # 次の dock で、下に場所が無ければ窓を縮めて出す
        logging.info("pad on")

    def want_height(self, wt_, wb):
        """出す高さ＝利用者がオレンジの線で決めた高さ（決めていなければ3行＋案内）。画面の高さの MAX_PAD_RATIO まで。"""
        h = max(self.min_height, int(self.pad_h or 0))
        return min(h, max(self.min_height, int((wb - wt_) * MAX_PAD_RATIO)))

    def hwnd(self):
        return user32.GetAncestor(self.win.winfo_id(), 2) or self.win.winfo_id()

    # --- Win＋矢印で寄せる（v0.9.0・4分の1は v0.9.1） ---
    # 今の位置から押した向きへ1段ずつ動く。上下の段＝(左右半分 ↔ 上下4分の1)、画面いっぱいは↑の行き止まり
    SNAP_UP = {"left": "top_left", "right": "top_right", "bottom_left": "left", "bottom_right": "right"}
    SNAP_DOWN = {"left": "bottom_left", "right": "bottom_right", "top_left": "left", "top_right": "right"}
    SNAP_SIDE = {("top_left", "right"): "top_right", ("top_right", "left"): "top_left",
                 ("bottom_left", "right"): "bottom_right", ("bottom_right", "left"): "bottom_left"}

    def snap(self, direction):
        """受け持ちの Windows Terminal の窓を寄せる。入力窓の分の高さは、いつも窓のすぐ下に空けておく。
        ↑＝画面いっぱい（左右半分のときは上の4分の1、下の4分の1のときは左右半分）
        ↓＝左右半分のときは下の4分の1、上の4分の1のときは左右半分、ほかに寄せていれば寄せる前の位置、寄せていなければ最小化
        ←→＝左半分・右半分（同じ向きをもう一度押すと隣の画面の反対側の半分へ、反対向きを押すと寄せる前の位置へ。
             4分の1のときは同じ高さの反対側の4分の1へ）"""
        t = self.target
        if not t or not user32.IsWindow(t):
            return
        if user32.IsZoomed(t):
            user32.ShowWindow(t, SW_RESTORE)
        cur = visible_rect(t)
        area = work_area(t)
        layouts = self.snap_layouts(area)
        state = next((name for name, r in layouts.items() if self.rect_close(cur, r)), None)
        if state is None and direction != "down":
            self.saved_rect = cur          # 寄せる前の位置を覚える
        new = None
        if direction == "up":
            new = layouts[self.SNAP_UP.get(state, "full")]
        elif direction == "down":
            if state is None:
                user32.ShowWindow(t, SW_MINIMIZE)
                logging.info("snap down: free -> minimized")
                return
            if state in self.SNAP_DOWN:
                new = layouts[self.SNAP_DOWN[state]]
            elif self.saved_rect:
                new = self.saved_rect
            else:
                # 寄せる前の位置を知らない（起動前から寄せてあった）ときは、画面の真ん中に 2/3 の大きさで出す
                l, t_, r, b = layouts["full"]
                w, h = (r - l) * 2 // 3, (b - t_) * 2 // 3
                x, y = l + (r - l - w) // 2, t_ + (b - t_ - h) // 2
                new = (x, y, x + w, y + h)
        elif (state, direction) in self.SNAP_SIDE:
            new = layouts[self.SNAP_SIDE[(state, direction)]]
        else:
            same, other = ("left", "right") if direction == "left" else ("right", "left")
            if state == same or (state or "").endswith("_" + same):
                # 端にいるのに同じ向きをもう一度＝その向きの隣の画面の、反対側の半分へ
                x = area[0] - 1 if direction == "left" else area[2] + 1
                next_area = work_area_at(x, (area[1] + area[3]) // 2)
                if next_area is None:
                    return
                new = self.snap_layouts(next_area)[other]
            elif state == other and self.saved_rect:
                new = self.saved_rect      # 反対向き＝元の位置へ（Windows と同じ）
            else:
                new = layouts[same]
        set_visible_rect(t, *new)
        if new == self.saved_rect:
            self.saved_rect = None
        logging.info("snap %s: %s -> %s", direction, state or "free", new)
        self.dock_once()

    def snap_layouts(self, area):
        """その画面で寄せる先の位置。どれも、窓のすぐ下に入力窓の分を空ける
        （4分の1は、上下それぞれの半分の中に「窓＋入力窓」が収まる形）。"""
        wl, wt_, wr, wb = area
        ph = self.want_height(wt_, wb)
        mid_x, mid_y = (wl + wr) // 2, (wt_ + wb) // 2
        return {
            "full": (wl, wt_, wr, wb - ph),
            "left": (wl, wt_, mid_x, wb - ph), "right": (mid_x, wt_, wr, wb - ph),
            "top_left": (wl, wt_, mid_x, mid_y - ph), "top_right": (mid_x, wt_, wr, mid_y - ph),
            "bottom_left": (wl, mid_y, mid_x, wb - ph), "bottom_right": (mid_x, mid_y, wr, wb - ph),
        }

    @staticmethod
    def rect_close(a, b):
        return all(abs(x - y) <= SNAP_TOLERANCE for x, y in zip(a, b))

    # --- くっつく ---
    def dock(self):
        """200ms ごとに PadManager から呼ばれる（v0.7.0 までは自分で次の回を決めていた）。"""
        try:
            self.dock_once()
            if self.cfg.get("auto_focus", True) and not self.sending:
                self.auto_focus()
        except Exception:
            logging.exception("dock failed")

    def dock_once(self):
        """受け持ちの Windows Terminal の窓の下にくっつける（受け持ちの窓は作ったときに決まり、変わらない・v0.8.0）。"""
        if self.sending:
            return
        if self.off or user32.IsIconic(self.target) or is_cloaked(self.target):
            # 別の仮想デスクトップへ移した窓は「見えている」と答えるが画面には無いので、隠れているものとして扱う
            self.hide("off" if self.off else ("terminal minimized" if user32.IsIconic(self.target) else "terminal cloaked"))
            return

        wl, wt_, wr, wb = work_area(self.target)
        h = self.want_height(wt_, wb)
        if user32.IsZoomed(self.target):
            # 最大化のままでは下に置けないので、元に戻して「画面いっぱい−入力窓の分」にする
            user32.ShowWindow(self.target, SW_RESTORE)
            set_visible_rect(self.target, wl, wt_, wr, wb - h)
            logging.info("terminal un-maximized and shrunk for pad (h=%d)", h)
        vl, vt, vr, vb = visible_rect(self.target)
        dragging = user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000
        if vb + h > wb and not dragging and not self.grip_dragging:
            new_bottom = wb - h
            if new_bottom - vt >= MIN_TERMINAL_HEIGHT:
                set_visible_rect(self.target, vl, vt, vr, new_bottom)
                logging.info("terminal shrunk bottom %d -> %d", vb, new_bottom)
                vl, vt, vr, vb = visible_rect(self.target)
        self.place_below(vl, vb, vr, h, wb)
        self.show()
        self.keep_z_order()

    def auto_focus(self):
        """入力窓を出しているとき、Windows Terminal が選ばれたら自動で入力窓へ移る（v0.6.0）。
        入力窓から Esc・Ctrl+Shift+J で自分から元の窓へ戻ったときは移さない（許可の質問に答える・Esc で止めるなど、元の窓で打つため）。
        ほかの窓を一度選んでから戻ってくると、また移る。
        マウスのボタンを押している間は待つ（Windows Terminal の中で文字をなぞって選んでいる途中で奪わないため）。"""
        fg = user32.GetForegroundWindow()
        me = self.hwnd()
        if not fg:
            return   # 窓を切り替える途中の「どの窓も選ばれていない」一瞬は数えない（v0.6.1）
        # Windows Terminal のほかの窓・ほかの入力窓は、同じプログラムでも別の窓として数える（v0.8.0。窓ごとに入力窓があるため）
        if fg != self.target and same_process(fg, self.target) and not is_terminal(fg):
            fg = self.target   # Windows Terminal 自身の小さな窓は、Windows Terminal として数える（v0.6.1）
        elif fg != me and same_process(fg, me) and fg not in self.manager.pad_hwnds():
            fg = me            # 入力窓自身の別の窓（右クリックのメニューなど）は、入力窓として数える（v0.6.1）
        if fg not in (self.target, me) and self.stay_in_target:
            # v0.6.0 では Esc で戻っても引き戻された。
            # 何の窓のせいでこの印を消したかを残し、次に起きたら原因を追えるようにする
            self.stay_in_target = False
            logging.info("stay cleared by %r", class_name(fg))
        if fg != self.target:
            self.focus_pending = False
        elif self.prev_fg != self.target:
            self.focus_pending = True
            self.pending_from = class_name(self.prev_fg) if self.prev_fg else "(none)"
        self.prev_fg = fg
        if not self.focus_pending or user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
            return
        self.focus_pending = False
        if self.stay_in_target or self.off or not self.shown:
            return
        logging.info("auto focus -> pad (from %r)", getattr(self, "pending_from", ""))
        self.activate()

    def keep_z_order(self):
        """Windows Terminal か入力窓が選ばれている間は「いつも手前」にし、ほかの窓が選ばれたらその後ろへ下がる（v0.4.2）。
        以前は HWND_TOP で手前に出していたが、選ばれていないプログラムからは Windows が止めることがあり、
        入力窓が Chrome の後ろに隠れたまま出てこなかった（2026-10-01 10:47〜11:01）。"""
        fg = user32.GetForegroundWindow()
        me = self.hwnd()
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        if fg in (self.target, me):
            if not self.topmost:
                user32.SetWindowPos(me, HWND_TOPMOST, 0, 0, 0, 0, flags)
                self.topmost = True
        elif self.topmost:
            user32.SetWindowPos(me, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            if fg:
                user32.SetWindowPos(me, fg, 0, 0, 0, 0, flags)   # いま選ばれている窓のすぐ後ろへ
            self.topmost = False

    def place_below(self, vl, vb, vr, h, wb):
        """窓のすぐ下に、決めた高さ h で出す（v0.4.0）。
        下に入りきらないときは、入る分まで低くし、それでも最小に足りなければ窓の一番下に重ねる。"""
        gap = wb - vb
        if gap >= h:
            y = vb
        elif gap >= self.min_height:
            h, y = gap, vb
        else:
            h, y = self.min_height, vb - self.min_height
        layout = (vl, y, vr - vl, h)
        if layout != self.last_layout:
            self.win.geometry(f"{vr - vl}x{h}+{vl}+{y}")
            self.last_layout = layout

    # --- 上の線をつかんで高さを変える ---
    def on_grip_press(self, event):
        """つかんだ時点の入力窓の下のふちを覚える（動かしている間、下のふちは動かさず、上の線だけを動かす）。"""
        self.grip_dragging = True
        self.drag_pad_bottom = (self.last_layout[1] + self.last_layout[3]) if self.last_layout else None

    def on_grip_drag(self, event):
        if not self.target or not user32.IsWindow(self.target) or self.drag_pad_bottom is None:
            return
        wl, wt_, wr, wb = work_area(self.target)
        vl, vt, vr, vb = visible_rect(self.target)
        bottom = self.drag_pad_bottom
        lowest = bottom - self.min_height                                        # 入力窓をこれより低くしない
        highest = max(vt + MIN_TERMINAL_HEIGHT, bottom - int((wb - wt_) * MAX_PAD_RATIO))
        new_top = max(highest, min(event.y_root, lowest))
        if new_top != vb:
            self.pad_h = bottom - new_top
            set_visible_rect(self.target, vl, vt, vr, new_top)
            self.place_below(vl, new_top, vr, self.pad_h, wb)

    def on_grip_release(self, event):
        self.grip_dragging = False
        if self.pad_h:
            save_config_value("pad_height", int(self.pad_h))
            self.cfg["pad_height"] = int(self.pad_h)   # これから開く窓の入力窓も同じ高さにする
            for pad in self.manager.pads.values():   # 高さもすべての入力窓でそろえる（v0.8.0。次の回にそれぞれの窓で合わせ直す）
                if pad is not self:
                    pad.pad_h = self.pad_h
                    pad.last_layout = None
        logging.info("pad resized by grip: pad h=%s", self.pad_h)

    def show(self):
        # 「出している」という自分の覚えではなく、Windows に毎回聞いて確かめる（v0.4.1）。
        # 2026-10-01 10:37、Windows Terminal を最小化→元に戻したあと入力窓が隠れたまま出てこなかった
        if not user32.IsWindowVisible(self.hwnd()):
            self.win.deiconify()
            self.last_layout = None
            logging.info("pad shown")
        self.shown = True

    def hide(self, reason=""):
        if user32.IsWindowVisible(self.hwnd()) or self.shown:
            self.win.withdraw()
            logging.info("pad hidden (%s)", reason)
        self.shown = False

    # --- 行き来 ---
    def on_hotkey(self, fg):
        if self.off:
            self.turn_on()
            self.dock_once()
            self.activate()
            return
        if fg == self.hwnd():
            self.focus_target()
            return
        self.activate()

    def destroy(self):
        """受け持ちの窓が閉じられたので、この入力窓も消す（v0.8.0）。"""
        self.alive = False
        try:
            self.win.destroy()
        except Exception:
            logging.exception("pad destroy failed")

    def activate(self):
        # 入力窓へ戻ったら、自動で入力窓へ移る働きも戻す（v0.6.2）
        self.stay_in_target = False
        self.manager.last_pad = self
        if self.target and user32.IsIconic(self.target):
            user32.ShowWindow(self.target, SW_RESTORE)
        self.show()
        force_foreground(self.hwnd())
        self.text.focus_force()

    def focus_target(self):
        self.stay_in_target = True    # 自分から戻ったので、自動で入力窓へ移さない（auto_focus）
        logging.info("back to terminal (stay)")
        if self.target and user32.IsWindow(self.target):
            force_foreground(self.target)

    def on_ctrl_c(self, event):
        """入力窓の中の Ctrl+C（v0.7.0）。
        文字を選んでいるときは今までどおりコピー。選んでいないときは元の窓へ Ctrl+C を送り、Claude Code・Codex の動きを止める。
        v0.6.3 までは Tk が Ctrl+C をコピーとして受け取って元の窓へ届かず、元の窓をクリックしても入力窓へ引き戻されるので、止める手が Esc で戻ってからしか無かった。"""
        if self.text.tag_ranges("sel"):
            return None
        self.send_ctrl_c()
        return "break"

    def send_ctrl_c(self):
        self.send_key(VK_C, "ctrl+c", with_ctrl=True)

    def send_key(self, vk, label, with_ctrl=False):
        """元の窓を前に出してキーを1回送り、入力窓へ戻る（Ctrl+C・v0.7.0／↑↓Enter・v0.10.0）。"""
        if not self.target or not user32.IsWindow(self.target):
            self.status.config(text=f"{label} の送り先の Windows Terminal が見つかりません。", fg="#ff8080")
            logging.warning("%s aborted: no target", label)
            return
        self.sending = True
        try:
            if not force_foreground(self.target):
                logging.warning("SetForegroundWindow failed target=%s", self.target)
            time.sleep(0.15)
            tap(vk, with_ctrl=with_ctrl)
            time.sleep(0.15)
            logging.info("%s sent target=%r", label, window_title(self.target))
        finally:
            self.sending = False
        self.activate()   # 送ったあとも入力窓へ戻り、続けて打てるようにする

    def composing(self):
        """日本語入力の変換中か（変換中の ↑↓Enter は候補を選ぶ・確定するためのキーなので、元の窓へ送らない）。"""
        try:
            # 確定文字は inner の窓に届いている（記録の「ime result at inner」）。キーが届いている窓と入力窓の3つの窓を全部見る
            for hwnd in {user32.GetFocus(), self.text.winfo_id(), self.win.winfo_id(), self.hwnd()}:
                if not hwnd:
                    continue
                ctx = imm32.ImmGetContext(hwnd)
                if not ctx:
                    continue
                try:
                    if imm32.ImmGetCompositionStringW(ctx, GCS_COMPSTR, None, 0) > 0:
                        return True
                finally:
                    imm32.ImmReleaseContext(hwnd, ctx)
            return False
        except Exception:
            logging.exception("composing check failed")
            return True   # 分からないときは送らない側に倒す

    def on_nav_key(self, event, vk):
        """入力窓が空で、Shift・Ctrl を押しておらず、変換中でないときだけ、↑↓ を元の窓へ送る。
        Claude Code の「このフォルダを信用しますか」や許可の質問は ↑↓ で選ぶので、入力窓にいると選べなかった（2026-10-05）。"""
        if self.current_text() or event.state & 0x5 or self.composing():
            return None   # 文字があるときは、入力窓の中でカーソルを動かす
        self.send_key(vk, "up" if vk == VK_UP else "down")
        return "break"

    def on_return(self, event):
        """文字があれば今までどおり送信。空なら Enter を元の窓へ送る（選ぶ画面で決める・v0.10.0）。"""
        if self.current_text() == "" and not self.composing():
            self.send_key(VK_RETURN, "enter")
        else:
            self.send(submit=True)
        return "break"

    def on_shift_enter(self, event):
        self.text.insert("insert", "\n")
        self.text.see("insert")
        return "break"

    # --- 貼り付け ---
    def show_status(self, text, color, ms=5000):
        """下の案内の行に知らせを出し、ms ミリ秒たったら元のキーの案内へ戻す。"""
        if not hasattr(self, "status_help"):
            self.status_help = (self.status.cget("text"), self.status.cget("fg"))
        self.status.config(text=text, fg=color)
        if getattr(self, "status_job", None):
            self.root.after_cancel(self.status_job)
        self.status_job = self.root.after(ms, lambda: self.status.config(text=self.status_help[0], fg=self.status_help[1]))

    def save_memo(self, body):
        """「メモ：」の文を、元の窓へ送らずに受け取りファイルへ書く（v0.11.0・config.json の memo_file を入れたときだけ）。
        Claude Code のフックでメモを止めると、止めた文が Claude Code の入力欄へ戻り、入力窓からは消せずに次の文とつながった
        （2026-10-10 に2回）。入力窓で受け取れば、元の窓へは1文字も行かない。
        書けたら欄を空にする。書けなければ欄に文を残し、赤字で知らせる（メモを消さない）。"""
        text = memo_body(body)
        if not text:
            self.show_status("メモの中身が空でした。「メモ：」のあとに書いて送ってください。", "#ff8080")
            return
        try:
            write_memo(self.cfg["memo_file"], text, window_title(self.target) if self.target else "")
        except Exception as e:
            logging.exception("memo save failed")
            self.show_status(f"メモを書けませんでした（{e}）。文は欄に残してあります。", "#ff8080", ms=15000)
            return
        logging.info("memo saved %d chars", len(text))
        self.text.delete("1.0", "end")
        self.text.edit_reset()
        self.update_placeholder()
        self.show_status("メモを受け取りファイルへ書きました（元の窓へは送っていません）", "#7ee787")

    def send(self, submit):
        body = self.current_text()
        if not body.strip():
            return
        if self.cfg.get("memo_file") and memo_body(body) is not None:
            self.save_memo(body)
            return
        if not self.target or not user32.IsWindow(self.target):
            self.status.config(text="貼り付け先の Windows Terminal が見つかりません。", fg="#ff8080")
            logging.warning("send aborted: no target")
            return
        self.sending = True
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(body)
            self.root.update()
            wait_modifiers_released()
            if not force_foreground(self.target):
                logging.warning("SetForegroundWindow failed target=%s", self.target)
            time.sleep(0.15)
            tap(VK_V, with_ctrl=True)
            if submit:
                time.sleep(0.35)
                tap(VK_RETURN)
            time.sleep(0.15)
            logging.info("sent %d chars submit=%s target=%r", len(body), submit, window_title(self.target))
            self.text.delete("1.0", "end")
            self.text.edit_reset()
            self.update_placeholder()
        finally:
            self.sending = False
        self.activate()   # 送ったあとも入力窓へ戻り、続けて打てるようにする

    def quit_app(self):
        logging.info("quit by user")
        self.root.event_generate("<<QuitPad>>")


class PadManager:
    """Windows Terminal の窓を数え、窓ごとに入力窓を1つ作り、窓が閉じたら消す（v0.8.0）。
    v0.7.0 までは入力窓が1つで、選んだ窓の下へ移っていた（書きかけの文は窓をまたいで1つだった）。
    ホットキー・Tab・自動で入力窓へ移る働きは、いま前にある窓の入力窓へ向ける。"""

    def __init__(self, root, cfg):
        self.root = root
        self.cfg = cfg
        self.font = tkfont.Font(family=cfg["font_family"], size=int(cfg["font_size"]))
        self.font_bold = tkfont.Font(family=cfg["font_family"], size=int(cfg["font_size"]), weight="bold")
        self.pads = {}          # 受け持ちの Windows Terminal の窓 → 入力窓
        self.pad_to_target = {}  # 入力窓 → 受け持ちの窓（キーの見張りのスレッドから読む。Tk を呼ばずに引けるよう控える・v0.9.0）
        self.last_pad = None    # 最後に使った入力窓（Windows Terminal 以外が前にあるときのホットキーの行き先）
        self.sync()

    def pad_hwnds(self):
        return {p.hwnd() for p in self.pads.values()}

    def sync(self):
        """新しく開いた窓には入力窓を作り、閉じた窓の入力窓は消す。
        消すのは窓そのものが無くなったときだけ（隠れた・別の仮想デスクトップへ移しただけなら、書きかけを残すため消さない）。"""
        for h in list_terminals():
            if h not in self.pads:
                self.pads[h] = Pad(self.root, self.cfg, self, h)
                logging.info("pad created for %s %r (pads=%d)", h, window_title(h), len(self.pads))
        for h in [h for h in self.pads if not (user32.IsWindow(h) and class_name(h) == TERMINAL_CLASS)]:
            pad = self.pads.pop(h)
            if self.last_pad is pad:
                self.last_pad = None
            pad.destroy()
            logging.info("pad removed for closed terminal %s (pads=%d)", h, len(self.pads))
        self.pad_to_target = {p.hwnd(): h for h, p in self.pads.items()}   # 丸ごと差し替える（読む側と取り合わない）

    def tick(self):
        """200ms ごとに、窓を数え直し、それぞれの入力窓をくっつける。"""
        try:
            self.sync()
            for pad in list(self.pads.values()):
                pad.dock()
        except Exception:
            logging.exception("tick failed")
        finally:
            self.root.after(DOCK_INTERVAL_MS, self.tick)

    def pad_for(self, hwnd):
        """その窓（Windows Terminal の窓か、入力窓自身）を受け持つ入力窓。"""
        if hwnd in self.pads:
            return self.pads[hwnd]
        for p in self.pads.values():
            if p.hwnd() == hwnd:
                return p
        return None

    def on_hotkey(self, fg):
        pad = self.pad_for(fg)
        if pad is None:   # Windows Terminal 以外が前にあるときは、最後に使った入力窓へ
            pad = self.last_pad if self.last_pad and self.last_pad.alive else next(iter(self.pads.values()), None)
        if pad is None:
            logging.info("hotkey: no terminal window")
            return
        pad.on_hotkey(fg)

    def snap_target(self, fg):
        """入力窓が選ばれているなら、その受け持ちの Windows Terminal の窓（キーの見張りのスレッドから呼ばれる）。"""
        return self.pad_to_target.get(fg)

    def on_snap(self, target, direction):
        pad = self.pads.get(target)
        if pad is not None and not pad.off:
            pad.snap(direction)

    def tab_allowed(self, fg):
        """Tab を横取りしてよいか（キーの見張りのスレッドから呼ばれる）。その窓の入力窓があり、しまっていないときだけ。"""
        pad = self.pads.get(fg)
        return pad is not None and not pad.off


def parse_hotkey(cfg):
    mods = 0
    table = {"ctrl": MOD_CONTROL, "shift": MOD_SHIFT, "alt": MOD_ALT, "win": MOD_WIN}
    for m in cfg["hotkey_modifiers"]:
        mods |= table[m.lower()]
    key = str(cfg["hotkey_key"]).upper()
    vk = ord(key) if len(key) == 1 else int(key, 0)
    return mods, vk


def main():
    setup_logging()
    if not single_instance():
        logging.info("already running; exit")
        return
    set_dpi_aware()
    cfg = load_config()
    mods, vk = parse_hotkey(cfg)

    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    root.withdraw()
    if not TkinterDnD:
        logging.warning("tkinterdnd2 が無いので、ファイルを落とす機能は使えません")
    root.title(APP_NAME)
    manager = PadManager(root, cfg)

    events = queue.Queue()
    # 入力窓をしまっている間は Tab を横取りしない（しまったのは使う人の意思なので、Tab で勝手に出さない）
    tab_allowed = manager.tab_allowed if cfg.get("tab_jump", True) else None
    hk = HotkeyThread(mods, vk, events, tab_allowed, manager.snap_target)
    hk.start()
    hk.ok.wait(3)
    if hk.error is not None:
        logging.error("RegisterHotKey failed (error %s) mods=%s vk=%s", hk.error, mods, vk)
        from tkinter import messagebox
        messagebox.showerror(APP_NAME, "ホットキーを登録できませんでした。ほかのアプリが同じキーを使っている可能性があります。\n"
                                       f"config.json の hotkey_key を変えて起動し直してください。（エラー {hk.error}）")
        root.destroy()
        return
    logging.info("start v%s pid=%s hotkey mods=%s vk=%s pads=%d", VERSION, kernel32.GetCurrentProcessId(), mods, vk, len(manager.pads))

    def poll():
        try:
            while True:
                kind, arg = events.get_nowait()
                if kind == "hotkey":
                    manager.on_hotkey(arg)
                elif kind == "snap":
                    try:
                        manager.on_snap(*arg)
                    except Exception:
                        logging.exception("snap failed")
        except queue.Empty:
            pass
        root.after(50, poll)

    def quit_all(_=None):
        hk.stop()
        root.destroy()

    root.bind("<<QuitPad>>", quit_all)
    root.after(50, poll)
    root.after(DOCK_INTERVAL_MS, manager.tick)
    root.mainloop()
    logging.info("stop")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("crashed")
        raise
