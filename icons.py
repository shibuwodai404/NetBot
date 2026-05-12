"""
图标模块（macOS 菜单栏）

三种状态：
  · ok       → 像素机器人 template PNG（资产文件 tray_ok_template.png）
  · checking → SF Symbol  arrow.triangle.2.circlepath（旋转双箭头）
  · error    → SF Symbol  exclamationmark.triangle.fill（警告三角）

为什么 ok 用机器人、其余用 SF Symbol：
  机器人是品牌形象，正常态展示。异常 / 检测中用 SF Symbol 形状区分，
  比颜色变化更醒目（template 模式下颜色会被系统强制反色）。
"""

import os
import shutil
import tempfile
from typing import Optional

from AppKit import NSImage, NSBitmapImageRep
from Foundation import NSData  # noqa: F401  # PyInstaller hooks 有时需要显式 import

# ============== SF Symbol 名称配置 ==============
SYMBOL_CHECKING = "arrow.triangle.2.circlepath"  # 检测中：刷新箭头
SYMBOL_ERROR = "exclamationmark.triangle.fill"   # 错误：警告三角

# ok 状态用打包好的 template PNG
_OK_TEMPLATE_PARTS = ("assets", "icons", "tray", "tray_ok_template.png")

# 菜单栏图标像素尺寸（菜单栏高度约 22pt，18 看着比较协调）
ICON_SIZE = 18

# NSBitmapImageFileType.png = 4
_NS_PNG_FILE_TYPE = 4


def _asset_path(*parts: str) -> str:
    """兼容 PyInstaller 冻结环境的资源路径。"""
    import sys
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)


def _render_symbol_to_png(symbol_name: str, out_path: str, size: int = ICON_SIZE) -> bool:
    """把一个 SF Symbol 渲染成单色 PNG（保留透明度，可当 template 用）。"""
    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
    if image is None:
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


def _copy_asset(src: str, dst: str) -> bool:
    """把仓库内的 template PNG 复制到缓存目录，让所有图标路径风格一致。"""
    try:
        shutil.copyfile(src, dst)
        return True
    except OSError:
        return False


def prepare_icons() -> dict[str, Optional[str]]:
    """
    准备三个状态图标，返回 {state: png_path}。
    渲染失败时该 state 的值是 None，调用方应当处理。
    """
    cache_dir = os.path.join(tempfile.gettempdir(), "netbot_icons")
    os.makedirs(cache_dir, exist_ok=True)

    result: dict[str, Optional[str]] = {}

    # ok：从资产里拷贝出来
    ok_src = _asset_path(*_OK_TEMPLATE_PARTS)
    ok_dst = os.path.join(cache_dir, "ok.png")
    result["ok"] = ok_dst if os.path.exists(ok_src) and _copy_asset(ok_src, ok_dst) else None

    # checking / error：现场渲染 SF Symbol
    for state, symbol in (("checking", SYMBOL_CHECKING), ("error", SYMBOL_ERROR)):
        out = os.path.join(cache_dir, f"{state}.png")
        result[state] = out if _render_symbol_to_png(symbol, out) else None

    return result
