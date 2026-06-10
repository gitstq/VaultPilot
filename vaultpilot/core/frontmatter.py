"""YAML Frontmatter 解析器 - 轻量级实现

不依赖 PyYAML，自行实现一个支持常用 YAML 子集的解析器。
支持的数据类型：字符串、数字、布尔值、列表、日期。
"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union


class FrontmatterParser:
    """YAML Frontmatter 解析器

    解析 Markdown 文件开头的 YAML 格式元数据。
    Frontmatter 格式为以 --- 分隔的 YAML 块：

    ```
    ---
    title: 笔记标题
    tags: [标签1, 标签2]
    created: 2024-01-01
    ---
    正文内容
    ```

    支持的 YAML 特性：
    - 键值对（key: value）
    - 字符串（带引号和不带引号）
    - 数字（整数和浮点数）
    - 布尔值（true/false/yes/no）
    - 列表（行内格式 [a, b] 和多行格式）
    - 日期（YYYY-MM-DD 格式）
    - 多行字符串
    """

    # Frontmatter 分隔符
    DELIMITER = "---"

    # 布尔值映射
    _BOOL_MAP = {
        "true": True, "false": False,
        "yes": True, "no": False,
        "on": True, "off": False,
        "1": True, "0": False,
    }

    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """解析包含 frontmatter 的 Markdown 内容

        Args:
            content: 完整的 Markdown 文件内容

        Returns:
            元组：(frontmatter 字典, 正文内容)
            如果没有 frontmatter，返回空字典和原始内容
        """
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        if not content.startswith(self.DELIMITER):
            return {}, content

        # 查找第二个分隔符
        rest = content[len(self.DELIMITER):]
        end_index = rest.find(self.DELIMITER)

        if end_index == -1:
            return {}, content

        fm_text = rest[:end_index].strip()
        body = rest[end_index + len(self.DELIMITER):].strip()

        metadata = self._parse_yaml(fm_text)
        return metadata, body

    def dump(self, metadata: Dict[str, Any], body: str = "") -> str:
        """将元数据和正文序列化为带 frontmatter 的 Markdown

        Args:
            metadata: 元数据字典
            body: 正文内容

        Returns:
            完整的 Markdown 字符串
        """
        yaml_text = self._dump_yaml(metadata)
        result = f"{self.DELIMITER}\n{yaml_text}{self.DELIMITER}\n"
        if body:
            result += f"\n{body}\n"
        return result

    def _parse_yaml(self, text: str) -> Dict[str, Any]:
        """解析 YAML 文本为字典

        Args:
            text: YAML 格式文本

        Returns:
            解析后的字典
        """
        result: Dict[str, Any] = {}
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 跳过空行和注释
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # 检查是否是键值对
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_ -]*)\s*:\s*(.*)", stripped)
            if match:
                key = match.group(1).strip()
                value_str = match.group(2).strip()

                if not value_str:
                    # 值在下一行（可能是多行字符串或列表）
                    i += 1
                    value, i = self._parse_block_value(lines, i)
                elif value_str in ("|", ">", "|+", "|-", ">+", ">-"):
                    # 多行字符串指示符
                    i += 1
                    value, i = self._parse_block_value(lines, i)
                else:
                    value = self._parse_value(value_str)
                    i += 1

                result[key] = value
            else:
                i += 1

        return result

    def _parse_block_value(self, lines: List[str], start: int) -> Tuple[Any, int]:
        """解析块级值（多行字符串或列表）

        Args:
            lines: 所有行
            start: 起始行索引

        Returns:
            元组：(解析后的值, 下一行索引)
        """
        if start >= len(lines):
            return None, start

        first_line = lines[start].strip()

        # 列表项检测（以 "- " 开头）
        if first_line.startswith("- "):
            return self._parse_multiline_list(lines, start)

        # 多行字符串（缩进块）
        if first_line.startswith("|") or first_line.startswith(">"):
            return self._parse_multiline_string(lines, start)

        # 缩进的块值
        if lines[start].startswith("  ") or lines[start].startswith("\t"):
            return self._parse_indented_block(lines, start)

        return self._parse_value(first_line), start + 1

    def _parse_multiline_list(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """解析多行列表

        Args:
            lines: 所有行
            start: 起始行索引

        Returns:
            元组：(列表值, 下一行索引)
        """
        result: List[str] = []
        i = start

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            if stripped.startswith("- "):
                item = stripped[2:].strip()
                result.append(self._parse_value(item))
                i += 1
            else:
                break

        return result, i

    def _parse_multiline_string(self, lines: List[str], start: int) -> Tuple[str, int]:
        """解析多行字符串

        Args:
            lines: 所有行
            start: 起始行索引

        Returns:
            元组：(字符串值, 下一行索引)
        """
        result_lines: List[str] = []
        i = start + 1

        while i < len(lines):
            line = lines[i]
            if not line.strip() or line[0] == " ":
                result_lines.append(line.strip())
                i += 1
            else:
                break

        return "\n".join(result_lines), i

    def _parse_indented_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """解析缩进块

        Args:
            lines: 所有行
            start: 起始行索引

        Returns:
            元组：(字符串值, 下一行索引)
        """
        result_lines: List[str] = []
        i = start

        while i < len(lines):
            line = lines[i]
            if line.startswith("  ") or line.startswith("\t"):
                result_lines.append(line.strip())
                i += 1
            elif line.strip():
                break
            else:
                i += 1

        return "\n".join(result_lines), i

    def _parse_value(self, value_str: str) -> Any:
        """解析单个值

        自动检测值的类型：布尔、数字、列表、日期、字符串。

        Args:
            value_str: 值字符串

        Returns:
            解析后的值
        """
        value_str = value_str.strip()

        if not value_str:
            return ""

        # 空值
        if value_str in ("null", "~", "None", ""):
            return None

        # 布尔值
        lower = value_str.lower()
        if lower in self._BOOL_MAP:
            return self._BOOL_MAP[lower]

        # 行内列表 [a, b, c]
        if value_str.startswith("[") and value_str.endswith("]"):
            return self._parse_inline_list(value_str)

        # 行内字典 {key: value}
        if value_str.startswith("{") and value_str.endswith("}"):
            return self._parse_inline_dict(value_str)

        # 带引号的字符串
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # 数字
        return self._parse_number(value_str)

    def _parse_number(self, value_str: str) -> Union[int, float, str]:
        """尝试解析数字

        Args:
            value_str: 值字符串

        Returns:
            整数、浮点数或原始字符串
        """
        # 尝试解析日期
        date_val = self._parse_date(value_str)
        if date_val is not None:
            return date_val

        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str

    @staticmethod
    def _parse_date(value_str: str) -> Optional[Union[str, date, datetime]]:
        """尝试解析日期字符串

        Args:
            value_str: 值字符串

        Returns:
            日期对象或 None
        """
        # YYYY-MM-DD
        date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", value_str)
        if date_match:
            try:
                return date(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )
            except ValueError:
                pass

        # YYYY-MM-DD HH:MM:SS
        datetime_match = re.match(
            r"^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$", value_str
        )
        if datetime_match:
            try:
                return datetime(
                    int(datetime_match.group(1)),
                    int(datetime_match.group(2)),
                    int(datetime_match.group(3)),
                    int(datetime_match.group(4)),
                    int(datetime_match.group(5)),
                    int(datetime_match.group(6)),
                )
            except ValueError:
                pass

        return None

    def _parse_inline_list(self, value_str: str) -> List[Any]:
        """解析行内列表 [a, b, c]

        Args:
            value_str: 列表字符串（含方括号）

        Returns:
            解析后的列表
        """
        inner = value_str[1:-1].strip()
        if not inner:
            return []

        items: List[Any] = []
        current = ""
        in_quotes = False
        quote_char = ""

        for char in inner:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = ""
            elif char == "," and not in_quotes:
                items.append(self._parse_value(current.strip()))
                current = ""
                continue
            current += char

        if current.strip():
            items.append(self._parse_value(current.strip()))

        return items

    def _parse_inline_dict(self, value_str: str) -> Dict[str, Any]:
        """解析行内字典 {key: value}

        Args:
            value_str: 字典字符串（含花括号）

        Returns:
            解析后的字典
        """
        inner = value_str[1:-1].strip()
        if not inner:
            return {}

        result: Dict[str, Any] = {}
        pairs = inner.split(",")

        for pair in pairs:
            if ":" in pair:
                key, val = pair.split(":", 1)
                result[key.strip()] = self._parse_value(val.strip())

        return result

    def _dump_yaml(self, metadata: Dict[str, Any], indent: int = 0) -> str:
        """将字典序列化为 YAML 格式文本

        Args:
            metadata: 元数据字典
            indent: 缩进级别

        Returns:
            YAML 格式字符串
        """
        lines: List[str] = []
        prefix = "  " * indent

        for key, value in metadata.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._dump_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    lines.append(f"{prefix}  - {self._dump_value(item)}")
            else:
                lines.append(f"{prefix}{key}: {self._dump_value(value)}")

        return "\n".join(lines) + "\n"

    def _dump_value(self, value: Any) -> str:
        """将单个值序列化为 YAML 格式

        Args:
            value: 要序列化的值

        Returns:
            YAML 格式字符串
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, str):
            # 包含特殊字符时加引号
            if any(c in value for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`")):
                return f'"{value}"'
            return value
        return str(value)
