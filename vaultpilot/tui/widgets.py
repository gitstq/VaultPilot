"""自定义组件模块 - TUI 界面组件

提供 TUI 界面中使用的各种自定义组件，包括列表、搜索框、确认对话框等。
基于标准库 curses 实现。
"""

import curses
from typing import Any, Callable, Dict, List, Optional, Tuple


class Widget:
    """TUI 组件基类

    所有 TUI 组件的基类，提供基本的绘制和事件处理接口。

    Attributes:
        window: curses 窗口对象
        x: 组件左上角 x 坐标
        y: 组件左上角 y 坐标
        width: 组件宽度
        height: 组件高度
        visible: 是否可见
        focused: 是否获得焦点
    """

    def __init__(
        self,
        window: Any,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        height: int = 24,
    ) -> None:
        """初始化组件

        Args:
            window: curses 窗口对象
            x: x 坐标
            y: y 坐标
            width: 宽度
            height: 高度
        """
        self.window = window
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.visible: bool = True
        self.focused: bool = False

    def draw(self) -> None:
        """绘制组件"""
        if not self.visible:
            return
        self._draw_content()

    def _draw_content(self) -> None:
        """绘制组件内容（子类实现）"""
        pass

    def handle_key(self, key: int) -> bool:
        """处理按键事件

        Args:
            key: curses 按键码

        Returns:
            是否处理了该按键
        """
        return False

    def resize(self, width: int, height: int) -> None:
        """调整组件大小

        Args:
            width: 新宽度
            height: 新高度
        """
        self.width = width
        self.height = height

    def set_focus(self, focused: bool) -> None:
        """设置焦点状态

        Args:
            focused: 是否获得焦点
        """
        self.focused = focused

    def _safe_addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """安全地添加字符串到窗口

        防止字符串超出窗口边界。

        Args:
            y: 行号
            x: 列号
            text: 文本
            attr: 文本属性
        """
        try:
            max_y, max_x = self.window.getmaxyx()
            if y < max_y and x < max_x:
                available = max_x - x
                if len(text) > available:
                    text = text[:available]
                self.window.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _draw_border(self) -> None:
        """绘制组件边框"""
        if self.height < 2 or self.width < 2:
            return
        try:
            self.window.border(
                0, 0, 0, 0, 0, 0, 0, 0
            )
        except curses.error:
            pass

    def _clear_area(self) -> None:
        """清除组件区域"""
        try:
            for row in range(self.y, min(self.y + self.height, self.window.getmaxyx()[0])):
                for col in range(self.x, min(self.x + self.width, self.window.getmaxyx()[1])):
                    try:
                        self.window.addch(row, col, " ")
                    except curses.error:
                        pass
        except curses.error:
            pass


