"""编辑器调用模块 - 检测并调用系统文本编辑器

支持自动检测系统编辑器，也支持通过配置指定编辑器。
跨平台兼容 Linux、macOS 和 Windows。
"""

import os
import subprocess
import sys
import tempfile
from typing import Optional


class Editor:
    """系统编辑器调用器

    自动检测系统环境中的文本编辑器，并提供统一的调用接口。
    检测顺序：配置指定 > EDITOR 环境变量 > VISUAL 环境变量 > 平台默认编辑器。

    Attributes:
        editor_cmd: 检测到的编辑器命令
    """

    # 各平台默认编辑器列表，按优先级排序
    _DEFAULT_EDITORS_LINUX = ["vim", "nano", "vi", "emacs"]
    _DEFAULT_EDITORS_MACOS = ["vim", "nano", "vi", "emacs", "code", "subl"]
    _DEFAULT_EDITORS_WINDOWS = ["notepad", "notepad++", "code"]

    def __init__(self, editor_cmd: Optional[str] = None) -> None:
        """初始化编辑器调用器

        Args:
            editor_cmd: 手动指定的编辑器命令，为 None 时自动检测
        """
        self.editor_cmd: str = editor_cmd or self._detect_editor()

    def _detect_editor(self) -> str:
        """自动检测系统编辑器

        按照以下优先级检测：
        1. EDITOR 环境变量
        2. VISUAL 环境变量
        3. 平台默认编辑器列表

        Returns:
            检测到的编辑器命令

        Raises:
            RuntimeError: 未检测到任何可用编辑器时抛出
        """
        # 优先使用环境变量
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
        if editor:
            return editor

        # 根据平台选择默认编辑器列表
        if sys.platform == "win32":
            candidates = self._DEFAULT_EDITORS_WINDOWS
        elif sys.platform == "darwin":
            candidates = self._DEFAULT_EDITORS_MACOS
        else:
            candidates = self._DEFAULT_EDITORS_LINUX

        # 检查编辑器是否可用
        for candidate in candidates:
            if self._is_editor_available(candidate):
                return candidate

        raise RuntimeError(
            "未检测到可用的文本编辑器。请设置 EDITOR 环境变量或通过配置指定编辑器。"
        )

    @staticmethod
    def _is_editor_available(editor: str) -> bool:
        """检查编辑器是否在系统 PATH 中可用

        Args:
            editor: 编辑器命令名称

        Returns:
            编辑器是否可用
        """
        try:
            result = subprocess.run(
                ["which", editor],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def edit_file(self, filepath: str) -> None:
        """使用系统编辑器打开文件进行编辑

        Args:
            filepath: 要编辑的文件路径

        Raises:
            FileNotFoundError: 文件不存在时抛出
            RuntimeError: 编辑器启动失败时抛出
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        cmd = self._build_command(filepath)
        try:
            subprocess.run(cmd, check=True)
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"编辑器启动失败: {e}")

    def _build_command(self, filepath: str) -> list:
        """构建编辑器命令行

        处理带参数的编辑器命令（如 'code --wait'）。

        Args:
            filepath: 要编辑的文件路径

        Returns:
            完整的命令行参数列表
        """
        parts = self.editor_cmd.split()
        parts.append(filepath)
        return parts

    def edit_content(self, content: str, suffix: str = ".md") -> str:
        """在临时文件中编辑内容并返回修改后的结果

        创建一个临时文件写入内容，打开编辑器编辑，然后读取修改后的内容。

        Args:
            content: 初始内容
            suffix: 临时文件后缀名

        Returns:
            编辑后的内容字符串
        """
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="vaultpilot_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            self.edit_file(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def edit_new_note(self, title: str, template: str = "") -> str:
        """编辑新笔记

        使用标题生成临时文件名，提供模板内容进行编辑。

        Args:
            title: 笔记标题
            template: 笔记模板内容

        Returns:
            编辑后的笔记内容
        """
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_title = safe_title.replace(" ", "-")[:50]
        return self.edit_content(template, suffix=f"_{safe_title}.md")
