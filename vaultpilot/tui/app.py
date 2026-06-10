"""TUI 主应用 - 交互式终端界面

使用标准库 curses 实现交互式终端界面，支持笔记浏览、搜索、编辑等功能。
提供键盘导航和快捷操作。
"""

import curses
import os
import sys
from typing import Any, Dict, List, Optional

from .widgets import ListWidget, SearchWidget, StatusWidget, ConfirmWidget
from .themes import Theme, get_theme

# Windows 平台兼容
if sys.platform == "win32":
    try:
        import msvcrt
    except ImportError:
        msvcrt = None


class TUIApp:
    """TUI 主应用

    基于 curses 的交互式终端界面，提供知识库的完整交互操作。

    Attributes:
        vault_path: 知识库路径
        vault: Vault 实例
        theme: 当前主题
        stdscr: curses 标准屏幕
        running: 是否运行中
        current_mode: 当前模式
    """

    # 模式常量
    MODE_LIST = "list"
    MODE_SEARCH = "search"
    MODE_DETAIL = "detail"
    MODE_HELP = "help"
    MODE_TAG_FILTER = "tag_filter"

    def __init__(self, vault_path: str, theme_name: str = "default") -> None:
        """初始化 TUI 应用

        Args:
            vault_path: 知识库根目录路径
            theme_name: 主题名称
        """
        self.vault_path: str = os.path.abspath(vault_path)
        self.theme: Theme = get_theme(theme_name)
        self.stdscr: Any = None
        self.running: bool = False
        self.current_mode: str = self.MODE_LIST
        self._vault: Any = None
        self._notes: List[Dict[str, Any]] = []
        self._filtered_notes: List[Dict[str, Any]] = []
        self._search_query: str = ""
        self._tag_filter: str = ""
        self._detail_note: Optional[Dict[str, Any]] = None
        self._detail_scroll: int = 0

        # 组件（在 run() 中初始化）
        self._list_widget: Optional[ListWidget] = None
        self._search_widget: Optional[SearchWidget] = None
        self._status_widget: Optional[StatusWidget] = None

    def run(self) -> None:
        """启动 TUI 应用

        初始化 curses 环境并进入主循环。
        """
        # 延迟导入 Vault 以避免循环依赖
        from ..core.vault import Vault

        try:
            self._vault = Vault(self.vault_path)
        except ValueError as e:
            print(f"错误: {e}")
            return

        # 加载笔记
        self._load_notes()

        # 启动 curses
        try:
            curses.wrapper(self._main_loop)
        except curses.error as e:
            print(f"TUI 启动失败: {e}")
        except KeyboardInterrupt:
            pass

    def _main_loop(self, stdscr: Any) -> None:
        """curses 主循环

        Args:
            stdscr: curses 标准屏幕
        """
        self.stdscr = stdscr
        self.running = True

        # 初始化 curses 设置
        self._init_curses()

        # 初始化组件
        self._init_widgets()

        # 初始绘制
        self._draw_screen()

        # 主事件循环
        while self.running:
            try:
                key = self.stdscr.getch()
                self._handle_key(key)
                self._draw_screen()
            except curses.error:
                continue

    def _init_curses(self) -> None:
        """初始化 curses 环境设置"""
        curses.curs_set(0)  # 隐藏光标
        self.stdscr.nodelay(True)  # 非阻塞输入
        self.stdscr.timeout(100)  # 输入超时 100ms

        # 启用颜色
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # 初始化颜色对
            for i in range(8):
                curses.init_pair(i + 1, i, 0)
            curses.init_pair(9, curses.COLOR_RED, 0)
            curses.init_pair(10, curses.COLOR_GREEN, 0)
            curses.init_pair(11, curses.COLOR_YELLOW, 0)
            curses.init_pair(12, curses.COLOR_BLUE, 0)

        # 允许功能键
        self.stdscr.keypad(True)

    def _init_widgets(self) -> None:
        """初始化 UI 组件"""
        max_y, max_x = self.stdscr.getmaxyx()

        # 列表组件
        self._list_widget = ListWidget(
            self.stdscr,
            x=0, y=1,
            width=max_x,
            height=max_y - 2,
            items=self._filtered_notes,
        )

        # 搜索组件
        self._search_widget = SearchWidget(
            self.stdscr,
            x=0, y=0,
            width=max_x,
            prompt="/ ",
        )
        self._search_widget.on_search = self._on_search
        self._search_widget.on_cancel = self._on_search_cancel

        # 状态栏组件
        self._status_widget = StatusWidget(self.stdscr, y=max_y - 1)

    def _load_notes(self) -> None:
        """从知识库加载笔记数据"""
        if not self._vault:
            return

        notes = self._vault.list_notes(limit=1000)
        self._notes = []
        for note in notes:
            self._notes.append({
                "title": note.title,
                "tags": note.tags,
                "date": note.updated.strftime("%Y-%m-%d"),
                "word_count": note.get_word_count(),
                "filename": note.get_filename(),
                "body": note.body,
                "links": note.links,
                "backlinks": note.backlinks,
            })

        self._apply_filter()

    def _apply_filter(self) -> None:
        """应用当前过滤条件"""
        self._filtered_notes = list(self._notes)

        # 标签过滤
        if self._tag_filter:
            tag_lower = self._tag_filter.lower()
            self._filtered_notes = [
                n for n in self._filtered_notes
                if tag_lower in [t.lower() for t in n.get("tags", [])]
            ]

        # 搜索过滤
        if self._search_query:
            query_lower = self._search_query.lower()
            self._filtered_notes = [
                n for n in self._filtered_notes
                if query_lower in n.get("title", "").lower()
                or query_lower in n.get("body", "").lower()
            ]

        if self._list_widget:
            self._list_widget.set_items(self._filtered_notes)

    def _draw_screen(self) -> None:
        """绘制完整屏幕"""
        if not self.stdscr:
            return

        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()

        if self.current_mode == self.MODE_HELP:
            self._draw_help()
        elif self.current_mode == self.MODE_DETAIL:
            self._draw_detail()
        else:
            self._draw_list_mode()

        self.stdscr.refresh()

    def _draw_list_mode(self) -> None:
        """绘制列表模式界面"""
        max_y, max_x = self.stdscr.getmaxyx()

        # 标题栏
        title = "VaultPilot"
        if self._tag_filter:
            title += f" [tag: {self._tag_filter}]"
        if self._search_query:
            title += f" [search: {self._search_query}]"
        title += f" ({len(self._filtered_notes)} notes)"

        try:
            self.stdscr.attron(curses.A_BOLD)
            self.stdscr.addstr(0, 1, title[:max_x - 2])
            self.stdscr.attroff(curses.A_BOLD)
        except curses.error:
            pass

        # 绘制列表
        if self._list_widget:
            self._list_widget.y = 1
            self._list_widget.height = max_y - 2
            self._list_widget.width = max_x
            self._list_widget.draw()

        # 状态栏
        if self._status_widget:
            self._status_widget.y = max_y - 1
            self._status_widget.set_text(
                left="j/k:move  Enter:open  /:search  n:new  d:delete  t:tag  g:graph  h:help  q:quit",
                right=f"[{self.current_mode}]",
            )

    def _draw_detail(self) -> None:
        """绘制笔记详情界面"""
        if not self._detail_note:
            self.current_mode = self.MODE_LIST
            return

        max_y, max_x = self.stdscr.getmaxyx()

        # 标题
        title = self._detail_note.get("title", "Untitled")
        try:
            self.stdscr.attron(curses.A_BOLD)
            self.stdscr.addstr(0, 1, title[:max_x - 2])
            self.stdscr.attroff(curses.A_BOLD)
        except curses.error:
            pass

        # 元数据
        meta_y = 1
        tags = self._detail_note.get("tags", [])
        date = self._detail_note.get("date", "")
        word_count = self._detail_note.get("word_count", 0)

        meta_text = f"Tags: {', '.join(tags) if tags else '(none)'} | Date: {date} | Words: {word_count}"
        try:
            self.stdscr.addstr(meta_y, 1, meta_text[:max_x - 2], curses.A_DIM)
        except curses.error:
            pass

        # 正文内容
        body = self._detail_note.get("body", "")
        lines = body.split("\n")
        visible_height = max_y - 4

        for i in range(visible_height):
            line_idx = self._detail_scroll + i
            if line_idx >= len(lines):
                break

            line = lines[line_idx]
            # 截断过长行
            if len(line) > max_x - 2:
                line = line[:max_x - 3] + ".."

            try:
                self.stdscr.addstr(meta_y + 1 + i, 1, line)
            except curses.error:
                pass

        # 滚动指示
        total_lines = len(lines)
        if total_lines > visible_height:
            scroll_pct = int(self._detail_scroll / max(1, total_lines - visible_height) * 100)
            scroll_text = f"Scroll: {scroll_pct}% ({self._detail_scroll + 1}/{total_lines})"
        else:
            scroll_text = ""

        # 状态栏
        if self._status_widget:
            self._status_widget.y = max_y - 1
            self._status_widget.set_text(
                left="j/k:scroll  q:back  e:edit  d:delete",
                right=scroll_text,
            )

    def _draw_help(self) -> None:
        """绘制帮助界面"""
        max_y, max_x = self.stdscr.getmaxyx()

        help_lines: List[str] = [
            "",
            "  VaultPilot TUI - Keyboard Shortcuts",
            "",
            "  Navigation:",
            "    j / Down    - Move down",
            "    k / Up      - Move up",
            "    g           - Go to top",
            "    G           - Go to bottom",
            "    Enter       - Open note",
            "    q / Esc     - Back / Quit",
            "",
            "  Actions:",
            "    n           - New note",
            "    e           - Edit note",
            "    d           - Delete note",
            "    t           - Tag filter",
            "    /           - Search",
            "    s           - Stats",
            "",
            "  Other:",
            "    h / ?       - This help",
            "    g           - Knowledge graph",
            "    r           - Refresh",
            "",
            "  Press any key to go back...",
        ]

        for i, line in enumerate(help_lines):
            if i >= max_y:
                break
            try:
                self.stdscr.addstr(i, 0, line[:max_x - 1])
            except curses.error:
                pass

    def _handle_key(self, key: int) -> None:
        """处理按键事件

        Args:
            key: curses 按键码
        """
        if self.current_mode == self.MODE_HELP:
            self.current_mode = self.MODE_LIST
            return

        if self.current_mode == self.MODE_DETAIL:
            self._handle_detail_key(key)
            return

        if self.current_mode == self.MODE_SEARCH:
            if self._search_widget:
                self._search_widget.handle_key(key)
            return

        # 列表模式
        if self._list_widget and self._list_widget.handle_key(key):
            return

        # 全局快捷键
        if key in (ord("q"), ord("Q"), 27):
            self.running = False
        elif key in (ord("/"),):
            self.current_mode = self.MODE_SEARCH
            if self._search_widget:
                self._search_widget.activate()
        elif key in (ord("n"), ord("N")):
            self._create_note()
        elif key in (ord("e"), ord("E")):
            self._edit_selected_note()
        elif key in (ord("d"), ord("D")):
            self._delete_selected_note()
        elif key in (ord("h"), ord("?")):
            self.current_mode = self.MODE_HELP
        elif key in (ord("t"), ord("T")):
            self._tag_filter_mode()
        elif key in (ord("r"), ord("R")):
            self._load_notes()
        elif key in (curses.KEY_ENTER, 10, 13):
            self._open_selected_note()
        elif key == curses.KEY_RESIZE:
            self._handle_resize()

    def _handle_detail_key(self, key: int) -> None:
        """处理详情模式的按键

        Args:
            key: curses 按键码
        """
        if key in (ord("q"), ord("Q"), 27):
            self.current_mode = self.MODE_LIST
            self._detail_note = None
            self._detail_scroll = 0
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            self._detail_scroll = max(0, self._detail_scroll - 1)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self._detail_scroll += 1
        elif key in (curses.KEY_PPAGE, curses.KEY_HOME):
            self._detail_scroll = max(0, self._detail_scroll - 10)
        elif key in (curses.KEY_NPAGE, curses.KEY_END):
            self._detail_scroll += 10
        elif key in (ord("e"), ord("E")):
            self._edit_selected_note()
        elif key in (ord("d"), ord("D")):
            self._delete_selected_note()

    def _handle_resize(self) -> None:
        """处理窗口大小变化"""
        if not self.stdscr:
            return
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()
        curses.resizeterm(max_y, max_x)

        if self._list_widget:
            self._list_widget.resize(max_x, max_y - 2)
        if self._status_widget:
            self._status_widget.width = max_x
            self._status_widget.y = max_y - 1

    def _on_search(self, query: str) -> None:
        """搜索回调

        Args:
            query: 搜索查询
        """
        self._search_query = query
        self.current_mode = self.MODE_LIST
        if self._search_widget:
            self._search_widget.deactivate()
        self._apply_filter()

    def _on_search_cancel(self) -> None:
        """取消搜索回调"""
        self._search_query = ""
        self.current_mode = self.MODE_LIST
        if self._search_widget:
            self._search_widget.deactivate()
        self._apply_filter()

    def _open_selected_note(self) -> None:
        """打开选中的笔记"""
        if not self._list_widget:
            return
        item = self._list_widget.get_selected_item()
        if item:
            self._detail_note = item
            self._detail_scroll = 0
            self.current_mode = self.MODE_DETAIL

    def _create_note(self) -> None:
        """创建新笔记"""
        if not self._vault:
            return

        # 退出 curses 临时创建笔记
        curses.endwin()
        try:
            title = input("Note title: ").strip()
            if title:
                self._vault.new_note(title)
                self._load_notes()
        except (EOFError, KeyboardInterrupt):
            pass

        # 重新初始化 curses
        self.stdscr = curses.initscr()
        self._init_curses()
        self._init_widgets()

    def _edit_selected_note(self) -> None:
        """编辑选中的笔记"""
        if not self._list_widget or not self._vault:
            return
        item = self._list_widget.get_selected_item()
        if item:
            filename = item.get("filename", "")
            curses.endwin()
            try:
                self._vault.edit_note(filename)
                self._load_notes()
            except Exception:
                pass
            self.stdscr = curses.initscr()
            self._init_curses()
            self._init_widgets()

    def _delete_selected_note(self) -> None:
        """删除选中的笔记"""
        if not self._list_widget or not self._vault:
            return
        item = self._list_widget.get_selected_item()
        if item:
            filename = item.get("filename", "")
            curses.endwin()
            try:
                confirm = input(f"Delete '{item.get('title', '')}'? [y/N]: ").strip().lower()
                if confirm == "y":
                    self._vault.delete_note(filename)
                    self._load_notes()
                    if self.current_mode == self.MODE_DETAIL:
                        self.current_mode = self.MODE_LIST
            except (EOFError, KeyboardInterrupt):
                pass
            self.stdscr = curses.initscr()
            self._init_curses()
            self._init_widgets()

    def _tag_filter_mode(self) -> None:
        """进入标签过滤模式"""
        if not self._vault:
            return

        curses.endwin()
        try:
            tags = self._vault.list_tags()
            if tags:
                print("\nAvailable tags:")
                for tag, count in tags:
                    print(f"  {tag} ({count})")
                tag_input = input("\nFilter by tag (empty to clear): ").strip()
                if tag_input:
                    self._tag_filter = tag_input
                else:
                    self._tag_filter = ""
                self._apply_filter()
            else:
                print("No tags found.")
                input("Press Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            pass

        self.stdscr = curses.initscr()
        self._init_curses()
        self._init_widgets()
