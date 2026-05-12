"""
PIL 图标渲染（用于 Linux / Windows 系统托盘）

为什么需要这个：
  Win / Linux 的托盘图标旁边不能像 macOS 那样显示文字，
  唯一办法是把国家码直接画进图标。
  这里生成一个圆角彩色背景 + 三字母国家码的小图，状态靠背景色区分。
"""

import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ============== 配置区 ==============

# 图标尺寸（像素）。64×64 足够高 DPI 显示，托盘会自动缩放
ICON_SIZE = 64

# 状态对应的背景色（RGBA）
STATE_COLORS = {
    "ok":       (76, 175, 80, 255),    # 绿 - 正常
    "ok_risk":  (255, 152, 0, 255),    # 橙 - 联网正常但有隐私风险
    "error":    (244, 67, 54, 255),    # 红 - 网络异常
    "checking": (255, 193, 7, 255),    # 琥珀黄 - 检测中
}

# 文字颜色（与上面三种背景都有足够对比度）
TEXT_COLOR = (0, 0, 0, 255)

# 常见系统字体路径（按平台依次尝试）。任何一个能加载就行
FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
    "C:\\Windows\\Fonts\\segoeuib.ttf",
]


_font_cache: dict[int, ImageFont.ImageFont] = {}


def _load_font(point_size: int) -> ImageFont.ImageFont:
    """加载一个粗体 TTF，找不到就 fall back 到 PIL 内置位图字体。"""
    if point_size in _font_cache:
        return _font_cache[point_size]
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size=point_size)
                _font_cache[point_size] = font
                return font
            except OSError:
                continue
    font = ImageFont.load_default()
    _font_cache[point_size] = font
    return font


def render_country_icon(
    country_code: Optional[str],
    state: str = "ok",
    size: int = ICON_SIZE,
) -> Image.Image:
    """
    生成一个 size×size 的 RGBA PNG 图像（PIL.Image 对象）。
    pystray 直接接受 PIL.Image，不必落盘。
    """
    text = (country_code or "...").strip().upper()
    if len(text) > 3:
        text = text[:3]
    bg = STATE_COLORS.get(state, STATE_COLORS["ok"])

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆角矩形背景
    margin = max(1, size // 32)
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=size // 5,
        fill=bg,
    )

    # 居中绘制文字（字号约画布高度的 45%）
    font_size = max(10, int(size * 0.45))
    font = _load_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pos = ((size - tw) // 2 - bbox[0], (size - th) // 2 - bbox[1])
    draw.text(pos, text, fill=TEXT_COLOR, font=font)

    return img
