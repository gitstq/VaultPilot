<p align="center">
  <img src="logo.jpg" alt="VaultPilot Logo" width="120" height="120" />
</p>

<h1 align="center">VaultPilot</h1>

<p align="center">
  <strong>🚀 Lightweight Terminal Markdown Knowledge Base Engine</strong><br/>
  轻量级终端 Markdown 知识库管理引擎
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License" />
  <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies" />
  <img src="https://img.shields.io/badge/Tests-62%20Passed-brightgreen.svg" alt="Tests" />
  <img src="https://img.shields.io/badge/Code-7%2C000%2B%20Lines-orange.svg" alt="Code Lines" />
</p>

<p align="center">
  <a href="#-项目介绍">简体中文</a> ·
  <a href="#-專案介紹">繁體中文</a> ·
  <a href="#-introduction">English</a> ·
  <a href="#-プロジェクト紹介">日本語</a>
</p>

---

## 🎉 项目介绍

**VaultPilot** 是一款轻量级、零外部依赖的终端 Markdown 知识库管理引擎。灵感来源于 GitHub Trending 热门项目 [tolaria](https://github.com/refactoringhq/tolaria)，但聚焦于纯终端场景，为开发者提供高效的知识管理体验。

你的笔记以纯 Markdown 文件存储，完全由你掌控。支持 TF-IDF 全文搜索、双向 Wiki 链接、ASCII 知识图谱、Git 版本管理、交互式 TUI 界面等核心功能。

### 与 tolaria 的差异化定位

| 维度 | tolaria | VaultPilot |
|------|---------|------------|
| 界面 | 桌面 GUI（Tauri） | 纯终端 CLI + TUI |
| 依赖 | Node.js + Rust + pnpm | Python 3.8+ 标准库 |
| 安装 | 下载安装包 | pip install |
| 搜索 | 基础搜索 | TF-IDF（支持中文 n-gram） |
| 链接 | 单向链接 | 双向 Wiki 链接 + 反向索引 |
| 图谱 | 无 | ASCII 知识图谱 |
| 包大小 | ~100MB+ | ~200KB |
| 目标用户 | 普通用户 | 开发者/终端用户 |

## ✨ 核心特性

- **📦 零外部依赖** — 仅使用 Python 标准库，`rich` 为可选增强
- **🔍 TF-IDF 搜索** — 自实现全文搜索引擎，支持中文 n-gram 分词
- **🔗 双向链接** — `[[wiki-links]]` 自动解析，生成反向链接索引
- **🗺️ 知识图谱** — ASCII 字符画可视化笔记关系网络
- **📝 笔记管理** — 完整 CRUD，YAML frontmatter 元数据
- **🏷️ 标签系统** — 灵活的标签分类与过滤
- **📊 统计面板** — 知识库多维度统计分析
- **🔄 Git 集成** — 内置版本管理，支持 commit/push/pull
- **📥 导入导出** — 批量导入 Markdown，导出 JSON/HTML
- **🖥️ TUI 模式** — curses 交互式终端界面，键盘导航
- **🌍 多语言** — 中英文双语界面

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/VaultPilot.git
cd VaultPilot

# 安装（开发模式）
pip install -e .

# 或直接运行
python -m vaultpilot --help
```

### 三步上手

```bash
# 1. 初始化知识库
vault init ./my-vault

# 2. 创建第一篇笔记
vault new "欢迎来到 VaultPilot"

# 3. 打开交互式界面
vault tui
```

## 📖 详细使用指南

### 知识库管理

```bash
# 初始化新知识库
vault init ./my-vault

# 在已有目录初始化
vault init ./existing-dir --force

# 查看知识库信息
vault info
```

### 笔记操作

```bash
# 创建笔记（自动生成 YAML frontmatter）
vault new "Python 学习笔记"
vault new "项目架构设计" --tag "architecture" --tag "design"

# 列出所有笔记
vault list
vault list --tag "python"           # 按标签过滤
vault list --sort updated           # 按更新时间排序
vault list --limit 20              # 限制数量

# 查看笔记详情
vault show "Python 学习笔记"

# 编辑笔记（自动调用 $EDITOR）
vault edit "Python 学习笔记"

# 删除笔记（移到回收站，可恢复）
vault delete "Python 学习笔记"
```

### 全文搜索

```bash
# 关键词搜索（TF-IDF 相关性排序）
vault search "机器学习算法"

# 限定搜索范围
vault search "API设计" --tag "architecture"

# 搜索并显示摘要
vault search "数据库优化" --context 3
```

### 双向链接

在笔记中使用 `[[笔记标题]]` 创建链接：

```markdown
# 系统设计

今天完成了 [[API 网关设计]] 和 [[数据库优化方案]] 的评审。

参见 [[微服务架构]] 了解整体架构。
```

VaultPilot 会自动解析链接并生成反向链接索引。

### 标签系统

```bash
# 添加标签
vault tag add "Python 学习笔记" python tutorial

# 移除标签
vault tag remove "Python 学习笔记" tutorial

# 列出所有标签
vault tag list

# 查看标签下的笔记
vault tag show python
```

### 知识图谱

```bash
# 生成 ASCII 知识图谱
vault graph

# 仅显示特定标签的图谱
vault graph --tag "architecture"

# 深度限制
vault graph --depth 2
```

### 统计面板

```bash
# 查看知识库统计
vault stats

# 详细统计
vault stats --verbose
```

### 导入导出

```bash
# 批量导入 Markdown 文件
vault import ./source-directory

# 导出为 JSON
vault export output.json --format json

# 导出为 HTML
vault export output.html --format html

# 导出特定标签的笔记
vault export notes.json --format json --tag "python"
```

### Git 集成

```bash
# 初始化 Git 仓库
vault git init

# 查看状态
vault git status

# 提交更改
vault git commit -m "更新笔记"

# 推送到远程
vault git push

# 拉取更新
vault git pull

# 查看提交历史
vault git log --limit 10
```

### 交互式 TUI

```bash
# 启动交互式终端界面
vault tui

# 快捷键：
# j/k 或 上/下箭头: 导航
# Enter: 查看笔记
# e: 编辑笔记
# n: 新建笔记
# /: 搜索
# g: 知识图谱
# s: 统计
# q: 退出
```

## 💡 设计思路与迭代规划

### 设计哲学

1. **文件优先** — 笔记即文件，零锁定，随时可用任何编辑器
2. **终端优先** — 为键盘用户优化，所有操作可 CLI 完成
3. **零依赖** — 核心功能仅使用标准库，降低安装门槛
4. **渐进增强** — `rich` 为可选依赖，有则美化，无则降级

### 迭代规划

- [x] v1.0.0 — 核心功能（CRUD、搜索、链接、图谱、Git）
- [ ] v1.1.0 — 插件系统、模板引擎
- [ ] v1.2.0 — MCP 协议支持、AI Agent 集成
- [ ] v2.0.0 — Web UI、多用户协作

## 📦 打包与部署指南

```bash
# 使用 Makefile 构建
make install      # 安装
make test         # 运行测试
make clean        # 清理
make build        # 构建 sdist

# 手动安装
pip install .

# 作为 CLI 工具使用
python -m vaultpilot <command>
```

### 环境要求

- Python 3.8+
- 可选：`rich` 库（终端美化）
- 可选：`git`（版本管理功能）

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

提交信息请遵循 [Angular 提交规范](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)。

## 📄 开源协议说明

本项目基于 [MIT License](LICENSE) 开源。

---

## 🎉 專案介紹

**VaultPilot** 是一款輕量級、零外部依賴的終端 Markdown 知識庫管理引擎。靈感來源於 GitHub Trending 熱門專案 [tolaria](https://github.com/refactoringhq/tolaria)，但聚焦於純終端場景，為開發者提供高效的知識管理體驗。

你的筆記以純 Markdown 文件存儲，完全由你掌控。支援 TF-IDF 全文搜索、雙向 Wiki 連結、ASCII 知識圖譜、Git 版本管理、互動式 TUI 介面等核心功能。

## ✨ 核心特性

- **📦 零外部依賴** — 僅使用 Python 標準庫，`rich` 為可選增強
- **🔍 TF-IDF 搜索** — 自實現全文搜索引擎，支援中文 n-gram 分詞
- **🔗 雙向連結** — `[[wiki-links]]` 自動解析，生成反向連結索引
- **🗺️ 知識圖譜** — ASCII 字元畫可視化筆記關係網絡
- **📝 筆記管理** — 完整 CRUD，YAML frontmatter 元資料
- **🏷️ 標籤系統** — 靈活的標籤分類與過濾
- **📊 統計面板** — 知識庫多維度統計分析
- **🔄 Git 整合** — 內建版本管理，支援 commit/push/pull
- **📥 匯入匯出** — 批次匯入 Markdown，匯出 JSON/HTML
- **🖥️ TUI 模式** — curses 互動式終端介面，鍵盤導航

## 🚀 快速開始

```bash
# 安裝
pip install -e .

# 三步上手
vault init ./my-vault
vault new "歡迎來到 VaultPilot"
vault tui
```

## 📖 詳細使用指南

```bash
# 筆記操作
vault new "Python 學習筆記"
vault list --tag "python"
vault show "Python 學習筆記"
vault edit "Python 學習筆記"
vault delete "Python 學習筆記"

# 全文搜索
vault search "機器學習演算法"

# 標籤管理
vault tag add "筆記名" python tutorial
vault tag list

# 知識圖譜
vault graph

# Git 整合
vault git init
vault git commit -m "更新筆記"
vault git push

# 互動式 TUI
vault tui
```

## 🤝 貢獻指南

歡迎貢獻！請遵循 Angular 提交規範提交 Pull Request。

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

## 🎉 Introduction

**VaultPilot** is a lightweight, zero-dependency terminal Markdown knowledge base engine. Inspired by the GitHub Trending project [tolaria](https://github.com/refactoringhq/tolaria), it focuses on the pure terminal experience, providing developers with efficient knowledge management.

Your notes are stored as plain Markdown files — fully portable and under your control. It features a self-implemented TF-IDF search engine, bidirectional wiki-links, ASCII knowledge graph visualization, Git integration, and an interactive TUI mode.

### Key Differentiators vs tolaria

| Dimension | tolaria | VaultPilot |
|-----------|---------|------------|
| Interface | Desktop GUI (Tauri) | Terminal CLI + TUI |
| Dependencies | Node.js + Rust + pnpm | Python 3.8+ stdlib |
| Install | Download package | pip install |
| Search | Basic | TF-IDF with Chinese n-gram |
| Links | One-way | Bidirectional with backlinks |
| Graph | None | ASCII knowledge graph |
| Size | ~100MB+ | ~200KB |
| Target | General users | Developers / terminal users |

## ✨ Core Features

- **📦 Zero Dependencies** — Core uses only Python stdlib, `rich` is optional
- **🔍 TF-IDF Search** — Self-implemented full-text search with Chinese n-gram support
- **🔗 Bidirectional Links** — `[[wiki-links]]` auto-resolution with backlink indexing
- **🗺️ Knowledge Graph** — ASCII visualization of note relationships
- **📝 Note Management** — Full CRUD with YAML frontmatter metadata
- **🏷️ Tag System** — Flexible categorization and filtering
- **📊 Statistics Dashboard** — Multi-dimensional knowledge base analytics
- **🔄 Git Integration** — Built-in version control (commit/push/pull)
- **📥 Import/Export** — Bulk Markdown import, JSON/HTML export
- **🖥️ TUI Mode** — Interactive curses-based terminal interface
- **🌍 i18n** — Bilingual Chinese/English interface

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/gitstq/VaultPilot.git
cd VaultPilot
pip install -e .

# Three steps to get started
vault init ./my-vault
vault new "Welcome to VaultPilot"
vault tui
```

## 📖 Usage Guide

### Note Operations

```bash
vault new "Python Learning Notes"
vault list --tag "python"
vault show "Python Learning Notes"
vault edit "Python Learning Notes"
vault delete "Python Learning Notes"
```

### Full-Text Search

```bash
vault search "machine learning algorithms"
vault search "API design" --tag "architecture"
vault search "database optimization" --context 3
```

### Bidirectional Links

Use `[[Note Title]]` in your notes to create links:

```markdown
# System Design

Today we reviewed [[API Gateway Design]] and [[Database Optimization]].

See [[Microservices Architecture]] for the overall architecture.
```

### Tag Management

```bash
vault tag add "Python Learning Notes" python tutorial
vault tag remove "Python Learning Notes" tutorial
vault tag list
vault tag show python
```

### Knowledge Graph

```bash
vault graph
vault graph --tag "architecture"
vault graph --depth 2
```

### Git Integration

```bash
vault git init
vault git status
vault git commit -m "update notes"
vault git push
vault git pull
vault git log --limit 10
```

### Interactive TUI

```bash
vault tui

# Shortcuts:
# j/k or Up/Down: Navigate
# Enter: View note
# e: Edit note
# n: New note
# /: Search
# g: Graph
# s: Stats
# q: Quit
```

## 💡 Design Philosophy & Roadmap

### Design Principles

1. **Files-first** — Notes are files, zero lock-in
2. **Terminal-first** — Optimized for keyboard users
3. **Zero dependencies** — Core uses only stdlib
4. **Progressive enhancement** — `rich` optional

### Roadmap

- [x] v1.0.0 — Core features (CRUD, search, links, graph, Git)
- [ ] v1.1.0 — Plugin system, template engine
- [ ] v1.2.0 — MCP protocol support, AI Agent integration
- [ ] v2.0.0 — Web UI, multi-user collaboration

## 📦 Build & Deploy

```bash
make install      # Install
make test         # Run tests
make clean        # Clean
make build        # Build sdist
```

### Requirements

- Python 3.8+
- Optional: `rich` (terminal beautification)
- Optional: `git` (version control)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

Please follow the [Angular Commit Convention](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit).

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🎉 プロジェクト紹介

**VaultPilot** は、軽量で外部依存なしのターミナル Markdown 知識ベース管理エンジンです。GitHub Trending プロジェクト [tolaria](https://github.com/refactoringhq/tolaria) にインスパイアされ、純粋なターミナル環境に特化して開発者に効率的な知識管理体験を提供します。

ノートはプレーン Markdown ファイルとして保存され、完全にあなたの管理下に置かれます。TF-IDF 全文検索、双方向 Wiki リンク、ASCII 知識グラフ、Git バージョン管理、インタラクティブ TUI モードなどの機能を備えています。

## ✨ 主な機能

- **📦 ゼロ依存** — Python 標準ライブラリのみ使用
- **🔍 TF-IDF 検索** — 中国語 n-gram サポート付き全文検索
- **🔗 双方向リンク** — `[[wiki-links]]` 自動解決とバックリンク
- **🗺️ 知識グラフ** — ASCII ビジュアライゼーション
- **📝 ノート管理** — CRUD + YAML frontmatter
- **🏷️ タグシステム** — 柔軟な分類とフィルタリング
- **📊 統計ダッシュボード** — 多次元分析
- **🔄 Git 統合** — コミット/プッシュ/プル
- **🖥️ TUI モード** — curses ベースのインタラクティブ UI

## 🚀 クイックスタート

```bash
git clone https://github.com/gitstq/VaultPilot.git
cd VaultPilot
pip install -e .

vault init ./my-vault
vault new "VaultPilot へようこそ"
vault tui
```

## 📄 ライセンス

[MIT License](LICENSE) の下でオープンソースとして公開されています。
