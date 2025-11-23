"""
VideoClip 安装配置
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# 读取requirements文件
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="videoclip",
    version="1.0.0",
    description="智能视频剪辑工具 - 从 YouTube 视频中提取精彩片段",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="VideoClip Team",
    packages=find_packages(exclude=["tests", "scripts"]),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "videoclip=videoclip.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

