"""Vault 知识库核心类 - 知识库管理引擎

Vault 是 VaultPilot 的核心类，封装了知识库的所有管理功能。
提供笔记 CRUD、搜索、标签管理、链接索引、图谱生成等功能的统一接口。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .note import Note
from .search import SearchEngine
from .indexer import LinkIndexer
from .graph import KnowledgeGraph
from .git import GitManager
from .importer import ImportExportEngine
from .stats import StatsEngine
from ..utils.config import Config
from ..utils.editor import Editor
from ..utils.output import OutputFormatter
from ..utils.path import PathHelper


class Vault:
    """知识库管理核心类

    Vault 是 VaultPilot 的核心引擎，管理知识库的完整生命周期。
    包括知识库初始化、笔记管理、搜索、标签、链接索引、图谱、
    Git 集成、导入导出和统计分析等功能。

    Attributes:
        vault_path: 知识库根目录路径
        config: 配置管理器
        path_helper: 路径工具
        output: 输出格式化器
        editor: 编辑器调用器
        search_engine: 搜索引擎
        link_indexer: 链接索引器
        knowledge_graph: 知识图谱
        git_manager: Git 管理器
        import_export: 导入导出引擎
        stats_engine: 统计分析引擎
        _notes_cache: 笔记缓存
    """

    def __init__(self, vault_path: str) -> None:
        """初始化知识库管理器

        Args:
            vault_path: 知识库根目录路径

        Raises:
            ValueError: 路径不是有效的知识库时抛出
        """
        self.vault_path: str = os.path.abspath(vault_path)
        self.config: Config = Config(self.vault_path)
        self.path_helper: PathHelper = PathHelper(self.vault_path)
        self.output: OutputFormatter = OutputFormatter()
        self.editor: Editor = Editor(self.config.get("editor"))

        # 核心引擎
        self.search_engine: SearchEngine = SearchEngine()
        self.link_indexer: LinkIndexer = LinkIndexer()
        self.knowledge_graph: KnowledgeGraph = KnowledgeGraph(
            self.config.get("graph_max_nodes", 50)
        )
        self.git_manager: GitManager = GitManager(self.vault_path)
        self.import_export: ImportExportEngine = ImportExportEngine(
            self.vault_path, self.path_helper.notes_dir
        )
        self.stats_engine: StatsEngine = StatsEngine(self.vault_path)

        # 笔记缓存
        self._notes_cache: Dict[str, Note] = {}

        # 验证知识库
        if not self.path_helper.is_vault_initialized():
            raise ValueError(f"目录不是有效的 VaultPilot 知识库: {self.vault_path}")

    @classmethod
    def init(cls, vault_path: str) -> "Vault":
        """初始化新的知识库

        创建知识库目录结构和配置文件。

        Args:
            vault_path: 知识库根目录路径

        Returns:
            初始化后的 Vault 实例

        Raises:
            ValueError: 目录已存在且不为空时抛出
        """
        vault_path = os.path.abspath(vault_path)
        path_helper = PathHelper(vault_path)
        output = OutputFormatter()

        # 检查目录
        if os.path.exists(vault_path):
            if path_helper.is_vault_initialized():
                output.warning("知识库已存在，跳过初始化")
                return cls(vault_path)
            # 目录存在但不是知识库
            contents = os.listdir(vault_path)
            if contents:
                raise ValueError(f"目录不为空且不是知识库: {vault_path}")

        # 创建目录结构
        path_helper.ensure_directories()

        # 创建初始配置
        config = Config(vault_path)
        config.save_vault_config()

        # 创建 .gitignore
        gitignore_path = os.path.join(vault_path, ".vault", ".gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("*.tmp\n*.bak\n")

        # 创建欢迎笔记
        notes_dir = path_helper.notes_dir
        welcome_path = os.path.join(notes_dir, "welcome.md")
        welcome_content = """---
title: Welcome to VaultPilot
tags: [welcome, getting-started]
created: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
---

# Welcome to VaultPilot

VaultPilot 是一个轻量级终端 Markdown 知识库管理引擎。

