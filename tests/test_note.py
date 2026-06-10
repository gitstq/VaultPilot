"""Note 笔记模型测试"""

import os
import shutil
import tempfile
import unittest

from vaultpilot.core.note import Note


class TestNote(unittest.TestCase):
    """Note 笔记模型测试用例"""

    def setUp(self) -> None:
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="vaultpilot_note_test_")

    def tearDown(self) -> None:
        """每个测试后清理临时目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_note(self) -> None:
        """测试创建笔记"""
        filepath = os.path.join(self.test_dir, "test.md")
        note = Note.create(filepath, "测试标题", tags=["tag1", "tag2"], body="正文内容")
        self.assertEqual(note.title, "测试标题")
        self.assertEqual(note.tags, ["tag1", "tag2"])
        self.assertTrue(os.path.exists(filepath))

    def test_from_file(self) -> None:
        """测试从文件加载笔记"""
        filepath = os.path.join(self.test_dir, "load-test.md")
        Note.create(filepath, "加载测试", tags=["test"], body="测试正文")
        note = Note.from_file(filepath)
        self.assertEqual(note.title, "加载测试")
        self.assertIn("test", note.tags)
        self.assertEqual(note.body, "测试正文")

    def test_from_file_not_found(self) -> None:
        """测试加载不存在的文件"""
        filepath = os.path.join(self.test_dir, "nonexistent.md")
        with self.assertRaises(FileNotFoundError):
            Note.from_file(filepath)

    def test_save_note(self) -> None:
        """测试保存笔记"""
        filepath = os.path.join(self.test_dir, "save-test.md")
        note = Note.create(filepath, "保存测试", body="初始内容")
        note.body = "更新后的内容"
        note.save()
        reloaded = Note.from_file(filepath)
        self.assertEqual(reloaded.body, "更新后的内容")

    def test_add_tag(self) -> None:
        """测试添加标签"""
        note = Note(filepath="dummy", title="测试")
        note.add_tag("python")
        note.add_tag("python")  # 重复添加
        self.assertEqual(len(note.tags), 1)
        self.assertIn("python", note.tags)

    def test_remove_tag(self) -> None:
        """测试移除标签"""
        note = Note(filepath="dummy", title="测试", tags=["a", "b"])
        result = note.remove_tag("a")
        self.assertTrue(result)
        self.assertNotIn("a", note.tags)
        result = note.remove_tag("nonexistent")
        self.assertFalse(result)

    def test_word_count(self) -> None:
        """测试字数统计"""
        note = Note(filepath="dummy", title="测试", body="Hello world 你好世界")
        count = note.get_word_count()
        self.assertGreater(count, 0)

    def test_char_count(self) -> None:
        """测试字符数统计"""
        note = Note(filepath="dummy", title="测试", body="abc")
        self.assertEqual(note.get_char_count(), 3)

    def test_line_count(self) -> None:
        """测试行数统计"""
        note = Note(filepath="dummy", title="测试", body="line1\nline2\nline3")
        self.assertEqual(note.get_line_count(), 3)

    def test_extract_links(self) -> None:
        """测试提取 wiki-links"""
        body = "参见 [[Python教程]] 和 [[Go入门|Go 语言]]"
        filepath = os.path.join(self.test_dir, "links.md")
        note = Note.create(filepath, "链接测试", body=body)
        self.assertIn("Python教程", note.links)
        self.assertIn("Go入门", note.links)

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        note = Note(filepath="/tmp/test.md", title="字典测试", tags=["t"])
        d = note.to_dict()
        self.assertEqual(d["title"], "字典测试")
        self.assertIn("tags", d)
        self.assertIn("created", d)
        self.assertIn("updated", d)

    def test_repr(self) -> None:
        """测试字符串表示"""
        note = Note(filepath="dummy", title="表示测试")
        r = repr(note)
        self.assertIn("表示测试", r)

    def test_equality(self) -> None:
        """测试相等性判断"""
        n1 = Note(filepath="/tmp/a.md", title="A")
        n2 = Note(filepath="/tmp/a.md", title="B")
        n3 = Note(filepath="/tmp/b.md", title="A")
        self.assertEqual(n1, n2)
        self.assertNotEqual(n1, n3)

    def test_from_string(self) -> None:
        """测试从字符串创建笔记"""
        content = """---
title: 字符串测试
tags: [a, b]
created: 2024-01-01 00:00:00
updated: 2024-01-01 00:00:00
---

# 测试内容

这是正文。
"""
        note = Note.from_string(content, "/tmp/string-test.md")
        self.assertEqual(note.title, "字符串测试")
        self.assertEqual(note.tags, ["a", "b"])
        self.assertIn("测试内容", note.body)


if __name__ == "__main__":
    unittest.main()
