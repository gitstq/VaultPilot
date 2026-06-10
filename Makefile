.PHONY: install dev test lint clean help

# 默认目标
all: help

# 安装到系统
install:
	pip install -e .

# 开发安装（含可选依赖）
dev:
	pip install -e ".[rich]"

# 运行测试
test:
	python -m pytest tests/ -v

# 快速测试
test-quick:
	python -m pytest tests/ -v --tb=short

# 运行单个测试文件
test-vault:
	python -m pytest tests/test_vault.py -v

test-note:
	python -m pytest tests/test_note.py -v

test-search:
	python -m pytest tests/test_search.py -v

test-frontmatter:
	python -m pytest tests/test_frontmatter.py -v

# 代码检查
lint:
	python -m flake8 vaultpilot/ tests/ || true

# 清理构建产物
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ 2>/dev/null || true

# 构建
build:
	python setup.py sdist bdist_wheel

# 帮助
help:
	@echo "VaultPilot Makefile"
	@echo ""
	@echo "可用命令:"
	@echo "  make install    - 安装到系统"
	@echo "  make dev        - 开发安装（含 rich）"
	@echo "  make test       - 运行所有测试"
	@echo "  make test-quick - 快速测试"
	@echo "  make lint       - 代码检查"
	@echo "  make clean      - 清理构建产物"
	@echo "  make build      - 构建"
	@echo "  make help       - 显示帮助"
