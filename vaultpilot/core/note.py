"""笔记模型 - Note 类定义

封装笔记的数据模型，提供笔记的创建、读取、更新和序列化功能。
每篇笔记包含 YAML frontmatter 元数据和 Markdown 正文。
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .frontmatter import FrontmatterParser


class Note:
    """笔记数据模型

    表示知识库中的一篇笔记，包含元数据和正文内容。
    支持从文件加载、保存到文件以及元数据的增删改查。

    Attributes:
        filepath: 笔记文件路径
        title: 笔记标题
        tags: 标签列表
        created: 创建时间
        updated: 更新时间
        metadata: 完整的 frontmatter 元数据
        body: Markdown 正文内容
        links: 笔记中引用的其他笔记链接
        backlinks: 引用此笔记的其他笔记链接
    """

    _fm_parser: FrontmatterParser = FrontmatterParser()

    def __init__(
        self,
        filepath: str,
        title: str = "",
        tags: Optional[List[str]] = None,
        created: Optional[datetime] = None,
        updated: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        body: str = "",
    ) -> None:
        """初始化笔记对象

        Args:
            filepath: 笔记文件路径
            title: 笔记标题
            tags: 标签列表
            created: 创建时间
            updated: 更新时间
            metadata: 额外的元数据
            body: Markdown 正文内容
        """
        self.filepath: str = filepath
        self.title: str = title
        self.tags: List[str] = tags or []
        self.created: datetime = created or datetime.now()
        self.updated: datetime = updated or datetime.now()
        self.metadata: Dict[str, Any] = metadata or {}
        self.body: str = body
        self.links: List[str] = []
        self.backlinks: List[str] = []

    @classmethod
    def from_file(cls, filepath: str) -> "Note":
        """从 Markdown 文件加载笔记

        解析文件的 YAML frontmatter 和正文内容。

        Args:
            filepath: 笔记文件路径

        Returns:
            加载的 Note 对象

        Raises:
            FileNotFoundError: 文件不存在时抛出
            IOError: 文件读取失败时抛出
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"笔记文件不存在: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        metadata, body = cls._fm_parser.parse(content)

        title = metadata.pop("title", "")
        tags = metadata.pop("tags", [])
        created = metadata.pop("created", None)
        updated = metadata.pop("updated", None)

        # 转换日期字符串
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except (ValueError, TypeError):
                created = datetime.now()
        if isinstance(updated, str):
            try:
                updated = datetime.fromisoformat(updated)
            except (ValueError, TypeError):
                updated = datetime.now()

        if not isinstance(created, datetime):
            created = datetime.now()
        if not isinstance(updated, datetime):
            updated = datetime.now()

        note = cls(
            filepath=filepath,
            title=str(title),
            tags=list(tags) if isinstance(tags, list) else [],
            created=created,
            updated=updated,
            metadata=metadata,
            body=body,
        )

        # 解析 wiki-links
        note.links = note._extract_links()
        return note

    @classmethod
    def from_string(cls, content: str, filepath: str) -> "Note":
        """从字符串内容创建笔记对象

        解析 frontmatter 和正文，但不保存到文件。

        Args:
            content: Markdown 内容字符串
            filepath: 笔记文件路径

        Returns:
            Note 对象
        """
        metadata, body = cls._fm_parser.parse(content)

        title = metadata.pop("title", "")
        tags = metadata.pop("tags", [])
        created = metadata.pop("created", None)
        updated = metadata.pop("updated", None)

        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except (ValueError, TypeError):
                created = datetime.now()
        if isinstance(updated, str):
            try:
                updated = datetime.fromisoformat(updated)
            except (ValueError, TypeError):
                updated = datetime.now()

        if not isinstance(created, datetime):
            created = datetime.now()
        if not isinstance(updated, datetime):
            updated = datetime.now()

        note = cls(
            filepath=filepath,
            title=str(title),
            tags=list(tags) if isinstance(tags, list) else [],
            created=created,
            updated=updated,
            metadata=metadata,
            body=body,
        )
        note.links = note._extract_links()
        return note

    @classmethod
    def create(
        cls,
        filepath: str,
        title: str,
        tags: Optional[List[str]] = None,
        body: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Note":
        """创建新笔记

        Args:
            filepath: 笔记文件路径
            title: 笔记标题
            tags: 标签列表
            body: 正文内容
            metadata: 额外元数据

        Returns:
            新创建的 Note 对象
        """
        now = datetime.now()
        note = cls(
            filepath=filepath,
            title=title,
            tags=tags or [],
            created=now,
            updated=now,
            metadata=metadata or {},
            body=body,
        )
        note.links = note._extract_links()
        note.save()
        return note

    def save(self) -> None:
        """保存笔记到文件

        将元数据和正文序列化为带 frontmatter 的 Markdown 格式并写入文件。
        """
        self.updated = datetime.now()

        fm_data: Dict[str, Any] = {
            "title": self.title,
            "tags": self.tags,
            "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
            "updated": self.updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
        fm_data.update(self.metadata)

        content = self._fm_parser.dump(fm_data, self.body)

        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def update_metadata(self, key: str, value: Any) -> None:
        """更新笔记元数据

        Args:
            key: 元数据键名
            value: 元数据值
        """
        if key == "title":
            self.title = str(value)
        elif key == "tags":
            self.tags = list(value) if isinstance(value, list) else [value]
        elif key == "created":
            if isinstance(value, str):
                try:
                    self.created = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    pass
            elif isinstance(value, datetime):
                self.created = value
        else:
            self.metadata[key] = value

    def add_tag(self, tag: str) -> None:
        """添加标签

        Args:
            tag: 标签名称
        """
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> bool:
        """移除标签

        Args:
            tag: 标签名称

        Returns:
            是否成功移除
        """
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def _extract_links(self) -> List[str]:
        """从正文中提取 wiki-links

        解析 [[wiki-link]] 和 [[wiki-link|display]] 格式的双向链接。
        返回链接目标名称（不含显示名称）。

        Returns:
            链接目标列表
        """
        import re
        pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        matches = re.findall(pattern, self.body)
        return list(dict.fromkeys(m.strip() for m in matches))

    def get_filename(self) -> str:
        """获取笔记文件名

        Returns:
            文件名字符串
        """
        return os.path.basename(self.filepath)

    def get_word_count(self) -> int:
        """计算笔记正文的字数

        Returns:
            正文字数
        """
        # 移除 Markdown 语法标记
        import re
        clean = re.sub(r"[#*`\[\]()>_~-]", "", self.body)
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean:
            return 0
        # 中文字符按字计数，英文按词计数
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", clean))
        english_words = len(re.findall(r"[a-zA-Z]+", clean))
        return chinese_chars + english_words

    def get_char_count(self) -> int:
        """计算笔记正文的字符数

        Returns:
            正文字符数
        """
        return len(self.body)

    def get_line_count(self) -> int:
        """计算笔记正文的行数

        Returns:
            正文行数
        """
        if not self.body:
            return 0
        return len(self.body.split("\n"))

    def to_dict(self) -> Dict[str, Any]:
        """将笔记转换为字典

        Returns:
            包含笔记所有信息的字典
        """
        return {
            "filepath": self.filepath,
            "filename": self.get_filename(),
            "title": self.title,
            "tags": self.tags,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "metadata": self.metadata,
            "body": self.body,
            "links": self.links,
            "backlinks": self.backlinks,
            "word_count": self.get_word_count(),
            "char_count": self.get_char_count(),
            "line_count": self.get_line_count(),
        }

    def __repr__(self) -> str:
        """笔记的字符串表示

        Returns:
            格式化的字符串
        """
        return (
            f"Note(title={self.title!r}, "
            f"tags={self.tags}, "
            f"created={self.created.strftime('%Y-%m-%d')})"
        )

    def __eq__(self, other: object) -> bool:
        """判断两个笔记是否相等

        Args:
            other: 另一个对象

        Returns:
            是否相等
        """
        if not isinstance(other, Note):
            return NotImplemented
        return self.filepath == other.filepath

    def __hash__(self) -> int:
        """笔记的哈希值

        Returns:
            基于文件路径的哈希值
        """
        return hash(self.filepath)
