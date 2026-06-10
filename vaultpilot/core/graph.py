"""知识图谱生成器 - ASCII 字符画知识图谱

在终端中使用 ASCII 字符绘制笔记之间的关系图谱。
展示笔记间的双向链接关系。
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


class KnowledgeGraph:
    """知识图谱生成器

    使用 ASCII 字符在终端中绘制笔记关系图。
    支持多种布局模式和输出格式。

    Attributes:
        _nodes: 图节点 {node_id: label}
        _edges: 图边 [(from_id, to_id)]
        _max_nodes: 最大显示节点数
    """

    def __init__(self, max_nodes: int = 50) -> None:
        """初始化知识图谱生成器

        Args:
            max_nodes: 最大显示节点数，超过此数量的节点将被折叠
        """
        self._nodes: Dict[str, str] = {}
        self._edges: List[Tuple[str, str]] = []
        self._max_nodes: int = max_nodes

    def build_from_indexer(
        self,
        forward_links: Dict[str, List[str]],
        back_links: Dict[str, List[str]],
        note_titles: Dict[str, str],
    ) -> None:
        """从链接索引器构建图谱

        Args:
            forward_links: 正向链接 {note_id: [linked_ids]}
            back_links: 反向链接 {note_id: [source_ids]}
            note_titles: 笔记 ID 到标题的映射
        """
        self._nodes.clear()
        self._edges.clear()

        # 收集所有节点
        all_note_ids: Set[str] = set(forward_links.keys())
        for targets in forward_links.values():
            all_note_ids.update(targets)

        # 如果节点过多，选择连接数最多的节点
        if len(all_note_ids) > self._max_nodes:
            connection_counts: Dict[str, int] = defaultdict(int)
            for note_id, targets in forward_links.items():
                connection_counts[note_id] += len(targets)
                for target in targets:
                    connection_counts[target] += 1
            sorted_nodes = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
            selected: Set[str] = set(nid for nid, _ in sorted_nodes[:self._max_nodes])
            all_note_ids = selected

        # 设置节点标签
        for note_id in all_note_ids:
            title = note_titles.get(note_id, note_id)
            # 截断过长的标题
            if len(title) > 20:
                title = title[:18] + ".."
            self._nodes[note_id] = title

        # 设置边（去重）
        edge_set: Set[Tuple[str, str]] = set()
        for note_id, targets in forward_links.items():
            if note_id not in self._nodes:
                continue
            for target in targets:
                if target in self._nodes:
                    edge = tuple(sorted([note_id, target]))
                    edge_set.add(edge)
        self._edges = list(edge_set)

    def render_ascii(self, title: str = "Knowledge Graph") -> str:
        """渲染 ASCII 知识图谱

        使用树状布局在终端中展示笔记关系图。

        Args:
            title: 图谱标题

        Returns:
            ASCII 图谱字符串
        """
        if not self._nodes:
            return f"  {title}: (empty)"

        lines: List[str] = []
        lines.append("")
        lines.append(f"  ╔══ {title} ═══════════════════════════════════╗")
        lines.append(f"  ║  Nodes: {len(self._nodes):<4}  Edges: {len(self._edges):<4}"
                     f"{' ' * max(1, 30 - len(str(len(self._nodes))) - len(str(len(self._edges))))}║")
        lines.append(f"  ╠════════════════════════════════════════════╣")

        # 计算每个节点的连接数
        connections: Dict[str, Set[str]] = defaultdict(set)
        for from_id, to_id in self._edges:
            connections[from_id].add(to_id)
            connections[to_id].add(from_id)

        # 按连接数排序节点
        sorted_nodes = sorted(
            self._nodes.keys(),
            key=lambda n: len(connections.get(n, set())),
            reverse=True,
        )

        # 渲染节点列表和连接关系
        for i, node_id in enumerate(sorted_nodes):
            label = self._nodes[node_id]
            node_connections = connections.get(node_id, set())

            # 节点标记
            if len(node_connections) >= 5:
                marker = "[*]"  # 高连接节点
            elif len(node_connections) >= 2:
                marker = "[o]"  # 中等连接
            else:
                marker = "[.]"  # 低连接/孤立

            line = f"  ║  {marker} {label:<20}"
            lines.append(line)

            # 显示连接
            if node_connections and i < 15:
                conn_labels: List[str] = []
                for conn_id in sorted(node_connections)[:5]:
                    conn_label = self._nodes.get(conn_id, conn_id)
                    conn_labels.append(conn_label)
                if conn_labels:
                    conn_str = ", ".join(conn_labels)
                    if len(node_connections) > 5:
                        conn_str += f" +{len(node_connections) - 5} more"
                    lines.append(f"  ║      └──> {conn_str}")

        lines.append(f"  ╚════════════════════════════════════════════╝")
        lines.append(f"  Legend: [*] hub(5+)  [o] linked(2+)  [.] leaf")
        lines.append("")

        return "\n".join(lines)

    def render_compact(self) -> str:
        """渲染紧凑格式的图谱

        使用更紧凑的格式展示节点和连接。

        Returns:
            紧凑格式图谱字符串
        """
        if not self._nodes:
            return "  (empty graph)"

        lines: List[str] = []
        lines.append("")
        lines.append(f"  Nodes ({len(self._nodes)}):")

        for node_id, label in sorted(self._nodes.items(), key=lambda x: x[1]):
            lines.append(f"    - {label}")

        lines.append("")
        lines.append(f"  Edges ({len(self._edges)}):")

        for from_id, to_id in self._edges[:30]:
            from_label = self._nodes.get(from_id, from_id)
            to_label = self._nodes.get(to_id, to_id)
            lines.append(f"    {from_label} --> {to_label}")

        if len(self._edges) > 30:
            lines.append(f"    ... and {len(self._edges) - 30} more edges")

        lines.append("")
        return "\n".join(lines)

    def render_mermaid(self) -> str:
        """生成 Mermaid 格式的图谱定义

        可用于在支持 Mermaid 的环境中渲染图谱。

        Returns:
            Mermaid 格式字符串
        """
        lines: List[str] = []
        lines.append("graph LR")

        # 生成节点定义（使用安全的 ID）
        safe_ids: Dict[str, str] = {}
        for i, (node_id, label) in enumerate(self._nodes.items()):
            safe_id = f"n{i}"
            safe_ids[node_id] = safe_id
            # 转义特殊字符
            safe_label = label.replace('"', "'").replace("[", "(").replace("]", ")")
            lines.append(f'    {safe_id}["{safe_label}"]')

        # 生成边定义
        for from_id, to_id in self._edges:
            if from_id in safe_ids and to_id in safe_ids:
                lines.append(f"    {safe_ids[from_id]} --> {safe_ids[to_id]}")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, int]:
        """获取图谱统计信息

        Returns:
            统计信息字典
        """
        # 计算度数
        degrees: Dict[str, int] = defaultdict(int)
        for from_id, to_id in self._edges:
            degrees[from_id] += 1
            degrees[to_id] += 1

        max_degree = max(degrees.values()) if degrees else 0
        avg_degree = sum(degrees.values()) / len(self._nodes) if self._nodes else 0

        # 计算孤立节点
        connected_nodes: Set[str] = set()
        for from_id, to_id in self._edges:
            connected_nodes.add(from_id)
            connected_nodes.add(to_id)
        orphan_count = len(self._nodes) - len(connected_nodes)

        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "max_degree": max_degree,
            "avg_degree": int(avg_degree),
            "orphan_nodes": orphan_count,
        }
