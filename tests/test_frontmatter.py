"""YAML Frontmatter 解析器测试"""

import unittest
from datetime import date, datetime

from vaultpilot.core.frontmatter import FrontmatterParser


class TestFrontmatterParser(unittest.TestCase):
    """Frontmatter 解析器测试用例"""

    def setUp(self) -> None:
        """每个测试前创建解析器实例"""
        self.parser = FrontmatterParser()

    def test_parse_basic(self) -> None:
        """测试基本 frontmatter 解析"""
        content = """---
title: 测试标题
tags: [a, b, c]
---

正文内容"""
        metadata, body = self.parser.parse(content)
        self.assertEqual(metadata["title"], "测试标题")
        self.assertEqual(metadata["tags"], ["a", "b", "c"])
        self.assertEqual(body, "正文内容")

    def test_parse_no_frontmatter(self) -> None:
        """测试无 frontmatter 的内容"""
        content = "这是普通 Markdown 内容"
        metadata, body = self.parser.parse(content)
        self.assertEqual(metadata, {})
        self.assertEqual(body, content)

    def test_parse_string_value(self) -> None:
        """测试字符串值解析"""
        content = """---
title: "带引号的标题"
description: '单引号描述'
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["title"], "带引号的标题")
        self.assertEqual(metadata["description"], "单引号描述")

    def test_parse_number(self) -> None:
        """测试数字解析"""
        content = """---
count: 42
price: 3.14
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["count"], 42)
        self.assertEqual(metadata["price"], 3.14)

    def test_parse_boolean(self) -> None:
        """测试布尔值解析"""
        content = """---
published: true
draft: false
visible: yes
hidden: no
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertTrue(metadata["published"])
        self.assertFalse(metadata["draft"])
        self.assertTrue(metadata["visible"])
        self.assertFalse(metadata["hidden"])

    def test_parse_date(self) -> None:
        """测试日期解析"""
        content = """---
date: 2024-01-15
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertIsInstance(metadata["date"], date)
        self.assertEqual(metadata["date"].year, 2024)

    def test_parse_datetime(self) -> None:
        """测试日期时间解析"""
        content = """---
created: 2024-01-15 10:30:00
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertIsInstance(metadata["created"], datetime)

    def test_parse_null(self) -> None:
        """测试空值解析"""
        content = """---
value: null
empty: ~
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertIsNone(metadata["value"])
        self.assertIsNone(metadata["empty"])

    def test_parse_multiline_list(self) -> None:
        """测试多行列表解析"""
        content = """---
tags:
  - python
  - java
  - go
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["tags"], ["python", "java", "go"])

    def test_parse_inline_list(self) -> None:
        """测试行内列表解析"""
        content = """---
tags: [python, java, go]
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["tags"], ["python", "java", "go"])

    def test_parse_empty_list(self) -> None:
        """测试空列表解析"""
        content = """---
tags: []
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["tags"], [])

    def test_parse_multiline_string(self) -> None:
        """测试多行字符串解析"""
        content = """---
description: |
  第一行
  第二行
  第三行
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertIn("第一行", metadata["description"])
        self.assertIn("第二行", metadata["description"])

    def test_parse_comments(self) -> None:
        """测试注释忽略"""
        content = """---
# 这是注释
title: 测试
# 另一个注释
---

正文"""
        metadata, _ = self.parser.parse(content)
        self.assertEqual(metadata["title"], "测试")
        self.assertNotIn("#", metadata)

    def test_dump_basic(self) -> None:
        """测试基本序列化"""
        metadata = {"title": "测试", "tags": ["a", "b"]}
        result = self.parser.dump(metadata, "正文")
        self.assertIn("---", result)
        self.assertIn("title: 测试", result)
        self.assertIn("正文", result)

    def test_dump_and_parse_roundtrip(self) -> None:
        """测试序列化后反序列化的一致性"""
        original_metadata = {
            "title": "往返测试",
            "tags": ["x", "y"],
            "count": 10,
            "published": True,
        }
        original_body = "这是正文内容"

        dumped = self.parser.dump(original_metadata, original_body)
        parsed_metadata, parsed_body = self.parser.parse(dumped)

        self.assertEqual(parsed_metadata["title"], original_metadata["title"])
        self.assertEqual(parsed_metadata["tags"], original_metadata["tags"])
        self.assertEqual(parsed_metadata["count"], original_metadata["count"])
        self.assertEqual(parsed_metadata["published"], original_metadata["published"])
        self.assertEqual(parsed_body, original_body)

    def test_parse_with_windows_line_endings(self) -> None:
        """测试 Windows 换行符"""
        content = "---\r\ntitle: Windows测试\r\n---\r\n正文"
        metadata, body = self.parser.parse(content)
        self.assertEqual(metadata["title"], "Windows测试")
        self.assertEqual(body, "正文")

    def test_parse_complex_metadata(self) -> None:
        """测试复杂元数据"""
        content = """---
title: 复杂测试
author: VaultPilot
version: 1.0
tags: [test, example]
created: 2024-01-01
published: true
---

正文内容"""
        metadata, body = self.parser.parse(content)
        self.assertEqual(len(metadata), 6)
        self.assertEqual(metadata["title"], "复杂测试")
        self.assertEqual(metadata["version"], 1.0)
        self.assertEqual(body.strip(), "正文内容")


if __name__ == "__main__":
    unittest.main()
