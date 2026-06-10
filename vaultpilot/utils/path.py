"""路径工具模块 - 文件路径处理和验证

提供知识库相关的路径操作工具函数，包括安全路径检查、
文件名规范化、知识库目录结构管理等。
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class PathHelper:
    """路径工具类

    封装知识库相关的路径操作，提供安全的路径处理方法。

    Attributes:
        vault_root: 知识库根目录路径
        notes_dir: 笔记存储目录
        trash_dir: 回收站目录
        meta_dir: 元数据目录
        index_file: 索引文件路径
    """

    # 符号链接目录名
    VAULT_META_DIR = ".vault"
    NOTES_DIR = "notes"
    ATTACHMENTS_DIR = "attachments"
    TRASH_DIR = "trash"
    INDEX_FILE = "index.json"
    CONFIG_FILE = "config.json"

    # 不安全的文件名字符
    _UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    def __init__(self, vault_root: str) -> None:
        """初始化路径工具

        Args:
            vault_root: 知识库根目录的绝对路径
        """
        self.vault_root: str = os.path.abspath(vault_root)
        self.notes_dir: str = os.path.join(self.vault_root, self.NOTES_DIR)
        self.attachments_dir: str = os.path.join(self.vault_root, self.ATTACHMENTS_DIR)
        self.trash_dir: str = os.path.join(self.vault_root, self.VAULT_META_DIR, self.TRASH_DIR)
        self.meta_dir: str = os.path.join(self.vault_root, self.VAULT_META_DIR)
        self.index_file: str = os.path.join(self.meta_dir, self.INDEX_FILE)
        self.config_file: str = os.path.join(self.meta_dir, self.CONFIG_FILE)

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 200) -> str:
        """规范化文件名，移除不安全字符

        将文件名中的不安全字符替换为下划线，截断过长的文件名。

        Args:
            filename: 原始文件名
            max_length: 文件名最大长度

        Returns:
            安全的文件名
        """
        # 替换不安全字符
        safe = PathHelper._UNSAFE_CHARS.sub("_", filename)
        # 替换连续空格和点
        safe = re.sub(r"\s+", " ", safe).strip()
        safe = re.sub(r"\.+", ".", safe)
        # 移除首尾的点和空格
        safe = safe.strip(". ")
        # 截断长度
        if len(safe) > max_length:
            safe = safe[:max_length].rstrip(". ")
        if not safe:
            safe = "untitled"
        return safe

    @staticmethod
    def title_to_filename(title: str) -> str:
        """将笔记标题转换为文件名

        将标题中的空格替换为连字符，转换为小写。

        Args:
            title: 笔记标题

        Returns:
            对应的文件名（不含扩展名）
        """
        safe_title = PathHelper.sanitize_filename(title)
        return safe_title.lower().replace(" ", "-")

    def note_path(self, filename: str) -> str:
        """获取笔记文件的完整路径

        Args:
            filename: 笔记文件名

        Returns:
            笔记文件的完整路径
        """
        if not filename.endswith(".md"):
            filename += ".md"
        return os.path.join(self.notes_dir, filename)

    def ensure_directories(self) -> None:
        """确保知识库所需的所有目录都存在

        创建笔记目录、附件目录、回收站目录和元数据目录。
        """
        for directory in (self.notes_dir, self.attachments_dir, self.trash_dir, self.meta_dir):
            os.makedirs(directory, exist_ok=True)

    def is_inside_vault(self, filepath: str) -> bool:
        """检查文件路径是否在知识库目录内

        防止路径遍历攻击。

        Args:
            filepath: 要检查的文件路径

        Returns:
            文件是否在知识库内
        """
        abs_path = os.path.abspath(filepath)
        return abs_path.startswith(self.vault_root)

    def is_vault_initialized(self) -> bool:
        """检查知识库是否已初始化

        Returns:
            知识库是否已初始化（.vault 目录是否存在）
        """
        return os.path.isdir(self.meta_dir)

    def move_to_trash(self, filepath: str) -> str:
        """将文件移动到回收站

        在回收站中保留原始目录结构，使用时间戳避免重名。

        Args:
            filepath: 要删除的文件路径

        Returns:
            回收站中的文件路径

        Raises:
            FileNotFoundError: 源文件不存在时抛出
            ValueError: 文件不在知识库内时抛出
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        if not self.is_inside_vault(filepath):
            raise ValueError("只能删除知识库内的文件")

        # 计算相对路径
        rel_path = os.path.relpath(filepath, self.vault_root)
        trash_path = os.path.join(self.trash_dir, rel_path)

        # 添加时间戳避免重名
        if os.path.exists(trash_path):
            base, ext = os.path.splitext(trash_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trash_path = f"{base}_{timestamp}{ext}"

        # 确保目标目录存在
        os.makedirs(os.path.dirname(trash_path), exist_ok=True)

        shutil.move(filepath, trash_path)
        return trash_path

    def restore_from_trash(self, trash_path: str) -> str:
        """从回收站恢复文件

        Args:
            trash_path: 回收站中的文件路径

        Returns:
            恢复后的文件路径

        Raises:
            FileNotFoundError: 回收站文件不存在时抛出
        """
        if not os.path.exists(trash_path):
            raise FileNotFoundError(f"回收站文件不存在: {trash_path}")

        # 计算原始路径（去掉时间戳后缀）
        rel_path = os.path.relpath(trash_path, self.trash_dir)
        # 移除时间戳后缀 _YYYYMMDD_HHMMSS
        rel_path = re.sub(r"_\d{8}_\d{6}(\.\w+)$", r"\1", rel_path)
        original_path = os.path.join(self.vault_root, rel_path)

        os.makedirs(os.path.dirname(original_path), exist_ok=True)
        shutil.move(trash_path, original_path)
        return original_path

    def list_trash(self) -> List[str]:
        """列出回收站中的所有文件

        Returns:
            回收站文件路径列表
        """
        if not os.path.exists(self.trash_dir):
            return []
        result: List[str] = []
        for root, _dirs, files in os.walk(self.trash_dir):
            for filename in files:
                result.append(os.path.join(root, filename))
        return sorted(result)

    def empty_trash(self) -> int:
        """清空回收站

        Returns:
            删除的文件数量
        """
        if not os.path.exists(self.trash_dir):
            return 0
        count = 0
        for root, _dirs, files in os.walk(self.trash_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    os.unlink(filepath)
                    count += 1
                except OSError:
                    pass
        return count

    def list_notes(self) -> List[str]:
        """列出所有笔记文件

        Returns:
            笔记文件路径列表
        """
        if not os.path.exists(self.notes_dir):
            return []
        result: List[str] = []
        for filename in os.listdir(self.notes_dir):
            if filename.endswith(".md"):
                result.append(os.path.join(self.notes_dir, filename))
        return sorted(result)

    def find_note_by_title(self, title: str) -> Optional[str]:
        """根据标题查找笔记文件

        Args:
            title: 笔记标题（可以是文件名或标题）

        Returns:
            笔记文件路径，未找到返回 None
        """
        # 先尝试精确匹配文件名
        filename = PathHelper.title_to_filename(title) + ".md"
        exact_path = os.path.join(self.notes_dir, filename)
        if os.path.exists(exact_path):
            return exact_path

        # 尝试直接作为文件名
        if title.endswith(".md"):
            direct_path = os.path.join(self.notes_dir, title)
            if os.path.exists(direct_path):
                return direct_path

        # 模糊匹配：遍历所有笔记，检查 frontmatter 中的标题
        for note_path in self.list_notes():
            try:
                with open(note_path, "r", encoding="utf-8") as f:
                    content = f.read(500)
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        fm = content[3:end].strip()
                        for line in fm.split("\n"):
                            if line.startswith("title:"):
                                note_title = line.split(":", 1)[1].strip().strip("\"'")
                                if note_title.lower() == title.lower():
                                    return note_path
            except (IOError, OSError):
                continue

        return None

    def get_relative_path(self, filepath: str) -> str:
        """获取相对于知识库根目录的路径

        Args:
            filepath: 绝对路径

        Returns:
            相对路径字符串
        """
        return os.path.relpath(filepath, self.vault_root)
