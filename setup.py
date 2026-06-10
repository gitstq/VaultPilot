"""VaultPilot - 轻量级终端 Markdown 知识库管理引擎"""

from setuptools import setup, find_packages

setup(
    name="vaultpilot",
    version="0.1.0",
    description="轻量级终端 Markdown 知识库管理引擎",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="VaultPilot Team",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "rich": ["rich>=13.0.0"],
    },
    entry_points={
        "console_scripts": [
            "vault=vaultpilot.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
)
