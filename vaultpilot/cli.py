"""VaultPilot CLI 入口 - 命令行界面

解析命令行参数，调用对应的知识库管理功能。
支持子命令模式：vault <command> [args]。
"""

import argparse
import os
import sys
from typing import List, Optional

from vaultpilot import __version__
from vaultpilot.utils.output import OutputFormatter


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 主入口函数

    解析命令行参数并执行对应的命令。

    Args:
        argv: 命令行参数列表，为 None 时使用 sys.argv[1:]

    Returns:
        退出码（0 成功，非 0 失败）
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"VaultPilot v{__version__}")
        return 0

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n操作已取消")
        return 130
    except Exception as e:
        output = OutputFormatter()
        output.error(str(e))
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器

    Returns:
        配置好的 ArgumentParser 实例
    """
    parser = argparse.ArgumentParser(
        prog="vault",
        description="VaultPilot - 轻量级终端 Markdown 知识库管理引擎",
        epilog="使用 'vault <command> --help' 查看各命令的详细帮助",
    )

    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="显示版本号",
    )

    # 全局可选参数
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色输出",
    )

    parser.add_argument(
        "--vault-path", "-p",
        type=str,
        default=None,
        help="指定知识库路径（默认为当前目录）",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ========== vault init ==========
    init_parser = subparsers.add_parser("init", help="初始化新的知识库")
    init_parser.set_defaults(func=cmd_init)
    init_parser.add_argument("path", nargs="?", default=".", help="知识库路径")

    # ========== vault new ==========
    new_parser = subparsers.add_parser("new", help="创建新笔记")
    new_parser.set_defaults(func=cmd_new)
    new_parser.add_argument("title", help="笔记标题")
    new_parser.add_argument("--tag", "-t", action="append", default=[], help="标签")
    new_parser.add_argument("--no-edit", action="store_true", help="不打开编辑器")

    # ========== vault edit ==========
    edit_parser = subparsers.add_parser("edit", help="编辑笔记")
    edit_parser.set_defaults(func=cmd_edit)
    edit_parser.add_argument("identifier", help="笔记 ID 或标题")

    # ========== vault delete ==========
    delete_parser = subparsers.add_parser("delete", help="删除笔记（移到回收站）")
    delete_parser.set_defaults(func=cmd_delete)
    delete_parser.add_argument("identifier", help="笔记 ID 或标题")
    delete_parser.add_argument("--force", "-f", action="store_true", help="不确认直接删除")

    # ========== vault list ==========
    list_parser = subparsers.add_parser("list", help="列出所有笔记")
    list_parser.set_defaults(func=cmd_list)
    list_parser.add_argument("--tag", "-t", type=str, default=None, help="按标签过滤")
    list_parser.add_argument("--sort", "-s", type=str, default="updated",
                             choices=["title", "created", "updated", "word_count"],
                             help="排序字段")
    list_parser.add_argument("--limit", "-n", type=int, default=50, help="最大数量")
    list_parser.add_argument("--all", "-a", action="store_true", help="显示所有笔记")

    # ========== vault show ==========
    show_parser = subparsers.add_parser("show", help="查看笔记详情")
    show_parser.set_defaults(func=cmd_show)
    show_parser.add_argument("identifier", help="笔记 ID 或标题")

    # ========== vault search ==========
    search_parser = subparsers.add_parser("search", help="全文搜索笔记")
    search_parser.set_defaults(func=cmd_search)
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("--limit", "-n", type=int, default=20, help="最大结果数")

    # ========== vault tag ==========
    tag_parser = subparsers.add_parser("tag", help="标签管理")
    tag_parser.set_defaults(func=cmd_tag)
    tag_subparsers = tag_parser.add_subparsers(dest="tag_command")

    tag_add = tag_subparsers.add_parser("add", help="添加标签")
    tag_add.add_argument("identifier", help="笔记 ID 或标题")
    tag_add.add_argument("tag", help="标签名称")

    tag_remove = tag_subparsers.add_parser("remove", help="移除标签")
    tag_remove.add_argument("identifier", help="笔记 ID 或标题")
    tag_remove.add_argument("tag", help="标签名称")

    tag_list = tag_subparsers.add_parser("list", help="列出所有标签")

    # ========== vault graph ==========
    graph_parser = subparsers.add_parser("graph", help="显示知识图谱")
    graph_parser.set_defaults(func=cmd_graph)
    graph_parser.add_argument("--mermaid", action="store_true", help="输出 Mermaid 格式")

    # ========== vault stats ==========
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    stats_parser.set_defaults(func=cmd_stats)

    # ========== vault import ==========
    import_parser = subparsers.add_parser("import", help="导入 Markdown 文件")
    import_parser.set_defaults(func=cmd_import)
    import_parser.add_argument("source", help="源目录路径")
    import_parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    import_parser.add_argument("--no-attachments", action="store_true", help="不复制附件")

    # ========== vault export ==========
    export_parser = subparsers.add_parser("export", help="导出笔记")
    export_parser.set_defaults(func=cmd_export)
    export_parser.add_argument("output", help="输出文件路径")
    export_parser.add_argument("--format", "-f", type=str, default="json",
                               choices=["json", "html"], help="导出格式")

    # ========== vault git ==========
    git_parser = subparsers.add_parser("git", help="Git 版本管理")
    git_parser.set_defaults(func=cmd_git)
    git_subparsers = git_parser.add_subparsers(dest="git_command")

    git_init = git_subparsers.add_parser("init", help="初始化 Git 仓库")
    git_commit = git_subparsers.add_parser("commit", help="提交更改")
    git_commit.add_argument("-m", "--message", type=str, default="auto commit", help="提交信息")
    git_push = git_subparsers.add_parser("push", help="推送到远程")
    git_pull = git_subparsers.add_parser("pull", help="从远程拉取")
    git_log = git_subparsers.add_parser("log", help="查看提交日志")
    git_log.add_argument("-n", "--count", type=int, default=10, help="显示数量")
    git_status = git_subparsers.add_parser("status", help="查看状态")
    git_auto = git_subparsers.add_parser("auto", help="自动提交所有更改")

    # ========== vault tui ==========
    tui_parser = subparsers.add_parser("tui", help="交互式终端界面")
    tui_parser.set_defaults(func=cmd_tui)
    tui_parser.add_argument("--theme", type=str, default="default", help="主题名称")

    return parser


def _get_vault_path(args: argparse.Namespace) -> str:
    """获取知识库路径

    优先使用命令行参数指定的路径，其次使用环境变量，最后使用当前目录。

    Args:
        args: 命令行参数

    Returns:
        知识库路径
    """
    if hasattr(args, "vault_path") and args.vault_path:
        return args.vault_path
    env_path = os.environ.get("VAULT_PATH")
    if env_path:
        return env_path
    return "."


def _load_vault(args: argparse.Namespace):
    """加载知识库实例

    Args:
        args: 命令行参数

    Returns:
        Vault 实例
    """
    from vaultpilot.core.vault import Vault

    vault_path = _get_vault_path(args)
    return Vault(vault_path)


# ========== 命令处理函数 ==========

def cmd_init(args: argparse.Namespace) -> int:
    """处理 init 命令 - 初始化知识库

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    from vaultpilot.core.vault import Vault

    try:
        Vault.init(args.path)
        return 0
    except ValueError as e:
        output = OutputFormatter()
        output.error(str(e))
        return 1


