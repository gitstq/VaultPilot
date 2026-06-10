"""主题配置模块 - TUI 界面主题定义

提供多种预定义主题，支持自定义颜色方案。
"""

from typing import Dict, Tuple


class Theme:
    """TUI 主题配置

    定义终端界面的颜色方案和显示样式。
    使用 curses 颜色对 (foreground, background) 来定义各 UI 元素的颜色。

    Attributes:
        name: 主题名称
        colors: 颜色配置字典
        styles: 样式配置字典
    """

    def __init__(
        self,
        name: str,
        colors: Optional[Dict[str, Tuple[int, int]]] = None,
        styles: Optional[Dict[str, bool]] = None,
    ) -> None:
        """初始化主题

        Args:
            name: 主题名称
            colors: 颜色配置 {元素名: (前景色, 背景色)}
            styles: 样式配置 {样式名: 是否启用}
        """
        self.name: str = name
        self.colors: Dict[str, Tuple[int, int]] = colors or {}
        self.styles: Dict[str, bool] = styles or {}

    def get_color(self, element: str) -> Tuple[int, int]:
        """获取元素颜色

        Args:
            element: 元素名称

        Returns:
            (前景色, 背景色) 元组
        """
        return self.colors.get(element, (7, 0))  # 默认白底黑字

    def get_style(self, style_name: str) -> bool:
        """获取样式状态

        Args:
            style_name: 样式名称

        Returns:
            是否启用该样式
        """
        return self.styles.get(style_name, False)


# 预定义主题
THEME_DEFAULT = Theme(
    name="default",
    colors={
        "title": (6, 0),        # 青色
        "subtitle": (3, 0),     # 黄色
        "highlight": (1, 0),     # 红色
        "selected": (0, 6),     # 黑字青底
        "tag": (2, 0),           # 绿色
        "link": (4, 0),          # 蓝色
        "border": (6, 0),        # 青色
        "text": (7, 0),          # 白色
        "dim": (8, 0),           # 灰色
        "error": (1, 0),         # 红色
        "success": (2, 0),       # 绿色
        "warning": (3, 0),       # 黄色
        "info": (4, 0),          # 蓝色
        "status": (7, 4),        # 白字蓝底
        "input": (7, 0),          # 白色
        "cursor": (0, 7),        # 黑字白底
    },
    styles={
        "bold_title": True,
        "show_borders": True,
        "show_line_numbers": True,
        "show_tags": True,
        "show_dates": True,
        "unicode_borders": True,
    },
)

THEME_DARK = Theme(
    name="dark",
    colors={
        "title": (6, 0),
        "subtitle": (3, 0),
        "highlight": (5, 0),     # 品红
        "selected": (0, 5),
        "tag": (2, 0),
        "link": (4, 0),
        "border": (8, 0),
        "text": (7, 0),
        "dim": (8, 0),
        "error": (9, 0),
        "success": (10, 0),
        "warning": (11, 0),
        "info": (12, 0),
        "status": (7, 4),
        "input": (7, 0),
        "cursor": (0, 7),
    },
    styles={
        "bold_title": True,
        "show_borders": True,
        "show_line_numbers": True,
        "show_tags": True,
        "show_dates": True,
        "unicode_borders": True,
    },
)

THEME_MONO = Theme(
    name="mono",
    colors={
        "title": (7, 0),
        "subtitle": (7, 0),
        "highlight": (7, 0),
        "selected": (0, 7),
        "tag": (7, 0),
        "link": (7, 0),
        "border": (7, 0),
        "text": (7, 0),
        "dim": (8, 0),
        "error": (7, 0),
        "success": (7, 0),
        "warning": (7, 0),
        "info": (7, 0),
        "status": (0, 7),
        "input": (7, 0),
        "cursor": (0, 7),
    },
    styles={
        "bold_title": False,
        "show_borders": True,
        "show_line_numbers": True,
        "show_tags": True,
        "show_dates": True,
        "unicode_borders": False,
    },
)

# 主题注册表
_THEME_REGISTRY: Dict[str, Theme] = {
    "default": THEME_DEFAULT,
    "dark": THEME_DARK,
    "mono": THEME_MONO,
}


def get_theme(name: str = "default") -> Theme:
    """获取指定名称的主题

    Args:
        name: 主题名称

    Returns:
        主题对象，未找到时返回默认主题
    """
    return _THEME_REGISTRY.get(name, THEME_DEFAULT)


def register_theme(theme: Theme) -> None:
    """注册自定义主题

    Args:
        theme: 主题对象
    """
    _THEME_REGISTRY[theme.name] = theme


def list_themes() -> list:
    """列出所有可用主题

    Returns:
        主题名称列表
    """
    return list(_THEME_REGISTRY.keys())
