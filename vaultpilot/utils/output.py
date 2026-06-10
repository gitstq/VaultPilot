"""输出格式化模块 - 终端输出美化

支持 rich 库的美化输出，当 rich 不可用时自动降级为纯文本输出。
提供统一的输出接口，屏蔽底层渲染差异。
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple


class OutputFormatter:
    """终端输出格式化器

    自动检测 rich 库是否可用，有则使用 rich 进行美化输出，
    无则降级为纯文本 ANSI 转义序列输出。

    Attributes:
        use_rich: 是否使用 rich 库
        _console: rich Console 实例（仅当 use_rich 为 True 时有效）
        _colors: ANSI 颜色代码映射
    """

    # ANSI 颜色代码
    _COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "underline": "\033[4m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
        "bg_black": "\033[40m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
        "bg_magenta": "\033[45m",
        "bg_cyan": "\033[46m",
        "bg_white": "\033[47m",
    }

    def __init__(self, no_color: bool = False) -> None:
        """初始化输出格式化器

        Args:
            no_color: 是否禁用颜色输出
        """
        self.no_color: bool = no_color or not self._supports_color()
        self.use_rich: bool = False
        self._console: Any = None

        if not self.no_color:
            self._try_init_rich()

    @staticmethod
    def _supports_color() -> bool:
        """检测终端是否支持颜色输出

        检查 NO_COLOR 环境变量和终端类型。

        Returns:
            终端是否支持颜色
        """
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM") in ("dumb", ""):
            return False
        # Windows 10+ 支持 ANSI 颜色
        if sys.platform == "win32":
            return os.environ.get("ANSICON") is not None or "256color" in os.environ.get("TERM", "")
        return True

    def _try_init_rich(self) -> None:
        """尝试初始化 rich 库

        如果 rich 可用则设置 use_rich 为 True 并创建 Console 实例。
        """
        try:
            from rich.console import Console

            self._console = Console()
            self.use_rich = True
        except ImportError:
            self.use_rich = False

    def _colorize(self, text: str, color: str) -> str:
        """使用 ANSI 转义序列为文本着色

        Args:
            text: 要着色的文本
            color: 颜色名称

        Returns:
            着色后的文本字符串
        """
        if self.no_color:
            return text
        code = self._COLORS.get(color, "")
        reset = self._COLORS["reset"]
        return f"{code}{text}{reset}"

    def title(self, text: str) -> None:
        """输出标题文本

        Args:
            text: 标题内容
        """
        if self.use_rich and self._console:
            from rich.text import Text

            styled = Text(text, style="bold bright_cyan")
            self._console.print(styled)
        else:
            print(self._colorize(f"\n{'=' * 60}", "cyan"))
            print(self._colorize(f"  {text}", "bold bright_cyan"))
            print(self._colorize(f"{'=' * 60}", "cyan"))

    def subtitle(self, text: str) -> None:
        """输出副标题文本

        Args:
            text: 副标题内容
        """
        if self.use_rich and self._console:
            from rich.text import Text

            styled = Text(text, style="bold yellow")
            self._console.print(styled)
        else:
            print(self._colorize(f"\n--- {text} ---", "bold yellow"))

    def info(self, text: str) -> None:
        """输出信息文本

        Args:
            text: 信息内容
        """
        if self.use_rich and self._console:
            self._console.print(f"[blue]ℹ[/blue] {text}")
        else:
            print(self._colorize("i", "blue") + f" {text}")

    def success(self, text: str) -> None:
        """输出成功提示

        Args:
            text: 成功信息内容
        """
        if self.use_rich and self._console:
            self._console.print(f"[green]✔[/green] {text}")
        else:
            print(self._colorize("[OK]", "green") + f" {text}")

    def warning(self, text: str) -> None:
        """输出警告信息

        Args:
            text: 警告内容
        """
        if self.use_rich and self._console:
            self._console.print(f"[yellow]⚠[/yellow] {text}")
        else:
            print(self._colorize("[WARN]", "yellow") + f" {text}")

    def error(self, text: str) -> None:
        """输出错误信息

        Args:
            text: 错误内容
        """
        if self.use_rich and self._console:
            self._console.print(f"[red]✖[/red] {text}")
        else:
            print(self._colorize("[ERROR]", "red") + f" {text}", file=sys.stderr)

    def table(
        self,
        headers: List[str],
        rows: List[List[str]],
        title: Optional[str] = None,
    ) -> None:
        """输出表格数据

        Args:
            headers: 表头列表
            rows: 数据行列表
            title: 表格标题（可选）
        """
        if not rows:
            self.info("无数据")
            return

        if self.use_rich and self._console:
            from rich.table import Table

            table = Table(title=title, show_lines=True)
            for header in headers:
                table.add_column(header, style="bold bright_cyan")
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self._console.print(table)
        else:
            if title:
                print(self._colorize(f"\n  {title}", "bold"))
            self._print_plain_table(headers, rows)

    def _print_plain_table(self, headers: List[str], rows: List[List[str]]) -> None:
        """使用纯文本输出表格

        自动计算列宽，使用 Unicode 边框绘制表格。

        Args:
            headers: 表头列表
            rows: 数据行列表
        """
        # 计算每列最大宽度
        col_widths: List[int] = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    cell_len = self._display_width(str(row[i]))
                    max_width = max(max_width, cell_len)
            col_widths.append(min(max_width + 2, 40))

        # 计算总宽度
        total_width = sum(col_widths) + len(col_widths) + 1

        # 输出表头
        header_line = "|" + "|".join(
            self._colorize(h.center(w), "bold bright_cyan")
            for h, w in zip(headers, col_widths)
        ) + "|"
        separator = "+" + "+".join("-" * w for w in col_widths) + "+"

        print(separator)
        print(header_line)
        print(separator)

        # 输出数据行
        for row in rows:
            cells: List[str] = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    cells.append(str(cell).ljust(col_widths[i]))
            line = "|" + "|".join(cells) + "|"
            print(line)

        print(separator)

    @staticmethod
    def _display_width(text: str) -> int:
        """计算字符串的显示宽度（考虑中文字符占两列）

        Args:
            text: 输入字符串

        Returns:
            显示宽度
        """
        width = 0
        for char in text:
            if ord(char) > 0x2000:
                width += 2
            else:
                width += 1
        return width

    def key_value(self, key: str, value: str, indent: int = 2) -> None:
        """输出键值对

        Args:
            key: 键名
            value: 值
            indent: 缩进空格数
        """
        prefix = " " * indent
        if self.use_rich and self._console:
            from rich.text import Text

            styled = Text()
            styled.append(f"{prefix}{key}: ", style="bold cyan")
            styled.append(str(value))
            self._console.print(styled)
        else:
            print(f"{prefix}{self._colorize(key, 'bold cyan')}: {value}")

    def list_item(self, text: str, index: Optional[int] = None, indent: int = 2) -> None:
        """输出列表项

        Args:
            text: 列表项内容
            index: 序号（可选）
            indent: 缩进空格数
        """
        prefix = " " * indent
        if index is not None:
            marker = self._colorize(f"{index + 1}.", "yellow")
        else:
            marker = self._colorize("*", "yellow")
        print(f"{prefix}{marker} {text}")

    def progress(self, current: int, total: int, label: str = "") -> None:
        """输出进度信息

        Args:
            current: 当前进度
            total: 总数
            label: 进度标签
        """
        if total == 0:
            return
        percent = int(current / total * 100)
        bar_width = 30
        filled = int(bar_width * current / total)
        bar = self._colorize("█" * filled, "green") + "░" * (bar_width - filled)
        msg = f"\r  {label} [{bar}] {percent}% ({current}/{total})"
        print(msg, end="", flush=True)
        if current == total:
            print()

    def blank(self, count: int = 1) -> None:
        """输出空行

        Args:
            count: 空行数量
        """
        print("\n" * (count - 1))

    def highlight(self, text: str, query: str) -> str:
        """高亮文本中匹配查询的部分

        Args:
            text: 原始文本
            query: 要高亮的关键词

        Returns:
            高亮后的文本
        """
        if not query:
            return text
        if self.use_rich:
            return f"[bold bright_red]{query}[/bold bright_red]".join(
                part for part in text.split(query)
            )
        return self._colorize(query, "bold bright_red").join(
            part for part in text.split(query)
        )

    def print(self, text: str = "", style: str = "") -> None:
        """通用文本输出

        Args:
            text: 输出内容
            style: 样式名称（仅 rich 模式生效）
        """
        if self.use_rich and self._console:
            self._console.print(text, style=style)
        else:
            print(text)

    def rule(self, title: str = "") -> None:
        """输出分隔线

        Args:
            title: 分隔线标题（可选）
        """
        if self.use_rich and self._console:
            from rich.rule import Rule

            self._console.print(Rule(title))
        else:
            if title:
                print(self._colorize(f"── {title} {'─' * max(1, 50 - len(title))}", "dim"))
            else:
                print(self._colorize("─" * 60, "dim"))

    def panel(self, text: str, title: Optional[str] = None) -> None:
        """输出面板（带边框的文本块）

        Args:
            text: 面板内容
            title: 面板标题（可选）
        """
        if self.use_rich and self._console:
            from rich.panel import Panel

            self._console.print(Panel(text, title=title, border_style="cyan"))
        else:
            width = max(len(line) for line in text.split("\n")) + 4
            if title:
                width = max(width, len(title) + 6)
            border = self._colorize("─" * width, "cyan")
            title_line = self._colorize(f"┌─ {title} {'─' * max(1, width - len(title) - 5)}", "cyan")
            bottom = self._colorize(f"└{'─' * (width - 1)}", "cyan")
            print(title_line)
            for line in text.split("\n"):
                print(self._colorize("│", "cyan") + f" {line}")
            print(bottom)

    def markdown(self, text: str) -> None:
        """输出 Markdown 格式文本（简化渲染）

        将 Markdown 文本转换为终端友好的格式输出。

        Args:
            text: Markdown 文本内容
        """
        if self.use_rich and self._console:
            from rich.markdown import Markdown

            self._console.print(Markdown(text))
        else:
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("# "):
                    print(self._colorize(f"\n{'=' * 60}", "cyan"))
                    print(self._colorize(stripped[2:], "bold bright_cyan"))
                    print(self._colorize(f"{'=' * 60}", "cyan"))
                elif stripped.startswith("## "):
                    print(self._colorize(f"\n--- {stripped[3:]} ---", "bold yellow"))
                elif stripped.startswith("### "):
                    print(self._colorize(f"\n  > {stripped[4:]}", "bold green"))
                elif stripped.startswith("- "):
                    print(f"  {self._colorize('*', 'yellow')} {stripped[2:]}")
                elif stripped.startswith("> "):
                    print(self._colorize(f"  │ {stripped[2:]}", "dim"))
                elif stripped.startswith("**") and stripped.endswith("**"):
                    print(self._colorize(stripped[2:-2], "bold"))
                elif stripped.startswith("`") and stripped.endswith("`"):
                    print(self._colorize(stripped, "bg_black bright_white"))
                else:
                    print(line)
