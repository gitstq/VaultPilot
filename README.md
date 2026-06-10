# VaultPilot

轻量级终端 Markdown 知识库管理引擎。

## 安装

```bash
pip install -e .
```

## 快速开始

```bash
# 初始化知识库
vault init ./my-vault

# 创建笔记
vault new "我的第一篇笔记"

# 列出笔记
vault list

# 搜索笔记
vault search "关键词"

# 查看笔记详情
vault show "我的第一篇笔记"

# 编辑笔记
vault edit "我的第一篇笔记"

# 删除笔记
vault delete "我的第一篇笔记"

# 标签管理
vault tag add "笔记名" "标签"
vault tag list

# 知识图谱
vault graph

# 统计信息
vault stats

# 导入导出
vault import ./source-dir
vault export output.json --format json
vault export output.html --format html

# Git 集成
vault git init
vault git status
vault git commit -m "update notes"

# 交互式界面
vault tui
```

## 特性

- 零外部依赖（仅使用 Python 标准库）
- 可选 rich 库美化终端输出
- TF-IDF 全文搜索引擎（支持中文）
- 双向链接 [[wiki-links]]
- ASCII 知识图谱
- Git 版本管理集成
- 交互式 TUI 界面（curses）

## 许可证

MIT License
