"""TF-IDF 搜索引擎 - 全文搜索实现

自行实现 TF-IDF 算法，支持中文分词（基于字符的 n-gram）。
不依赖任何外部搜索库。
"""

import math
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple


class SearchEngine:
    """基于 TF-IDF 的全文搜索引擎

    实现倒排索引和 TF-IDF 排序算法，支持中文和英文文本搜索。
    中文分词使用基于字符的 bigram 方法。

    Attributes:
        _documents: 文档索引 {doc_id: token列表}
        _doc_paths: 文档路径映射 {doc_id: filepath}
        _inverted_index: 倒排索引 {token: {doc_id: tf}}
        _doc_lengths: 文档长度 {doc_id: token数量}
        _avg_doc_length: 平均文档长度
        _ngram_size: n-gram 大小
        _total_docs: 总文档数
    """

    def __init__(self, ngram_size: int = 2) -> None:
        """初始化搜索引擎

        Args:
            ngram_size: 中文分词的 n-gram 大小，默认为 2（bigram）
        """
        self._documents: Dict[str, List[str]] = {}
        self._doc_paths: Dict[str, str] = {}
        self._inverted_index: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self._ngram_size: int = ngram_size
        self._total_docs: int = 0

        # 停用词列表
        self._stop_words: Set[str] = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
            "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那",
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "shall", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "above", "below", "between", "and", "but", "or",
            "not", "no", "if", "then", "than", "so", "too", "very", "just",
            "about", "up", "out", "this", "that", "it", "its",
        }

    def index_document(self, doc_id: str, content: str, filepath: str = "") -> None:
        """索引单个文档

        对文档内容进行分词并建立索引。

        Args:
            doc_id: 文档唯一标识
            content: 文档文本内容
            filepath: 文档文件路径
        """
        tokens = self._tokenize(content)
        self._documents[doc_id] = tokens
        self._doc_paths[doc_id] = filepath
        self._doc_lengths[doc_id] = len(tokens)

        # 更新倒排索引
        token_counts = Counter(tokens)
        for token, count in token_counts.items():
            self._inverted_index[token][doc_id] = count

        self._update_stats()

    def index_documents(self, documents: List[Tuple[str, str, str]]) -> None:
        """批量索引文档

        Args:
            documents: 文档列表，每项为 (doc_id, content, filepath) 元组
        """
        for doc_id, content, filepath in documents:
            self.index_document(doc_id, content, filepath)

    def remove_document(self, doc_id: str) -> None:
        """从索引中移除文档

        Args:
            doc_id: 文档唯一标识
        """
        if doc_id not in self._documents:
            return

        # 从倒排索引中移除
        tokens = set(self._documents[doc_id])
        for token in tokens:
            if token in self._inverted_index and doc_id in self._inverted_index[token]:
                del self._inverted_index[token][doc_id]
                if not self._inverted_index[token]:
                    del self._inverted_index[token]

        del self._documents[doc_id]
        if doc_id in self._doc_paths:
            del self._doc_paths[doc_id]
        if doc_id in self._doc_lengths:
            del self._doc_lengths[doc_id]

        self._update_stats()

    def search(
        self,
        query: str,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> List[Tuple[str, float, str]]:
        """搜索文档

        使用 TF-IDF 算法计算查询与文档的相关性得分。

        Args:
            query: 搜索查询字符串
            limit: 返回结果最大数量
            min_score: 最低得分阈值

        Returns:
            搜索结果列表，每项为 (doc_id, score, filepath) 元组，按得分降序排列
        """
        if not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}

        for token in query_tokens:
            if token not in self._inverted_index:
                continue

            idf = self._compute_idf(token)
            doc_entries = self._inverted_index[token]

            for doc_id, tf in doc_entries.items():
                tfidf = tf * idf
                scores[doc_id] = scores.get(doc_id, 0.0) + tfidf

        # 归一化得分
        results: List[Tuple[str, float, str]] = []
        for doc_id, score in scores.items():
            if score >= min_score:
                filepath = self._doc_paths.get(doc_id, "")
                results.append((doc_id, score, filepath))

        # 按得分降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _tokenize(self, text: str) -> List[str]:
        """文本分词

        对文本进行预处理和分词，支持中英文混合文本。
        英文按空格分词，中文使用 n-gram 方法。

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        # 统一为小写
        text = text.lower()

        # 移除 Markdown 语法
        text = re.sub(r"[#*`\[\]()>_~|]", " ", text)
        text = re.sub(r"https?://\S+", " ", text)

        tokens: List[str] = []

        # 分离中文字符和英文单词
        segments = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text)

        for segment in segments:
            if re.match(r"[\u4e00-\u9fff]", segment):
                # 中文使用 n-gram
                ngram_tokens = self._chinese_ngram(segment)
                tokens.extend(ngram_tokens)
            else:
                # 英文直接作为 token
                if len(segment) > 1 and segment not in self._stop_words:
                    tokens.append(segment)

        # 过滤停用词和短 token
        tokens = [
            t for t in tokens
            if t not in self._stop_words and len(t) >= self._ngram_size
        ]

        return tokens

    def _chinese_ngram(self, text: str) -> List[str]:
        """中文文本 n-gram 分词

        将中文文本切分为 n-gram 片段。

        Args:
            text: 中文文本

        Returns:
            n-gram 列表
        """
        if len(text) < self._ngram_size:
            return [text] if text else []

        tokens: List[str] = []
        for i in range(len(text) - self._ngram_size + 1):
            gram = text[i:i + self._ngram_size]
            if gram not in self._stop_words:
                tokens.append(gram)

        # 同时保留单个字作为索引（用于精确匹配）
        for char in text:
            if char not in self._stop_words:
                tokens.append(char)

        return tokens

    def _compute_idf(self, token: str) -> float:
        """计算逆文档频率 (IDF)

        IDF = log(N / df)，其中 N 是总文档数，df 是包含该词的文档数。

        Args:
            token: 词项

        Returns:
            IDF 值
        """
        if self._total_docs == 0:
            return 0.0

        df = len(self._inverted_index.get(token, {}))
        if df == 0:
            return 0.0

        return math.log(self._total_docs / df) + 1.0

    def _update_stats(self) -> None:
        """更新索引统计信息"""
        self._total_docs = len(self._documents)
        if self._total_docs > 0:
            total_length = sum(self._doc_lengths.values())
            self._avg_doc_length = total_length / self._total_docs
        else:
            self._avg_doc_length = 0.0

    def get_stats(self) -> Dict[str, int]:
        """获取搜索引擎统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "total_documents": self._total_docs,
            "total_tokens": sum(self._doc_lengths.values()),
            "unique_tokens": len(self._inverted_index),
            "avg_doc_length": int(self._avg_doc_length),
        }

    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """根据前缀建议搜索词

        Args:
            prefix: 搜索前缀
            limit: 返回建议数量

        Returns:
            匹配的 token 列表
        """
        prefix = prefix.lower()
        suggestions: List[str] = []
        for token in self._inverted_index:
            if token.startswith(prefix):
                suggestions.append(token)
                if len(suggestions) >= limit:
                    break
        return suggestions

    def highlight_matches(self, text: str, query: str, context_chars: int = 50) -> str:
        """在文本中高亮匹配的搜索词

        Args:
            text: 原始文本
            query: 搜索查询
            context_chars: 匹配位置前后的上下文字符数

        Returns:
            带高亮标记的文本片段
        """
        query_lower = query.lower()
        text_lower = text.lower()
        matches: List[Tuple[int, int]] = []

        # 查找所有匹配位置
        pos = text_lower.find(query_lower)
        while pos != -1:
            matches.append((pos, pos + len(query)))
            pos = text_lower.find(query_lower, pos + 1)

        if not matches:
            # 返回文本开头
            return text[:context_chars * 2] + ("..." if len(text) > context_chars * 2 else "")

        # 提取匹配上下文
        result_parts: List[str] = []
        last_end = 0

        for start, end in matches:
            ctx_start = max(0, start - context_chars)
            ctx_end = min(len(text), end + context_chars)

            if ctx_start > last_end:
                if last_end > 0:
                    result_parts.append("...")
                result_parts.append(text[ctx_start:start])
            elif start > last_end:
                result_parts.append(text[last_end:start])

            result_parts.append(f"[{text[start:end]}]")
            last_end = end

        if last_end < len(text):
            result_parts.append(text[last_end:ctx_end])
            if ctx_end < len(text):
                result_parts.append("...")

        return "".join(result_parts)

    def clear(self) -> None:
        """清空所有索引数据"""
        self._documents.clear()
        self._doc_paths.clear()
        self._inverted_index.clear()
        self._doc_lengths.clear()
        self._total_docs = 0
        self._avg_doc_length = 0.0