class ListWidget(Widget):
    """列表组件

    显示可滚动的列表项，支持键盘导航和选择。

    Attributes:
        items: 列表项数据
        selected_index: 当前选中项索引
        scroll_offset: 滚动偏移量
        on_select: 选择回调函数
        on_activate: 激活（双击/回车）回调函数
    """

    def __init__(
        self,
        window: Any,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        height: int = 20,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """初始化列表组件

        Args:
            window: curses 窗口对象
            x: x 坐标
            y: y 坐标
            width: 宽度
            height: 高度
            items: 初始列表项
        """
        super().__init__(window, x, y, width, height)
        self.items: List[Dict[str, Any]] = items or []
        self.selected_index: int = 0
        self.scroll_offset: int = 0
        self.on_select: Optional[Callable[[int], None]] = None
        self.on_activate: Optional[Callable[[int], None]] = None

    def set_items(self, items: List[Dict[str, Any]]) -> None:
        """设置列表项

        Args:
            items: 列表项数据
        """
        self.items = items
        self.selected_index = 0
        self.scroll_offset = 0
        self.draw()

    def _draw_content(self) -> None:
        """绘制列表内容"""
        if not self.items:
            self._safe_addstr(
                self.y + self.height // 2,
                self.x + 2,
                "(empty)",
                curses.A_DIM,
            )
            return

        visible_height = self.height - 2  # 减去边框
        if visible_height <= 0:
            return

        # 调整滚动偏移
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_height:
            self.scroll_offset = self.selected_index - visible_height + 1

        for i in range(visible_height):
            item_index = self.scroll_offset + i
            if item_index >= len(self.items):
                break

            item = self.items[item_index]
            row_y = self.y + 1 + i

            # 确定显示文本
            title = item.get("title", str(item))
            tags = item.get("tags", [])
            date_str = item.get("date", "")

            # 构建显示行
            line_parts: List[str] = []
            line_parts.append(f" {item_index + 1:>3}. {title}")

            if tags:
                tag_str = " ".join(f"[{t}]" for t in tags[:3])
                line_parts.append(f"  {tag_str}")

            if date_str:
                line_parts.append(f"  {date_str}")

            line = "".join(line_parts)

            # 截断过长行
            max_line_width = self.width - 3
            if len(line) > max_line_width:
                line = line[:max_line_width - 1] + ".."

            # 设置颜色属性
            if item_index == self.selected_index:
                attr = curses.A_REVERSE
            else:
                attr = curses.A_NORMAL

            self._safe_addstr(row_y, self.x + 1, line, attr)

        # 滚动条指示
        if len(self.items) > visible_height:
            scroll_ratio = visible_height / len(self.items)
            scroll_pos = int(self.scroll_offset / len(self.items) * visible_height)
            bar_y = self.y + 1 + scroll_pos
            self._safe_addstr(bar_y, self.x + self.width - 1, "|", curses.A_DIM)

    def handle_key(self, key: int) -> bool:
        """处理按键事件

        Args:
            key: curses 按键码

        Returns:
            是否处理了该按键
        """
        if not self.items:
            return False

        if key in (curses.KEY_UP, ord("k"), ord("K")):
            self.selected_index = max(0, self.selected_index - 1)
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        elif key in (curses.KEY_PPAGE, curses.KEY_HOME):
            self.selected_index = 0
            self.scroll_offset = 0
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        elif key in (curses.KEY_NPAGE, curses.KEY_END):
            self.selected_index = len(self.items) - 1
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        elif key in (curses.KEY_ENTER, 10, 13):
            if self.on_activate:
                self.on_activate(self.selected_index)
            return True

        elif key == ord("g"):
            self.selected_index = 0
            self.scroll_offset = 0
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        elif key == ord("G"):
            self.selected_index = len(self.items) - 1
            if self.on_select:
                self.on_select(self.selected_index)
            self.draw()
            return True

        return False

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """获取当前选中项

        Returns:
            选中的列表项，无选中返回 None
        """
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None


class SearchWidget(Widget):
    """搜索框组件

    提供文本输入和搜索功能。

    Attributes:
        text: 输入文本
        cursor_pos: 光标位置
        prompt: 提示文本
        on_search: 搜索回调函数
        on_cancel: 取消回调函数
    """

    def __init__(
        self,
        window: Any,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        prompt: str = "Search: ",
    ) -> None:
        """初始化搜索框

        Args:
            window: curses 窗口对象
            x: x 坐标
            y: y 坐标
            width: 宽度
            prompt: 提示文本
        """
        super().__init__(window, x, y, width, 1)
        self.text: str = ""
        self.cursor_pos: int = 0
        self.prompt: str = prompt
        self.on_search: Optional[Callable[[str], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None
        self.active: bool = False

    def _draw_content(self) -> None:
        """绘制搜索框"""
        # 绘制提示和文本
        display_text = self.prompt + self.text
        attr = curses.A_REVERSE if self.active else curses.A_NORMAL
        self._safe_addstr(self.y, self.x, display_text, attr)

        # 绘制光标
        if self.active:
            cursor_x = self.x + len(self.prompt) + self.cursor_pos
            try:
                self.window.move(self.y, cursor_x)
                curses.curs_set(1)
            except curses.error:
                pass

    def handle_key(self, key: int) -> bool:
        """处理按键事件

        Args:
            key: curses 按键码

        Returns:
            是否处理了该按键
        """
        if not self.active:
            return False

        if key == curses.KEY_ENTER or key in (10, 13):
            if self.on_search and self.text.strip():
                self.on_search(self.text.strip())
            return True

        elif key == 27:  # ESC
            self.text = ""
            self.cursor_pos = 0
            self.active = False
            if self.on_cancel:
                self.on_cancel()
            return True

        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
            return True

        elif key == curses.KEY_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return True

        elif key == curses.KEY_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            return True

        elif key == curses.KEY_HOME:
            self.cursor_pos = 0
            return True

        elif key == curses.KEY_END:
            self.cursor_pos = len(self.text)
            return True

        elif key == curses.KEY_DC:  # Delete
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
            return True

        elif 32 <= key <= 126:  # 可打印字符
            self.text = self.text[:self.cursor_pos] + chr(key) + self.text[self.cursor_pos:]
            self.cursor_pos += 1
            return True

        return False

    def activate(self) -> None:
        """激活搜索框"""
        self.active = True
        self.text = ""
        self.cursor_pos = 0
        self.draw()

    def deactivate(self) -> None:
        """取消激活搜索框"""
        self.active = False
        curses.curs_set(0)
        self.draw()


class ConfirmWidget(Widget):
    """确认对话框组件

    显示确认/取消对话框。

    Attributes:
        message: 确认消息
        confirmed: 是否确认
        on_confirm: 确认回调
        on_cancel: 取消回调
    """

    def __init__(
        self,
        window: Any,
        message: str = "Are you sure?",
    ) -> None:
        """初始化确认对话框

        Args:
            window: curses 窗口对象
            message: 确认消息
        """
        max_y, max_x = window.getmaxyx()
        width = min(len(message) + 10, max_x - 4)
        height = 5
        x = (max_x - width) // 2
        y = (max_y - height) // 2

        super().__init__(window, x, y, width, height)
        self.message: str = message
        self.confirmed: bool = False
        self.on_confirm: Optional[Callable[[], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

    def _draw_content(self) -> None:
        """绘制确认对话框"""
        # 边框
        try:
            self.window.box()
        except curses.error:
            pass

        # 消息
        self._safe_addstr(self.y + 1, self.x + 2, self.message)

        # 选项
        self._safe_addstr(
            self.y + 3,
            self.x + 2,
            "[Y] Yes  [N] No",
            curses.A_BOLD,
        )

    def handle_key(self, key: int) -> bool:
        """处理按键事件

        Args:
            key: curses 按键码

        Returns:
            是否处理了该按键
        """
        if key in (ord("y"), ord("Y"), curses.KEY_ENTER, 10, 13):
            self.confirmed = True
            if self.on_confirm:
                self.on_confirm()
            return True
        elif key in (ord("n"), ord("N"), 27):
            self.confirmed = False
            if self.on_cancel:
                self.on_cancel()
            return True
        return False


class StatusWidget(Widget):
    """状态栏组件

    显示底部状态信息。

    Attributes:
        left_text: 左侧文本
        right_text: 右侧文本
    """

    def __init__(self, window: Any, y: int = 0) -> None:
        """初始化状态栏

        Args:
            window: curses 窗口对象
            y: y 坐标（通常为窗口底部）
        """
        max_y, max_x = window.getmaxyx()
        super().__init__(window, 0, y, max_x, 1)
        self.left_text: str = ""
        self.right_text: str = ""

    def set_text(self, left: str = "", right: str = "") -> None:
        """设置状态栏文本

        Args:
            left: 左侧文本
            right: 右侧文本
        """
        self.left_text = left
        self.right_text = right
        self.draw()

    def _draw_content(self) -> None:
        """绘制状态栏"""
        try:
            self.window.attron(curses.A_REVERSE)
            # 左侧文本
            self._safe_addstr(self.y, 0, self.left_text.ljust(self.width))
            # 右侧文本
            if self.right_text:
                right_x = self.width - len(self.right_text) - 1
                if right_x > 0:
                    self._safe_addstr(self.y, right_x, self.right_text)
            self.window.attroff(curses.A_REVERSE)
        except curses.error:
            pass