## 快速开始

- 使用 `vault new <title>` 创建新笔记
- 使用 `vault list` 查看所有笔记
- 使用 `vault search <query>` 搜索笔记
- 使用 `vault tag add <note> <tag>` 添加标签
- 使用 `vault graph` 查看知识图谱
- 使用 `vault tui` 进入交互式界面

## 双向链接

你可以使用 `[[wiki-link]]` 语法在笔记间创建双向链接。

例如：[[welcome]] 会链接到这篇欢迎笔记。

## 标签系统

使用标签来组织你的笔记。每篇笔记可以有多个标签。

相关笔记：[[getting-started]]
"""

        with open(welcome_path, "w", encoding="utf-8") as f:
            f.write(welcome_content)

        output.success(f"知识库已初始化: {vault_path}")
        return cls(vault_path)

    # ========== 笔记 CRUD ==========

    def new_note(
        self,
        title: str,
        tags: Optional[List[str]] = None,
        body: str = "",
        open_editor: bool = True,
    ) -> Note:
        """创建新笔记

        Args:
            title: 笔记标题
            tags: 标签列表
            body: 初始正文内容
            open_editor: 是否打开编辑器

        Returns:
            创建的 Note 对象
        """
        filename = PathHelper.title_to_filename(title) + ".md"
        filepath = self.path_helper.note_path(filename)

        # 生成模板
        if not body:
            body = f"\n# {title}\n\n"

        template = f"""---
