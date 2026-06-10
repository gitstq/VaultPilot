"""Git 集成管理 - 知识库版本控制

封装 Git 命令，为知识库提供版本管理功能。
通过 subprocess 调用系统 Git 命令。
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple


class GitManager:
    """Git 版本控制管理器

    封装常用的 Git 操作，提供统一的接口管理知识库的版本控制。

    Attributes:
        vault_path: 知识库根目录路径
        _git_dir: .git 目录路径
    """

    def __init__(self, vault_path: str) -> None:
        """初始化 Git 管理器

        Args:
            vault_path: 知识库根目录路径
        """
        self.vault_path: str = os.path.abspath(vault_path)
        self._git_dir: str = os.path.join(self.vault_path, ".git")

    def is_git_initialized(self) -> bool:
        """检查知识库是否已初始化 Git 仓库

        Returns:
            是否已初始化 Git
        """
        return os.path.isdir(self._git_dir)

    def init(self) -> Tuple[bool, str]:
        """初始化 Git 仓库

        Returns:
            元组 (是否成功, 输出信息)
        """
        if self.is_git_initialized():
            return True, "Git 仓库已存在"

        return self._run_git(["init"])

    def add(self, paths: Optional[List[str]] = None) -> Tuple[bool, str]:
        """添加文件到暂存区

        Args:
            paths: 文件路径列表，为 None 时添加所有文件

        Returns:
            元组 (是否成功, 输出信息)
        """
        if paths:
            args = ["add"] + paths
        else:
            args = ["add", "-A"]
        return self._run_git(args)

    def commit(self, message: str = "auto commit") -> Tuple[bool, str]:
        """提交更改

        Args:
            message: 提交信息

        Returns:
            元组 (是否成功, 输出信息)
        """
        return self._run_git(["commit", "-m", message])

    def status(self) -> Tuple[bool, str]:
        """查看仓库状态

        Returns:
            元组 (是否成功, 状态信息)
        """
        return self._run_git(["status", "--short"])

    def log(self, count: int = 10) -> Tuple[bool, str]:
        """查看提交日志

        Args:
            count: 显示的提交数量

        Returns:
            元组 (是否成功, 日志信息)
        """
        return self._run_git([
            "log",
            f"--max-count={count}",
            "--pretty=format:%h %ad %s",
            "--date=short",
        ])

    def push(self, remote: str = "origin", branch: str = "main") -> Tuple[bool, str]:
        """推送到远程仓库

        Args:
            remote: 远程仓库名称
            branch: 分支名称

        Returns:
            元组 (是否成功, 输出信息)
        """
        return self._run_git(["push", remote, branch])

    def pull(self, remote: str = "origin", branch: str = "main") -> Tuple[bool, str]:
        """从远程仓库拉取

        Args:
            remote: 远程仓库名称
            branch: 分支名称

        Returns:
            元组 (是否成功, 输出信息)
        """
        return self._run_git(["pull", remote, branch])

    def diff(self) -> Tuple[bool, str]:
        """查看未暂存的更改

        Returns:
            元组 (是否成功, diff 信息)
        """
        return self._run_git(["diff", "--stat"])

    def add_remote(self, name: str, url: str) -> Tuple[bool, str]:
        """添加远程仓库

        Args:
            name: 远程仓库名称
            url: 远程仓库 URL

        Returns:
            元组 (是否成功, 输出信息)
        """
        return self._run_git(["remote", "add", name, url])

    def get_current_branch(self) -> str:
        """获取当前分支名称

        Returns:
            当前分支名称，失败返回空字符串
        """
        success, output = self._run_git(["branch", "--show-current"])
        if success:
            return output.strip()
        return ""

    def get_remotes(self) -> List[Dict[str, str]]:
        """获取远程仓库列表

        Returns:
            远程仓库信息列表
        """
        success, output = self._run_git(["remote", "-v"])
        if not success:
            return []

        remotes: List[Dict[str, str]] = {}
        for line in output.strip().split("\n"):
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    name = parts[0]
                    url = parts[1]
                    remote_type = parts[2].strip("()") if len(parts) >= 3 else ""
                    if name not in remotes:
                        remotes[name] = {"name": name, "url": url, "type": remote_type}

        return list(remotes.values())

    def auto_commit(self, message: Optional[str] = None) -> Tuple[bool, str]:
        """自动提交所有更改

        添加所有文件并提交，如果没有更改则跳过。

        Args:
            message: 提交信息，为 None 时自动生成

        Returns:
            元组 (是否成功, 输出信息)
        """
        if not message:
            import datetime
            message = f"vault auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # 检查是否有更改
        success, status = self.status()
        if not success:
            return False, status

        if not status.strip():
            return True, "没有需要提交的更改"

        # 添加并提交
        success, output = self.add()
        if not success:
            return False, output

        return self.commit(message)

    def _run_git(self, args: List[str]) -> Tuple[bool, str]:
        """执行 Git 命令

        Args:
            args: Git 命令参数列表

        Returns:
            元组 (是否成功, 命令输出)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                return True, output
            else:
                error = result.stderr.strip()
                return False, error or output
        except FileNotFoundError:
            return False, "Git 未安装，请先安装 Git"
        except subprocess.TimeoutExpired:
            return False, "Git 命令执行超时"
        except OSError as e:
            return False, f"Git 命令执行失败: {e}"
