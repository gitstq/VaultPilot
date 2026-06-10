"""配置管理模块 - 管理知识库和用户配置

支持全局配置和知识库级别配置，使用 JSON 格式存储。
配置文件优先级：知识库配置 > 全局配置 > 默认配置。
"""

import json
import os
from typing import Any, Dict, Optional


class Config:
    """配置管理器

    管理全局配置 (~/.vaultpilot/config.json) 和知识库级别配置 (.vault/config.json)。
    支持配置的读取、写入和合并操作。

    Attributes:
        global_config_path: 全局配置文件路径
        vault_config_path: 知识库配置文件路径
        _global_config: 全局配置缓存
        _vault_config: 知识库配置缓存
        _defaults: 默认配置值
    """

    _defaults: Dict[str, Any] = {
        "editor": "",
        "theme": "default",
        "default_tags": [],
        "filename_template": "{title}.md",
        "auto_index": True,
        "search_min_length": 2,
        "graph_max_nodes": 50,
        "trash_dir": ".vault/trash",
        "export_format": "json",
        "git_auto_commit": False,
        "tui_keybindings": {
            "quit": "q",
            "help": "?",
            "up": "k",
            "down": "j",
            "open": "Enter",
            "search": "/",
            "back": "Escape",
            "delete": "d",
            "edit": "e",
            "new": "n",
            "tag": "t",
        },
    }

    def __init__(self, vault_path: Optional[str] = None) -> None:
        """初始化配置管理器

        Args:
            vault_path: 知识库根目录路径，为 None 时仅使用全局配置
        """
        self.global_config_path: str = os.path.expanduser("~/.vaultpilot/config.json")
        self.vault_config_path: str = ""
        self._global_config: Dict[str, Any] = {}
        self._vault_config: Dict[str, Any] = {}

        if vault_path:
            self.vault_config_path = os.path.join(vault_path, ".vault", "config.json")

        self._load_configs()

    def _load_configs(self) -> None:
        """从磁盘加载配置文件

        依次尝试加载全局配置和知识库配置，加载失败时使用空字典。
        """
        self._global_config = self._load_json_file(self.global_config_path)
        if self.vault_config_path:
            self._vault_config = self._load_json_file(self.vault_config_path)

    @staticmethod
    def _load_json_file(path: str) -> Dict[str, Any]:
        """从 JSON 文件加载配置

        Args:
            path: JSON 文件路径

        Returns:
            解析后的字典，文件不存在或解析失败时返回空字典
        """
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"[警告] 加载配置文件失败 {path}: {e}")
            return {}

    @staticmethod
    def _save_json_file(path: str, data: Dict[str, Any]) -> None:
        """将配置保存到 JSON 文件

        Args:
            path: JSON 文件路径
            data: 要保存的配置数据
        """
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            print(f"[错误] 保存配置文件失败 {path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        按照知识库配置 > 全局配置 > 默认配置的优先级查找。

        Args:
            key: 配置键名，支持点号分隔的嵌套键（如 'tui_keybindings.quit'）
            default: 所有层级都未找到时的默认值

        Returns:
            找到的配置值
        """
        if "." in key:
            parts = key.split(".")
            return self._get_nested(parts)

        if key in self._vault_config:
            return self._vault_config[key]
        if key in self._global_config:
            return self._global_config[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    def _get_nested(self, parts: list) -> Any:
        """获取嵌套配置值

        Args:
            parts: 配置键的各层级名称列表

        Returns:
            找到的嵌套配置值，未找到返回 None
        """
        for source in (self._vault_config, self._global_config, self._defaults):
            value = source
            found = True
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    found = False
                    break
            if found:
                return value
        return None

    def set(self, key: str, value: Any, scope: str = "vault") -> None:
        """设置配置值

        Args:
            key: 配置键名
            value: 配置值
            scope: 配置作用域，'vault' 为知识库级别，'global' 为全局级别

        Raises:
            ValueError: 作用域参数不合法时抛出
        """
        if scope not in ("vault", "global"):
            raise ValueError(f"无效的配置作用域: {scope}，必须是 'vault' 或 'global'")

        if scope == "vault":
            self._vault_config[key] = value
            if self.vault_config_path:
                self._save_json_file(self.vault_config_path, self._vault_config)
        else:
            self._global_config[key] = value
            self._save_json_file(self.global_config_path, self._global_config)

    def get_all(self) -> Dict[str, Any]:
        """获取合并后的完整配置

        将默认配置、全局配置和知识库配置合并返回。
        知识库配置优先级最高。

        Returns:
            合并后的完整配置字典
        """
        result: Dict[str, Any] = {}
        result.update(self._defaults)
        self._deep_merge(result, self._global_config)
        self._deep_merge(result, self._vault_config)
        return result

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """深度合并两个字典

        override 中的值会覆盖 base 中的同名键，嵌套字典递归合并。

        Args:
            base: 基础字典（会被原地修改）
            override: 覆盖字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    def save_vault_config(self) -> None:
        """保存知识库级别配置到磁盘"""
        if self.vault_config_path:
            self._save_json_file(self.vault_config_path, self._vault_config)

    def save_global_config(self) -> None:
        """保存全局配置到磁盘"""
        self._save_json_file(self.global_config_path, self._global_config)