title: {title}
tags: {tags or []}
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{body}"""

        if open_editor:
            edited_content = self.editor.edit_content(template)
            note = Note.from_string(edited_content, filepath)
            note.save()
        else:
            note = Note.create(filepath, title, tags, body)

        self._invalidate_cache()
        self._rebuild_index()
        self.output.success(f"笔记已创建: {title}")
        return note

    def get_note(self, identifier: str) -> Optional[Note]:
        """获取笔记

        通过 ID（文件名）或标题查找笔记。

        Args:
            identifier: 笔记文件名或标题

        Returns:
            Note 对象，未找到返回 None
        """
        # 先查缓存
        if identifier in self._notes_cache:
            return self._notes_cache[identifier]

        # 按文件名查找
        filepath = self.path_helper.note_path(identifier)
        if os.path.exists(filepath):
            note = Note.from_file(filepath)
            self._notes_cache[identifier] = note
            return note

        # 按标题查找
        found_path = self.path_helper.find_note_by_title(identifier)
        if found_path:
            note = Note.from_file(found_path)
            self._notes_cache[identifier] = note
            return note

        return None

    def edit_note(self, identifier: str) -> Optional[Note]:
        """编辑笔记

        打开系统编辑器编辑指定笔记。

        Args:
            identifier: 笔记文件名或标题

        Returns:
            编辑后的 Note 对象，未找到返回 None
        """
        note = self.get_note(identifier)
        if not note:
            self.output.error(f"笔记不存在: {identifier}")
            return None

        # 读取当前内容
        with open(note.filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 编辑
        edited = self.editor.edit_content(content)
        if edited != content:
            with open(note.filepath, "w", encoding="utf-8") as f:
                f.write(edited)
            self._invalidate_cache()
            self._rebuild_index()
            self.output.success(f"笔记已更新: {note.title}")
        else:
            self.output.info("笔记内容未变更")

        return self.get_note(identifier)

    def delete_note(self, identifier: str) -> bool:
        """删除笔记（移到回收站）

        Args:
            identifier: 笔记文件名或标题

        Returns:
            是否成功删除
        """
        note = self.get_note(identifier)
        if not note:
            self.output.error(f"笔记不存在: {identifier}")
            return False

        try:
            trash_path = self.path_helper.move_to_trash(note.filepath)
            self._invalidate_cache()
            self._rebuild_index()
            self.output.success(f"笔记已移到回收站: {note.title}")
            self.output.info(f"回收站路径: {trash_path}")
            return True
        except (FileNotFoundError, ValueError, OSError) as e:
            self.output.error(f"删除失败: {e}")
            return False

    def list_notes(
        self,
        tag: Optional[str] = None,
        sort_by: str = "updated",
        reverse: bool = True,
        limit: int = 50,
    ) -> List[Note]:
        """列出所有笔记

        Args:
            tag: 按标签过滤
            sort_by: 排序字段 (title, created, updated, word_count)
            reverse: 是否降序
            limit: 最大返回数量

        Returns:
            笔记列表
        """
        notes = self._get_all_notes()

        # 标签过滤
        if tag:
            tag_lower = tag.lower()
            notes = [n for n in notes if tag_lower in [t.lower() for t in n.tags]]

        # 排序
        sort_key = self._get_sort_key(sort_by)
        notes.sort(key=sort_key, reverse=reverse)

        return notes[:limit]

    def show_note(self, identifier: str) -> Optional[Note]:
        """查看笔记详情

        Args:
            identifier: 笔记文件名或标题

        Returns:
            Note 对象，未找到返回 None
        """
        note = self.get_note(identifier)
        if not note:
            self.output.error(f"笔记不存在: {identifier}")
            return None

        # 显示笔记信息
        self.output.title(note.title)
        self.output.key_value("文件", note.get_filename())
        self.output.key_value("标签", ", ".join(note.tags) if note.tags else "(无)")
        self.output.key_value("创建时间", note.created.strftime("%Y-%m-%d %H:%M:%S"))
        self.output.key_value("更新时间", note.updated.strftime("%Y-%m-%d %H:%M:%S"))
        self.output.key_value("字数", str(note.get_word_count()))
        self.output.key_value("行数", str(note.get_line_count()))

        if note.links:
            self.output.key_value("正向链接", ", ".join(note.links))
        if note.backlinks:
            self.output.key_value("反向链接", ", ".join(note.backlinks))

        self.output.rule("Content")
        self.output.markdown(note.body)

        return note

    # ========== 搜索 ==========

    def search(self, query: str, limit: int = 20) -> List[Tuple[str, float, str]]:
        """全文搜索笔记

        Args:
            query: 搜索查询
            limit: 最大结果数

        Returns:
            搜索结果列表 (doc_id, score, filepath)
        """
        self._ensure_index()
        return self.search_engine.search(query, limit=limit)

    # ========== 标签管理 ==========

    def add_tag(self, identifier: str, tag: str) -> bool:
        """为笔记添加标签

        Args:
            identifier: 笔记文件名或标题
            tag: 标签名称

        Returns:
            是否成功
        """
        note = self.get_note(identifier)
        if not note:
            self.output.error(f"笔记不存在: {identifier}")
            return False

        note.add_tag(tag)
        note.save()
        self._invalidate_cache()
        self._rebuild_index()
        self.output.success(f"已添加标签 '{tag}' 到笔记 '{note.title}'")
        return True

    def remove_tag(self, identifier: str, tag: str) -> bool:
        """移除笔记标签

        Args:
            identifier: 笔记文件名或标题
            tag: 标签名称

        Returns:
            是否成功
        """
        note = self.get_note(identifier)
        if not note:
            self.output.error(f"笔记不存在: {identifier}")
            return False

        if note.remove_tag(tag):
            note.save()
            self._invalidate_cache()
            self._rebuild_index()
            self.output.success(f"已移除标签 '{tag}' 从笔记 '{note.title}'")
            return True
        else:
            self.output.warning(f"标签 '{tag}' 不存在于笔记 '{note.title}'")
            return False

    def list_tags(self) -> List[Tuple[str, int]]:
        """列出所有标签及其使用次数

        Returns:
            (标签名, 使用次数) 列表
        """
        notes = self._get_all_notes()
        from collections import Counter
        tag_counter: Counter = Counter()
        for note in notes:
            for tag in note.tags:
                tag_counter[tag] += 1
        return tag_counter.most_common()

    # ========== 知识图谱 ==========

    def show_graph(self) -> str:
        """生成并显示知识图谱

        Returns:
            ASCII 图谱字符串
        """
        self._ensure_index()

        # 构建图谱数据
        note_titles: Dict[str, str] = {}
        notes_data: List[Tuple[str, str, str]] = []

        for note in self._get_all_notes():
            note_id = note.get_filename()
            note_titles[note_id] = note.title
            notes_data.append((note_id, note.title, note.body))

        self.link_indexer.build_index(notes_data)

        # 构建正向和反向链接
        forward: Dict[str, List[str]] = {}
        back: Dict[str, List[str]] = {}
        for note_id in note_titles:
            forward[note_id] = self.link_indexer.get_forward_links(note_id)
            back[note_id] = self.link_indexer.get_back_links(note_id)

        self.knowledge_graph.build_from_indexer(forward, back, note_titles)
        return self.knowledge_graph.render_ascii()

    # ========== 统计 ==========

    def show_stats(self) -> Dict[str, Any]:
        """显示知识库统计信息

        Returns:
            统计信息字典
        """
        notes = self._get_all_notes()
        notes_data = [n.to_dict() for n in notes]
        self.stats_engine.set_notes(notes_data)
        return self.stats_engine.analyze()

    # ========== 导入导出 ==========

    def import_files(
        self,
        source_dir: str,
        copy_attachments: bool = True,
        overwrite: bool = False,
    ) -> Tuple[int, int, List[str]]:
        """导入 Markdown 文件

        Args:
            source_dir: 源目录
            copy_attachments: 是否复制附件
            overwrite: 是否覆盖

        Returns:
            (成功数, 跳过数, 错误列表)
        """
        result = self.import_export.import_markdown_files(
            source_dir, copy_attachments, overwrite
        )
        self._invalidate_cache()
        self._rebuild_index()
        return result

    def export_notes(
        self,
        output_path: str,
        format_type: str = "json",
    ) -> Tuple[bool, str]:
        """导出笔记

        Args:
            output_path: 输出路径
            format_type: 导出格式 (json/html)

        Returns:
            (是否成功, 输出路径或错误信息)
        """
        notes = self._get_all_notes()
        notes_data = [n.to_dict() for n in notes]

        if format_type == "html":
            return self.import_export.export_html(notes_data, output_path)
        else:
            return self.import_export.export_json(notes_data, output_path)

    # ========== 内部方法 ==========

    def _get_all_notes(self) -> List[Note]:
        """获取所有笔记

        Returns:
            笔记列表
        """
        note_paths = self.path_helper.list_notes()
        notes: List[Note] = []

        for filepath in note_paths:
            try:
                note = Note.from_file(filepath)
                # 更新反向链接
                note.backlinks = self.link_indexer.get_back_links(note.get_filename())
                notes.append(note)
            except (IOError, OSError) as e:
                self.output.warning(f"加载笔记失败 {filepath}: {e}")

        return notes

    def _ensure_index(self) -> None:
        """确保搜索索引和链接索引是最新的"""
        if not self.search_engine._documents:
            self._rebuild_index()

    def _rebuild_index(self) -> None:
        """重建搜索索引和链接索引"""
        notes = self._get_all_notes()
        notes_data: List[Tuple[str, str, str]] = []

        for note in notes:
            note_id = note.get_filename()
            content = f"{note.title} {note.title} {note.body}"
            notes_data.append((note_id, content, note.filepath))

        # 重建搜索索引
        self.search_engine.clear()
        self.search_engine.index_documents(notes_data)

        # 重建链接索引
        link_data: List[Tuple[str, str, str]] = []
        for note in notes:
            note_id = note.get_filename()
            link_data.append((note_id, note.title, note.body))
        self.link_indexer.build_index(link_data)

    def _invalidate_cache(self) -> None:
        """清除笔记缓存"""
        self._notes_cache.clear()

    @staticmethod
    def _get_sort_key(sort_by: str):
        """获取排序键函数

        Args:
            sort_by: 排序字段名

        Returns:
            排序键函数
        """
        if sort_by == "title":
            return lambda n: n.title.lower()
        elif sort_by == "created":
            return lambda n: n.created
        elif sort_by == "word_count":
            return lambda n: n.get_word_count()
        else:
            return lambda n: n.updated
