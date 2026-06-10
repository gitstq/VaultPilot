"""导入导出引擎 - 批量导入和导出笔记

支持批量导入 Markdown 文件，导出为 JSON 或 HTML 格式。
"""

import html
import json
import os
import re
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class ImportExportEngine:
    """导入导出引擎

    处理笔记的批量导入和导出操作。

    Attributes:
        vault_path: 知识库根目录路径
        notes_dir: 笔记目录路径
    """

    def __init__(self, vault_path: str, notes_dir: str) -> None:
        """初始化导入导出引擎

        Args:
            vault_path: 知识库根目录路径
            notes_dir: 笔记目录路径
        """
        self.vault_path: str = vault_path
        self.notes_dir: str = notes_dir

    def import_markdown_files(
        self,
        source_dir: str,
        copy_attachments: bool = True,
        overwrite: bool = False,
    ) -> Tuple[int, int, List[str]]:
        """批量导入 Markdown 文件

        将指定目录中的所有 .md 文件导入到知识库。

        Args:
            source_dir: 源目录路径
            copy_attachments: 是否同时复制附件文件
            overwrite: 是否覆盖已存在的文件

        Returns:
            元组 (成功数, 跳过数, 错误信息列表)
        """
        if not os.path.isdir(source_dir):
            return 0, 0, [f"源目录不存在: {source_dir}"]

        success_count = 0
        skip_count = 0
        errors: List[str] = []

        for filename in os.listdir(source_dir):
            if not filename.endswith(".md"):
                continue

            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(self.notes_dir, filename)

            if os.path.exists(dest_path) and not overwrite:
                skip_count += 1
                continue

            try:
                shutil.copy2(source_path, dest_path)
                success_count += 1
            except (IOError, OSError) as e:
                errors.append(f"导入失败 {filename}: {e}")

        # 复制附件
        if copy_attachments:
            attachment_dirs = ["images", "assets", "attachments", "files"]
            for ad in attachment_dirs:
                src_att = os.path.join(source_dir, ad)
                if os.path.isdir(src_att):
                    dest_att = os.path.join(self.vault_path, ad)
                    try:
                        if os.path.exists(dest_att):
                            for item in os.listdir(src_att):
                                s = os.path.join(src_att, item)
                                d = os.path.join(dest_att, item)
                                if os.path.isfile(s):
                                    shutil.copy2(s, d)
                        else:
                            shutil.copytree(src_att, dest_att)
                    except (IOError, OSError) as e:
                        errors.append(f"复制附件失败: {e}")

        return success_count, skip_count, errors

    def import_single_file(self, source_path: str, title: Optional[str] = None) -> Tuple[bool, str]:
        """导入单个 Markdown 文件

        Args:
            source_path: 源文件路径
            title: 新标题（可选，用于重命名）

        Returns:
            元组 (是否成功, 目标路径或错误信息)
        """
        if not os.path.isfile(source_path):
            return False, f"文件不存在: {source_path}"

        if title:
            filename = self._safe_filename(title) + ".md"
        else:
            filename = os.path.basename(source_path)

        dest_path = os.path.join(self.notes_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            return True, dest_path
        except (IOError, OSError) as e:
            return False, f"导入失败: {e}"

    def export_json(
        self,
        notes: List[Dict[str, Any]],
        output_path: str,
    ) -> Tuple[bool, str]:
        """导出笔记为 JSON 格式

        Args:
            notes: 笔记数据列表
            output_path: 输出文件路径

        Returns:
            元组 (是否成功, 输出路径或错误信息)
        """
        try:
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "total_notes": len(notes),
                "notes": notes,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True, output_path
        except (IOError, OSError) as e:
            return False, f"导出失败: {e}"

    def export_html(
        self,
        notes: List[Dict[str, Any]],
        output_path: str,
        title: str = "VaultPilot Export",
    ) -> Tuple[bool, str]:
        """导出笔记为 HTML 格式

        生成一个自包含的 HTML 文件，包含所有笔记内容。

        Args:
            notes: 笔记数据列表
            output_path: 输出文件路径
            title: HTML 页面标题

        Returns:
            元组 (是否成功, 输出路径或错误信息)
        """
        try:
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            html_content = self._generate_html(notes, title)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return True, output_path
        except (IOError, OSError) as e:
            return False, f"导出失败: {e}"

    def _generate_html(self, notes: List[Dict[str, Any]], title: str) -> str:
        """生成 HTML 内容

        Args:
            notes: 笔记数据列表
            title: 页面标题

        Returns:
            完整的 HTML 字符串
        """
        notes_html: List[str] = []

        for note in notes:
            note_title = html.escape(note.get("title", "Untitled"))
            note_body = self._markdown_to_html(note.get("body", ""))
            tags = note.get("tags", [])
            tags_html = " ".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
            created = note.get("created", "")
            updated = note.get("updated", "")

            note_html = f"""
        <article class="note">
            <h2 id="{html.escape(note.get('filename', ''))}">{note_title}</h2>
            <div class="meta">
                <span class="date">Created: {created}</span>
                <span class="date">Updated: {updated}</span>
                {f'<div class="tags">{tags_html}</div>' if tags else ''}
            </div>
            <div class="content">
                {note_body}
            </div>
        </article>"""
            notes_html.append(note_html)

        all_notes_html = "\n".join(notes_html)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #fafafa;
            color: #333;
            line-height: 1.6;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; margin-bottom: 15px; }}
        .note {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .meta {{ color: #888; font-size: 0.85em; margin-bottom: 15px; }}
        .tag {{
            display: inline-block;
            background: #e8f4fd;
            color: #2980b9;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
        }}
        .content {{ line-height: 1.8; }}
        .content code {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        .content pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .content blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 15px;
            color: #666;
            margin: 10px 0;
        }}
        .content a {{ color: #2980b9; text-decoration: none; }}
        .content a:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; color: #aaa; margin-top: 40px; font-size: 0.85em; }}
    </style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    <p class="meta">Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total: {len(notes)} notes</p>
    {all_notes_html}
    <div class="footer">Generated by VaultPilot</div>
</body>
</html>"""

    def _markdown_to_html(self, md_text: str) -> str:
        """简单的 Markdown 到 HTML 转换

        支持常见的 Markdown 语法：标题、粗体、斜体、代码、链接、列表、引用。

        Args:
            md_text: Markdown 文本

        Returns:
            HTML 字符串
        """
        if not md_text:
            return ""

        lines = md_text.split("\n")
        html_lines: List[str] = []
        in_code_block = False
        in_list = False
        in_blockquote = False

        for line in lines:
            # 代码块
            if line.strip().startswith("```"):
                if in_code_block:
                    html_lines.append("</code></pre>")
                    in_code_block = False
                else:
                    html_lines.append("<pre><code>")
                    in_code_block = True
                continue

            if in_code_block:
                html_lines.append(html.escape(line))
                continue

            stripped = line.strip()

            # 关闭列表
            if in_list and not stripped.startswith("- ") and not stripped.startswith("* "):
                html_lines.append("</ul>")
                in_list = False

            # 关闭引用
            if in_blockquote and not stripped.startswith(">"):
                html_lines.append("</blockquote>")
                in_blockquote = False

            # 标题
            if stripped.startswith("### "):
                html_lines.append(f"<h3>{self._inline_md(stripped[4:])}</h3>")
            elif stripped.startswith("## "):
                html_lines.append(f"<h3>{self._inline_md(stripped[3:])}</h3>")
            elif stripped.startswith("# "):
                html_lines.append(f"<h3>{self._inline_md(stripped[2:])}</h3>")
            # 列表
            elif stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{self._inline_md(stripped[2:])}</li>")
            # 引用
            elif stripped.startswith("> "):
                if not in_blockquote:
                    html_lines.append("<blockquote>")
                    in_blockquote = True
                html_lines.append(f"<p>{self._inline_md(stripped[2:])}</p>")
            # 水平线
            elif stripped in ("---", "***", "___"):
                html_lines.append("<hr>")
            # 空行
            elif not stripped:
                html_lines.append("")
            # 普通段落
            else:
                html_lines.append(f"<p>{self._inline_md(stripped)}</p>")

        # 关闭未闭合的标签
        if in_list:
            html_lines.append("</ul>")
        if in_blockquote:
            html_lines.append("</blockquote>")

        return "\n".join(html_lines)

    def _inline_md(self, text: str) -> str:
        """转换行内 Markdown 语法为 HTML

        处理粗体、斜体、行内代码和链接。

        Args:
            text: Markdown 文本

        Returns:
            HTML 字符串
        """
        text = html.escape(text)

        # 行内代码
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # 粗体
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # 斜体
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # 链接
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        # Wiki-links
        text = re.sub(r"\[\[([^\]]+)\]\]", r'<a class="wikilink">\1</a>', text)

        return text

    @staticmethod
    def _safe_filename(title: str) -> str:
        """生成安全的文件名

        Args:
            title: 标题字符串

        Returns:
            安全的文件名
        """
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title)
        filename = re.sub(r"\s+", "-", filename).strip("-.")
        return filename[:200] if filename else "untitled"