def cmd_new(args: argparse.Namespace) -> int:
    """处理 new 命令 - 创建新笔记

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    vault.new_note(
        title=args.title,
        tags=args.tag if args.tag else None,
        open_editor=not args.no_edit,
    )
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    """处理 edit 命令 - 编辑笔记

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    note = vault.edit_note(args.identifier)
    if note is None:
        return 1
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """处理 delete 命令 - 删除笔记

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)

    if not args.force:
        note = vault.get_note(args.identifier)
        if note:
            confirm = input(f"确认删除 '{note.title}'? [y/N]: ").strip().lower()
            if confirm != "y":
                print("操作已取消")
                return 0

    if vault.delete_note(args.identifier):
        return 0
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    """处理 list 命令 - 列出笔记

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    limit = args.limit if not args.all else 10000
    notes = vault.list_notes(
        tag=args.tag,
        sort_by=args.sort,
        limit=limit,
    )

    if not notes:
        vault.output.info("没有找到笔记")
        return 0

    vault.output.title(f"笔记列表 ({len(notes)} 篇)")

    headers = ["#", "标题", "标签", "字数", "更新时间"]
    rows: list = []
    for i, note in enumerate(notes):
        tags = ", ".join(note.tags[:3]) if note.tags else "-"
        if len(note.tags) > 3:
            tags += f" +{len(note.tags) - 3}"
        rows.append([
            str(i + 1),
            note.title[:30],
            tags[:20],
            str(note.get_word_count()),
            note.updated.strftime("%Y-%m-%d"),
        ])

    vault.output.table(headers, rows)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """处理 show 命令 - 查看笔记详情

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    note = vault.show_note(args.identifier)
    if note is None:
        return 1
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """处理 search 命令 - 全文搜索

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    results = vault.search(args.query, limit=args.limit)

    if not results:
        vault.output.info(f"未找到匹配 '{args.query}' 的笔记")
        return 0

    vault.output.title(f"搜索结果: '{args.query}' ({len(results)} 条)")

    headers = ["#", "文件名", "相关度"]
    rows: list = []
    for i, (doc_id, score, filepath) in enumerate(results):
        # 获取笔记标题
        note = vault.get_note(doc_id)
        title = note.title if note else doc_id
        rows.append([
            str(i + 1),
            title[:40],
            f"{score:.2f}",
        ])

    vault.output.table(headers, rows)
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    """处理 tag 命令 - 标签管理

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)

    if args.tag_command == "add":
        if vault.add_tag(args.identifier, args.tag):
            return 0
        return 1

    elif args.tag_command == "remove":
        if vault.remove_tag(args.identifier, args.tag):
            return 0
        return 1

    elif args.tag_command == "list" or args.tag_command is None:
        tags = vault.list_tags()
        if not tags:
            vault.output.info("没有标签")
            return 0

        vault.output.title(f"标签列表 ({len(tags)} 个)")
        headers = ["标签", "使用次数"]
        rows = [[tag, str(count)] for tag, count in tags]
        vault.output.table(headers, rows)
        return 0

    else:
        vault.output.error(f"未知的标签命令: {args.tag_command}")
        return 1


def cmd_graph(args: argparse.Namespace) -> int:
    """处理 graph 命令 - 显示知识图谱

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)

    if args.mermaid:
        vault.output.title("知识图谱 (Mermaid)")
        vault._ensure_index()
        # 构建图谱数据
        note_titles = {}
        notes_data = []
        for note in vault._get_all_notes():
            note_id = note.get_filename()
            note_titles[note_id] = note.title
            notes_data.append((note_id, note.title, note.body))
        vault.link_indexer.build_index(notes_data)
        forward = {nid: vault.link_indexer.get_forward_links(nid) for nid in note_titles}
        back = {nid: vault.link_indexer.get_back_links(nid) for nid in note_titles}
        vault.knowledge_graph.build_from_indexer(forward, back, note_titles)
        print(vault.knowledge_graph.render_mermaid())
    else:
        graph_text = vault.show_graph()
        print(graph_text)

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """处理 stats 命令 - 显示统计信息

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    stats = vault.show_stats()

    vault.output.title("知识库统计")

    summary = stats["summary"]
    vault.output.key_value("总笔记数", str(summary["total_notes"]))
    vault.output.key_value("总字数", str(summary["total_words"]))
    vault.output.key_value("总字符数", str(summary["total_chars"]))
    vault.output.key_value("总行数", str(summary["total_lines"]))
    vault.output.key_value("平均字数/篇", str(summary["avg_words_per_note"]))

    vault.output.blank()
    vault.output.subtitle("标签统计")
    tags = stats["tags"]
    vault.output.key_value("标签总数", str(tags["total_unique_tags"]))
    vault.output.key_value("无标签笔记", str(tags["untagged_notes"]))
    if tags["top_tags"]:
        vault.output.print("  热门标签:")
        for tag, count in tags["top_tags"][:10]:
            vault.output.list_item(f"{tag} ({count})", indent=4)

    vault.output.blank()
    vault.output.subtitle("链接统计")
    links = stats["links"]
    vault.output.key_value("正向链接", str(links["total_links"]))
    vault.output.key_value("反向链接", str(links["total_backlinks"]))
    vault.output.key_value("孤立笔记", str(links["unlinked_notes"]))

    vault.output.blank()
    vault.output.subtitle("活跃度")
    activity = stats["activity"]
    vault.output.key_value("本周新增", str(activity["notes_this_week"]))
    vault.output.key_value("本月新增", str(activity["notes_this_month"]))

    longest = stats["longest_note"]
    if longest["title"]:
        vault.output.key_value("最长笔记", f"{longest['title']} ({longest['word_count']} 字)")

    # 磁盘占用
    size_stats = vault.stats_engine.get_size_stats()
    vault.output.blank()
    vault.output.subtitle("磁盘占用")
    vault.output.key_value("总大小", vault.stats_engine.format_size(size_stats["total"]))
    vault.output.key_value("笔记", vault.stats_engine.format_size(size_stats["notes"]))
    vault.output.key_value("元数据", vault.stats_engine.format_size(size_stats["meta"]))

    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """处理 import 命令 - 导入文件

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    vault.output.info(f"从 {args.source} 导入文件...")

    success, skipped, errors = vault.import_files(
        source_dir=args.source,
        copy_attachments=not args.no_attachments,
        overwrite=args.overwrite,
    )

    vault.output.success(f"导入完成: {success} 成功, {skipped} 跳过")
    for err in errors:
        vault.output.warning(err)

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """处理 export 命令 - 导出笔记

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    vault.output.info(f"导出笔记为 {args.format} 格式...")

    success, result = vault.export_notes(args.output, args.format)
    if success:
        vault.output.success(f"导出成功: {result}")
        return 0
    else:
        vault.output.error(f"导出失败: {result}")
        return 1


def cmd_git(args: argparse.Namespace) -> int:
    """处理 git 命令 - Git 版本管理

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault = _load_vault(args)
    git = vault.git_manager

    if args.git_command == "init":
        success, msg = git.init()
    elif args.git_command == "commit":
        success, msg = git.auto_commit(args.message)
    elif args.git_command == "push":
        success, msg = git.push()
    elif args.git_command == "pull":
        success, msg = git.pull()
    elif args.git_command == "log":
        success, msg = git.log(args.count if hasattr(args, "count") else 10)
    elif args.git_command == "status":
        success, msg = git.status()
    elif args.git_command == "auto":
        success, msg = git.auto_commit()
    else:
        vault.output.error(f"未知的 Git 命令: {args.git_command}")
        return 1

    if success:
        vault.output.success(msg)
    else:
        vault.output.error(msg)

    return 0 if success else 1


def cmd_tui(args: argparse.Namespace) -> int:
    """处理 tui 命令 - 启动交互式界面

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    vault_path = _get_vault_path(args)

    try:
        from vaultpilot.tui.app import TUIApp

        app = TUIApp(vault_path, theme_name=args.theme)
        app.run()
        return 0
    except ImportError as e:
        output = OutputFormatter()
        output.error(f"TUI 启动失败: {e}")
        return 1
    except Exception as e:
        output = OutputFormatter()
        output.error(f"TUI 运行错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
