"""搜索引擎测试"""

import unittest

from vaultpilot.core.search import SearchEngine


class TestSearchEngine(unittest.TestCase):
    """搜索引擎测试用例"""

    def setUp(self) -> None:
        """每个测试前创建搜索引擎实例"""
        self.engine = SearchEngine(ngram_size=2)

    def test_index_document(self) -> None:
        """测试索引文档"""
        self.engine.index_document("doc1", "Python编程语言教程", "/path/doc1.md")
        self.engine.index_document("doc2", "Java编程入门指南", "/path/doc2.md")
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_documents"], 2)

    def test_search_basic(self) -> None:
        """测试基本搜索"""
        self.engine.index_document("doc1", "Python编程语言教程", "/path/doc1.md")
        self.engine.index_document("doc2", "Java编程入门指南", "/path/doc2.md")
        self.engine.index_document("doc3", "Go语言并发编程", "/path/doc3.md")

        results = self.engine.search("Python")
        self.assertGreater(len(results), 0)
        doc_ids = [r[0] for r in results]
        self.assertIn("doc1", doc_ids)

    def test_search_chinese(self) -> None:
        """测试中文搜索"""
        self.engine.index_document("doc1", "机器学习是人工智能的一个分支", "/path/doc1.md")
        self.engine.index_document("doc2", "深度学习在图像识别中表现优异", "/path/doc2.md")

        results = self.engine.search("机器学习")
        self.assertGreater(len(results), 0)

    def test_search_empty_query(self) -> None:
        """测试空查询"""
        self.engine.index_document("doc1", "测试内容", "/path/doc1.md")
        results = self.engine.search("")
        self.assertEqual(len(results), 0)

    def test_search_limit(self) -> None:
        """测试搜索结果数量限制"""
        for i in range(10):
            self.engine.index_document(f"doc{i}", f"文档编号{i}的内容", f"/path/doc{i}.md")

        results = self.engine.search("文档", limit=3)
        self.assertLessEqual(len(results), 3)

    def test_remove_document(self) -> None:
        """测试移除文档"""
        self.engine.index_document("doc1", "测试文档", "/path/doc1.md")
        self.engine.remove_document("doc1")
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_documents"], 0)

    def test_clear(self) -> None:
        """测试清空索引"""
        self.engine.index_document("doc1", "测试", "/path/doc1.md")
        self.engine.index_document("doc2", "测试", "/path/doc2.md")
        self.engine.clear()
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_documents"], 0)

    def test_suggest(self) -> None:
        """测试搜索建议"""
        self.engine.index_document("doc1", "Python编程", "/path/doc1.md")
        suggestions = self.engine.suggest("py")
        self.assertIsInstance(suggestions, list)

    def test_highlight_matches(self) -> None:
        """测试高亮匹配"""
        text = "这是一段测试文本，包含搜索关键词"
        result = self.engine.highlight_matches(text, "搜索关键词")
        self.assertIn("搜索关键词", result)

    def test_batch_index(self) -> None:
        """测试批量索引"""
        docs = [
            ("doc1", "Python教程", "/path/doc1.md"),
            ("doc2", "Java教程", "/path/doc2.md"),
            ("doc3", "Go教程", "/path/doc3.md"),
        ]
        self.engine.index_documents(docs)
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_documents"], 3)

    def test_tokenization(self) -> None:
        """测试分词"""
        tokens = self.engine._tokenize("Python编程语言")
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_idf_computation(self) -> None:
        """测试 IDF 计算"""
        self.engine.index_document("doc1", "Python", "/path/doc1.md")
        self.engine.index_document("doc2", "Python", "/path/doc2.md")
        self.engine.index_document("doc3", "Java", "/path/doc3.md")

        # Python 出现在 2 个文档中，IDF 应该较低
        idf_python = self.engine._compute_idf("python")
        idf_java = self.engine._compute_idf("java")
        # Java 只出现在 1 个文档中，IDF 应该更高
        self.assertGreater(idf_java, idf_python)

    def test_stats(self) -> None:
        """测试统计信息"""
        self.engine.index_document("doc1", "短文本", "/path/doc1.md")
        self.engine.index_document("doc2", "这是一段比较长的文本内容", "/path/doc2.md")
        stats = self.engine.get_stats()
        self.assertIn("total_documents", stats)
        self.assertIn("unique_tokens", stats)
        self.assertIn("avg_doc_length", stats)


if __name__ == "__main__":
    unittest.main()
