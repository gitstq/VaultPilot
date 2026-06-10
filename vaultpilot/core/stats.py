"""统计分析引擎 - 知识库统计信息

收集和计算知识库的各种统计数据，包括笔记数量、
字数统计、标签分布、活跃度等。
"""

import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class StatsEngine:
    """统计分析引擎

    分析知识库中的笔记数据，生成统计报告。

    Attributes:
        _notes_data: 笔记数据缓存
        _vault_path: 知识库路径
    """

    def __init__(self, vault_path: str = "") -> None:
        """初始化统计分析引擎

        Args:
            vault_path: 知识库根目录路径
        """
        self._notes_data: List[Dict[str, Any]] = []
        self._vault_path: str = vault_path

    def set_notes(self, notes: List[Dict[str, Any]]) -> None:
        """设置要分析的笔记数据

        Args:
            notes: 笔记数据列表（Note.to_dict() 的结果）
        """
        self._notes_data = notes

    def analyze(self) -> Dict[str, Any]:
        """执行完整的统计分析

        Returns:
            包含所有统计信息的字典
        """
        if not self._notes_data:
            return self._empty_stats()

        total_notes = len(self._notes_data)
        total_words = sum(n.get("word_count", 0) for n in self._notes_data)
        total_chars = sum(n.get("char_count", 0) for n in self._notes_data)
        total_lines = sum(n.get("line_count", 0) for n in self._notes_data)

        # 标签统计
        tag_counter: Counter = Counter()
        for note in self._notes_data:
            for tag in note.get("tags", []):
                tag_counter[tag] += 1

        # 链接统计
        total_links = sum(len(n.get("links", [])) for n in self._notes_data)
        total_backlinks = sum(len(n.get("backlinks", [])) for n in self._notes_data)

        # 时间统计
        dates = []
        for note in self._notes_data:
            created = note.get("created", "")
            if created:
                try:
                    dates.append(datetime.fromisoformat(created))
                except (ValueError, TypeError):
                    pass

        # 活跃度统计（最近 7 天、30 天创建的笔记数）
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        recent_week = sum(1 for d in dates if d >= week_ago)
        recent_month = sum(1 for d in dates if d >= month_ago)

        # 平均字数
        avg_words = total_words / total_notes if total_notes > 0 else 0
        avg_chars = total_chars / total_notes if total_notes > 0 else 0

        # 最长笔记
        longest_note = max(self._notes_data, key=lambda n: n.get("word_count", 0))

        # 最活跃的标签
        top_tags = tag_counter.most_common(10)

        # 无标签笔记
        untagged = sum(1 for n in self._notes_data if not n.get("tags"))

        # 无链接笔记
        unlinked = sum(
            1 for n in self._notes_data
            if not n.get("links") and not n.get("backlinks")
        )

        return {
            "summary": {
                "total_notes": total_notes,
                "total_words": total_words,
                "total_chars": total_chars,
                "total_lines": total_lines,
                "avg_words_per_note": int(avg_words),
                "avg_chars_per_note": int(avg_chars),
            },
            "tags": {
                "total_unique_tags": len(tag_counter),
                "top_tags": top_tags,
                "untagged_notes": untagged,
            },
            "links": {
                "total_links": total_links,
                "total_backlinks": total_backlinks,
                "unlinked_notes": unlinked,
            },
            "activity": {
                "notes_this_week": recent_week,
                "notes_this_month": recent_month,
                "total_days": len(set(d.date() for d in dates)) if dates else 0,
            },
            "longest_note": {
                "title": longest_note.get("title", ""),
                "word_count": longest_note.get("word_count", 0),
            },
            "analyzed_at": datetime.now().isoformat(),
        }

    def get_word_distribution(self) -> Dict[str, int]:
        """获取笔记字数分布

        Returns:
            字数区间到数量的映射
        """
        distribution: Dict[str, int] = {
            "0-100": 0,
            "101-500": 0,
            "501-1000": 0,
            "1001-5000": 0,
            "5000+": 0,
        }

        for note in self._notes_data:
            words = note.get("word_count", 0)
            if words <= 100:
                distribution["0-100"] += 1
            elif words <= 500:
                distribution["101-500"] += 1
            elif words <= 1000:
                distribution["501-1000"] += 1
            elif words <= 5000:
                distribution["1001-5000"] += 1
            else:
                distribution["5000+"] += 1

        return distribution

    def get_tag_cloud(self) -> List[Tuple[str, int]]:
        """生成标签云数据

        Returns:
            (标签, 使用次数) 列表，按使用次数降序排列
        """
        tag_counter: Counter = Counter()
        for note in self._notes_data:
            for tag in note.get("tags", []):
                tag_counter[tag] += 1
        return tag_counter.most_common()

    def get_timeline(self) -> List[Tuple[str, int]]:
        """获取笔记创建时间线

        按月统计笔记创建数量。

        Returns:
            (月份, 数量) 列表
        """
        monthly: Counter = Counter()
        for note in self._notes_data:
            created = note.get("created", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    month_key = dt.strftime("%Y-%m")
                    monthly[month_key] += 1
                except (ValueError, TypeError):
                    pass

        return sorted(monthly.items())

    def get_size_stats(self) -> Dict[str, int]:
        """获取知识库磁盘占用统计

        Returns:
            各部分大小统计（字节）
        """
        if not self._vault_path or not os.path.isdir(self._vault_path):
            return {"total": 0}

        total_size = 0
        notes_size = 0
        meta_size = 0
        other_size = 0

        for root, dirs, files in os.walk(self._vault_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    size = os.path.getsize(filepath)
                    total_size += size
                    if ".vault" in root:
                        meta_size += size
                    elif root.endswith("notes"):
                        notes_size += size
                    else:
                        other_size += size
                except OSError:
                    pass

        return {
            "total": total_size,
            "notes": notes_size,
            "meta": meta_size,
            "other": other_size,
        }

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小

        Args:
            size_bytes: 字节数

        Returns:
            人类可读的大小字符串
        """
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _empty_stats(self) -> Dict[str, Any]:
        """返回空统计信息

        Returns:
            空统计信息字典
        """
        return {
            "summary": {
                "total_notes": 0,
                "total_words": 0,
                "total_chars": 0,
                "total_lines": 0,
                "avg_words_per_note": 0,
                "avg_chars_per_note": 0,
            },
            "tags": {
                "total_unique_tags": 0,
                "top_tags": [],
                "untagged_notes": 0,
            },
            "links": {
                "total_links": 0,
                "total_backlinks": 0,
                "unlinked_notes": 0,
            },
            "activity": {
                "notes_this_week": 0,
                "notes_this_month": 0,
                "total_days": 0,
            },
            "longest_note": {
                "title": "",
                "word_count": 0,
            },
            "analyzed_at": datetime.now().isoformat(),
        }
