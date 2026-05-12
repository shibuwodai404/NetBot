"""
图标模块
启动时把 SF Symbols 渲染成 PNG（template 模式），缓存到临时目录后
交给 rumps 当菜单栏图标使用。

为什么不用 emoji？emoji 渲染依赖 Apple Color Emoji 字体，颜色固定、
风格和 macOS 系统不统一；SF Symbols 是 Apple 官方矢量图标库，
自动适配深色 / 浅色菜单栏，视觉更原生。
"""

import os
import tempfile
from typing import Optional

# AppKit 通过 rumps -> pyobjc 已经间接装好，这里直接 import
from AppKit import NSImage, NSBitmapImageRep
from Foundation import NSData  # noqa: F401  # 偶尔需要在 PyInstaller hooks 中显式引用

# ============== SF Symbol 名称配置 ==============
# 替换这三个名字即可换图标。可在 macOS 的 SF Symbols.app 里搜名字。
SYMBOL_OK = "network"                          # 正常联网：地球+信号
SYMBOL_ERROR = "exclamationmark.triangle.fill" # 错误：警告三角
SYMBOL_CHECKING = "arrow.triangle.2.circlepath" # 检测中：刷新箭头

# 菜单栏图标像素尺寸（macOS 菜单栏高度约 22pt，18 看着比较协调）
ICON_SIZE = 18

# NSBitmapImageFileType.png = 4（避免 import 整套枚举）
_NS_PNG_FILE_TYPE = 4


def _render_symbol_to_png(symbol_name: str, out_path: str, size: int = ICON_SIZE) -> bool:
    """把一个 SF Symbol 渲染成单色 PNG（保留透明度，可当 template 用）。"""
    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
    if image is None:
        # 系统找不到这个 symbol（可能 macOS 版本太低）
        return False

    image.setSize_((size, size))
    image.setTemplate_(True)

    tiff_data = image.TIFFRepresentation()
    if tiff_data is None:
        return False
    rep = NSBitmapImageRep.imageRepWithData_(tiff_data)
    if rep is None:
        return False
    png_data = rep.representationUsingType_properties_(_NS_PNG_FILE_TYPE, None)
    if png_data is None:
        return False
    return bool(png_data.writeToFile_atomically_(out_path, True))


def prepare_icons() -> dict[str, Optional[str]]:
    """
    渲染三个状态图标，返回 {state: png_path}。
    渲染失败时该 state 的值是 None，调用方应当处理（回退到文字）。
    """
    cache_dir = os.path.join(tempfile.gettempdir(), "netbot_icons")
    os.makedirs(cache_dir, exist_ok=True)

    mapping = {
        "ok": SYMBOL_OK,
        "error": SYMBOL_ERROR,
        "checking": SYMBOL_CHECKING,
    }
    result: dict[str, Optional[str]] = {}
    for state, symbol in mapping.items():
        out = os.path.join(cache_dir, f"{state}.png")
        ok = _render_symbol_to_png(symbol, out)
        result[state] = out if ok else None
    return result
