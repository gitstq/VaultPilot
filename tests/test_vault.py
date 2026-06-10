"""Vault 知识库核心类测试"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from vaultpilot.core.vault import Vault
from vaultpilot.utils.path import PathHelper


class TestVault(unittest.TestCase):
    """Vault 核心类测试用例"""

    def setUp(self) -> None:
        """每个测试前创建临时知识库"""
        self.test_dir = tempfile.mkdtemp(prefix="vaultpilot_test_")
        self.vault = Vault.init(self.test_dir)

    def tearDown(self) -> None:
        """每个测试后清理临时目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_vault(self) -> None:
        """测试知识库初始化"""
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, ".vault")))
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, "notes")))
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, "attachments")))
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, ".vault", "trash")))

    def test_init_existing_vault(self) -> None:
        """测试重复初始化已存在的知识库"""
        vault2 = Vault.init(self.test_dir)
        self.assertIsInstance(vault2, Vault)

    def test_init_nonempty_dir(self) -> None:
        """测试在非空目录初始化"""
        other_dir = tempfile.mkdtemp(prefix="vaultpilot_test2_")
        try:
            with open(os.path.join(other_dir, "readme.txt"), "w") as f:
                f.write("hello")
            with self.assertRaises(ValueError):
                Vault.init(other_dir)
        finally:
            shutil.rmtree(other_dir)

    def test_new_note(self) -> None:
        """测试创建笔记"""
        note = self.vault.new_note("测试笔记", tags=["test"], open_editor=False)
        self.assertEqual(note.title, "测试笔记")
        self.assertIn("test", note.tags)
        self.assertTrue(os.path.exists(note.filepath))

    def test_get_note(self) -> None:
        """测试获取笔记"""
        self.vault.new_note("获取测试", open_editor=False)
        note = self.vault.get_note("获取测试")
        self.assertIsNotNone(note)
        self.assertEqual(note.title, "获取测试")

    def test_get_note_by_filename(self) -> None:
        """测试通过文件名获取笔记"""
        self.vault.new_note("文件名测试", open_editor=False)
        note = self.vault.get_note("文件名测试.md")
        self.assertIsNotNone(note)

    def test_get_note_not_found(self) -> None:
        """测试获取不存在的笔记"""
        note = self.vault.get_note("不存在的笔记")
        self.assertIsNone(note)

    def test_delete_note(self) -> None:
        """测试删除笔记"""
        self.vault.new_note("待删除笔记", open_editor=False)
        result = self.vault.delete_note("待删除笔记")
        self.assertTrue(result)
        note = self.vault.get_note("待删除笔记")
        self.assertIsNone(note)

    def test_delete_note_not_found(self) -> None:
        """测试删除不存在的笔记"""
        result = self.vault.delete_note("不存在")
        self.assertFalse(result)

    def test_list_notes(self) -> None:
        """测试列出笔记"""
        self.vault.new_note("笔记1", open_editor=False)
        self.vault.new_note("笔记2", open_editor=False)
        notes = self.vault.list_notes()
        self.assertGreaterEqual(len(notes), 2)

    def test_list_notes_with_tag_filter(self) -> None:
        """测试按标签过滤笔记"""
        self.vault.new_note("Python笔记", tags=["python"], open_editor=False)
        self.vault.new_note("Go笔记", tags=["go"], open_editor=False)
        notes = self.vault.list_notes(tag="python")
        titles = [n.title for n in notes]
        self.assertIn("Python笔记", titles)

    def test_add_tag(self) -> None:
        """测试添加标签"""
        self.vault.new_note("标签测试", open_editor=False)
        result = self.vault.add_tag("标签测试", "newtag")
        self.assertTrue(result)
        note = self.vault.get_note("标签测试")
        self.assertIn("newtag", note.tags)

    def test_remove_tag(self) -> None:
        """测试移除标签"""
        self.vault.new_note("移除标签测试", tags=["removeme"], open_editor=False)
        result = self.vault.remove_tag("移除标签测试", "removeme")
        self.assertTrue(result)
        note = self.vault.get_note("移除标签测试")
        self.assertNotIn("removeme", note.tags)

    def test_list_tags(self) -> None:
        """测试列出标签"""
        self.vault.new_note("标签1", tags=["a", "b"], open_editor=False)
        self.vault.new_note("标签2", tags=["a", "c"], open_editor=False)
        tags = self.vault.list_tags()
        tag_names = [t[0] for t in tags]
        self.assertIn("a", tag_names)
        self.assertIn("b", tag_names)

    def test_search(self) -> None:
        """测试全文搜索"""
        self.vault.new_note("Python编程", tags=["python"], open_editor=False)
        self.vault.new_note("Java编程", tags=["java"], open_editor=False)
        results = self.vault.search("Python")
        self.assertGreater(len(results), 0)

    def test_stats(self) -> None:
        """测试统计信息"""
        self.vault.new_note("统计测试", open_editor=False)
        stats = self.vault.show_stats()
        self.assertGreater(stats["summary"]["total_notes"], 0)

    def test_export_json(self) -> None:
        """测试导出为 JSON"""
        self.vault.new_note("导出测试", open_editor=False)
        output_path = os.path.join(self.test_dir, "export.json")
        success, result = self.vault.export_notes(output_path, "json")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))

    def test_export_html(self) -> None:
        """测试导出为 HTML"""
        self.vault.new_note("导出测试", open_editor=False)
        output_path = os.path.join(self.test_dir, "export.html")
        success, result = self.vault.export_notes(output_path, "html")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()
