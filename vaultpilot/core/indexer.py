"""双向链接索引器 - Wiki-Link 解析与反向链接管理

自动解析 Markdown 文件中的 [[wiki-links]] 格式双向链接，
构建正向和反向链接索引。
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple


class LinkIndexer:
    """双向链接索引器

    扫描知识库中所有笔记，解析 [[wiki-link]] 格式的链接，
    维护正向链接（笔记引用了哪些笔记）和反向链接（哪些笔记引用了当前笔记）的索引。

    Attributes:
        _forward_links: 正向链接 {note_id: [linked_note_ids]}
        _back_links: 反向链接 {note_id: [source_note_ids]}
        _unresolved: 未解析的链接 {note_id: [unresolved_link_names]}
        _notes_index: 笔记名称到 ID 的映射 {title: note_id}
    """

    # Wiki-link 正则表达式
    WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+?)(?:\|([^\]]+))?\]\]")

    def __init__(self) -> None:
        """初始化链接索引器"""
        self._forward_links: Dict[str, List[str]] = {}
        self._back_links: Dict[str, List[str]] = {}
        self._unresolved: Dict[str, List[str]] = {}
        self._notes_index: Dict[str, str] = {}

    def build_index(self, notes: List[Tuple[str, str, str]]) -> None:
        """构建完整的链接索引

        扫描所有笔记，解析 wiki-links，建立正向和反向链接索引。

        Args:
            notes: 笔记列表，每项为 (note_id, title, content) 元组
        """
        self._forward_links.clear()
        self._back_links.clear()
        self._unresolved.clear()
        self._notes_index.clear()

        # 构建笔记名称索引
        for note_id, title, _content in notes:
            self._notes_index[title.lower()] = note_id
            # 同时用文件名（不含扩展名）建立索引
            filename = os.path.splitext(os.path.basename(note_id))[0].lower()
            self._notes_index[filename] = note_id

        # 解析链接
        for note_id, _title, content in notes:
            links = self._extract_links(content)
            self._forward_links[note_id] = []

            for link_name in links:
                resolved_id = self._resolve_link(link_name)
                if resolved_id:
                    self._forward_links[note_id].append(resolved_id)
                    # 更新反向链接
                    if resolved_id not in self._back_links:
                        self._back_links[resolved_id] = []
                    if note_id not in self._back_links[resolved_id]:
                        self._back_links[resolved_id].append(note_id)
                else:
                    if note_id not in self._unresolved:
                        self._unresolved[note_id] = []
                    if link_name not in self._unresolved[note_id]:
                        self._unresolved[note_id].append(link_name)

    def _extract_links(self, content: str) -> List[str]:
        """从内容中提取 wiki-links

        Args:
            content: Markdown 内容

        Returns:
            链接名称列表
        """
        matches = self.WIKI_LINK_PATTERN.findall(content)
        # 返回链接目标（忽略显示名称）
        return [m[0].strip() for m in matches]

    def _resolve_link(self, link_name: str) -> Optional[str]:
        """解析链接名称到笔记 ID

        Args:
            link_name: 链接名称

        Returns:
            笔记 ID，未找到返回 None
        """
        # 精确匹配
        if link_name.lower() in self._notes_index:
            return self._notes_index[link_name.lower()]

        # 尝试文件名匹配
        filename = os.path.splitext(link_name)[0].lower()
        if filename in self._notes_index:
            return self._notes_index[filename]

        return None

    def get_forward_links(self, note_id: str) -> List[str]:
        """获取笔记的正向链接

        Args:
            note_id: 笔记 ID

        Returns:
            该笔记引用的其他笔记 ID 列表
        """
        return self._forward_links.get(note_id, [])

    def get_back_links(self, note_id: str) -> List[str]:
        """获取笔记的反向链接

        Args:
            note_id: 笔记 ID

        Returns:
            引用该笔记的其他笔记 ID 列表
        """
        return self._back_links.get(note_id, [])

    def get_unresolved_links(self, note_id: str) -> List[str]:
        """获取笔记中未解析的链接

        Args:
            note_id: 笔记 ID

        Returns:
            未解析的链接名称列表
        """
        return self._unresolved.get(note_id, [])

    def get_all_unresolved(self) -> Dict[str, List[str]]:
        """获取所有未解析的链接

        Returns:
            未解析链接字典 {note_id: [link_names]}
        """
        return dict(self._unresolved)

    def get_orphan_notes(self) -> List[str]:
        """获取孤立笔记（没有任何链接指向的笔记）

        Returns:
            孤立笔记 ID 列表
        """
        all_ids = set(self._forward_links.keys())
        referenced_ids = set(self._back_links.keys())
        return sorted(all_ids - referenced_ids)

    def get_linked_notes(self, note_id: str) -> Set[str]:
        """获取与指定笔记有关联的所有笔记

        包括正向链接和反向链接。

        Args:
            note_id: 笔记 ID

        Returns:
            关联笔记 ID 集合
        """
        linked: Set[str] = set()
        linked.update(self.get_forward_links(note_id))
        linked.update(self.get_back_links(note_id))
        return linked

    def get_link_count(self, note_id: str) -> Tuple[int, int]:
        """获取笔记的链接统计

        Args:
            note_id: 笔记 ID

        Returns:
            元组 (正向链接数, 反向链接数)
        """
        forward = len(self.get_forward_links(note_id))
        backward = len(self.get_back_links(note_id))
        return forward, backward

    def get_stats(self) -> Dict[str, int]:
        """获取链接索引统计信息

        Returns:
            统计信息字典
        """
        total_forward = sum(len(v) for v in self._forward_links.values())
        total_backward = sum(len(v) for v in self._back_links.values())
        total_unresolved = sum(len(v) for v in self._unresolved.values())

        return {
            "total_notes": len(self._forward_links),
            "total_forward_links": total_forward,
            "total_back_links": total_backward,
            "total_unresolved_links": total_unresolved,
            "orphan_notes": len(self.get_orphan_notes()),
        }

    def render_links(self, content: str, note_titles: Dict[str, str]) -> str:
        """将 wiki-links 渲染为可读格式

        将 [[link|display]] 格式替换为显示名称。

        Args:
            content: 原始 Markdown 内容
            note_titles: 笔记 ID 到标题的映射

        Returns:
            渲染后的内容
        """
        def replace_link(match: re.Match) -> str:
            link_name = match.group(1).strip()
            display_name = match.group(2)
            if display_name:
                return display_name
            return link_name

        return self.WIKI_LINK_PATTERN.sub(replace_link, content)
